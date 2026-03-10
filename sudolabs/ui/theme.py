"""Rich theme and console singleton for SudoLabs."""

from rich.console import Console
from rich.theme import Theme

sudo_theme = Theme({
    "sudo.easy": "bold green",
    "sudo.medium": "bold yellow",
    "sudo.hard": "bold red",
    "sudo.elite": "bold magenta",
    "sudo.success": "bold green",
    "sudo.danger": "bold red",
    "sudo.warning": "bold yellow",
    "sudo.info": "bold cyan",
    "sudo.hint": "bold blue",
    "sudo.banner": "bold red",
    "sudo.muted": "dim",
    "sudo.score": "bold bright_yellow",
    "sudo.rank": "bold bright_cyan",
    "sudo.flag": "bold bright_green",
    "sudo.stage.done": "green",
    "sudo.stage.active": "yellow",
    "sudo.stage.locked": "dim",
})

console = Console(theme=sudo_theme)
