"""Knapsack game enums."""

from enum import Enum


class KnapsackAction(str, Enum):
    """Actions for Knapsack game."""

    SELECT = "select"
    DESELECT = "deselect"
