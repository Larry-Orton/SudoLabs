"""Hunt session state machine for SudoLabs."""

import uuid
import time
from dataclasses import dataclass, field

from sudolabs.db import queries
from sudolabs.engine.flags import generate_session_flags, verify_flag
from sudolabs.scoring.engine import calculate_stage_score, calculate_hint_multiplier
from sudolabs.targets.models import Target


@dataclass
class HuntSession:
    """Manages the state of an active hunt."""
    session_id: str
    target: Target
    current_stage: int = 0
    flags: list[dict] = field(default_factory=list)
    hints_used: dict = field(default_factory=dict)  # stage_index -> {l1: count, l2: count, l3: count}
    start_time: float = 0.0
    total_score: int = 0
    completed: bool = False

    @classmethod
    def create(cls, target: Target) -> "HuntSession":
        """Create a new hunt session."""
        session_id = str(uuid.uuid4())
        flags = generate_session_flags(target.stage_count)

        # Create session in database
        queries.create_session(session_id, target.slug)

        # Update target progress
        queries.upsert_target_progress(
            slug=target.slug,
            difficulty=target.difficulty,
            status="in_progress",
        )

        return cls(
            session_id=session_id,
            target=target,
            flags=flags,
            start_time=time.time(),
        )

    @classmethod
    def resume(cls, session_data: dict, target: Target) -> "HuntSession":
        """Resume an existing session from database."""
        session = cls(
            session_id=session_data["session_id"],
            target=target,
            current_stage=session_data["current_stage"],
            start_time=time.time() - session_data.get("time_elapsed_secs", 0),
            total_score=session_data.get("total_score", 0),
        )
        # Regenerate flags for remaining stages
        session.flags = generate_session_flags(target.stage_count)
        return session

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
    def current_stage_obj(self):
        if self.current_stage < len(self.target.attack_chain):
            return self.target.attack_chain[self.current_stage]
        return None

    @property
    def is_final_stage(self) -> bool:
        return self.current_stage >= len(self.target.attack_chain) - 1

    def get_current_flag(self) -> str | None:
        """Get the plaintext flag for the current stage."""
        if self.current_stage < len(self.flags):
            return self.flags[self.current_stage]["flag"]
        return None

    def get_current_flag_hash(self) -> str | None:
        """Get the hash of the current stage's flag."""
        if self.current_stage < len(self.flags):
            return self.flags[self.current_stage]["hash"]
        return None

    def record_hint(self, level: int):
        """Record that a hint was used at the given level."""
        stage_key = self.current_stage
        if stage_key not in self.hints_used:
            self.hints_used[stage_key] = {"l1": 0, "l2": 0, "l3": 0}

        level_key = f"l{level}"
        self.hints_used[stage_key][level_key] = self.hints_used[stage_key].get(level_key, 0) + 1

        # Log to database
        queries.log_hint(self.session_id, self.current_stage, level)

    def get_stage_hints_count(self) -> dict:
        """Get hint counts for the current stage."""
        return self.hints_used.get(self.current_stage, {"l1": 0, "l2": 0, "l3": 0})

    def submit_flag(self, submitted_flag: str) -> dict:
        """Submit a flag for the current stage.

        Returns:
            Dict with 'correct', 'stage_name', 'points', 'completed'.
        """
        expected_hash = self.get_current_flag_hash()
        if not expected_hash:
            return {"correct": False, "message": "No active stage"}

        if not verify_flag(submitted_flag, expected_hash):
            return {"correct": False, "message": "Incorrect flag. Keep trying!"}

        # Flag is correct
        stage = self.current_stage_obj
        hints = self.get_stage_hints_count()

        # Calculate score
        hint_mult = calculate_hint_multiplier(hints["l1"], hints["l2"], hints["l3"])
        elapsed = self.elapsed_seconds
        par = self.target.par_time_minutes * 60
        stage_score = calculate_stage_score(stage.points, hint_mult, elapsed, par)

        # Record in database
        queries.record_stage_completion(
            session_id=self.session_id,
            stage_index=self.current_stage,
            stage_name=stage.name,
            flag_submitted=submitted_flag.strip(),
            points_earned=stage_score,
            hints_l1=hints["l1"],
            hints_l2=hints["l2"],
            hints_l3=hints["l3"],
            hint_multiplier=hint_mult,
        )

        self.total_score += stage_score

        # Check if hunt is complete
        result = {
            "correct": True,
            "stage_name": stage.name,
            "points": stage_score,
            "hint_multiplier": hint_mult,
            "completed": False,
        }

        if self.is_final_stage:
            self.completed = True
            result["completed"] = True

            # Update session and target progress
            queries.complete_session(
                self.session_id, self.total_score, self.elapsed_seconds
            )
            queries.upsert_target_progress(
                slug=self.target.slug,
                difficulty=self.target.difficulty,
                status="completed",
                best_score=self.total_score,
                best_time_secs=self.elapsed_seconds,
            )

            # Recalculate total profile score
            all_progress = queries.get_all_progress()
            profile_total = sum(p.get("best_score", 0) for p in all_progress.values())
            queries.update_profile_score(profile_total)
        else:
            self.current_stage += 1
            queries.update_session(
                self.session_id,
                current_stage=self.current_stage,
                total_score=self.total_score,
                time_elapsed_secs=self.elapsed_seconds,
            )

        return result

    def abort(self):
        """Abort the current hunt session."""
        queries.update_session(
            self.session_id,
            status="abandoned",
            time_elapsed_secs=self.elapsed_seconds,
        )

    def pause(self):
        """Pause the current hunt session."""
        queries.update_session(
            self.session_id,
            status="paused",
            time_elapsed_secs=self.elapsed_seconds,
        )
