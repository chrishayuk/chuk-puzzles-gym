"""Minesweeper game enums."""

from enum import Enum


class MinesweeperAction(str, Enum):
    """Actions for Minesweeper game."""

    REVEAL = "reveal"
    R = "r"
    FLAG = "flag"
    F = "f"
