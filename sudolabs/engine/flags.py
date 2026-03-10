"""Flag generation, placement, and verification for SudoLabs."""

import hashlib
import secrets


def generate_flag() -> str:
    """Generate a unique random flag."""
    hex_part = secrets.token_hex(16)
    return f"SUDO{{{hex_part}}}"


def hash_flag(flag: str) -> str:
    """Hash a flag for storage and comparison."""
    return hashlib.sha256(flag.encode()).hexdigest()


def verify_flag(submitted: str, expected_hash: str) -> bool:
    """Verify a submitted flag against its expected hash."""
    submitted_hash = hash_flag(submitted.strip())
    return submitted_hash == expected_hash


def generate_session_flags(stage_count: int) -> list[dict]:
    """Generate a set of flags for a hunt session.

    Returns:
        List of dicts with 'flag' (plaintext) and 'hash' keys.
    """
    flags = []
    for _ in range(stage_count):
        flag = generate_flag()
        flags.append({
            "flag": flag,
            "hash": hash_flag(flag),
        })
    return flags
