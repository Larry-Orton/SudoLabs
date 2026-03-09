"""Attack chain stage tracker for Howl."""

from howl.engine.session import HuntSession
from howl.docker.manager import DockerManager
from howl.ui.theme import console
from howl.ui.panels import flag_panel


def inject_flags_into_containers(session: HuntSession, container_ids: list[str], docker_mgr: DockerManager):
    """Inject session flags into running containers at the paths defined in target.yaml.

    Args:
        session: The active hunt session with generated flags.
        container_ids: List of container IDs to inject into.
        docker_mgr: DockerManager instance.
    """
    if not container_ids:
        return

    primary_container = container_ids[0]

    for i, stage in enumerate(session.target.attack_chain):
        if i >= len(session.flags):
            break

        flag_text = session.flags[i]["flag"]
        flag_path = stage.flag.path

        # Ensure the directory exists and write the flag (as root to overwrite placeholders)
        flag_dir = "/".join(flag_path.split("/")[:-1])
        docker_mgr.exec_in_container(
            primary_container,
            f"mkdir -p {flag_dir} && echo '{flag_text}' > {flag_path}",
            user="root",
        )

    console.print("  [dim]Flags injected into target environment.[/dim]")


def run_post_start_commands(target, container_ids: list[str], docker_mgr: DockerManager):
    """Run post_start commands defined in target.yaml."""
    if not target.docker.post_start:
        return

    for cmd_def in target.docker.post_start:
        # Find container matching the service name, or use first container
        container_id = container_ids[0]
        try:
            docker_mgr.exec_in_container(container_id, cmd_def.command, user="root")
        except Exception as e:
            console.print(f"  [dim yellow]Post-start command failed: {e}[/dim yellow]")


def display_stage_info(session: HuntSession):
    """Display current stage information."""
    stage = session.current_stage_obj
    if not stage:
        console.print("[yellow]No active stage.[/yellow]")
        return

    console.print(f"\n  [bold]Stage {session.current_stage + 1}/{session.target.stage_count}:[/bold] "
                  f"[bold bright_cyan]{stage.name}[/bold bright_cyan]")
    console.print(f"  {stage.description}")
    if stage.tools_suggested:
        console.print(f"  [dim]Suggested tools:[/dim] [cyan]{', '.join(stage.tools_suggested)}[/cyan]")
    console.print()
