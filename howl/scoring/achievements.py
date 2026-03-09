"""Achievement definitions and unlock logic for Howl."""

from dataclasses import dataclass
from typing import Callable

from howl.db import queries


@dataclass
class AchievementDef:
    """Definition of an achievement."""
    id: str
    name: str
    description: str
    points: int
    check: Callable[..., bool]


def _check_first_blood(**kwargs) -> bool:
    progress = queries.get_all_progress()
    return any(p["status"] == "completed" for p in progress.values())


def _check_ghost(**kwargs) -> bool:
    session_id = kwargs.get("session_id")
    if not session_id:
        return False
    hints = queries.get_hints_for_stage(session_id, 0)  # Check all stages
    # Actually need to check total hints for this session
    from howl.db.database import get_db
    with get_db() as db:
        row = db.execute(
            "SELECT COUNT(*) as cnt FROM hint_log WHERE session_id = ?",
            (session_id,)
        ).fetchone()
        return row["cnt"] == 0


def _check_speed_demon(**kwargs) -> bool:
    session = kwargs.get("session_data")
    target = kwargs.get("target")
    if not session or not target:
        return False
    elapsed = session.get("time_elapsed_secs", 0)
    par = target.par_time_minutes * 60
    return elapsed > 0 and elapsed < par * 0.5


def _check_clean_sweep_easy(**kwargs) -> bool:
    stats = queries.get_completion_stats()
    return stats["counts"].get("easy", 0) >= 10


def _check_clean_sweep_medium(**kwargs) -> bool:
    stats = queries.get_completion_stats()
    return stats["counts"].get("medium", 0) >= 10


def _check_clean_sweep_hard(**kwargs) -> bool:
    stats = queries.get_completion_stats()
    return stats["counts"].get("hard", 0) >= 10


def _check_clean_sweep_elite(**kwargs) -> bool:
    stats = queries.get_completion_stats()
    return stats["counts"].get("elite", 0) >= 10


def _check_perfectionist(**kwargs) -> bool:
    session = kwargs.get("session_data")
    target = kwargs.get("target")
    if not session or not target:
        return False
    max_score = target.total_points
    return session.get("total_score", 0) >= max_score * 1.3  # Got time bonuses


def _check_hint_addict(**kwargs) -> bool:
    total = queries.get_total_hints_used()
    return total >= 50


def _check_marathon(**kwargs) -> bool:
    from howl.db.database import get_db
    with get_db() as db:
        row = db.execute(
            """SELECT COUNT(*) as cnt FROM sessions
               WHERE status = 'completed'
               AND date(completed_at) = date('now')"""
        ).fetchone()
        return row["cnt"] >= 5


def _check_apex_predator(**kwargs) -> bool:
    progress = queries.get_all_progress()
    completed = sum(1 for p in progress.values() if p["status"] == "completed")
    return completed >= 40


ACHIEVEMENTS = [
    AchievementDef("first_blood", "First Blood", "Complete any target", 100, _check_first_blood),
    AchievementDef("ghost", "Ghost", "Complete a target with zero hints", 300, _check_ghost),
    AchievementDef("speed_demon", "Speed Demon", "Complete a target under 50% par time", 200, _check_speed_demon),
    AchievementDef("clean_sweep_easy", "Clean Sweep (Easy)", "Complete all 10 easy targets", 500, _check_clean_sweep_easy),
    AchievementDef("clean_sweep_medium", "Clean Sweep (Medium)", "Complete all 10 medium targets", 750, _check_clean_sweep_medium),
    AchievementDef("clean_sweep_hard", "Clean Sweep (Hard)", "Complete all 10 hard targets", 1000, _check_clean_sweep_hard),
    AchievementDef("clean_sweep_elite", "Clean Sweep (Elite)", "Complete all 10 elite targets", 2000, _check_clean_sweep_elite),
    AchievementDef("perfectionist", "Perfectionist", "Complete a target with a perfect+ score", 400, _check_perfectionist),
    AchievementDef("hint_addict", "Hint Addict", "Use 50 total hints", 50, _check_hint_addict),
    AchievementDef("marathon", "Marathon", "Complete 5 targets in one day", 250, _check_marathon),
    AchievementDef("apex_predator", "Apex Predator", "Complete all 40 targets", 5000, _check_apex_predator),
]


def check_achievements(session_id: str | None = None, session_data: dict | None = None, target=None) -> list[AchievementDef]:
    """Check and unlock any newly earned achievements.

    Returns:
        List of newly unlocked achievements.
    """
    newly_unlocked = []

    for ach in ACHIEVEMENTS:
        if queries.is_achievement_unlocked(ach.id):
            continue

        try:
            if ach.check(
                session_id=session_id,
                session_data=session_data,
                target=target,
            ):
                success = queries.unlock_achievement(
                    achievement_id=ach.id,
                    name=ach.name,
                    description=ach.description,
                    points=ach.points,
                    trigger_session=session_id,
                    trigger_target=target.slug if target else None,
                )
                if success:
                    newly_unlocked.append(ach)
        except Exception:
            pass  # Don't let achievement checks crash the hunt

    return newly_unlocked
