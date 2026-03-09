"""Named query functions for Howl database operations."""

from howl.db.database import get_db


# ── Profile ──────────────────────────────────────────────

def get_profile() -> dict:
    with get_db() as db:
        row = db.execute("SELECT * FROM profile LIMIT 1").fetchone()
        return dict(row) if row else {"username": "hunter", "total_score": 0}


def update_profile_score(total_score: int):
    with get_db() as db:
        db.execute("UPDATE profile SET total_score = ? WHERE id = 1", (total_score,))


def set_profile_username(username: str):
    with get_db() as db:
        db.execute("UPDATE profile SET username = ? WHERE id = 1", (username,))


# ── Target Progress ──────────────────────────────────────

def get_all_progress() -> dict:
    """Returns a dict mapping target_slug -> progress dict."""
    with get_db() as db:
        rows = db.execute("SELECT * FROM target_progress").fetchall()
        return {row["target_slug"]: dict(row) for row in rows}


def get_target_progress(slug: str) -> dict | None:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM target_progress WHERE target_slug = ?", (slug,)
        ).fetchone()
        return dict(row) if row else None


def upsert_target_progress(
    slug: str,
    difficulty: str,
    status: str,
    best_score: int = 0,
    best_time_secs: int | None = None,
):
    with get_db() as db:
        existing = db.execute(
            "SELECT * FROM target_progress WHERE target_slug = ?", (slug,)
        ).fetchone()

        if existing:
            updates = ["status = ?", "attempts = attempts + 1"]
            params = [status]

            if best_score > existing["best_score"]:
                updates.append("best_score = ?")
                params.append(best_score)

            if best_time_secs and (
                existing["best_time_secs"] is None
                or best_time_secs < existing["best_time_secs"]
            ):
                updates.append("best_time_secs = ?")
                params.append(best_time_secs)

            if status == "completed" and not existing["completed_at"]:
                updates.append("completed_at = datetime('now')")

            params.append(slug)
            db.execute(
                f"UPDATE target_progress SET {', '.join(updates)} WHERE target_slug = ?",
                params,
            )
        else:
            db.execute(
                """INSERT INTO target_progress
                   (target_slug, difficulty, status, best_score, best_time_secs, attempts, first_started)
                   VALUES (?, ?, ?, ?, ?, 1, datetime('now'))""",
                (slug, difficulty, status, best_score, best_time_secs),
            )


def reset_target_progress(slug: str):
    with get_db() as db:
        db.execute("DELETE FROM target_progress WHERE target_slug = ?", (slug,))
        db.execute("DELETE FROM sessions WHERE target_slug = ?", (slug,))


def reset_all_progress():
    with get_db() as db:
        db.execute("DELETE FROM target_progress")
        db.execute("DELETE FROM sessions")
        db.execute("DELETE FROM stage_completions")
        db.execute("DELETE FROM hint_log")
        db.execute("DELETE FROM achievements")
        db.execute("UPDATE profile SET total_score = 0")


# ── Sessions ─────────────────────────────────────────────

def create_session(session_id: str, target_slug: str) -> str:
    with get_db() as db:
        db.execute(
            """INSERT INTO sessions (session_id, target_slug, status)
               VALUES (?, ?, 'active')""",
            (session_id, target_slug),
        )
    return session_id


