"""Puzzle game implementations."""

from .binary import BinaryPuzzleGame
from .futoshiki import FutoshikiGame
from .kakuro import KakuroGame
from .kenken import KenKenGame
from .logic_grid import LogicGridGame
from .nonogram import NonogramGame
from .sudoku import SudokuGame

# Registry of available games
AVAILABLE_GAMES = {
    "sudoku": SudokuGame,
    "kenken": KenKenGame,
    "kakuro": KakuroGame,
    "binary": BinaryPuzzleGame,
    "futoshiki": FutoshikiGame,
    "nonogram": NonogramGame,
    "logic": LogicGridGame,
}

__all__ = [
    "SudokuGame",
    "KenKenGame",
    "KakuroGame",
    "BinaryPuzzleGame",
    "FutoshikiGame",
    "NonogramGame",
    "LogicGridGame",
    "AVAILABLE_GAMES",
]
