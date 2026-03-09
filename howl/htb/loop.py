"""HTB mode interactive hunt loop."""

import os
import subprocess

from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.rule import Rule

from howl.ui.theme import console
from howl.ui.panels import info_panel, success_panel, warning_panel, hint_panel
from howl.ui.terminal import FixedBar
from howl.ai.helper import AIHelper
from howl.htb.session import HtbSession, HtbMilestone, MILESTONE_LABELS, MILESTONE_ORDER


def _clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def _draw_status_bar(session: HtbSession):
    """Draw the persistent status bar at the top of the screen."""
    ms_count = len(session.milestones)
    ms_total = len(MILESTONE_ORDER)

    # Build milestone indicators
    ms_indicators = ""
    short_labels = ["REC", "FTH", "USR", "UFL", "RT", "RFL"]
    for i, ms in enumerate(MILESTONE_ORDER):
        if ms.value in session.milestones:
            ms_indicators += f"[green]{short_labels[i]}[/green] "
        else:
            ms_indicators += f"[dim]{short_labels[i]}[/dim] "

    # Build services summary
    svc_count = len(session.discovered_services) if session.discovered_services else 0
    svc_text = f"{svc_count} services" if svc_count else "no scan"

    hostname_text = f" ({session.hostname})" if session.hostname else ""

    header = (
        f"  [bold bright_red]HTB[/bold bright_red] [bold]{session.machine_name}[/bold]{hostname_text}"
        f"  |  [bold]{session.machine_ip}[/bold]"
        f"  |  {svc_text}"
        f"  |  [bold]{session.elapsed_formatted}[/bold]"
        f"  |  {session.current_phase}"
    )
    milestones_line = f"  {ms_indicators} [{ms_count}/{ms_total}]"

    console.print(Panel(
        f"{header}\n{milestones_line}",
        border_style="bright_red",
        padding=(0, 1),
    ))


def render_htb_milestone_progress(session: HtbSession):
    """Render the milestone progress display for HTB mode."""
    lines = []
    for ms in MILESTONE_ORDER:
        label = MILESTONE_LABELS[ms]
        if ms.value in session.milestones:
            lines.append(f"  [green][x][/green] {label}")
        else:
            lines.append(f"  [dim][ ] {label}[/dim]")

    console.print(Panel(
        "\n".join(lines),
        title="[bold]MILESTONES[/bold]",
        border_style="bright_red",
    ))


def _get_walkthrough_info(session: HtbSession, extra_query: str = "") -> str | None:
    """Fetch walkthrough info from the web for the current machine."""
    from howl.ai.websearch import search_walkthroughs

    try:
        return search_walkthroughs(session.machine_name, extra_query)
    except Exception:
        return None


def _run_shell_command(cmd: str, command_history: list[dict], ai: AIHelper | None = None) -> None:
    """Run a shell command, display output, and store it in command history."""
    console.print(f"  [dim]$ {cmd}[/dim]\n")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=300,
        )
        output = ""
        if result.stdout:
            print(result.stdout, end="")
            output += result.stdout
        if result.stderr:
            print(result.stderr, end="")
            output += result.stderr

        # Store in history (keep last 10 commands, truncate long output)
        truncated = output[:3000] if len(output) > 3000 else output
        command_history.append({"cmd": cmd, "output": truncated})
        if len(command_history) > 10:
            command_history.pop(0)

        # Feed into AI conversation memory
        if ai:
            ai.add_command(cmd, truncated)

    except subprocess.TimeoutExpired:
        console.print("  [red]Command timed out (5 min limit).[/red]")
    except Exception as e:
        console.print(f"  [red]Error running command: {e}[/red]")


def _build_history_context(command_history: list[dict]) -> str | None:
    """Build a text summary of recent command history for AI context."""
    if not command_history:
        return None

    lines = []
    for entry in command_history[-5:]:  # Last 5 commands for the prompt
        lines.append(f"$ {entry['cmd']}")
        if entry["output"]:
            # Truncate per-command output in prompt to 1500 chars
            out = entry["output"][:1500]
            lines.append(out)
        lines.append("")

    return "\n".join(lines)


