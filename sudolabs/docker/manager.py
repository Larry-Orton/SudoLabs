"""Docker lifecycle manager for SudoLabs targets."""

import subprocess
import time
from pathlib import Path

from sudolabs.ui.theme import console


class DockerManager:
    """Manages Docker container lifecycle for targets."""

    def __init__(self):
        self._check_docker()

    def _check_docker(self):
        """Verify Docker is available and running."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace",
            )
            if result.returncode != 0:
                raise RuntimeError("Docker daemon is not running")
        except FileNotFoundError:
            raise RuntimeError("Docker is not installed")

    def launch_target(self, target_dir: Path, slug: str) -> dict:
        """Launch a target's Docker environment.

        Args:
            target_dir: Path to the target directory containing docker-compose.yml.
            slug: Target slug for naming.

        Returns:
            Dict with connection info (ip, ports, container_ids).
        """
        compose_file = target_dir / "docker-compose.yml"
        if not compose_file.exists():
            raise FileNotFoundError(f"No docker-compose.yml found in {target_dir}")

        project_name = f"sudolabs_{slug}"

        console.print(f"  [dim]Building and starting containers...[/dim]")

        # Build and start
        result = subprocess.run(
            ["docker", "compose", "-p", project_name, "-f", str(compose_file), "up", "-d", "--build"],
            capture_output=True, text=True, cwd=str(target_dir),
            timeout=300, encoding="utf-8", errors="replace",
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to start target: {result.stderr}")

        # Get container info
        info = self._get_container_info(project_name)
        return info

    def _get_container_info(self, project_name: str) -> dict:
        """Get running container info for a project."""
        result = subprocess.run(
            ["docker", "compose", "-p", project_name, "ps", "--format", "json"],
            capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace",
        )

        # Get the IP of the first container
        ip_result = subprocess.run(
            ["docker", "compose", "-p", project_name, "ps", "-q"],
            capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace",
        )

        container_ids = ip_result.stdout.strip().split("\n") if ip_result.stdout.strip() else []
        target_ip = "127.0.0.1"
        ports = []

        for cid in container_ids:
            if not cid:
                continue
            port_result = subprocess.run(
                ["docker", "port", cid],
                capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace",
            )
            if port_result.stdout:
                for line in port_result.stdout.strip().split("\n"):
                    if "->" in line:
                        parts = line.split("->")
                        host_part = parts[1].strip() if len(parts) > 1 else ""
                        if host_part:
                            ports.append(host_part)

        return {
            "ip": target_ip,
            "ports": ports,
            "container_ids": container_ids,
            "project_name": project_name,
        }

    def stop_target(self, target_dir: Path, slug: str):
        """Stop a target's containers without removing them."""
        project_name = f"sudolabs_{slug}"
        subprocess.run(
            ["docker", "compose", "-p", project_name, "-f", str(target_dir / "docker-compose.yml"), "stop"],
            capture_output=True, text=True, cwd=str(target_dir),
            timeout=60, encoding="utf-8", errors="replace",
        )

    def destroy_target(self, target_dir: Path, slug: str):
        """Destroy a target's containers, volumes, and networks."""
        project_name = f"sudolabs_{slug}"
        subprocess.run(
            ["docker", "compose", "-p", project_name, "-f", str(target_dir / "docker-compose.yml"),
             "down", "-v", "--remove-orphans"],
            capture_output=True, text=True, cwd=str(target_dir),
            timeout=60, encoding="utf-8", errors="replace",
        )

    def is_running(self, slug: str) -> bool:
        """Check if a target's containers are running."""
        project_name = f"sudolabs_{slug}"
        result = subprocess.run(
            ["docker", "compose", "-p", project_name, "ps", "-q", "--filter", "status=running"],
            capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace",
        )
        return bool(result.stdout.strip())

    def exec_in_container(self, container_id: str, command: str, user: str | None = None) -> str:
        """Execute a command inside a container."""
        cmd = ["docker", "exec"]
        if user:
            cmd += ["-u", user]
        cmd += [container_id, "sh", "-c", command]
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace",
        )
        return result.stdout.strip()

    def wait_for_healthy(self, slug: str, timeout: int = 120) -> bool:
        """Wait for all containers in a target to be healthy/running."""
        project_name = f"sudolabs_{slug}"
        start = time.time()

        while time.time() - start < timeout:
            result = subprocess.run(
                ["docker", "compose", "-p", project_name, "ps", "-q"],
                capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace",
            )
            container_ids = [c for c in result.stdout.strip().split("\n") if c]

            if not container_ids:
                time.sleep(2)
                continue

            all_running = True
            for cid in container_ids:
                status_result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Status}}", cid],
                    capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace",
                )
                if status_result.stdout.strip() != "running":
                    all_running = False
                    break

            if all_running:
                return True

            time.sleep(2)

        return False

    def cleanup_all(self):
        """Remove all SudoLabs-related Docker resources."""
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "label=com.docker.compose.project", "--format", "{{.Labels}}"],
            capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace",
        )
        # Find and remove sudolabs_ projects
        projects_seen = set()
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                if "sudolabs_" in line:
                    # Extract project name
                    for part in line.split(","):
                        if "com.docker.compose.project=" in part:
                            proj = part.split("=")[1]
                            if proj.startswith("sudolabs_"):
                                projects_seen.add(proj)

        for proj in projects_seen:
            subprocess.run(
                ["docker", "compose", "-p", proj, "down", "-v", "--remove-orphans"],
                capture_output=True, text=True, timeout=60,
            )
