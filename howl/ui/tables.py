"""Target list tables and score tables for Howl."""

from rich.table import Table

from howl.ui.theme import console
from howl.constants import (
    Difficulty, DIFFICULTY_COLORS, DIFFICULTY_ICONS,
    STATUS_ICONS, TargetStatus,
)


def render_target_table(targets: list, progress_map: dict | None = None):
    """Render a table of all targets with their status.

    Args:
        targets: List of Target model objects.
        progress_map: Dict mapping target_slug -> {status, best_score, best_time}.
    """
    if progress_map is None:
        progress_map = {}

    table = Table(
        title="[bold]Howl Targets[/bold]",
        border_style="bright_red",
        header_style="bold bright_red",
        show_lines=False,
        padding=(0, 1),
    )

    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Target", min_width=30)
    table.add_column("Difficulty", width=12, justify="center")
    table.add_column("Status", width=14, justify="center")
    table.add_column("Score", width=8, justify="right")
    table.add_column("Best Time", width=10, justify="right")

    for i, target in enumerate(targets, 1):
        slug = target.slug
        progress = progress_map.get(slug, {})
        status = progress.get("status", TargetStatus.NOT_STARTED)
        best_score = progress.get("best_score", 0)
        best_time = progress.get("best_time_secs")

        diff = Difficulty(target.difficulty)
        color = DIFFICULTY_COLORS[diff]
        diff_display = f"{DIFFICULTY_ICONS[diff]} [{color}]{diff.value.capitalize()}[/{color}]"

        status_enum = TargetStatus(status) if isinstance(status, str) else status
        status_display = f"{STATUS_ICONS[status_enum]} {status_enum.value.replace('_', ' ').title()}"

        score_display = f"[bright_yellow]{best_score}[/bright_yellow]" if best_score > 0 else "[dim]--[/dim]"

        if best_time:
            mins, secs = divmod(best_time, 60)
            hours, mins = divmod(mins, 60)
            time_display = f"{hours:02d}:{mins:02d}:{secs:02d}"
        else:
            time_display = "[dim]--[/dim]"

        table.add_row(
            str(i),
            f"[bold]{target.name}[/bold]",
            diff_display,
            status_display,
            score_display,
            time_display,
        )

    console.print()
    console.print(table)
    console.print()


def render_score_table(completions: list):
    """Render a detailed score breakdown table."""
    table = Table(
        title="[bold]Score Breakdown[/bold]",
        border_style="bright_yellow",
        header_style="bold bright_yellow",
    )

    table.add_column("Stage", min_width=20)
    table.add_column("Base Points", width=12, justify="right")
    table.add_column("Hint Penalty", width=12, justify="right")
    table.add_column("Time Bonus", width=12, justify="right")
    table.add_column("Final Score", width=12, justify="right")

    for comp in completions:
        base = comp.get("points_earned", 0)
        hint_mult = comp.get("hint_multiplier", 1.0)
        time_mult = comp.get("time_bonus", 1.0)
        final = int(base * hint_mult * time_mult)

        hint_display = f"[red]x{hint_mult:.2f}[/red]" if hint_mult < 1.0 else "[green]x1.00[/green]"
        time_display = f"[green]x{time_mult:.2f}[/green]" if time_mult > 1.0 else f"x{time_mult:.2f}"

        table.add_row(
            comp.get("stage_name", "Unknown"),
            str(base),
            hint_display,
            time_display,
            f"[bold bright_yellow]{final}[/bold bright_yellow]",
        )

    console.print(table)