def htb_hunt_loop(session: HtbSession):
    """Main HTB hunt interaction loop."""
    ai = AIHelper()
    last_output: list[str] = []
    command_history: list[dict] = []

    # Command bar shortcuts for HTB mode
    HTB_COMMANDS = [
        ("ask", "AI Help"),
        ("hint", "Get Hint"),
        ("scan", "Nmap"),
        ("milestone", "Progress"),
        ("note", "Add Note"),
        ("help", "All Cmds"),
    ]

    bar = FixedBar(HTB_COMMANDS, "howl/htb")

    def _redraw(show_last_output: bool = True):
        """Clear scroll area and redraw the status header."""
        bar.clear_scroll_area()
        _draw_status_bar(session)
        if show_last_output and last_output:
            console.print()
            for line in last_output:
                console.print(line)

    # Activate fixed bar and initial display
    bar.activate()
    try:
        _draw_status_bar(session)

        while not session.completed:
            user_input = bar.get_input()
            parts = user_input.strip().split(maxsplit=1)

            if not parts:
                continue

            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""
            last_output.clear()

            if cmd == "clear":
                _redraw(show_last_output=False)

            elif cmd == "scan":
                _handle_scan(session, arg)

            elif cmd == "milestone":
                prev_phase = session.current_phase
                _handle_milestone(session, arg)
                if session.current_phase != prev_phase:
                    ai.add_event(
                        f"Milestone reached: '{session.current_phase}'. "
                        f"Student advanced from phase '{prev_phase}'."
                    )
                _redraw(show_last_output=False)

            elif cmd == "hint":
                level = 1
                if arg:
                    try:
                        level = int(arg)
                        level = max(1, min(3, level))
                    except ValueError:
                        pass
                _handle_hint(session, ai, level, command_history)

            elif cmd == "ask":
                if not arg:
                    arg = Prompt.ask("  [bold blue]Ask the AI[/bold blue]")
                if not arg:
                    continue
                _handle_ask(session, ai, arg, command_history)

            elif cmd == "info":
                _redraw(show_last_output=False)
                console.print()
                render_htb_milestone_progress(session)
                console.print(f"\n  [bold]Phase:[/bold] {session.current_phase}")
                if session.discovered_services:
                    console.print(f"\n  [bold]Discovered Services:[/bold]")
                    for svc in session.discovered_services:
                        ver = f" ({svc['version']})" if svc.get("version") else ""
                        console.print(
                            f"    {svc['port']}/{svc['protocol']} "
                            f"{svc['service']}{ver}"
                        )

            elif cmd == "status":
                _redraw(show_last_output=False)

            elif cmd == "target":
                console.print(f"  [bold]Target IP:[/bold] {session.machine_ip}")
                if session.hostname:
                    console.print(f"  [bold]Hostname:[/bold] {session.hostname}")
                if session.discovered_services:
                    for svc in session.discovered_services:
                        ver = f" ({svc['version']})" if svc.get("version") else ""
                        console.print(
                            f"  [bold]{svc['service']}:[/bold] "
                            f"{session.machine_ip}:{svc['port']} "
                            f"({svc['protocol']}){ver}"
                        )

            elif cmd == "note":
                if not arg:
                    arg = Prompt.ask("  [bold]Note[/bold]")
                if arg:
                    session.add_note(arg)
                    console.print(f"  [green]Note saved.[/green]")

            elif cmd == "notes":
                if session.notes:
                    console.print("\n  [bold]Session Notes:[/bold]")
                    for i, note in enumerate(session.notes, 1):
                        console.print(f"  {i}. {note}")
                else:
                    console.print("  [dim]No notes yet. Use 'note <text>' to add one.[/dim]")

            elif cmd == "done":
                if Confirm.ask("  Mark this HTB session as complete?"):
                    session.finish()
                    _display_htb_summary(session)
                    break

            elif cmd == "pause":
                session.pause()
                console.print("  [yellow]Session paused.[/yellow]")
                break

            elif cmd in ("abort", "quit", "exit"):
                if Confirm.ask("  [red]Abort this HTB session?[/red]"):
                    session.abort()
                    console.print("  [red]Session aborted.[/red]")
                    break

            elif cmd == "help":
                info_panel("HTB Commands", (
                    "[bold blue]ask[/bold blue] <question> [bold]Ask the AI anything[/bold] (e.g. 'ask what nmap command should I run')\n"
                    "[bold]hint[/bold] [1-3]     Get a hint (1=nudge, 2=direction, 3=walkthrough)\n"
                    "[bold]scan[/bold] [type]    Run nmap scan (quick/default/full)\n"
                    "[bold]milestone[/bold]      Mark a milestone (recon/foothold/user/root)\n"
                    "[bold]info[/bold]           Show milestones and discovered services\n"
                    "[bold]target[/bold]         Show target IP and services\n"
                    "[bold]status[/bold]         Refresh status header\n"
                    "[bold]clear[/bold]          Clear screen and redraw header\n"
                    "[bold]note[/bold] <text>    Save a note\n"
                    "[bold]notes[/bold]          View saved notes\n"
                    "[bold]done[/bold]           Mark session complete\n"
                    "[bold]pause[/bold]          Pause session\n"
                    "[bold]abort[/bold]          Abandon session\n"
                    "[bold]help[/bold]           Show this help\n"
                    "\n"
                    "[dim]Any unrecognized input is passed directly to the system shell,\n"
                    "so you can run nmap, curl, gobuster, etc. right here.[/dim]"
                ), border_style="cyan")

            else:
                # Pass unrecognized input to the system shell
                _run_shell_command(user_input.strip(), command_history, ai=ai)

    finally:
        bar.deactivate()


