"""Score dashboard and profile views for SudoLabs."""

from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text

from sudolabs.ui.theme import console
from sudolabs.constants import Difficulty, DIFFICULTY_COLORS, get_rank


def render_score_dashboard(
    total_score: int,
    easy_completed: int,
    medium_completed: int,
    hard_completed: int,
    elite_completed: int,
    easy_score: int,
    medium_score: int,
    hard_score: int,
    elite_score: int,
    achievements: list[dict],
    htb_completed: int = 0,
    category_stats: list[dict] | None = None,
):
    """Render the full score dashboard."""
    rank = get_rank(total_score)

    # Progress bars
    def progress_bar(completed: int, total: int, color: str) -> str:
        filled = int((completed / total) * 20) if total > 0 else 0
        bar = f"[{color}]#[/{color}]" * filled + "[dim]-[/dim]" * (20 - filled)
        return bar

    # Category progress section
    cat_section = ""
    if category_stats:
        cat_section = "  [bold]CATEGORIES[/bold]\n  ----------------\n"
        for cat in category_stats:
            color = cat["color"]
            name = cat["name"]
            completed = cat["completed"]
            total = cat["total"]
            score = cat["total_score"]
            bar = progress_bar(completed, total, color)
            score_str = f"{score:,} pts" if score > 0 else "--"
            cat_section += (
                f"  {bar}  [{color}]{name:<24}[/{color}] "
                f"{completed}/{total}   [dim]{score_str}[/dim]\n"
            )
        cat_section += "\n"

    # Difficulty breakdown
    diff_section = (
        f"  [bold]BY DIFFICULTY[/bold]\n  ----------------\n"
        f"  {progress_bar(easy_completed, 10, 'green')}  "
        f"[green]Easy[/green]    {easy_completed}/10   [dim]{easy_score:,} pts[/dim]\n"
        f"  {progress_bar(medium_completed, 10, 'yellow')}  "
        f"[yellow]Medium[/yellow]  {medium_completed}/10   [dim]{medium_score:,} pts[/dim]\n"
        f"  {progress_bar(hard_completed, 10, 'red')}  "
        f"[red]Hard[/red]    {hard_completed}/10   [dim]{hard_score:,} pts[/dim]\n"
        f"  {progress_bar(elite_completed, 10, 'magenta')}  "
        f"[magenta]Elite[/magenta]   {elite_completed}/10   [dim]{elite_score:,} pts[/dim]\n"
    )

    dashboard = (
        f"  [bold]Total Score:[/bold]  [bold bright_yellow]{total_score:,}[/bold bright_yellow] pts\n"
        f"  [bold]Rank:[/bold]         [bold bright_cyan]{rank}[/bold bright_cyan]\n"
        f"\n"
        f"{cat_section}"
        f"{diff_section}"
    )

    if htb_completed > 0:
        dashboard += (
            f"\n  [bold bright_red]HTB Machines:[/bold bright_red] {htb_completed} completed\n"
        )

    # Achievements section
    if achievements:
        dashboard += "\n  [bold]ACHIEVEMENTS[/bold]\n  ----------------\n"
        for ach in achievements:
            dashboard += (
                f"  [bright_yellow]*[/bright_yellow] "
                f"[bold]{ach['name']}[/bold] "
                f"[dim]{ach['description']}[/dim]  "
                f"[bright_yellow]+{ach['points']}[/bright_yellow]\n"
            )

    console.print(Panel(
        dashboard.rstrip(),
        title="[bold bright_yellow]SUDOLABS SCOREBOARD[/bold bright_yellow]",
        border_style="bright_yellow",
        padding=(1, 2),
    ))


def render_profile(
    username: str,
    rank: str,
    total_score: int,
    targets_completed: int,
    total_targets: int,
    total_time: str,
    total_hints: int,
    achievements_count: int,
    total_achievements: int,
):
    """Render the hunter profile view."""
    content = (
        f"  [bold]Hunter:[/bold]       [bold bright_cyan]{username}[/bold bright_cyan]\n"
        f"  [bold]Rank:[/bold]         [bold bright_cyan]{rank}[/bold bright_cyan]\n"
        f"  [bold]Total Score:[/bold]  [bold bright_yellow]{total_score:,}[/bold bright_yellow] pts\n"
        f"\n"
        f"  [bold]Targets:[/bold]      {targets_completed} / {total_targets} completed\n"
        f"  [bold]Total Time:[/bold]   {total_time}\n"
        f"  [bold]Hints Used:[/bold]   {total_hints}\n"
        f"  [bold]Achievements:[/bold] {achievements_count} / {total_achievements}\n"
    )

    console.print(Panel(
        content.rstrip(),
        title=f"[bold bright_cyan]HUNTER PROFILE[/bold bright_cyan]",
        border_style="bright_cyan",
        padding=(1, 2),
    ))