def get_active_session(target_slug: str | None = None) -> dict | None:
    with get_db() as db:
        if target_slug:
            row = db.execute(
                "SELECT * FROM sessions WHERE target_slug = ? AND status = 'active' ORDER BY started_at DESC LIMIT 1",
                (target_slug,),
            ).fetchone()
        else:
            row = db.execute(
                "SELECT * FROM sessions WHERE status = 'active' ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
        return dict(row) if row else None


def update_session(session_id: str, **kwargs):
    if not kwargs:
        return
    with get_db() as db:
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        vals = list(kwargs.values()) + [session_id]
        db.execute(f"UPDATE sessions SET {sets} WHERE session_id = ?", vals)


def complete_session(session_id: str, total_score: int, time_elapsed: int):
    with get_db() as db:
        db.execute(
            """UPDATE sessions
               SET status = 'completed',
                   completed_at = datetime('now'),
                   total_score = ?,
                   time_elapsed_secs = ?
               WHERE session_id = ?""",
            (total_score, time_elapsed, session_id),
        )


# ── Stage Completions ────────────────────────────────────

def record_stage_completion(
    session_id: str,
    stage_index: int,
    stage_name: str,
    flag_submitted: str,
    points_earned: int,
    hints_l1: int = 0,
    hints_l2: int = 0,
    hints_l3: int = 0,
    hint_multiplier: float = 1.0,
    time_bonus: float = 1.0,
):
    with get_db() as db:
        db.execute(
            """INSERT OR REPLACE INTO stage_completions
               (session_id, stage_index, stage_name, flag_submitted,
                points_earned, hints_used_l1, hints_used_l2, hints_used_l3,
                hint_multiplier, time_bonus)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id, stage_index, stage_name, flag_submitted,
                points_earned, hints_l1, hints_l2, hints_l3,
                hint_multiplier, time_bonus,
            ),
        )


def get_stage_completions(session_id: str) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM stage_completions WHERE session_id = ? ORDER BY stage_index",
            (session_id,),
        ).fetchall()
        return [dict(row) for row in rows]


# ── Hints ────────────────────────────────────────────────

def log_hint(session_id: str, stage_index: int, hint_level: int, source: str = "static"):
    with get_db() as db:
        db.execute(
            """INSERT INTO hint_log (session_id, stage_index, hint_level, hint_source)
               VALUES (?, ?, ?, ?)""",
            (session_id, stage_index, hint_level, source),
        )


def get_hints_for_stage(session_id: str, stage_index: int) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM hint_log WHERE session_id = ? AND stage_index = ? ORDER BY requested_at",
            (session_id, stage_index),
        ).fetchall()
        return [dict(row) for row in rows]


def get_total_hints_used() -> int:
    with get_db() as db:
        row = db.execute("SELECT COUNT(*) as cnt FROM hint_log").fetchone()
        return row["cnt"] if row else 0


# ── Achievements ─────────────────────────────────────────

def unlock_achievement(
    achievement_id: str,
    name: str,
    description: str,
    points: int,
    trigger_session: str | None = None,
    trigger_target: str | None = None,
):
    with get_db() as db:
        try:
            db.execute(
                """INSERT INTO achievements
                   (achievement_id, name, description, points, trigger_session, trigger_target)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (achievement_id, name, description, points, trigger_session, trigger_target),
            )
            return True
        except Exception:
            return False  # Already unlocked


def get_all_achievements() -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM achievements ORDER BY unlocked_at"
        ).fetchall()
        return [dict(row) for row in rows]


def is_achievement_unlocked(achievement_id: str) -> bool:
    with get_db() as db:
        row = db.execute(
            "SELECT 1 FROM achievements WHERE achievement_id = ?", (achievement_id,)
        ).fetchone()
        return row is not None


# ── Stats ────────────────────────────────────────────────

def get_completion_stats() -> dict:
    """Get completion stats by difficulty."""
    with get_db() as db:
        stats = {"easy": 0, "medium": 0, "hard": 0, "elite": 0, "htb": 0}
        scores = {"easy": 0, "medium": 0, "hard": 0, "elite": 0, "htb": 0}
        rows = db.execute(
            "SELECT difficulty, COUNT(*) as cnt, COALESCE(SUM(best_score), 0) as total FROM target_progress WHERE status = 'completed' GROUP BY difficulty"
        ).fetchall()
        for row in rows:
            diff = row["difficulty"]
            if diff in stats:
                stats[diff] = row["cnt"]
                scores[diff] = row["total"] or 0
        return {"counts": stats, "scores": scores}


def get_total_time() -> int:
    """Get total time across all completed sessions in seconds."""
    with get_db() as db:
        row = db.execute(
            "SELECT COALESCE(SUM(time_elapsed_secs), 0) as total FROM sessions WHERE status = 'completed'"
        ).fetchone()
        return row["total"] if row else 0
