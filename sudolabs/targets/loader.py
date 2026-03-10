"""YAML target definition parser for SudoLabs."""

from pathlib import Path

import yaml

from sudolabs.targets.models import Target


def load_target(target_dir: Path, category: str = "") -> Target | None:
    """Load a target from a directory containing target.yaml.

    Args:
        target_dir: Path to the target directory.
        category: Category slug inferred from parent directory name.

    Returns:
        A Target model instance, or None if no valid target.yaml found.
    """
    yaml_path = target_dir / "target.yaml"
    if not yaml_path.exists():
        return None

    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    if not data:
        return None

    # Inject category from directory structure if not in YAML
    if category and not data.get("category"):
        data["category"] = category

    return Target(**data)


def load_targets_from_directory(base_dir: Path) -> list[Target]:
    """Load all targets from a base directory (recursively).

    Expects structure: base_dir/<category>/<target_slug>/target.yaml

    Args:
        base_dir: Path to the targets/ directory.

    Returns:
        List of Target model instances.
    """
    targets = []

    if not base_dir.exists():
        return targets

    for category_dir in sorted(base_dir.iterdir()):
        if not category_dir.is_dir():
            continue

        category_slug = category_dir.name

        for target_dir in sorted(category_dir.iterdir()):
            if not target_dir.is_dir():
                continue

            target = load_target(target_dir, category=category_slug)
            if target:
                targets.append(target)

    return targets
