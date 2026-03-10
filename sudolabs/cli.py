"""SudoLabs CLI - Main command router."""

import os
import sys

import typer
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.spinner import Spinner

from sudolabs import __version__
from sudolabs.ui.theme import console
from sudolabs.ui.banner import display_banner
from sudolabs.ui.menu import show_main_menu
from sudolabs.ui.tables import render_target_table, render_category_table
from sudolabs.ui.panels import (
    info_panel, success_panel, error_panel, warning_panel,
    hint_panel, flag_panel, achievement_panel, hunt_panel,
)
from sudolabs.ui.terminal import FixedBar
from sudolabs.ui.progress import render_attack_chain, render_hunt_status
from sudolabs.ui.dashboard import render_score_dashboard, render_profile
from sudolabs.targets.registry import TargetRegistry
from sudolabs.db import queries
from sudolabs.db.database import init_db
from sudolabs.config import get_api_key, set_api_key, get_username, set_username
from sudolabs.constants import get_rank

app = typer.Typer(
    name="sudolabs",
    help="SudoLabs - Terminal Cybersecurity Hacking Lab",
    no_args_is_help=False,
    rich_markup_mode="rich",
    add_completion=False,
)


def _ensure_db():
    """Ensure the database is initialized."""
    init_db()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Launch the SudoLabs interactive menu."""
    if ctx.invoked_subcommand is not None:
        return

    _ensure_db()

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        display_banner()
        choice = show_main_menu()

        if choice == "1":
            _interactive_hunt()
        elif choice == "2":
            _interactive_htb()
        elif choice == "3":
            _show_targets()
        elif choice == "4":
            _show_score()
        elif choice == "5":
            _show_profile()
        elif choice == "6":
            _interactive_ai_chat()
        elif choice == "7":
            _run_doctor()
        elif choice == "8":
            _show_config()
        elif choice == "9":
            console.print("\n  [dim]Session ended.[/dim]\n")
            raise typer.Exit()

        # Pause so the user can read output before the screen clears.
        # Options 1 (Hunt) and 2 (HTB) enter their own interactive loops.
        # Option 5 (Profile) has its own edit loop with Enter to go back.
        if choice in ("3", "4", "6", "7", "8"):
            Prompt.ask("\n  [dim]Press Enter to continue[/dim]", default="")


def _select_category(registry: TargetRegistry) -> str | None:
    """Show category selection and return a category slug, 'all', or None."""
    progress_map = queries.get_all_progress()
    cat_stats = registry.get_category_stats(progress_map)
    render_category_table(cat_stats)

    console.print("  [dim]Enter a number, 'all' for all targets, or 'back' to return.[/dim]")
    selection = Prompt.ask("  [bold]Select category[/bold]")

    if not selection or selection.lower() == "back":
        return None

    if selection.lower() == "all":
        return "all"

    # Try as a number
    try:
        idx = int(selection) - 1
        if 0 <= idx < len(cat_stats):
            return cat_stats[idx]["slug"]
    except ValueError:
        pass

    # Try as a slug
    for cat in cat_stats:
        if selection.lower() == cat["slug"]:
            return cat["slug"]

    error_panel("Invalid Selection", f"'{selection}' is not a valid category.")
    return None


def _interactive_hunt():
    """Interactive target selection and hunt launch."""
    registry = TargetRegistry()
    target_list = registry.get_all()

    if not target_list:
        error_panel("No Targets", "No targets found. Check your targets/ directory.")
        return

    # Step 1: Category selection
    cat_choice = _select_category(registry)
    if cat_choice is None:
        return

    # Step 2: Show targets in selected category
    if cat_choice == "all":
        filtered = target_list
        title = "All Targets"
    else:
        from sudolabs.constants import CATEGORY_DISPLAY_NAMES, Category
        filtered = registry.get_by_category(cat_choice)
        try:
            display_name = CATEGORY_DISPLAY_NAMES[Category(cat_choice)]
        except (ValueError, KeyError):
            display_name = cat_choice.replace("-", " ").title()
        title = display_name

    if not filtered:
        warning_panel("No Targets", f"No targets found in this category.")
        return

    progress_map = queries.get_all_progress()
    render_target_table(filtered, progress_map, title=title)

    selection = Prompt.ask("\n  [bold]Enter target number or slug[/bold]")

    # Try as a number first
    target = None
    try:
        idx = int(selection) - 1
        if 0 <= idx < len(filtered):
            target = filtered[idx]
    except ValueError:
        pass

    # Fall back to slug lookup
    if not target:
        target = registry.get_by_slug(selection)

    if not target:
        error_panel("Not Found", f"Target '{selection}' not found.")
        return

    _launch_hunt(target.slug)


def _interactive_htb():
    """Interactive HTB mode launch from main menu."""
    console.print("\n  [bold bright_red]HTB MODE[/bold bright_red] - Hack an external machine\n")

    ip = Prompt.ask("  [bold]Target IP address[/bold]")
    if not ip:
        return

    name = Prompt.ask("  [bold]Machine name[/bold] [dim](optional)[/dim]", default="")
    hostname = Prompt.ask("  [bold]Hostname for /etc/hosts[/bold] [dim](optional, e.g. box.htb)[/dim]", default="")

    _launch_htb(
        ip=ip.strip(),
        name=name.strip() or None,
        hostname=hostname.strip() or None,
        no_hosts=False,
    )


@app.command()
def htb(
    ip: str = typer.Argument(..., help="Target machine IP address"),
    name: str = typer.Option(None, "--name", "-n", help="Machine name (e.g., 'Lame')"),
    hostname: str = typer.Option(None, "--hostname", "-H", help="Hostname to add to /etc/hosts"),
    no_hosts: bool = typer.Option(False, "--no-hosts", help="Skip /etc/hosts modification"),
):
    """Start an HTB hacking session against an external machine."""
    _ensure_db()
    _launch_htb(ip, name, hostname, no_hosts)


def _launch_htb(ip: str, name: str | None, hostname: str | None, no_hosts: bool):
    """Internal HTB session launcher."""
    from sudolabs.htb.session import HtbSession
    from sudolabs.htb.loop import htb_hunt_loop

    machine_name = name or f"HTB-{ip.replace('.', '-')}"

    console.print(f"\n  [bold bright_red]HTB MODE[/bold bright_red]\n")
    console.print(f"  [bold]Machine:[/bold] {machine_name}")
    console.print(f"  [bold]Target IP:[/bold] {ip}")

    # Handle /etc/hosts
    if hostname and not no_hosts:
        from sudolabs.htb.hosts import add_host_entry
        console.print(f"\n  [dim]Adding {hostname} -> {ip} to hosts file...[/dim]")
        success = add_host_entry(ip, hostname)
        if success:
            console.print(f"  [green]Host entry added: {hostname} -> {ip}[/green]")
    elif hostname:
        console.print(f"  [dim]Skipping hosts file (--no-hosts).[/dim]")

    console.print()

    # Check for existing active session for this machine
    target_slug = f"htb:{machine_name.lower().replace(' ', '-')}"
    existing = queries.get_active_session(target_slug)

    if existing:
        if Confirm.ask(f"  Resume existing session for [bold]{machine_name}[/bold]?"):
            session = HtbSession.resume(existing, machine_ip=ip, hostname=hostname)
            console.print(f"  [green]Session resumed.[/green]")
        else:
            queries.update_session(existing["session_id"], status="abandoned")
            session = HtbSession.create(ip, machine_name, hostname)
    else:
        session = HtbSession.create(ip, machine_name, hostname)

    htb_hunt_loop(session)

    # Offer to clean up hosts entry
    if hostname and not no_hosts:
        if Confirm.ask(f"\n  Remove {hostname} from /etc/hosts?"):
            from sudolabs.htb.hosts import remove_host_entry
            remove_host_entry(ip, hostname)
            console.print(f"  [dim]Host entry removed.[/dim]")


@app.command()
def targets(
    difficulty: str = typer.Option(None, "--difficulty", "-d", help="Filter by difficulty (easy/medium/hard/elite)"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category slug"),
):
    """List all available targets with their status."""
    _ensure_db()
    _show_targets(difficulty=difficulty, category=category)


def _show_targets(difficulty: str | None = None, category: str | None = None):
    """Internal target listing with optional category browsing."""
    registry = TargetRegistry()

    # If no filter specified, show category selection
    if not difficulty and not category:
        cat_choice = _select_category(registry)
        if cat_choice is None:
            return
        if cat_choice != "all":
            category = cat_choice

    target_list = registry.get_all(difficulty=difficulty, category=category)

    if not target_list:
        warning_panel("No Targets", "No targets found matching your criteria.")
        return

    # Build title
    if category:
        from sudolabs.constants import CATEGORY_DISPLAY_NAMES, Category
        try:
            title = CATEGORY_DISPLAY_NAMES[Category(category)]
        except (ValueError, KeyError):
            title = category.replace("-", " ").title()
    elif difficulty:
        title = f"{difficulty.capitalize()} Targets"
    else:
        title = "All Targets"

    progress_map = queries.get_all_progress()
    render_target_table(target_list, progress_map, title=title)

    # Summary line
    total = len(target_list)
    completed = sum(1 for t in target_list if progress_map.get(t.slug, {}).get("status") == "completed")
    total_score = sum(p.get("best_score", 0) for p in progress_map.values())
    console.print(f"  [dim]Completed: {completed}/{total}  |  Total Score: {total_score:,}[/dim]\n")


@app.command()
def hunt(
    target_slug: str = typer.Argument(..., help="Target slug to hunt"),
):
    """Launch a target and begin the hunt."""
    _ensure_db()
    _launch_hunt(target_slug)


def _launch_hunt(target_slug: str):
    """Internal hunt launcher."""
    from sudolabs.engine.session import HuntSession
    from sudolabs.engine.tracker import inject_flags_into_containers, run_post_start_commands, display_stage_info
    from sudolabs.scoring.achievements import check_achievements

    registry = TargetRegistry()
    target = registry.get_by_slug(target_slug)

    if not target:
        error_panel("Not Found", f"Target '{target_slug}' not found.")
        return

    # Check for existing active session
    existing = queries.get_active_session(target_slug)
    if existing:
        if Confirm.ask(f"  Resume existing session for [bold]{target.name}[/bold]?"):
            session = HuntSession.resume(existing, target)
            console.print(f"  [green]Session resumed.[/green]")
        else:
            queries.update_session(existing["session_id"], status="abandoned")
            session = None
    else:
        session = None

    # Launch Docker environment
    console.print(f"\n  [bold bright_red]Preparing: {target.name}[/bold bright_red]\n")

    target_dir = registry.get_target_dir(target_slug)
    if not target_dir or not (target_dir / "docker-compose.yml").exists():
        warning_panel(
            "No Docker Environment",
            f"Target '{target_slug}' has no docker-compose.yml.\n"
            f"Running in practice mode (no live containers).\n\n"
            f"Target dir: {target_dir}"
        )
        # Still allow session for practice/demo
        if not session:
            session = HuntSession.create(target)
        _hunt_loop(session, container_info=None)
        return

    try:
        from sudolabs.docker.manager import DockerManager
        docker_mgr = DockerManager()

        with console.status("[bold yellow]Starting target environment...[/bold yellow]"):
            container_info = docker_mgr.launch_target(target_dir, target_slug)

        console.print("  [green]Target environment is running.[/green]\n")

        # Create session and inject flags
        if not session:
            session = HuntSession.create(target)

        if container_info.get("container_ids"):
            run_post_start_commands(target, container_info["container_ids"], docker_mgr)
            inject_flags_into_containers(session, container_info["container_ids"], docker_mgr)

        _hunt_loop(session, container_info)

        # Cleanup after hunt
        if session.completed or Confirm.ask("\n  Destroy target containers?"):
            with console.status("[bold yellow]Cleaning up...[/bold yellow]"):
                docker_mgr.destroy_target(target_dir, target_slug)
            console.print("  [dim]Target environment destroyed.[/dim]\n")

    except RuntimeError as e:
        error_panel("Docker Error", str(e))
        console.print("  [dim]Run 'sudolabs doctor' to diagnose issues.[/dim]\n")


def _draw_hunt_status_bar(session, target, target_ip):
    """Draw a compact status bar for the Docker hunt loop."""
    from rich.panel import Panel
    svc_text = ", ".join(f"{svc.name}:{svc.port}" for svc in target.services) or "none"
    header = (
        f"  [bold bright_red]{target.name}[/bold bright_red]"
        f"  |  [bold]{target_ip}[/bold]"
        f"  |  {svc_text}"
        f"  |  [bold]{session.elapsed_formatted}[/bold]"
        f"  |  Stage {session.current_stage + 1}/{target.stage_count}"
        f"  |  [bright_yellow]{session.total_score} pts[/bright_yellow]"
    )
    console.print(Panel(header, border_style="bright_red", padding=(0, 1)))


def _hunt_loop(session, container_info: dict | None):
    """Main hunt interaction loop."""
    from sudolabs.engine.tracker import display_stage_info
    from sudolabs.scoring.achievements import check_achievements
    from sudolabs.ai.helper import AIHelper

    target = session.target
    ai = AIHelper()

    # Determine target IP
    target_ip = "127.0.0.1"
    if container_info:
        target_ip = container_info.get("ip", "127.0.0.1")

    # Smart notes manager
    from sudolabs.notes import NoteManager, get_auto_notes_enabled
    notes_mgr = NoteManager(
        session_id=session.session_id,
        target_slug=target.slug,
        target_name=target.name,
        target_ip=target_ip,
        difficulty=target.difficulty,
        ai=ai,
    )

    # Command bar shortcuts for Docker hunt mode
    HUNT_COMMANDS = [
        ("ask", "AI Help"),
        ("hint", "Get Hint"),
        ("submit", "Flag"),
        ("info", "Progress"),
        ("note", "Notes"),
        ("help", "All Cmds"),
    ]

    bar = FixedBar(HUNT_COMMANDS, "sudolabs")

    def _redraw():
        bar.clear_scroll_area()
        _draw_hunt_status_bar(session, target, target_ip)

    # Activate fixed bar and initial display
    bar.activate()

    # Display briefing
    if target.briefing:
        console.print()
        info_panel("MISSION BRIEFING", target.briefing, border_style="bright_red")

    # Show target connection info
    console.print(f"\n  [bold]Target:[/bold] {target_ip}")
    for svc in target.services:
        console.print(f"  [bold]{svc.name}:[/bold] {target_ip}:{svc.port} ({svc.protocol})")
    console.print()

    # Show initial attack chain
    stages = [{"name": s.name, "points": s.points} for s in target.attack_chain]
    render_attack_chain(stages, session.current_stage)
    display_stage_info(session)

    # Track command history so the AI can see what the user has run
    command_history: list[dict] = []

    # Hunt loop
    try:
        while not session.completed:
            user_input = bar.get_input()

            if not user_input.strip():
                continue

            parts = user_input.strip().split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd == "clear":
                _redraw()
                render_attack_chain(stages, session.current_stage)
                display_stage_info(session)

            elif cmd == "submit":
                if not arg:
                    arg = Prompt.ask("  [bold]Enter flag[/bold]")
                result = session.submit_flag(arg)

                if result["correct"]:
                    flag_panel(arg.strip(), result["stage_name"], result["points"])
                    ai.add_event(
                        f"Flag captured! Stage '{result['stage_name']}' complete. "
                        f"+{result['points']} pts. "
                        f"Now on stage {session.current_stage + 1}/{target.stage_count}."
                    )

                    # Auto-note: flag captured
                    if get_auto_notes_enabled():
                        hints = session.get_stage_hints_count()
                        notes_mgr.add_auto_note(
                            "flag_captured",
                            stage_name=result["stage_name"],
                            points=result["points"],
                            elapsed=session.elapsed_formatted,
                            hints=sum(hints.values()),
                        )

                    # Check achievements
                    session_data = {
                        "session_id": session.session_id,
                        "total_score": session.total_score,
                        "time_elapsed_secs": session.elapsed_seconds,
                    }
                    new_achievements = check_achievements(
                        session_id=session.session_id,
                        session_data=session_data,
                        target=target,
                    )
                    for ach in new_achievements:
                        achievement_panel(ach.name, ach.description, ach.points)

                    if result["completed"]:
                        console.print()
                        success_panel(
                            "HUNT COMPLETE",
                            f"[bold]Target:[/bold] {target.name}\n"
                            f"[bold]Total Score:[/bold] [bright_yellow]{session.total_score}[/bright_yellow]\n"
                            f"[bold]Time:[/bold] {session.elapsed_formatted}\n"
                            f"\n[bold green]Excellent work, hunter![/bold green]"
                        )
                        break
                    else:
                        # Show updated attack chain
                        render_attack_chain(stages, session.current_stage)
                        display_stage_info(session)
                else:
                    console.print(f"  [red]{result['message']}[/red]")

            elif cmd == "hint":
                level = 1
                if arg:
                    try:
                        level = int(arg)
                        level = max(1, min(3, level))
                    except ValueError:
                        pass

                from sudolabs.htb.loop import _build_history_context
                history_ctx = _build_history_context(command_history)
                hint_text, source = ai.get_hint(session, level, target_ip=target_ip, command_history=history_ctx)
                session.record_hint(level)

                score_impact = {1: "-15%", 2: "-35%", 3: "-60%"}.get(level, "varies")
                hint_panel(hint_text, level, score_impact)

                # Auto-note: hint used
                if get_auto_notes_enabled():
                    stage_name = session.current_stage_obj.name if session.current_stage_obj else "Unknown"
                    notes_mgr.add_auto_note("hint_used", level=level, phase=stage_name)

            elif cmd == "ask":
                if not arg:
                    arg = Prompt.ask("  [bold blue]Ask the AI[/bold blue]")
                if not arg:
                    continue

                if ai.is_available():
                    from sudolabs.htb.loop import _build_history_context
                    history_ctx = _build_history_context(command_history)
                    with console.status("[bold blue]Thinking...[/bold blue]"):
                        response = ai.chat(session, arg, target_ip=target_ip, command_history=history_ctx)
                    info_panel("AI Helper", response, border_style="blue")
                else:
                    warning_panel(
                        "AI Unavailable",
                        "Set your API key with: sudolabs config --set-api-key\n\n"
                        "Static hints are still available - try: hint 1"
                    )

            elif cmd == "info":
                render_attack_chain(stages, session.current_stage)
                display_stage_info(session)

            elif cmd == "status":
                _redraw()
                hints = session.get_stage_hints_count()
                total_hints = sum(hints.values())
                console.print(
                    f"\n  [bold]Session:[/bold] {session.session_id[:8]}  "
                    f"[bold]Time:[/bold] {session.elapsed_formatted}  "
                    f"[bold]Score:[/bold] [bright_yellow]{session.total_score}[/bright_yellow]  "
                    f"[bold]Hints:[/bold] {total_hints}  "
                    f"[bold]Stage:[/bold] {session.current_stage + 1}/{target.stage_count}"
                )

            elif cmd == "target":
                # Quick reference for target connection info
                console.print(f"  [bold]Target IP:[/bold] {target_ip}")
                for svc in target.services:
                    console.print(f"  [bold]{svc.name}:[/bold] {target_ip}:{svc.port} ({svc.protocol})")

            elif cmd == "note":
                if not arg:
                    arg = Prompt.ask("  [bold]Note[/bold]")
                if arg:
                    stage_name = session.current_stage_obj.name if session.current_stage_obj else "Unknown"
                    if ai.is_available():
                        with console.status("[bold green]Formatting note...[/bold green]"):
                            formatted = notes_mgr.add_user_note(arg, stage_name, session.elapsed_formatted)
                        info_panel("Note Saved", formatted, border_style="green")
                    else:
                        notes_mgr.add_user_note(arg, stage_name, session.elapsed_formatted)
                        console.print("  [green]Note saved.[/green]")

            elif cmd == "notes":
                session_notes = notes_mgr.get_session_notes()
                if session_notes:
                    console.print("\n  [bold]Session Notes:[/bold]")
                    for i, n in enumerate(session_notes, 1):
                        tag = "[dim][auto][/dim] " if n["note_type"] == "auto" else ""
                        console.print(f"  {i}. {tag}{n['raw_text']}")
                    console.print()
                else:
                    console.print("  [dim]No notes yet. Use 'note <text>' to add one.[/dim]")

            elif cmd == "flag":
                # Show the current flag (for development/testing only)
                current_flag = session.get_current_flag()
                if current_flag:
                    console.print(f"  [dim]Current flag (dev): {current_flag}[/dim]")
                else:
                    console.print("  [dim]No flag for current stage.[/dim]")

            elif cmd == "pause":
                session.pause()
                console.print("  [yellow]Session paused. Resume with 'sudolabs hunt {}'.".format(target.slug) + "[/yellow]")
                break

            elif cmd in ("abort", "quit", "exit"):
                if Confirm.ask("  [red]Abort this hunt?[/red]"):
                    session.abort()
                    console.print("  [red]Hunt aborted.[/red]")
                    break

            elif cmd == "help":
                info_panel("Hunt Commands", (
                    "[bold blue]ask[/bold blue] <question> [bold]Ask the AI anything[/bold] (e.g. 'ask what nmap command should I run')\n"
                    "[bold]hint[/bold] [1-3]     Get a hint (1=nudge, 2=direction, 3=walkthrough)\n"
                    "[bold]submit[/bold] <flag>  Submit a flag for the current stage\n"
                    "[bold green]note[/bold green] <text>   Save an AI-enhanced pentest note\n"
                    "[bold green]notes[/bold green]          View all saved notes for this session\n"
                    "[bold]info[/bold]           Show current stage info and attack chain\n"
                    "[bold]target[/bold]         Show target IP and ports\n"
                    "[bold]status[/bold]         Refresh status header\n"
                    "[bold]clear[/bold]          Clear screen and redraw header\n"
                    "[bold]pause[/bold]          Pause and save session\n"
                    "[bold]abort[/bold]          Abandon this hunt\n"
                    "[bold]help[/bold]           Show this help\n"
                    "\n"
                    "[dim]Any unrecognized input is passed directly to the system shell,\n"
                    "so you can run nmap, curl, gobuster, etc. right here.[/dim]"
                ), border_style="cyan")

            else:
                # Pass unrecognized input to the system shell (capture for AI context)
                full_cmd = user_input.strip()
                console.print(f"  [dim]$ {full_cmd}[/dim]\n")
                import subprocess as _sp
                try:
                    result = _sp.run(full_cmd, shell=True, capture_output=True, text=True, timeout=300)
                    output = ""
                    if result.stdout:
                        print(result.stdout, end="")
                        output += result.stdout
                    if result.stderr:
                        print(result.stderr, end="")
                        output += result.stderr
                    truncated = output[:3000] if len(output) > 3000 else output
                    command_history.append({"cmd": full_cmd, "output": truncated})
                    if len(command_history) > 10:
                        command_history.pop(0)
                    # Feed into AI conversation memory
                    ai.add_command(full_cmd, truncated)
                except _sp.TimeoutExpired:
                    console.print("  [red]Command timed out (5 min limit).[/red]")
                except Exception as e:
                    console.print(f"  [red]Error running command: {e}[/red]")

    finally:
        bar.deactivate()


@app.command()
def hint(
    level: int = typer.Option(1, "--level", "-l", min=1, max=3, help="Hint specificity (1-3)"),
):
    """Get a hint for the active hunt session."""
    _ensure_db()

    active = queries.get_active_session()
    if not active:
        error_panel("No Active Hunt", "Start a hunt first with: sudolabs hunt <target>")
        return

    from sudolabs.engine.session import HuntSession
    from sudolabs.ai.helper import AIHelper

    registry = TargetRegistry()
    target = registry.get_by_slug(active["target_slug"])
    if not target:
        error_panel("Target Not Found", f"Target '{active['target_slug']}' not found.")
        return

    session = HuntSession.resume(active, target)
    ai = AIHelper()

    hint_text, source = ai.get_hint(session, level)
    session.record_hint(level)

    score_impact = {1: "-15%", 2: "-35%", 3: "-60%"}.get(level, "varies")
    hint_panel(hint_text, level, score_impact)


@app.command(name="submit")
def submit_flag(
    flag: str = typer.Argument(..., help="Flag to submit"),
):
    """Submit a flag for the active hunt session."""
    _ensure_db()

    active = queries.get_active_session()
    if not active:
        error_panel("No Active Hunt", "Start a hunt first with: sudolabs hunt <target>")
        return

    from sudolabs.engine.session import HuntSession
    from sudolabs.scoring.achievements import check_achievements

    registry = TargetRegistry()
    target = registry.get_by_slug(active["target_slug"])
    if not target:
        error_panel("Target Not Found", f"Target '{active['target_slug']}' not found.")
        return

    session = HuntSession.resume(active, target)
    result = session.submit_flag(flag)

    if result["correct"]:
        flag_panel(flag.strip(), result["stage_name"], result["points"])
        if result["completed"]:
            success_panel("HUNT COMPLETE", f"Total Score: {session.total_score}")
    else:
        console.print(f"  [red]{result['message']}[/red]")


@app.command()
def score(
    target_slug: str = typer.Argument(None, help="Target for detailed score"),
):
    """View scores and achievements."""
    _ensure_db()
    _show_score(target_slug)


def _show_score(target_slug: str | None = None):
    """Internal score display."""
    if target_slug:
        # Show per-target scorecard
        from sudolabs.ui.tables import render_score_table
        registry = TargetRegistry()
        target = registry.get_by_slug(target_slug)
        if not target:
            error_panel("Not Found", f"Target '{target_slug}' not found.")
            return

        # Find the best session for this target
        from sudolabs.db.database import get_db
        with get_db() as db:
            row = db.execute(
                "SELECT * FROM sessions WHERE target_slug = ? AND status = 'completed' ORDER BY total_score DESC LIMIT 1",
                (target_slug,)
            ).fetchone()

        if not row:
            info_panel(target.name, "No completed sessions for this target yet.")
            return

        completions = queries.get_stage_completions(row["session_id"])
        render_score_table([dict(c) for c in completions])
    else:
        # Show overall dashboard
        stats = queries.get_completion_stats()
        achievements = queries.get_all_achievements()
        profile = queries.get_profile()

        # Get category progress stats
        registry = TargetRegistry()
        progress_map = queries.get_all_progress()
        cat_stats = registry.get_category_stats(progress_map)

        render_score_dashboard(
            total_score=profile["total_score"],
            easy_completed=stats["counts"].get("easy", 0),
            medium_completed=stats["counts"].get("medium", 0),
            hard_completed=stats["counts"].get("hard", 0),
            elite_completed=stats["counts"].get("elite", 0),
            easy_score=stats["scores"].get("easy", 0),
            medium_score=stats["scores"].get("medium", 0),
            hard_score=stats["scores"].get("hard", 0),
            elite_score=stats["scores"].get("elite", 0),
            achievements=[dict(a) for a in achievements],
            htb_completed=stats["counts"].get("htb", 0),
            category_stats=cat_stats,
        )


@app.command()
def profile(
    set_name: str = typer.Option(None, "--set-name", help="Set profile username"),
):
    """View your hunter profile and statistics."""
    _ensure_db()

    if set_name:
        set_username(set_name)
        console.print(f"  [green]Username set to: {set_name}[/green]")
        return

    _show_profile()


def _show_profile():
    """Internal profile display with interactive editing."""
    while True:
        prof = queries.get_profile()
        stats = queries.get_completion_stats()
        achievements = queries.get_all_achievements()
        total_time_secs = queries.get_total_time()
        total_hints = queries.get_total_hints_used()

        total_completed = sum(stats["counts"].values())
        total_targets = TargetRegistry().total_count

        hours, remainder = divmod(total_time_secs, 3600)
        mins, _ = divmod(remainder, 60)
        total_time_str = f"{hours}h {mins}m"

        render_profile(
            username=get_username(),
            rank=get_rank(prof["total_score"]),
            total_score=prof["total_score"],
            targets_completed=total_completed,
            total_targets=total_targets,
            total_time=total_time_str,
            total_hints=total_hints,
            achievements_count=len(achievements),
            total_achievements=11,
        )

        console.print("  [bold bright_cyan][1][/bold bright_cyan] [dim]Change username[/dim]")
        console.print("  [bold bright_cyan][2][/bold bright_cyan] [dim]Set API key[/dim]")
        console.print("  [dim]Press Enter to go back[/dim]\n")

        action = Prompt.ask("  [bold]Select option[/bold]", default="")

        if action == "1":
            current = get_username()
            new_name = Prompt.ask(
                f"  [bold]New username[/bold] [dim](current: {current})[/dim]",
                default="",
            )
            if new_name.strip():
                set_username(new_name.strip())
                console.print(f"  [green]Username updated to: {new_name.strip()}[/green]\n")
            else:
                console.print(f"  [dim]Username unchanged.[/dim]\n")
        elif action == "2":
            new_key = Prompt.ask("  [bold]Anthropic API key[/bold]", default="")
            if new_key.strip():
                set_api_key(new_key.strip())
                console.print(f"  [green]API key saved.[/green]\n")
            else:
                console.print(f"  [dim]API key unchanged.[/dim]\n")
        else:
            break


@app.command()
def reset(
    target_slug: str = typer.Argument(None, help="Target to reset"),
    all_targets: bool = typer.Option(False, "--all", help="Reset all progress"),
):
    """Reset target progress."""
    _ensure_db()

    if all_targets:
        if Confirm.ask("[red]Reset ALL progress? This cannot be undone.[/red]"):
            queries.reset_all_progress()
            success_panel("Reset Complete", "All progress has been reset.")
    elif target_slug:
        if Confirm.ask(f"[red]Reset progress for '{target_slug}'?[/red]"):
            queries.reset_target_progress(target_slug)

            # Also destroy Docker containers
            registry = TargetRegistry()
            target_dir = registry.get_target_dir(target_slug)
            if target_dir:
                try:
                    from sudolabs.docker.manager import DockerManager
                    docker_mgr = DockerManager()
                    docker_mgr.destroy_target(target_dir, target_slug)
                except Exception:
                    pass

            success_panel("Reset Complete", f"Progress for '{target_slug}' has been reset.")
    else:
        error_panel("Missing Argument", "Specify a target slug or use --all.")


@app.command()
def doctor():
    """Check system readiness for SudoLabs."""
    _ensure_db()
    _run_doctor()


def _run_doctor():
    """Internal system check."""
    import shutil
    import subprocess

    console.print("\n  [bold]SudoLabs System Check[/bold]\n")
    all_good = True

    # Python
    console.print(f"  Python {sys.version.split()[0]}", end="  ")
    console.print("[green]OK[/green]")

    # Docker
    docker_path = shutil.which("docker")
    if docker_path:
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, timeout=10)
            if result.returncode == 0:
                console.print("  Docker", end="  ")
                console.print("[green]OK (running)[/green]")
            else:
                console.print("  Docker", end="  ")
                console.print("[red]NOT RUNNING[/red]")
                all_good = False
        except Exception:
            console.print("  Docker", end="  ")
            console.print("[red]ERROR[/red]")
            all_good = False
    else:
        console.print("  Docker", end="  ")
        console.print("[red]NOT INSTALLED[/red]")
        all_good = False

    # docker compose
    try:
        result = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            console.print(f"  Docker Compose", end="  ")
            console.print("[green]OK[/green]")
        else:
            console.print("  Docker Compose", end="  ")
            console.print("[red]NOT AVAILABLE[/red]")
            all_good = False
    except Exception:
        console.print("  Docker Compose", end="  ")
        console.print("[red]NOT AVAILABLE[/red]")
        all_good = False

    # nmap
    nmap_path = shutil.which("nmap")
    if nmap_path:
        console.print("  Nmap", end="  ")
        console.print("[green]OK[/green]")
    else:
        console.print("  Nmap", end="  ")
        console.print("[yellow]NOT INSTALLED (HTB scan unavailable)[/yellow]")

    # API Key
    api_key = get_api_key()
    if api_key:
        console.print("  Anthropic API Key", end="  ")
        console.print(f"[green]SET ({api_key[:8]}...)[/green]")
    else:
        console.print("  Anthropic API Key", end="  ")
        console.print("[yellow]NOT SET (AI hints unavailable)[/yellow]")

    # Targets
    registry = TargetRegistry()
    target_count = registry.total_count
    console.print(f"  Targets Found", end="  ")
    if target_count > 0:
        console.print(f"[green]{target_count}[/green]")
    else:
        console.print("[yellow]0 (check targets/ directory)[/yellow]")

    # Database
    from sudolabs.config import DB_FILE
    console.print(f"  Database", end="  ")
    console.print(f"[green]{DB_FILE}[/green]")

    console.print()
    if all_good:
        console.print("  [bold green]All systems go. Happy hunting![/bold green]\n")
    else:
        console.print("  [bold yellow]Some issues detected. Fix them before hunting.[/bold yellow]\n")


@app.command()
def config(
    set_api_key_val: str = typer.Option(None, "--set-api-key", help="Set Anthropic API key"),
    notes_dir: str = typer.Option(None, "--notes-dir", help="Set notes directory path"),
    auto_notes: bool = typer.Option(None, "--auto-notes/--no-auto-notes", help="Toggle auto-notes"),
):
    """View or edit SudoLabs configuration."""
    _ensure_db()
    _show_config(set_api_key_val, notes_dir, auto_notes)


def _show_config(
    new_api_key: str | None = None,
    new_notes_dir: str | None = None,
    auto_notes_toggle: bool | None = None,
):
    """Internal config handler."""
    from sudolabs.config import (
        SUDOLABS_HOME, DB_FILE, TARGETS_DIR,
        get_notes_dir, set_notes_dir, get_auto_notes, set_auto_notes,
    )

    if new_api_key:
        set_api_key(new_api_key)
        console.print(f"  [green]API key saved.[/green]")
        return

    if new_notes_dir:
        set_notes_dir(new_notes_dir)
        console.print(f"  [green]Notes directory set to: {new_notes_dir}[/green]")
        return

    if auto_notes_toggle is not None:
        set_auto_notes(auto_notes_toggle)
        state = "enabled" if auto_notes_toggle else "disabled"
        console.print(f"  [green]Auto-notes {state}.[/green]")
        return

    console.print(f"\n  [bold]SudoLabs Configuration[/bold]\n")
    console.print(f"  SudoLabs Home: {SUDOLABS_HOME}")
    console.print(f"  Database:    {DB_FILE}")
    console.print(f"  Targets Dir: {TARGETS_DIR}")

    api_key = get_api_key()
    if api_key:
        console.print(f"  API Key:     {api_key[:8]}...{api_key[-4:]}")
    else:
        console.print(f"  API Key:     [yellow]Not set[/yellow]")

    console.print(f"  Username:    {get_username()}")

    nd = get_notes_dir()
    console.print(f"  Notes Dir:   {nd or '[yellow]Not set (will prompt on first use)[/yellow]'}")
    console.print(f"  Auto Notes:  {'[green]enabled[/green]' if get_auto_notes() else '[yellow]disabled[/yellow]'}")
    console.print()


def _interactive_ai_chat():
    """Interactive AI chat mode."""
    active = queries.get_active_session()
    if not active:
        warning_panel("No Active Hunt", "Start a hunt first to use the AI helper in context.\nYou can still set up your API key with: sudolabs config --set-api-key")
        return

    from sudolabs.engine.session import HuntSession
    from sudolabs.ai.helper import AIHelper

    registry = TargetRegistry()
    target = registry.get_by_slug(active["target_slug"])
    if not target:
        return

    session = HuntSession.resume(active, target)
    ai = AIHelper()

    if not ai.is_available():
        warning_panel("AI Unavailable", "Set your API key with: sudolabs config --set-api-key")
        return

    console.print("\n  [bold blue]AI Helper Chat[/bold blue] [dim](type 'quit' to exit)[/dim]\n")

    while True:
        question = Prompt.ask("  [bold blue]you[/bold blue]")
        if question.lower() in ("quit", "exit", "q"):
            break

        with console.status("[bold blue]Thinking...[/bold blue]"):
            response = ai.chat(session, question)

        console.print(f"\n  [bold cyan]AI[/bold cyan]: {response}\n")


@app.command()
def version():
    """Show SudoLabs version."""
    console.print(f"  SudoLabs v{__version__}")


@app.command()
def update(
    check: bool = typer.Option(False, "--check", "-c", help="Only check for updates, don't install."),
):
    """Update SudoLabs to the latest version.

    Pulls the latest code from GitHub and re-installs dependencies.
    Your progress, scores, and settings in ~/.sudolabs/ are never touched.
    """
    from sudolabs.updater import run_update, check_for_update, get_current_version

    console.print(f"\n  [bold red]SudoLabs[/bold red] v{get_current_version()}\n")

    if check:
        console.print("  Checking for updates...")
        available, local_sha, remote_sha = check_for_update()
        if available:
            console.print(f"  [bold green]Update available![/bold green]  local={local_sha}  remote={remote_sha}")
            console.print("  Run [cyan]sudolabs update[/cyan] to install it.\n")
        elif local_sha is None:
            console.print("  [yellow]Cannot check — not installed from git.[/yellow]\n")
        else:
            console.print(f"  [green]✓[/green] You're on the latest version ({local_sha}).\n")
        return

    console.print("  [bold]Updating SudoLabs...[/bold]\n")
    success = run_update(verbose=True)
    if not success:
        raise typer.Exit(code=1)
