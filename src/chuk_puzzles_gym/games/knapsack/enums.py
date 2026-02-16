"""Knapsack game enums."""

from enum import StrEnum


class KnapsackAction(StrEnum):
    """Actions for Knapsack game."""

    SELECT = "select"
    DESELECT = "deselect"
