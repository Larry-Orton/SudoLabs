"""Docker network management for isolated SudoLabs labs."""

import subprocess


def create_network(name: str, subnet: str | None = None) -> bool:
    """Create an isolated Docker bridge network."""
    cmd = ["docker", "network", "create", "--driver", "bridge"]
    if subnet:
        cmd.extend(["--subnet", subnet])
    cmd.append(name)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return result.returncode == 0


def remove_network(name: str) -> bool:
    """Remove a Docker network."""
    result = subprocess.run(
        ["docker", "network", "rm", name],
        capture_output=True, text=True, timeout=10,
    )
    return result.returncode == 0


def network_exists(name: str) -> bool:
    """Check if a Docker network exists."""
    result = subprocess.run(
        ["docker", "network", "inspect", name],
        capture_output=True, text=True, timeout=10,
    )
    return result.returncode == 0
