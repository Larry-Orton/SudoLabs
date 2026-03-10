"""Claude API integration for the SudoLabs AI Helper.

Maintains a multi-turn conversation history so the AI remembers
everything the student has discussed, every command they've run,
and every flag they've captured during the current session.
"""

from sudolabs.config import get_api_key
from sudolabs.ai.prompts import SYSTEM_PROMPT, build_hint_prompt, build_chat_prompt
from sudolabs.ai.context import build_hint_context, build_session_summary
from sudolabs.engine.session import HuntSession
from sudolabs.ui.theme import console


# Maximum conversation history entries to keep (prevents token overflow)
MAX_HISTORY = 40


class AIHelper:
    """AI-powered hint and chat system using Anthropic Claude.

    Keeps a running conversation history so the AI has full context
    of everything the student has done and discussed.
    """

    def __init__(self):
        self._client = None
        self.conversation: list[dict] = []

    def _get_client(self):
        """Lazy-load the Anthropic client."""
        if self._client is None:
            api_key = get_api_key()
            if not api_key:
                return None
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                console.print("[red]Anthropic SDK not installed. Run: pip install anthropic[/red]")
                return None
        return self._client

    def is_available(self) -> bool:
        """Check if AI helper is available (API key set)."""
        return get_api_key() is not None

    # ------------------------------------------------------------------
    # Conversation memory management
    # ------------------------------------------------------------------

    def add_event(self, event_text: str):
        """Inject a session event into the conversation as context.

        Use this to notify the AI about important things that happened
        outside of direct ask/hint interactions, e.g.:
          - Flag captured
          - Stage advanced
          - Shell command + output
          - Target container started/stopped
        """
        self.conversation.append({
            "role": "user",
            "content": f"[SESSION EVENT] {event_text}",
        })
        self.conversation.append({
            "role": "assistant",
            "content": "Noted.",
        })
        self._trim_history()

    def add_command(self, cmd: str, output: str):
        """Record a shell command and its output into conversation memory."""
        truncated = output[:3000] if len(output) > 3000 else output
        self.conversation.append({
            "role": "user",
            "content": f"[SHELL COMMAND]\n$ {cmd}\n{truncated}",
        })
        self.conversation.append({
            "role": "assistant",
            "content": "Noted.",
        })
        self._trim_history()

    def _trim_history(self):
        """Keep conversation history under MAX_HISTORY entries."""
        if len(self.conversation) > MAX_HISTORY:
            # Keep the first 2 entries (initial context) and trim the middle
            self.conversation = self.conversation[-MAX_HISTORY:]

    def _build_messages(self, user_message: str) -> list[dict]:
        """Build the full messages array: history + new user message."""
        messages = list(self.conversation)
        messages.append({"role": "user", "content": user_message})
        return messages

    # ------------------------------------------------------------------
    # Static hints (no API needed)
    # ------------------------------------------------------------------

    def get_static_hint(self, session: HuntSession, level: int) -> str | None:
        """Get a pre-written static hint from the target definition."""
        stage = session.current_stage_obj
        if not stage:
            return None
        for hint in stage.hints:
            if hint.level == level:
                return hint.text
        return None

    # ------------------------------------------------------------------
    # AI-powered hint (with conversation memory)
    # ------------------------------------------------------------------

    def get_ai_hint(
        self,
        session: HuntSession,
        level: int,
        target_ip: str = "127.0.0.1",
        command_history: str | None = None,
    ) -> str | None:
        """Get an AI-generated hint using the Claude API.

        The hint request is appended to the conversation history
        so the AI remembers it for future interactions.
        """
        client = self._get_client()
        if not client:
            return None

        context = build_hint_context(session, level, target_ip=target_ip)
        context["command_history"] = command_history
        user_message = build_hint_prompt(**context)

        messages = self._build_messages(user_message)

        try:
            # Build system prompt with live session summary
            system = SYSTEM_PROMPT + "\n\n" + build_session_summary(session, target_ip)

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                system=system,
                messages=messages,
            )
            reply = response.content[0].text

            # Store in conversation memory
            self.conversation.append({"role": "user", "content": user_message})
            self.conversation.append({"role": "assistant", "content": reply})
            self._trim_history()

            return reply
        except Exception as e:
            console.print(f"[red]AI Helper error: {e}[/red]")
            return None

    def get_hint(
        self,
        session: HuntSession,
        level: int = 1,
        target_ip: str = "127.0.0.1",
        command_history: str | None = None,
    ) -> tuple[str, str]:
        """Get a hint, preferring static then falling back to AI.

        Returns:
            Tuple of (hint_text, source) where source is 'static' or 'ai'.
        """
        static = self.get_static_hint(session, level)
        if static:
            static = (
                static
                .replace("<target_ip>", target_ip)
                .replace("<ip>", target_ip)
                .replace("<target>", target_ip)
            )
            # Record the static hint in conversation memory too
            self.add_event(f"Student requested hint L{level}. Static hint given: {static}")
            return static, "static"

        if self.is_available():
            ai_hint = self.get_ai_hint(session, level, target_ip=target_ip, command_history=command_history)
            if ai_hint:
                return ai_hint, "ai"

        return "No hint available for this level. Try a different level or check the target briefing.", "none"

    # ------------------------------------------------------------------
    # Free-form chat (with conversation memory)
    # ------------------------------------------------------------------

    def chat(
        self,
        session: HuntSession,
        question: str,
        target_ip: str = "127.0.0.1",
        command_history: str | None = None,
    ) -> str:
        """Free-form chat with the AI helper.

        Maintains full conversation context so the student can have
        a multi-turn dialogue about their approach.
        """
        client = self._get_client()
        if not client:
            return "AI Helper is not available. Set your Anthropic API key with: sudolabs config --set-api-key"

        stage = session.current_stage_obj
        target_ports = [
            {"name": svc.name, "port": svc.port, "protocol": svc.protocol}
            for svc in session.target.services
        ]
        user_message = build_chat_prompt(
            target_name=session.target.name,
            current_stage=stage.name if stage else "Unknown",
            stage_description=stage.description if stage else "",
            user_question=question,
            target_ip=target_ip,
            target_ports=target_ports,
            tools_suggested=stage.tools_suggested if stage else [],
            command_history=command_history,
        )

        messages = self._build_messages(user_message)

        try:
            system = SYSTEM_PROMPT + "\n\n" + build_session_summary(session, target_ip)

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                system=system,
                messages=messages,
            )
            reply = response.content[0].text

            # Store in conversation memory
            self.conversation.append({"role": "user", "content": user_message})
            self.conversation.append({"role": "assistant", "content": reply})
            self._trim_history()

            return reply
        except Exception as e:
            return f"AI Helper error: {e}"
