"""Configuration management for Howl."""

import os
from pathlib import Path

import yaml


HOWL_HOME = Path.home() / ".howl"
CONFIG_FILE = HOWL_HOME / "config.yaml"
DB_FILE = HOWL_HOME / "howl.db"

# Find the project root (where targets/ lives)
_this_dir = Path(__file__).resolve().parent
PROJECT_ROOT = _this_dir.parent
TARGETS_DIR = PROJECT_ROOT / "targets"


def ensure_howl_home():
    """Create ~/.howl/ directory if it doesn't exist."""
    HOWL_HOME.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from ~/.howl/config.yaml."""
    ensure_howl_home()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_config(config: dict):
    """Save configuration to ~/.howl/config.yaml."""
    ensure_howl_home()
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