def _handle_scan(session: HtbSession, scan_type: str):
    """Handle the scan command."""
    from howl.htb.scanner import is_nmap_available, run_nmap_scan

    if not is_nmap_available():
        warning_panel(
            "Nmap Not Found",
            "nmap is not installed. Install it with: sudo apt install nmap\n"
            "You can still run nmap manually in another terminal."
        )
        return

    scan_type = scan_type.strip().lower() if scan_type else "default"
    if scan_type not in ("quick", "default", "full"):
        console.print("  [dim]Scan types: quick, default, full[/dim]")
        return

    scan_labels = {"quick": "Quick (top 1000 ports)", "default": "Service Version (-sV -sC)", "full": "Full (-sV -sC -p-)"}
    console.print(f"  [bold yellow]Running nmap scan: {scan_labels[scan_type]}[/bold yellow]")
    console.print(f"  [bold yellow]Target: {session.machine_ip}[/bold yellow]")
    console.print(f"  [dim]This may take a few minutes...[/dim]")

    try:
        raw_output, services = run_nmap_scan(session.machine_ip, scan_type)
        session.store_nmap_results(raw_output, services)

        if services:
            console.print(f"\n  [green]Found {len(services)} open port(s):[/green]")
            for svc in services:
                ver = f" ({svc['version']})" if svc.get("version") else ""
                state_color = "green" if svc["state"] == "open" else "yellow"
                console.print(
                    f"  [{state_color}]{svc['port']}/{svc['protocol']}[/{state_color}] "
                    f"{svc['service']}{ver}"
                )
        else:
            console.print("  [yellow]No open ports found. Try a different scan type or check if the target is up.[/yellow]")

        console.print(f"\n  [dim]Scan results saved - the AI helper now knows about these services.[/dim]")

        # Auto-search for exploit info on discovered services
        console.print(f"  [dim]Searching online for service-specific exploit info...[/dim]")
        from howl.ai.websearch import search_exploit_info
        for svc in services:
            if svc.get("version"):
                result = search_exploit_info(svc["service"], svc["version"])
                if result:
                    console.print(f"  [dim]Found exploit info for {svc['service']} {svc['version']}[/dim]")

    except RuntimeError as e:
        console.print(f"  [red]Scan error: {e}[/red]")
    except subprocess.TimeoutExpired:
        console.print("  [red]Scan timed out (10 min limit). Try 'scan quick' for a faster scan.[/red]")


