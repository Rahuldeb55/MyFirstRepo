"""
Direction Logic Service
Implements auto-direction detection: determines if a student is entering or exiting
based on their last recorded direction in the database.
"""
from models import Direction


def determine_direction(
    last_direction: Direction,
    manual_override: str = None
) -> Direction:
    """
    Auto-Direction Logic:
    - If student's last direction was IN → they are now going OUT
    - If student's last direction was OUT → they are now coming IN
    - Manual override takes precedence if provided by the guard.
    """
    if manual_override:
        return Direction(manual_override)

    # Toggle logic
    if last_direction == Direction.IN:
        return Direction.OUT
    else:
        return Direction.IN
