"""Constants, enums, and ASCII art for Howl."""

from enum import Enum


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ELITE = "elite"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class TargetStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


DIFFICULTY_COLORS = {
    Difficulty.EASY: "green",
    Difficulty.MEDIUM: "yellow",
    Difficulty.HARD: "red",
    Difficulty.ELITE: "magenta",
}

DIFFICULTY_ICONS = {
    Difficulty.EASY: "[green]*[/green]",
    Difficulty.MEDIUM: "[yellow]*[/yellow]",
    Difficulty.HARD: "[red]*[/red]",
    Difficulty.ELITE: "[magenta]*[/magenta]",
}

STATUS_ICONS = {
    TargetStatus.NOT_STARTED: "[dim]o[/dim]",
    TargetStatus.IN_PROGRESS: "[yellow]>[/yellow]",
    TargetStatus.COMPLETED: "[green]v[/green]",
}

RANKS = [
    (0, "Pup"),
    (500, "Prowler"),
    (2000, "Stalker"),
    (5000, "Predator"),
    (10000, "Alpha"),
    (20000, "Dire Wolf"),
    (35000, "Apex Howler"),
]

WOLF_BANNER = r"""[bold red]
    ___  ___  ________  ___       __   ___
   |\  \|\  \|\   __  \|\  \     |\  \|\  \
   \ \  \\\  \ \  \|\  \ \  \    \ \  \ \  \
    \ \   __  \ \  \\\  \ \  \  __\ \  \ \  \
     \ \  \ \  \ \  \\\  \ \  \|\__\_\  \ \  \____
      \ \__\ \__\ \_______\ \____________\ \_______\
       \|__|\|__|\|_______|\|____________|\|_______|[/bold red]
"""

HOWL_TAGLINE = "[dim]The hunt begins in the terminal.[/dim]"


def get_rank(score: int) -> str:
    """Get rank title for a given score."""
    rank = "Pup"
    for threshold, title in RANKS:
        if score >= threshold:
            rank = title
    return rank
