"""Configuration management for SudoLabs."""

import os
from pathlib import Path

import yaml


SUDOLABS_HOME = Path.home() / ".sudolabs"
CONFIG_FILE = SUDOLABS_HOME / "config.yaml"
DB_FILE = SUDOLABS_HOME / "sudolabs.db"

# Find the project root (where targets/ lives)
_this_dir = Path(__file__).resolve().parent
PROJECT_ROOT = _this_dir.parent
TARGETS_DIR = PROJECT_ROOT / "targets"


def ensure_sudolabs_home():
    """Create ~/.sudolabs/ directory if it doesn't exist."""
    SUDOLABS_HOME.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from ~/.sudolabs/config.yaml."""
    ensure_sudolabs_home()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_config(config: dict):
    """Save configuration to ~/.sudolabs/config.yaml."""
    ensure_sudolabs_home()
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_api_key() -> str | None:
    """Get Anthropic API key from config or environment."""
    env_key = os.environ.get("ANTHROPIC_API_KEY")
    if env_key:
        return env_key
    config = load_config()
    return config.get("api_key")


def set_api_key(key: str):
    """Store Anthropic API key in config."""
    config = load_config()
    config["api_key"] = key
    save_config(config)


def get_username() -> str:
    """Get the user's profile name."""
    config = load_config()
    return config.get("username", "hunter")


def set_username(name: str):
    """Set the user's profile name."""
    config = load_config()
    config["username"] = name
    save_config(config)
