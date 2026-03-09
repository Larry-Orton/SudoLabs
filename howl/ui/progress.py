"""Attack chain progress display for Howl."""

from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.table import Table

from howl.ui.theme import console


def render_attack_chain(stages: list, current_stage: int, stage_scores: dict | None = None):
    """Render the attack chain progress display.

    Args:
        stages: List of stage dicts with 'name' and 'points' keys.
        current_stage: Index of the current active stage (0-based).
        stage_scores: Dict mapping stage index -> points earned.
    """
    if stage_scores is None:
        stage_scores = {}

    lines = []
    total_stages = len(stages)

    for i, stage in enumerate(stages):
        name = stage.get("name", f"Stage {i+1}")
        points = stage.get("points", 0)

        if i < current_stage:
            # Completed
            bar = "[green]#[/green]" * 10
            score_text = f"[green]+{stage_scores.get(i, points)} pts[/green]"
            icon = "[bold green][DONE][/bold green]"
            style = "howl.stage.done"
        elif i == current_stage:
            # Active
            filled = 5
            bar = "[yellow]=[/yellow]" * filled + "[dim]-[/dim]" * (10 - filled)
            score_text = "[yellow]In Progress[/yellow]"
            icon = "[bold yellow]<[/bold yellow]"
            style = "howl.stage.active"
        else:
            # Locked
            bar = "[dim]-[/dim]" * 10
            score_text = "[dim]Locked[/dim]"
            icon = "[dim].[/dim]"
            style = "howl.stage.locked"

        lines.append(f"  [{style}][{bar}] {name:<20} {icon}  {score_text}[/{style}]")

    content = "\n".join(lines)
    console.print(Panel(
        content,
        title="[bold]ATTACK CHAIN[/bold]",
        border_style="bright_red",
    ))


def render_hunt_status(
    target_name: str,
    difficulty: str,
    target_ip: str,
    ports: list[str],
    session_id: str,
    elapsed: str,
    current_stage_name: str,
    current_stage_desc: str,
    suggested_tools: list[str],
    total_score: int,
    hints_used: int,
    hint_penalty: str,
):
    """Render the full hunt status panel."""
    from howl.constants import DIFFICULTY_COLORS, Difficulty

    color = DIFFICULTY_COLORS.get(Difficulty(difficulty), "white")
    port_str = ", ".join(ports) if ports else "scanning..."

    content = (
        f"  Target IP: [bold]{target_ip}[/bold]    Ports: [bold]{port_str}[/bold]\n"
        f"  Session:   [dim]{session_id[:8]}[/dim]      Time: [bold]{elapsed}[/bold]\n"
        f"\n"
        f"  [bold]Current Objective:[/bold]\n"
        f"  {current_stage_desc}\n"
        f"\n"
        f"  [dim]Suggested Tools:[/dim] [cyan]{', '.join(suggested_tools)}[/cyan]\n"
        f"\n"
        f"  Score: [bright_yellow]{total_score}[/bright_yellow]    "
        f"Hints Used: [blue]{hints_used}[/blue]    "
        f"Hint Penalty: [red]{hint_penalty}[/red]"
    )

    console.print(Panel(
        content,
        title=f"[bold]HUNTING: {target_name}[/bold]",
        subtitle=f"[{color}]{difficulty.upper()}[/{color}]",
        border_style=color,
        padding=(1, 2),
    ))

    console.print()
    console.print(
        "  [dim]Commands:[/dim] "
        "[bold]submit[/bold] <flag>  "
        "[bold]hint[/bold]  "
        "[bold]info[/bold]  "
        "[bold]pause[/bold]  "
        "[bold]abort[/bold]"
    )
