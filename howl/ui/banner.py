"""ASCII wolf banner for Howl."""

from howl import __version__
from howl.ui.theme import console


WOLF_ART = r"""[bold red]
  _   _  _____  _    _  _
 | | | ||  _  || |  | || |
 | |_| || | | || |  | || |
 |  _  || | | || |/\| || |
 | | | |\ \_/ /\  /\  /| |____
 \_| |_/ \___/  \/  \/ \_____/[/bold red]"""


def display_banner():
    """Display the Howl banner with version info."""
    console.print(WOLF_ART)
    console.print()
    console.print(
        f"  [dim]v{__version__}[/dim]  [bold bright_red]|[/bold bright_red]  "
        f"[dim]Cybersecurity Hacking Lab[/dim]  [bold bright_red]|[/bold bright_red]  "
        f"[dim]The hunt begins here.[/dim]"
    )
    console.print()
