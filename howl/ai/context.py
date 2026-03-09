"""Context builder for AI helper API calls."""

from howl.engine.session import HuntSession
from howl.db import queries


def build_hint_context(session: HuntSession, hint_level: int, target_ip: str = "127.0.0.1") -> dict:
    """Build context payload for an AI hint request.

    Returns:
        Dict with all context needed for the AI prompt builder.
    """
    target = session.target
    stage = session.current_stage_obj

    # Get previous hints for this stage from the database
    prev_hints_data = queries.get_hints_for_stage(session.session_id, session.current_stage)
    previous_hints = [
        f"Level {h['hint_level']} hint was given"
        for h in prev_hints_data
    ]

    # Add static hints that were already shown
    if stage:
        for hint in stage.hints:
            if hint.level <= hint_level:
                for h in prev_hints_data:
                    if h["hint_level"] == hint.level:
                        previous_hints.append(f"L{hint.level}: {hint.text[:80]}...")
                        break

    # Build service/port info for the AI
    target_ports = [
        {"name": svc.name, "port": svc.port, "protocol": svc.protocol}
        for svc in target.services
    ]

    return {
        "target_name": target.name,
        "target_description": target.description,
        "cves": target.cves,
        "current_stage": stage.name if stage else "Unknown",
        "stage_description": stage.description if stage else "",
        "tools_suggested": stage.tools_suggested if stage else [],
        "hint_level": hint_level,
        "previous_hints": previous_hints,
        "flags_captured": session.current_stage,
        "total_stages": target.stage_count,
        "target_ip": target_ip,
        "target_ports": target_ports,
    }
