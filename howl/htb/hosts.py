"""Manage /etc/hosts entries for HTB machines."""

import platform
import subprocess
from pathlib import Path

from howl.ui.theme import console


def get_hosts_file_path() -> Path:
    """Get the platform-appropriate hosts file path."""
    if platform.system() == "Windows":
        return Path(r"C:\Windows\System32\drivers\etc\hosts")
    return Path("/etc/hosts")


def _entry_exists(hosts_path: Path, ip: str, hostname: str) -> bool:
    """Check if a hosts entry already exists."""
    try:
        content = hosts_path.read_text(encoding="utf-8", errors="replace")
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0] == ip and hostname in parts[1:]:
                return True
    except (PermissionError, OSError):
        pass
    return False


def add_host_entry(ip: str, hostname: str) -> bool:
    """Add an entry to the hosts file.

    Returns:
        True if successful or already exists.
    """
    hosts_path = get_hosts_file_path()
    entry = f"{ip}\t{hostname}"

    if _entry_exists(hosts_path, ip, hostname):
        console.print(f"  [dim]Host entry already exists: {hostname} -> {ip}[/dim]")
        return True

    system = platform.system()

    if system == "Windows":
        try:
            with open(hosts_path, "a", encoding="utf-8") as f:
                f.write(f"\n{entry}\n")
            return True
        except PermissionError:
            console.print(
                f"  [yellow]Cannot modify hosts file. Run as Administrator or add manually:[/yellow]\n"
                f"  [bold]{entry}[/bold] to {hosts_path}"
            )
            return False
    else:
        try:
            result = subprocess.run(
                ["sudo", "sh", "-c", f'echo "{entry}" >> {hosts_path}'],
                timeout=30,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            console.print(f"  [yellow]Timed out waiting for sudo. Add manually:[/yellow]")
            console.print(f"  [bold]echo \"{entry}\" | sudo tee -a {hosts_path}[/bold]")
            return False
        except Exception as e:
            console.print(f"  [yellow]Failed to update hosts file: {e}[/yellow]")
            console.print(f"  [dim]Add manually: echo \"{entry}\" | sudo tee -a {hosts_path}[/dim]")
            return False


def remove_host_entry(ip: str, hostname: str) -> bool:
    """Remove an entry from the hosts file."""
    hosts_path = get_hosts_file_path()

    if not _entry_exists(hosts_path, ip, hostname):
        return True

    system = platform.system()

    try:
        content = hosts_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            parts = stripped.split()
            if len(parts) >= 2 and parts[0] == ip and hostname in parts[1:]:
                continue
            new_lines.append(line)

        new_content = "\n".join(new_lines) + "\n"

        if system == "Windows":
            hosts_path.write_text(new_content, encoding="utf-8")
        else:
            subprocess.run(
                ["sudo", "sh", "-c", f"cat > {hosts_path} << 'HOWL_EOF'\n{new_content}HOWL_EOF"],
                timeout=30,
            )
        return True
    except Exception:
        return False
