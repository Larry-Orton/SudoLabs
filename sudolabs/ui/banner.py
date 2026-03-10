"""ASCII banner for SudoLabs."""

from sudolabs import __version__
from sudolabs.ui.theme import console
from sudolabs.constants import SUDOLABS_BANNER


def display_banner():
    """Display the SudoLabs banner with version info."""
    console.print(SUDOLABS_BANNER)
    console.print()
    console.print(
        f"  [dim]v{__version__}[/dim]  [bold bright_red]|[/bold bright_red]  "
        f"[dim]Cybersecurity Hacking Lab[/dim]  [bold bright_red]|[/bold bright_red]  "
        f"[dim]Your terminal. Your lab. Get root.[/dim]"
    )
    console.print()
