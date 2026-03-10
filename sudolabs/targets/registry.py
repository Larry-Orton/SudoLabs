"""Target registry - discovers and indexes all available targets."""

from pathlib import Path

from sudolabs.config import TARGETS_DIR
from sudolabs.targets.loader import load_targets_from_directory
from sudolabs.targets.models import Target
from sudolabs.constants import (
    Category, CATEGORY_DISPLAY_NAMES, CATEGORY_COLORS,
    CATEGORY_ICONS, CATEGORY_DESCRIPTIONS,
)


# Metadata for each category (display name, icon, color, description)
CATEGORY_META = {
    cat: {
        "slug": cat.value,
        "name": CATEGORY_DISPLAY_NAMES[cat],
        "icon": CATEGORY_ICONS[cat],
        "color": CATEGORY_COLORS[cat],
        "description": CATEGORY_DESCRIPTIONS[cat],
    }
    for cat in Category
}


class TargetRegistry:
    """Discovers, loads, and provides lookup for all targets."""

    def __init__(self, targets_dir: Path | None = None):
        self._targets_dir = targets_dir or TARGETS_DIR
        self._targets: list[Target] | None = None
        self._by_slug: dict[str, Target] | None = None
        self._by_category: dict[str, list[Target]] | None = None

    def _load(self):
        """Lazy-load all targets."""
        if self._targets is not None:
            return
        self._targets = load_targets_from_directory(self._targets_dir)
        self._by_slug = {t.slug: t for t in self._targets}

        # Build category index
        self._by_category = {}
        for t in self._targets:
            cat = t.category
            if cat not in self._by_category:
                self._by_category[cat] = []
            self._by_category[cat].append(t)

    def get_all(
        self,
        difficulty: str | None = None,
        category: str | None = None,
    ) -> list[Target]:
        """Get all targets, optionally filtered by difficulty and/or category."""
        self._load()
        targets = self._targets or []
        if difficulty:
            targets = [t for t in targets if t.difficulty == difficulty.lower()]
        if category:
            targets = [t for t in targets if t.category == category.lower()]
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

    def get_by_category(self, category: str) -> list[Target]:
        """Get all targets in a given category."""
        self._load()
        if self._by_category is None:
            return []
        return self._by_category.get(category, [])

    def get_categories(self) -> list[str]:
        """Get list of all categories that have at least one target."""
        self._load()
        if self._by_category is None:
            return []
        # Return in the canonical Category enum order
        ordered = []
        for cat in Category:
            if cat.value in self._by_category:
                ordered.append(cat.value)
        # Include any categories not in the enum (future-proofing)
        for cat_slug in self._by_category:
            if cat_slug not in ordered:
                ordered.append(cat_slug)
        return ordered

    def get_category_stats(self, progress_map: dict | None = None) -> list[dict]:
        """Get stats for each category for the category selection table.

        Returns list of dicts with keys:
            slug, name, icon, color, description,
            total, completed, total_score, difficulty_mix
        """
        self._load()
        if progress_map is None:
            progress_map = {}

        stats = []
        for cat in Category:
            cat_targets = self._by_category.get(cat.value, []) if self._by_category else []

            completed = 0
            total_score = 0
            diff_counts = {"easy": 0, "medium": 0, "hard": 0, "elite": 0}

            for t in cat_targets:
                prog = progress_map.get(t.slug, {})
                if prog.get("status") == "completed":
                    completed += 1
                total_score += prog.get("best_score", 0)
                diff_counts[t.difficulty] = diff_counts.get(t.difficulty, 0) + 1

            diff_mix = (
                f"{diff_counts['easy']}E "
                f"{diff_counts['medium']}M "
                f"{diff_counts['hard']}H "
                f"{diff_counts['elite']}EL"
            )

            meta = CATEGORY_META.get(cat, {})
            stats.append({
                "slug": cat.value,
                "name": meta.get("name", cat.value),
                "icon": meta.get("icon", "?"),
                "color": meta.get("color", "white"),
                "description": meta.get("description", ""),
                "total": len(cat_targets),
                "completed": completed,
                "total_score": total_score,
                "difficulty_mix": diff_mix,
            })

        return stats

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
        # New path structure: targets/<category>/<slug>
        return self._targets_dir / target.category / slug
