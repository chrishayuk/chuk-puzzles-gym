"""Minesweeper game enums."""

from enum import StrEnum


class MinesweeperAction(StrEnum):
    """Actions for Minesweeper game."""

    REVEAL = "reveal"
    R = "r"
    FLAG = "flag"
    F = "f"
