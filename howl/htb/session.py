"""HTB session state management for Howl."""

import uuid
import time
from dataclasses import dataclass, field
from enum import Enum

from howl.db import queries


class HtbMilestone(str, Enum):
    """Standard pentest milestones for HTB machines."""
    RECON = "recon"
    FOOTHOLD = "foothold"
    USER_SHELL = "user_shell"
    USER_FLAG = "user_flag"
    ROOT_SHELL = "root_shell"
    ROOT_FLAG = "root_flag"


MILESTONE_LABELS = {
    HtbMilestone.RECON: "Reconnaissance Complete",
    HtbMilestone.FOOTHOLD: "Initial Foothold Obtained",
    HtbMilestone.USER_SHELL: "User Shell Obtained",
    HtbMilestone.USER_FLAG: "User Flag Captured",
    HtbMilestone.ROOT_SHELL: "Root Shell Obtained",
    HtbMilestone.ROOT_FLAG: "Root Flag Captured",
}

MILESTONE_ORDER = [
    HtbMilestone.RECON,
    HtbMilestone.FOOTHOLD,
    HtbMilestone.USER_SHELL,
    HtbMilestone.USER_FLAG,
    HtbMilestone.ROOT_SHELL,
    HtbMilestone.ROOT_FLAG,
]


@dataclass
class HtbSession:
    """Manages the state of an HTB hacking session."""
    session_id: str
    machine_name: str
    machine_ip: str
    hostname: str | None = None
    start_time: float = 0.0
    completed: bool = False
    milestones: dict[str, float] = field(default_factory=dict)
    hints_used: int = 0
    nmap_results: str | None = None
    discovered_services: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, machine_ip: str, machine_name: str | None = None,
               hostname: str | None = None) -> "HtbSession":
        """Create a new HTB session."""
        session_id = str(uuid.uuid4())
        name = machine_name or f"HTB-{machine_ip.replace('.', '-')}"
        target_slug = f"htb:{name.lower().replace(' ', '-')}"

        queries.create_session(session_id, target_slug)
        queries.upsert_target_progress(
            slug=target_slug,
            difficulty="htb",
            status="in_progress",
        )

        return cls(
            session_id=session_id,
            machine_name=name,
            machine_ip=machine_ip,
            hostname=hostname,
            start_time=time.time(),
        )

    @classmethod
    def resume(cls, session_data: dict, machine_ip: str,
               hostname: str | None = None) -> "HtbSession":
        """Resume an existing HTB session from database."""
        slug = session_data["target_slug"]
        name = slug.replace("htb:", "").replace("-", " ").title()

        return cls(
            session_id=session_data["session_id"],
            machine_name=name,
            machine_ip=machine_ip,
            hostname=hostname,
            start_time=time.time() - session_data.get("time_elapsed_secs", 0),
        )

    @property
    def target_slug(self) -> str:
        return f"htb:{self.machine_name.lower().replace(' ', '-')}"

    @property
    def elapsed_seconds(self) -> int:
        return int(time.time() - self.start_time)

    @property
    def elapsed_formatted(self) -> str:
        secs = self.elapsed_seconds
        hours, remainder = divmod(secs, 3600)
        mins, secs = divmod(remainder, 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"

    @property
    def current_phase(self) -> str:
        """Determine current pentest phase based on milestones achieved."""
        if HtbMilestone.ROOT_FLAG.value in self.milestones:
            return "Complete"
        elif HtbMilestone.ROOT_SHELL.value in self.milestones:
            return "Post-Exploitation (Root)"
        elif HtbMilestone.USER_FLAG.value in self.milestones:
            return "Privilege Escalation"
        elif HtbMilestone.USER_SHELL.value in self.milestones:
            return "Post-Exploitation (User)"
        elif HtbMilestone.FOOTHOLD.value in self.milestones:
            return "Enumeration & Lateral Movement"
        elif HtbMilestone.RECON.value in self.milestones:
            return "Exploitation"
        else:
            return "Reconnaissance"

    def mark_milestone(self, milestone: HtbMilestone) -> bool:
        """Mark a milestone as achieved. Returns True if newly achieved."""
        if milestone.value in self.milestones:
            return False
        self.milestones[milestone.value] = time.time()

        if (HtbMilestone.ROOT_FLAG.value in self.milestones and
                HtbMilestone.USER_FLAG.value in self.milestones):
            self.completed = True

        queries.update_session(
            self.session_id,
            current_stage=len(self.milestones),
            time_elapsed_secs=self.elapsed_seconds,
        )
        return True

    def record_hint(self):
        """Record that a hint was used."""
        self.hints_used += 1
        queries.log_hint(self.session_id, 0, 1)

    def store_nmap_results(self, output: str, services: list[dict]):
        """Store nmap scan results for AI context."""
        self.nmap_results = output
        self.discovered_services = services

    def add_note(self, note: str):
        """Add a user note to the session."""
        self.notes.append(note)

    def finish(self):
        """Mark the session as complete."""
        self.completed = True
        queries.complete_session(self.session_id, 0, self.elapsed_seconds)
        queries.upsert_target_progress(
            slug=self.target_slug,
            difficulty="htb",
            status="completed",
            best_time_secs=self.elapsed_seconds,
        )

    def abort(self):
        """Abort the HTB session."""
        queries.update_session(
            self.session_id,
            status="abandoned",
            time_elapsed_secs=self.elapsed_seconds,
        )

    def pause(self):
        """Pause the HTB session."""
        queries.update_session(
            self.session_id,
            status="paused",
            time_elapsed_secs=self.elapsed_seconds,
        )
