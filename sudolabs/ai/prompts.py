"""System prompts for the SudoLabs AI Helper."""

SYSTEM_PROMPT = """You are the SudoLabs AI Helper - a cybersecurity instructor embedded in the SudoLabs hacking lab platform.

Your role is to guide students through penetration testing exercises by providing progressive hints and educational explanations. You are encouraging, knowledgeable, and precise.

RULES:
1. When the student asks what command to run, ALWAYS include the actual target IP and port in your example commands. Never use placeholder IPs like <target_ip> - use the real IP provided in context.
2. Always explain the "why" behind a technique, not just the "how"
3. Encourage the student to think critically and try things before asking for more help
4. Reference real-world tools and techniques that are commonly used in penetration testing
5. If the student asks a direct question like "what nmap command should I run", give them a direct, usable answer with the real target details filled in
6. Adjust your detail level based on the hint level requested:
   - Level 1 (Nudge): Vague direction. Ask a question or point to a concept.
   - Level 2 (Direction): More specific. Name the technique or tool, explain the approach.
   - Level 3 (Walkthrough): Near-explicit. Provide specific commands and step-by-step guidance.
7. Always remind students that these techniques should only be used in authorized environments
8. For free-form questions (not hint requests), be helpful and direct. If they ask "what command should I run", tell them.

You have context about the current target including its IP address, ports, attack stage, and the student's progress.
Respond concisely and in a terminal-friendly format (no markdown headers, use plain text)."""


def build_hint_prompt(
    target_name: str,
    target_description: str,
    cves: list[str],
    current_stage: str,
    stage_description: str,
    tools_suggested: list[str],
    hint_level: int,
    previous_hints: list[str],
    flags_captured: int,
    total_stages: int,
    target_ip: str = "127.0.0.1",
    target_ports: list[dict] | None = None,
    command_history: str | None = None,
) -> str:
    """Build the user message for a hint request."""
    cve_str = ", ".join(cves) if cves else "N/A"
    tools_str = ", ".join(tools_suggested) if tools_suggested else "N/A"
    prev_str = "\n".join(f"  - {h}" for h in previous_hints) if previous_hints else "  None"

    # Build port/service info
    port_lines = ""
    if target_ports:
        for svc in target_ports:
            port_lines += f"  - {svc['name']}: {target_ip}:{svc['port']} ({svc['protocol']})\n"
    else:
        port_lines = "  Unknown\n"

    level_names = {1: "Nudge (vague)", 2: "Direction (moderate)", 3: "Walkthrough (specific)"}
    level_name = level_names.get(hint_level, f"Level {hint_level}")

    history_section = ""
    if command_history:
        history_section = f"\nRECENT COMMAND HISTORY (commands the student has run and their output):\n{command_history}\n"

    return f"""TARGET: {target_name}
DESCRIPTION: {target_description}
CVEs: {cve_str}

TARGET IP: {target_ip}
SERVICES:
{port_lines}
{history_section}
CURRENT STAGE: {current_stage} (stage {flags_captured + 1} of {total_stages})
STAGE OBJECTIVE: {stage_description}
SUGGESTED TOOLS: {tools_str}

PREVIOUS HINTS THIS STAGE:
{prev_str}

HINT LEVEL REQUESTED: {hint_level} - {level_name}

Please provide a hint at the requested level for the current stage. When giving commands, use the real target IP {target_ip} and ports listed above. Reference the student's recent command output when relevant."""


def build_chat_prompt(
    target_name: str,
    current_stage: str,
    stage_description: str,
    user_question: str,
    target_ip: str = "127.0.0.1",
    target_ports: list[dict] | None = None,
    tools_suggested: list[str] | None = None,
    command_history: str | None = None,
) -> str:
    """Build a prompt for free-form AI chat."""
    # Build port/service info
    port_lines = ""
    if target_ports:
        for svc in target_ports:
            port_lines += f"  - {svc['name']}: {target_ip}:{svc['port']} ({svc['protocol']})\n"
    else:
        port_lines = "  Unknown\n"

    tools_str = ", ".join(tools_suggested) if tools_suggested else "N/A"

    history_section = ""
    if command_history:
        history_section = f"\nRECENT COMMAND HISTORY (commands the student has run and their output):\n{command_history}\n"

    return f"""TARGET: {target_name}
TARGET IP: {target_ip}
SERVICES:
{port_lines}
{history_section}
CURRENT STAGE: {current_stage}
STAGE OBJECTIVE: {stage_description}
SUGGESTED TOOLS: {tools_str}

STUDENT QUESTION: {user_question}

Provide a helpful, direct response. When suggesting commands, use the real target IP {target_ip} and real ports listed above - never use placeholders. If the student asks what command to run, give them the exact command they can copy and paste. Reference the student's recent command output when relevant."""
