"""Context builder for AI helper API calls.

Builds rich context objects that tell the AI everything about the
student's current session: target info, progress, captured flags,
timing, and command history.
"""

import time

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


def build_session_summary(
    session: HuntSession,
    target_ip: str = "127.0.0.1",
) -> str:
    """Build a concise text summary of the full session state.

    This is injected into the system prompt so the AI always knows
    the student's current situation, even across conversation turns.
    """
    target = session.target
    stage = session.current_stage_obj

    # Elapsed time
    elapsed = time.time() - session.start_time if session.start_time else 0
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    # Port/service info
    port_lines = []
    for svc in target.services:
        port_lines.append(f"  {svc.name}: {target_ip}:{svc.port} ({svc.protocol})")

    # Stage progress
    stages_info = []
    for i, stg in enumerate(target.attack_chain):
        if i < session.current_stage:
            stages_info.append(f"  [{i+1}] {stg.name} -- CAPTURED")
        elif i == session.current_stage:
            stages_info.append(f"  [{i+1}] {stg.name} -- CURRENT <-")
        else:
            stages_info.append(f"  [{i+1}] {stg.name} -- locked")

    # Hints used summary
    hints_summary = []
    for stage_idx, hint_counts in session.hints_used.items():
        total = sum(hint_counts.values())
        if total > 0:
            hints_summary.append(f"  Stage {int(stage_idx)+1}: {total} hints used")

    lines = [
        "LIVE SESSION STATE",
        "==================",
        f"Target: {target.name} ({target.difficulty})",
        f"Target IP: {target_ip}",
        "Services:",
        *port_lines,
        "",
        f"Progress: Stage {session.current_stage + 1} of {target.stage_count}"
        f" | Score: {session.total_score} pts | Time: {mins}m {secs}s",
        *stages_info,
        "",
        f"Current Stage: {stage.name if stage else 'Complete'}",
        f"Objective: {stage.description if stage else 'All flags captured!'}",
        f"Suggested Tools: {', '.join(stage.tools_suggested) if stage and stage.tools_suggested else 'N/A'}",
    ]

    if hints_summary:
        lines.append("")
        lines.append("Hints Used:")
        lines.extend(hints_summary)

    if session.completed:
        lines.append("")
        lines.append("STATUS: ALL FLAGS CAPTURED -- TARGET COMPLETE")

    return "\n".join(lines)