def _handle_milestone(session: HtbSession, arg: str):
    """Handle the milestone command."""
    milestone_shortcuts = {
        "recon": HtbMilestone.RECON,
        "foothold": HtbMilestone.FOOTHOLD,
        "user": HtbMilestone.USER_SHELL,
        "user_shell": HtbMilestone.USER_SHELL,
        "user_flag": HtbMilestone.USER_FLAG,
        "root": HtbMilestone.ROOT_SHELL,
        "root_shell": HtbMilestone.ROOT_SHELL,
        "root_flag": HtbMilestone.ROOT_FLAG,
    }

    if not arg:
        console.print("  [bold]Available milestones:[/bold]")
        for shortcut, ms in milestone_shortcuts.items():
            if shortcut in ("user_shell", "root_shell"):
                continue
            label = MILESTONE_LABELS[ms]
            achieved = "[green][x][/green]" if ms.value in session.milestones else "[dim][ ][/dim]"
            console.print(f"  {achieved} [bold]{shortcut}[/bold] - {label}")
        console.print("\n  [dim]Usage: milestone <name>[/dim]")
        return

    ms = milestone_shortcuts.get(arg.strip().lower())
    if not ms:
        console.print(f"  [red]Unknown milestone: {arg}[/red]")
        valid = [k for k in milestone_shortcuts if k not in ("user_shell", "root_shell")]
        console.print(f"  [dim]Options: {', '.join(valid)}[/dim]")
        return

    if session.mark_milestone(ms):
        success_panel(
            "MILESTONE ACHIEVED",
            f"[bold green]{MILESTONE_LABELS[ms]}[/bold green]\n"
            f"Time: {session.elapsed_formatted}"
        )

        if session.completed:
            console.print()
            success_panel(
                "MACHINE PWNED",
                f"[bold]{session.machine_name}[/bold] - All flags captured!\n"
                f"Time: {session.elapsed_formatted}\n"
                f"Hints Used: {session.hints_used}"
            )
    else:
        console.print(f"  [yellow]Milestone already achieved: {MILESTONE_LABELS[ms]}[/yellow]")


def _handle_hint(session: HtbSession, ai: AIHelper, level: int, command_history: list[dict] | None = None):
    """Handle hint requests in HTB mode."""
    from howl.ai.htb_prompts import HTB_SYSTEM_PROMPT, build_htb_hint_prompt

    if not ai.is_available():
        warning_panel(
            "AI Unavailable",
            "Set your API key with: howl config --set-api-key"
        )
        return

    milestones_achieved = [
        MILESTONE_LABELS[HtbMilestone(m)]
        for m in session.milestones.keys()
    ]

    # Fetch walkthrough info from the web for better hints
    walkthrough_info = None
    with console.status("[bold blue]Researching online...[/bold blue]"):
        walkthrough_info = _get_walkthrough_info(session, session.current_phase)

        # Also search for exploit info on discovered services
        if session.discovered_services:
            from howl.ai.websearch import search_exploit_info
            exploit_parts = []
            for svc in session.discovered_services:
                if svc.get("version"):
                    info = search_exploit_info(svc["service"], svc["version"])
                    if info:
                        exploit_parts.append(info)
            if exploit_parts:
                extra = "\n".join(exploit_parts[:2])
                if walkthrough_info:
                    walkthrough_info += f"\n\nSERVICE EXPLOIT INFO:\n{extra}"
                else:
                    walkthrough_info = f"SERVICE EXPLOIT INFO:\n{extra}"

    history_context = _build_history_context(command_history) if command_history else None

    prompt = build_htb_hint_prompt(
        machine_name=session.machine_name,
        machine_ip=session.machine_ip,
        current_phase=session.current_phase,
        milestones_achieved=milestones_achieved,
        hint_level=level,
        discovered_services=session.discovered_services,
        nmap_results=session.nmap_results,
        hostname=session.hostname,
        walkthrough_info=walkthrough_info,
        command_history=history_context,
    )

    try:
        client = ai._get_client()
        # Build messages with conversation history for multi-turn memory
        messages = list(ai.conversation)
        messages.append({"role": "user", "content": prompt})

        with console.status("[bold blue]Thinking...[/bold blue]"):
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=600,
                system=HTB_SYSTEM_PROMPT,
                messages=messages,
            )
        hint_text = response.content[0].text
        session.record_hint()

        # Store in conversation memory
        ai.conversation.append({"role": "user", "content": prompt})
        ai.conversation.append({"role": "assistant", "content": hint_text})
        ai._trim_history()

        hint_panel(hint_text, level, "N/A (HTB mode)")
    except Exception as e:
        console.print(f"  [red]AI Helper error: {e}[/red]")


