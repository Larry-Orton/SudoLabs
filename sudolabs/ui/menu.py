"""Interactive main menu for SudoLabs."""

from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

from sudolabs.ui.theme import console


MENU_OPTIONS = [
    ("1", "Hunt", "Start hunting a target", "bold red"),
    ("2", "HTB Mode", "Hack an external machine (HackTheBox)", "bold bright_red"),
    ("3", "Targets", "Browse all available targets", "bold cyan"),
    ("4", "Score", "View your scores & achievements", "bold yellow"),
    ("5", "Profile", "View your hunter profile", "bold green"),
    ("6", "AI Chat", "Talk to the AI helper", "bold blue"),
    ("7", "Doctor", "Check system readiness", "bold magenta"),
    ("8", "Config", "Settings & configuration", "dim"),
    ("9", "Quit", "Exit SudoLabs", "dim red"),
]


def show_main_menu() -> str:
    """Display the main menu and return the user's selection."""
    menu_text = ""
    for key, label, desc, style in MENU_OPTIONS:
        menu_text += f"   [{style}][{key}][/{style}]  [{style}]{label:<12}[/{style}] [dim]{desc}[/dim]\n"

    console.print(Panel(
        menu_text.rstrip(),
        border_style="bright_red",
        padding=(1, 3),
    ))

    choice = Prompt.ask(
        "\n  [bold]Select an option[/bold]",
        choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"],
        default="1",
    )
    return choice
