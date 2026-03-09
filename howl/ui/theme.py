"""Rich theme and console singleton for Howl."""

from rich.console import Console
from rich.theme import Theme

howl_theme = Theme({
    "howl.easy": "bold green",
    "howl.medium": "bold yellow",
    "howl.hard": "bold red",
    "howl.elite": "bold magenta",
    "howl.success": "bold green",
    "howl.danger": "bold red",
    "howl.warning": "bold yellow",
    "howl.info": "bold cyan",
    "howl.hint": "bold blue",
    "howl.banner": "bold red",
    "howl.muted": "dim",
    "howl.score": "bold bright_yellow",
    "howl.rank": "bold bright_cyan",
    "howl.flag": "bold bright_green",
    "howl.stage.done": "green",
    "howl.stage.active": "yellow",
    "howl.stage.locked": "dim",
})

console = Console(theme=howl_theme)
