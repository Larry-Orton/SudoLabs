"""Smart note-taking system for SudoLabs.

Provides AI-enhanced note formatting, per-target markdown files,
a global pentest playbook, and automatic event-driven notes.
"""

from datetime import datetime
from pathlib import Path

from rich.prompt import Prompt

from sudolabs.config import (
    SUDOLABS_HOME,
    get_notes_dir,
    set_notes_dir,
    get_auto_notes,
)
from sudolabs.db import queries
from sudolabs.ui.theme import console


# ---------------------------------------------------------------------------
# Auto-note templates (no API calls — instant, free)
# ---------------------------------------------------------------------------

AUTO_NOTE_TEMPLATES = {
    "flag_captured": (
        "## [auto] Flag Captured: {stage_name}\n"
        "- Points: {points} | Time: {elapsed} | Hints: {hints}\n"
    ),
    "stage_advanced": (
        "## [auto] Stage Advanced: {stage_name}\n"
        "- Stage {stage_num}/{total_stages} | Elapsed: {elapsed}\n"
    ),
    "nmap_services": (
        "## [auto] Nmap Scan Results\n"
        "- Scan: {scan_type} | Ports: {port_list}\n"
    ),
    "hint_used": (
        "## [auto] Hint Used (Level {level})\n"
        "- Phase: {phase}\n"
    ),
    "milestone_reached": (
        "## [auto] Milestone: {milestone_name}\n"
        "- Time: {elapsed}\n"
    ),
    "session_started": (
        "# {target_name}\n"
        "> **Target:** {target_ip} | **Difficulty:** {difficulty}\n"
        "> **Session:** {session_id} | **Started:** {timestamp}\n"
        "\n---\n"
    ),
}

# ---------------------------------------------------------------------------
# AI prompt for note formatting
# ---------------------------------------------------------------------------

NOTE_FORMAT_PROMPT = """You are a cybersecurity note-taking assistant integrated into a penetration testing lab. The user has jotted down a quick observation during an active hacking session.

Your job:
1. ENHANCE the note with proper technical terminology and structure
2. PRESERVE the user's core observation — do not invent findings they did not mention
3. FORMAT as a concise markdown section with a ## heading and bullet points
4. If the note describes a REUSABLE technique (not specific to one target), extract a PLAYBOOK entry

TARGET CONTEXT:
- Target: {target_name}
- IP: {target_ip}
- Current Phase: {stage_name}
- Difficulty: {difficulty}
- Time Elapsed: {elapsed}

USER'S RAW NOTE: {raw_text}

Respond in EXACTLY this format:
---NOTE---
## <descriptive heading>
- <enhanced bullet points>
- <add relevant technical context>

> *Original: "{raw_text}"*
---PLAYBOOK---
## <technique category> - <technique name>
- **Technique:** <brief description>
- **When to use:** <applicable scenarios>
---END---

If no reusable technique applies, put NONE between the PLAYBOOK markers.
Keep the note under 8 lines and the playbook entry under 5 lines. Be concise."""


# ---------------------------------------------------------------------------
# Helper: resolve notes directory
# ---------------------------------------------------------------------------

def _resolve_notes_dir() -> Path:
    """Get or prompt for the notes directory, saving the choice to config."""
    configured = get_notes_dir()
    if configured:
        return Path(configured)

    default = str(SUDOLABS_HOME / "notes")
    console.print()
    choice = Prompt.ask(
        "  [bold]Where should notes be saved?[/bold]",
        default=default,
    )
    path = Path(choice.strip()) if choice.strip() else Path(default)
    set_notes_dir(str(path))
    return path


def get_auto_notes_enabled() -> bool:
    """Check if auto-notes are enabled."""
    return get_auto_notes()


# ---------------------------------------------------------------------------
# NoteManager
# ---------------------------------------------------------------------------

