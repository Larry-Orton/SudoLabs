"""Constants, enums, and ASCII art for SudoLabs."""

from enum import Enum


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ELITE = "elite"


class Category(str, Enum):
    WEB_EXPLOITATION = "web-exploitation"
    NETWORK_SERVICES = "network-services"
    PRIVILEGE_ESCALATION = "privilege-escalation"
    API_HACKING = "api-hacking"
    CRYPTOGRAPHY_SECRETS = "cryptography-secrets"


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

CATEGORY_COLORS = {
    Category.WEB_EXPLOITATION: "red",
    Category.NETWORK_SERVICES: "blue",
    Category.PRIVILEGE_ESCALATION: "yellow",
    Category.API_HACKING: "cyan",
    Category.CRYPTOGRAPHY_SECRETS: "magenta",
}

CATEGORY_ICONS = {
    Category.WEB_EXPLOITATION: "W",
    Category.NETWORK_SERVICES: "N",
    Category.PRIVILEGE_ESCALATION: "P",
    Category.API_HACKING: "A",
    Category.CRYPTOGRAPHY_SECRETS: "C",
}

CATEGORY_DISPLAY_NAMES = {
    Category.WEB_EXPLOITATION: "Web Exploitation",
    Category.NETWORK_SERVICES: "Network Services",
    Category.PRIVILEGE_ESCALATION: "Privilege Escalation",
    Category.API_HACKING: "API Hacking",
    Category.CRYPTOGRAPHY_SECRETS: "Cryptography & Secrets",
}

CATEGORY_DESCRIPTIONS = {
    Category.WEB_EXPLOITATION: "SQLi, XSS, SSRF, file uploads, command injection, LFI, deserialization",
    Category.NETWORK_SERVICES: "FTP, SMB, SSH, Redis, SNMP, DNS, NFS, pivoting",
    Category.PRIVILEGE_ESCALATION: "SUID, sudo, cron, PATH injection, capabilities, Docker escape, kernel",
    Category.API_HACKING: "IDOR, JWT, GraphQL, mass assignment, CORS, OAuth, broken auth",
    Category.CRYPTOGRAPHY_SECRETS: "Hardcoded creds, .env exposure, git leaks, padding oracle, weak hashing",
}

STATUS_ICONS = {
    TargetStatus.NOT_STARTED: "[dim]o[/dim]",
    TargetStatus.IN_PROGRESS: "[yellow]>[/yellow]",
    TargetStatus.COMPLETED: "[green]v[/green]",
}

RANKS = [
    (0, "Script Kiddie"),
    (500, "Hacktivist"),
    (2000, "Pentester"),
    (5000, "Exploit Dev"),
    (10000, "Red Team"),
    (20000, "APT Operator"),
    (35000, "Zero Day"),
]

SUDOLABS_BANNER = r"""[bold red]
  ███████╗██╗   ██╗██████╗  ██████╗ ██╗      █████╗ ██████╗ ███████╗
  ██╔════╝██║   ██║██╔══██╗██╔═══██╗██║     ██╔══██╗██╔══██╗██╔════╝
  ███████╗██║   ██║██║  ██║██║   ██║██║     ███████║██████╔╝███████╗
  ╚════██║██║   ██║██║  ██║██║   ██║██║     ██╔══██║██╔══██╗╚════██║
  ███████║╚██████╔╝██████╔╝╚██████╔╝███████╗██║  ██║██████╔╝███████║
  ╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝[/bold red]
"""

SUDOLABS_TAGLINE = "[dim]Your terminal. Your lab. Get root.[/dim]"


def get_rank(score: int) -> str:
    """Get rank title for a given score."""
    rank = "Script Kiddie"
    for threshold, title in RANKS:
        if score >= threshold:
            rank = title
    return rank
