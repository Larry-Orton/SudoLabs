"""Target registry - discovers and indexes all available targets."""

from pathlib import Path

from howl.config import TARGETS_DIR
from howl.targets.loader import load_targets_from_directory
from howl.targets.models import Target


class TargetRegistry:
    """Discovers, loads, and provides lookup for all targets."""

    def __init__(self, targets_dir: Path | None = None):
        self._targets_dir = targets_dir or TARGETS_DIR
        self._targets: list[Target] | None = None
        self._by_slug: dict[str, Target] | None = None

    def _load(self):
        """Lazy-load all targets."""
        if self._targets is not None:
            return
        self._targets = load_targets_from_directory(self._targets_dir)
        self._by_slug = {t.slug: t for t in self._targets}

    def get_all(
        self,
        difficulty: str | None = None,
    ) -> list[Target]:
        """Get all targets, optionally filtered by difficulty."""
        self._load()
        targets = self._targets or []
        if difficulty:
            targets = [t for t in targets if t.difficulty == difficulty.lower()]
        return targets

    def get_by_slug(self, slug: str) -> Target | None:
        """Get a target by its slug."""
        self._load()
        if self._by_slug is None:
            return None
        return self._by_slug.get(slug)

    def get_by_difficulty(self, difficulty: str) -> list[Target]:
        """Get all targets of a given difficulty."""
        return self.get_all(difficulty=difficulty)

    def search(self, query: str) -> list[Target]:
        """Search targets by name, slug, description, or tags."""
        self._load()
        query_lower = query.lower()
        results = []
        for t in (self._targets or []):
            if (
                query_lower in t.name.lower()
                or query_lower in t.slug.lower()
                or query_lower in t.description.lower()
                or any(query_lower in tag.lower() for tag in t.tags)
            ):
                results.append(t)
        return results

    @property
    def total_count(self) -> int:
        self._load()
        return len(self._targets or [])

    def get_target_dir(self, slug: str) -> Path | None:
        """Get the filesystem path for a target's directory."""
        target = self.get_by_slug(slug)
        if not target:
            return None
        return self._targets_dir / target.difficulty / slug