class NoteManager:
    """Manages per-target notes and the global pentest playbook.

    Instantiate once per hunt loop.  Handles:
    - AI-enhanced user notes
    - Template-based auto-notes (no API calls)
    - Persisting notes to DB and .md files
    - Global playbook extraction
    """

    def __init__(
        self,
        session_id: str,
        target_slug: str,
        target_name: str,
        target_ip: str,
        difficulty: str,
        ai=None,
    ):
        self.session_id = session_id
        self.target_slug = target_slug
        self.target_name = target_name
        self.target_ip = target_ip
        self.difficulty = difficulty
        self.ai = ai  # AIHelper instance (can be None)

        self.notes_dir = _resolve_notes_dir()
        safe_slug = target_slug.replace(":", "-").replace(" ", "-")
        self.target_file = self.notes_dir / f"{safe_slug}.md"
        self.playbook_file = self.notes_dir / "playbook.md"

        self._ensure_files()

    # ── File initialization ────────────────────────────────

    def _ensure_files(self):
        """Create the notes directory and initialize files if needed."""
        self.notes_dir.mkdir(parents=True, exist_ok=True)

        # Initialize target notes file with header
        if not self.target_file.exists():
            header = AUTO_NOTE_TEMPLATES["session_started"].format(
                target_name=self.target_name,
                target_ip=self.target_ip,
                difficulty=self.difficulty,
                session_id=self.session_id[:8],
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            )
            self.target_file.write_text(header, encoding="utf-8")

        # Initialize playbook if it doesn't exist
        if not self.playbook_file.exists():
            self.playbook_file.write_text(
                "# SudoLabs Pentest Playbook\n"
                "*Reusable techniques extracted from your hunts.*\n\n---\n\n",
                encoding="utf-8",
            )

    # ── User notes (AI-enhanced) ───────────────────────────

    def add_user_note(self, raw_text: str, stage_name: str, elapsed: str) -> str:
        """Add a user note, optionally AI-enhanced.

        Returns the formatted note text for display.
        """
        formatted = raw_text
        playbook_entry = None

        # Try AI formatting if available
        if self.ai and self.ai.is_available():
            try:
                formatted, playbook_entry = self._ai_format_note(
                    raw_text, stage_name, elapsed
                )
            except Exception:
                formatted = f"## Note\n- {raw_text}\n"

        else:
            formatted = f"## Note\n- {raw_text}\n"

        # Save to .md file
        self._append_to_target_file(formatted)

        # Save playbook entry if extracted
        if playbook_entry:
            self._append_to_playbook(playbook_entry)

        # Save to DB
        self._save_to_db(raw_text, formatted, "user", stage_name)

        return formatted

    # ── Auto-notes (template-based, no API) ────────────────

    def add_auto_note(self, template_key: str, **kwargs):
        """Add a template-based auto-note (no API call)."""
        if not get_auto_notes():
            return

        template = AUTO_NOTE_TEMPLATES.get(template_key)
        if not template:
            return

        try:
            text = template.format(**kwargs)
        except KeyError:
            return

        self._append_to_target_file(text)

        stage_name = kwargs.get("stage_name", kwargs.get("phase", ""))
        self._save_to_db(text.strip(), text.strip(), "auto", stage_name)

    # ── Read notes ─────────────────────────────────────────

    def get_session_notes(self) -> list[dict]:
        """Get all notes for the current session from the DB."""
        return queries.get_session_notes(self.session_id)

    # ── AI formatting ──────────────────────────────────────

    def _ai_format_note(
        self, raw_text: str, stage_name: str, elapsed: str
    ) -> tuple[str, str | None]:
        """Use Claude to enhance a note and optionally extract a playbook entry.

        This is a SEPARATE API call that does NOT pollute the
        hint/ask conversation history.

        Returns (formatted_note, playbook_entry_or_none).
        """
        client = self.ai._get_client()
        if not client:
            return f"## Note\n- {raw_text}\n", None

        prompt = NOTE_FORMAT_PROMPT.format(
            target_name=self.target_name,
            target_ip=self.target_ip,
            stage_name=stage_name,
            difficulty=self.difficulty,
            elapsed=elapsed,
            raw_text=raw_text,
        )

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            system="You are a concise cybersecurity note-taking assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        reply = response.content[0].text

        # Parse the structured response
        formatted = raw_text
        playbook = None

        if "---NOTE---" in reply and "---END---" in reply:
            parts = reply.split("---NOTE---")
            if len(parts) > 1:
                rest = parts[1]
                if "---PLAYBOOK---" in rest:
                    note_part, pb_part = rest.split("---PLAYBOOK---", 1)
                    formatted = note_part.strip()

                    pb_text = pb_part.replace("---END---", "").strip()
                    if pb_text and pb_text.upper() != "NONE":
                        playbook = pb_text
                else:
                    formatted = rest.replace("---END---", "").strip()
        else:
            # Fallback: use the entire reply as the note
            formatted = reply.strip()

        return formatted, playbook

    # ── File I/O ───────────────────────────────────────────

    def _append_to_target_file(self, markdown_block: str):
        """Append a markdown block to the target notes file."""
        try:
            with open(self.target_file, "a", encoding="utf-8") as f:
                f.write(f"\n{markdown_block}\n\n---\n")
        except OSError:
            pass  # Silently fail on file write errors

    def _append_to_playbook(self, entry: str):
        """Append a technique entry to the global playbook."""
        try:
            source_line = (
                f"- *Source: {self.target_slug} "
                f"({datetime.now().strftime('%Y-%m-%d')})*"
            )
            with open(self.playbook_file, "a", encoding="utf-8") as f:
                f.write(f"\n{entry}\n{source_line}\n\n---\n")
        except OSError:
            pass

    def _save_to_db(
        self,
        raw_text: str,
        formatted_text: str,
        note_type: str,
        stage_name: str = "",
    ):
        """Persist a note to the database."""
        try:
            queries.save_note(
                session_id=self.session_id,
                target_slug=self.target_slug,
                raw_text=raw_text,
                formatted_text=formatted_text,
                note_type=note_type,
                stage_name=stage_name,
            )
        except Exception:
            pass  # Don't crash the hunt on DB errors