def _handle_ask(session: HtbSession, ai: AIHelper, question: str, command_history: list[dict] | None = None):
    """Handle free-form AI chat in HTB mode."""
    from howl.ai.htb_prompts import HTB_SYSTEM_PROMPT, build_htb_chat_prompt

    if not ai.is_available():
        warning_panel(
            "AI Unavailable",
            "Set your API key with: howl config --set-api-key"
        )
        return

    milestones_achieved = [
        MILESTONE_LABELS[HtbMilestone(m)]
        for m in session.milestones.keys()
    ]

    # Fetch walkthrough info from the web
    walkthrough_info = None
    with console.status("[bold blue]Researching online...[/bold blue]"):
        walkthrough_info = _get_walkthrough_info(session, question)

    history_context = _build_history_context(command_history) if command_history else None

    prompt = build_htb_chat_prompt(
        machine_name=session.machine_name,
        machine_ip=session.machine_ip,
        current_phase=session.current_phase,
        user_question=question,
        discovered_services=session.discovered_services,
        nmap_results=session.nmap_results,
        hostname=session.hostname,
        milestones_achieved=milestones_achieved,
        walkthrough_info=walkthrough_info,
        command_history=history_context,
    )

    try:
        client = ai._get_client()
        # Build messages with conversation history for multi-turn memory
        messages = list(ai.conversation)
        messages.append({"role": "user", "content": prompt})

        with console.status("[bold blue]Thinking...[/bold blue]"):
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                system=HTB_SYSTEM_PROMPT,
                messages=messages,
            )
        reply = response.content[0].text

        # Store in conversation memory
        ai.conversation.append({"role": "user", "content": prompt})
        ai.conversation.append({"role": "assistant", "content": reply})
        ai._trim_history()

        info_panel("AI Helper", reply, border_style="blue")
    except Exception as e:
        console.print(f"  [red]AI Helper error: {e}[/red]")


def _display_htb_summary(session: HtbSession):
    """Display session summary when completing an HTB machine."""
    ms_count = len(session.milestones)
    total = len(MILESTONE_ORDER)

    summary = (
        f"[bold]Machine:[/bold] {session.machine_name}\n"
        f"[bold]IP:[/bold] {session.machine_ip}\n"
        f"[bold]Time:[/bold] {session.elapsed_formatted}\n"
        f"[bold]Milestones:[/bold] {ms_count}/{total}\n"
        f"[bold]Hints Used:[/bold] {session.hints_used}\n"
    )

    if session.discovered_services:
        summary += f"[bold]Services Found:[/bold] {len(session.discovered_services)}\n"

    if session.notes:
        summary += f"\n[bold]Notes:[/bold]\n"
        for note in session.notes:
            summary += f"  - {note}\n"

    success_panel("HTB SESSION COMPLETE", summary)
