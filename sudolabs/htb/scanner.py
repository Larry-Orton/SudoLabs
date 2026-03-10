"""Nmap scanning integration for HTB mode."""

import subprocess
import shutil
import re


def is_nmap_available() -> bool:
    """Check if nmap is installed."""
    return shutil.which("nmap") is not None


def run_nmap_scan(target_ip: str, scan_type: str = "default") -> tuple[str, list[dict]]:
    """Run an nmap scan against the target.

    Args:
        target_ip: IP address to scan.
        scan_type: "quick" (top 1000), "default" (SV scan), "full" (all ports).

    Returns:
        Tuple of (raw_output, parsed_services).
    """
    if not is_nmap_available():
        raise RuntimeError("nmap is not installed. Install with: sudo apt install nmap")

    if scan_type == "quick":
        cmd = ["nmap", "-T4", "--top-ports", "1000", target_ip]
    elif scan_type == "full":
        cmd = ["nmap", "-sV", "-sC", "-p-", "-T4", target_ip]
    else:
        cmd = ["nmap", "-sV", "-sC", "-T4", target_ip]

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=600,
        encoding="utf-8", errors="replace",
    )

    if result.returncode != 0 and not result.stdout:
        raise RuntimeError(f"nmap scan failed: {result.stderr}")

    raw_output = result.stdout
    services = parse_nmap_output(raw_output)
    return raw_output, services


def parse_nmap_output(output: str) -> list[dict]:
    """Parse nmap output into a list of discovered services.

    Returns:
        List of dicts with keys: port, protocol, state, service, version.
    """
    services = []
    port_pattern = re.compile(
        r"^(\d+)/(tcp|udp)\s+(open|filtered)\s+(\S+)\s*(.*?)$",
        re.MULTILINE,
    )

    for match in port_pattern.finditer(output):
        services.append({
            "port": int(match.group(1)),
            "protocol": match.group(2),
            "state": match.group(3),
            "service": match.group(4),
            "version": match.group(5).strip(),
        })

    return services
