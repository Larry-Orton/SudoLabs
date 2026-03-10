"""Container health checks and readiness probes for SudoLabs."""

import socket
import time

from sudolabs.ui.theme import console


def wait_for_port(host: str, port: int, timeout: int = 60) -> bool:
    """Wait for a TCP port to become reachable."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except (ConnectionRefusedError, TimeoutError, OSError):
            time.sleep(1)
    return False


def check_services_ready(services: list[dict], host: str = "127.0.0.1", timeout: int = 60) -> bool:
    """Check that all target services are reachable.

    Args:
        services: List of service dicts with 'port' and 'name'.
        host: Host to connect to.
        timeout: Max seconds to wait.

    Returns:
        True if all services are ready.
    """
    for svc in services:
        port = svc.get("port")
        name = svc.get("name", f"port {port}")
        if not port:
            continue

        console.print(f"  [dim]Waiting for {name} on port {port}...[/dim]", end="")
        if wait_for_port(host, port, timeout):
            console.print(" [green]ready[/green]")
        else:
            console.print(" [red]timeout[/red]")
            return False

    return True
