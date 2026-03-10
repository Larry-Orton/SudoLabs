"""Score calculation engine for SudoLabs."""

import math


def calculate_hint_multiplier(l1_count: int, l2_count: int, l3_count: int) -> float:
    """Calculate the hint penalty multiplier.

    Each hint level has a per-use multiplier that compounds:
    - Level 1 (nudge): 0.85 per use
    - Level 2 (direction): 0.65 per use
    - Level 3 (walkthrough): 0.40 per use
    """
    multiplier = 1.0
    multiplier *= 0.85 ** l1_count
    multiplier *= 0.65 ** l2_count
    multiplier *= 0.40 ** l3_count
    return round(max(multiplier, 0.1), 4)  # Floor at 10%


def calculate_time_bonus(elapsed_secs: int, par_time_secs: int) -> float:
    """Calculate time bonus multiplier.

    - Under 25% of par: 1.5x
    - Under 50% of par: 1.3x
    - Under 75% of par: 1.15x
    - Under 100% of par: 1.0x
    - Over par: gradual decay, floor at 0.5x
    """
    if par_time_secs <= 0:
        return 1.0

    ratio = elapsed_secs / par_time_secs

    if ratio <= 0.25:
        return 1.5
    elif ratio <= 0.50:
        return 1.3
    elif ratio <= 0.75:
        return 1.15
    elif ratio <= 1.0:
        return 1.0
    else:
        # Gradual decay: 1.0 - 0.1 * (ratio - 1), floor at 0.5
        bonus = 1.0 - 0.1 * (ratio - 1.0)
        return round(max(bonus, 0.5), 4)


def calculate_stage_score(
    base_points: int,
    hint_multiplier: float,
    elapsed_secs: int,
    par_time_secs: int,
) -> int:
    """Calculate the final score for a completed stage."""
    time_bonus = calculate_time_bonus(elapsed_secs, par_time_secs)
    raw_score = base_points * hint_multiplier * time_bonus
    return max(int(round(raw_score)), 1)  # Minimum 1 point
