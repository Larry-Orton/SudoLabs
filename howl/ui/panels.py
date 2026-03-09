"""Reusable Rich panel builders for Howl."""

from rich.panel import Panel
from rich.text import Text

from howl.ui.theme import console
from howl.constants import DIFFICULTY_COLORS, Difficulty


def info_panel(title: str, content: str, border_style: str = "cyan"):
    """Display an info panel."""
    console.print(Panel(content, title=title, border_style=border_style))


def success_panel(title: str, content: str):
    """Display a success panel."""
    console.print(Panel(content, title=title, border_style="green"))


def error_panel(title: str, content: str):
    """Display an error panel."""
    console.print(Panel(content, title=title, border_style="red"))


def warning_panel(title: str, content: str):
    """Display a warning panel."""
    console.print(Panel(content, title=title, border_style="yellow"))


def hunt_panel(target_name: str, difficulty: str, content: str):
    """Display a hunt status panel."""
    color = DIFFICULTY_COLORS.get(Difficulty(difficulty), "white")
    console.print(Panel(
        content,
        title=f"[bold]HUNTING: {target_name}[/bold]",
        subtitle=f"[{color}]{difficulty.upper()}[/{color}]",
        border_style=color,
    ))


def hint_panel(hint_text: str, level: int, score_impact: str):
    """Display an AI hint panel."""
    level_labels = {1: "Nudge", 2: "Direction", 3: "Walkthrough"}
    label = level_labels.get(level, f"Level {level}")
    console.print(Panel(
        f"{hint_text}\n\n[dim]Score Impact: {score_impact}[/dim]",
        title=f"[bold blue]AI HELPER[/bold blue] - {label} (Level {level}/3)",
        border_style="blue",
    ))


def flag_panel(flag_text: str, stage_name: str, points: int):
    """Display a flag capture celebration panel."""
    console.print(Panel(
        f"[bold green]FLAG CAPTURED![/bold green]\n\n"
        f"  Stage: {stage_name}\n"
        f"  Flag:  [bright_green]{flag_text}[/bright_green]\n"
        f"  Points: [bright_yellow]+{points}[/bright_yellow]",
        title="[bold bright_green]SUCCESS[/bold bright_green]",
        border_style="green",
    ))


def achievement_panel(name: str, description: str, points: int):
    """Display an achievement unlock panel."""
    console.print(Panel(
        f"[bold bright_yellow]ACHIEVEMENT UNLOCKED![/bold bright_yellow]\n\n"
        f"  {name}\n"
        f"  [dim]{description}[/dim]\n"
        f"  [bright_yellow]+{points} pts[/bright_yellow]",
        title="[bold bright_yellow]ACHIEVEMENT[/bold bright_yellow]",
        border_style="bright_yellow",
    ))


def draw_command_bar(
    commands: list[tuple[str, str]],
    border_style: str = "bright_red",
):
    """Render a nano-style bottom command bar showing available shortcuts.

    Displays a horizontal bar of [shortcut] Label pairs inside a bordered panel.

    Args:
        commands: List of (shortcut, label) tuples.
        border_style: Rich border style for the panel border.
    """
    parts = []
    for shortcut, label in commands:
        parts.append(
            f"[bold bright_red]\\[{shortcut}][/bold bright_red] "
            f"[dim]{label}[/dim]"
        )

    bar_content = "   ".join(parts)

    console.print(Panel(
        f"  {bar_content}",
        border_style=border_style,
        padding=(0, 1),
    ))
