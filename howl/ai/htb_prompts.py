"""HTB-specific AI prompts for the Howl AI Helper."""

HTB_SYSTEM_PROMPT = """You are the Howl AI Helper - a cybersecurity instructor helping a student hack a HackTheBox machine.

Your role is to provide educational, step-by-step guidance through the penetration testing process. You are encouraging, knowledgeable, and follow a structured pentest methodology.

METHODOLOGY (guide the student through these phases in order):
1. RECONNAISSANCE - Port scanning, service enumeration, OS detection
2. ENUMERATION - Deep-dive into discovered services, directory fuzzing, version-specific research
3. EXPLOITATION - Finding and exploiting vulnerabilities to gain initial access
4. PRIVILEGE ESCALATION - Escalating from user to root
5. POST-EXPLOITATION - Capturing flags, documenting findings

RULES:
1. ALWAYS use the real target IP and discovered ports in example commands - never use placeholders
2. Explain the "why" behind every technique and tool suggestion
3. Encourage the student to try things before asking for more help
4. Reference real-world tools and techniques commonly used in CTF/pentesting
5. If nmap results are provided, analyze them and suggest specific next steps based on discovered services
6. Adjust detail level based on hint level:
   - Level 1 (Nudge): Point in a direction, ask a guiding question
   - Level 2 (Direction): Name the technique/tool, explain the approach
   - Level 3 (Walkthrough): Provide specific commands and step-by-step guidance
7. Remind students these techniques are for authorized environments only
8. For HTB machines, be aware that typical flags are at /home/*/user.txt and /root/root.txt
9. When the student seems stuck, suggest systematic enumeration before exploitation
10. Be concise and terminal-friendly (no markdown headers, use plain text)
11. When suggesting tools, briefly explain what they do and why you're suggesting them
12. If the student asks "what should I do next", base your answer on their current phase and what services/info they've discovered

You have context about the target IP, discovered services, the student's current phase, and their progress through milestones.

When ONLINE RESEARCH RESULTS are provided, use them to give more accurate and specific guidance. These results come from searching for walkthroughs and exploit info related to the target machine and its services. Cross-reference the research with the student's current phase to provide relevant, targeted hints. Do not just repeat the research verbatim - synthesize it into educational guidance."""


def build_htb_hint_prompt(
    machine_name: str,
    machine_ip: str,
    current_phase: str,
    milestones_achieved: list[str],
    hint_level: int,
    discovered_services: list[dict] | None = None,
    nmap_results: str | None = None,
    hostname: str | None = None,
    walkthrough_info: str | None = None,
    command_history: str | None = None,
) -> str:
    """Build the prompt for an HTB hint request."""
    service_lines = ""
    if discovered_services:
        for svc in discovered_services:
            version_str = f" ({svc['version']})" if svc.get("version") else ""
            service_lines += (
                f"  - {svc['port']}/{svc['protocol']} "
                f"{svc['state']} {svc['service']}{version_str}\n"
            )
    else:
        service_lines = "  No scan results yet - suggest running nmap first\n"

    if milestones_achieved:
        milestone_str = "\n".join(f"  [x] {m}" for m in milestones_achieved)
    else:
        milestone_str = "  None yet"

    level_names = {1: "Nudge (vague)", 2: "Direction (moderate)", 3: "Walkthrough (specific)"}
    level_name = level_names.get(hint_level, f"Level {hint_level}")

    hostname_line = f"\nHOSTNAME: {hostname}" if hostname else ""

    nmap_section = ""
    if nmap_results:
        truncated = nmap_results[:2000]
        nmap_section = f"\nNMAP SCAN RESULTS:\n{truncated}\n"

    research_section = ""
    if walkthrough_info:
        research_section = f"\nONLINE RESEARCH RESULTS:\n{walkthrough_info}\n"

    history_section = ""
    if command_history:
        history_section = f"\nRECENT COMMAND HISTORY (commands the student has run and their output):\n{command_history}\n"

    return f"""HTB MACHINE: {machine_name}
TARGET IP: {machine_ip}{hostname_line}

DISCOVERED SERVICES:
{service_lines}
{nmap_section}{research_section}{history_section}
CURRENT PHASE: {current_phase}

MILESTONES ACHIEVED:
{milestone_str}

HINT LEVEL REQUESTED: {hint_level} - {level_name}

Provide a hint at the requested level for the current phase. When giving commands, use the real target IP {machine_ip} and discovered ports. Focus on what the student should try next given their current progress. Use the online research results and the student's recent command output to give accurate, machine-specific guidance."""


def build_htb_chat_prompt(
    machine_name: str,
    machine_ip: str,
    current_phase: str,
    user_question: str,
    discovered_services: list[dict] | None = None,
    nmap_results: str | None = None,
    hostname: str | None = None,
    milestones_achieved: list[str] | None = None,
    walkthrough_info: str | None = None,
    command_history: str | None = None,
) -> str:
    """Build a prompt for free-form AI chat in HTB mode."""
    service_lines = ""
    if discovered_services:
        for svc in discovered_services:
            version_str = f" ({svc['version']})" if svc.get("version") else ""
            service_lines += (
                f"  - {svc['port']}/{svc['protocol']} "
                f"{svc['state']} {svc['service']}{version_str}\n"
            )
    else:
        service_lines = "  No scan results yet\n"

    hostname_line = f"\nHOSTNAME: {hostname}" if hostname else ""

    nmap_section = ""
    if nmap_results:
        truncated = nmap_results[:2000]
        nmap_section = f"\nNMAP SCAN RESULTS:\n{truncated}\n"

    milestone_str = ""
    if milestones_achieved:
        milestone_str = "\nMILESTONES: " + ", ".join(milestones_achieved)

    research_section = ""
    if walkthrough_info:
        research_section = f"\nONLINE RESEARCH RESULTS:\n{walkthrough_info}\n"

    history_section = ""
    if command_history:
        history_section = f"\nRECENT COMMAND HISTORY (commands the student has run and their output):\n{command_history}\n"

    return f"""HTB MACHINE: {machine_name}
TARGET IP: {machine_ip}{hostname_line}

DISCOVERED SERVICES:
{service_lines}
{nmap_section}{research_section}{history_section}
CURRENT PHASE: {current_phase}{milestone_str}

STUDENT QUESTION: {user_question}

Provide a helpful, direct response. Use the online research results and the student's recent command output to give accurate, machine-specific guidance. When suggesting commands, use the real target IP {machine_ip} - never use placeholders. If the student asks what command to run, give them the exact command they can copy and paste."""
