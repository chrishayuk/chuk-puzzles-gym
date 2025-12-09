"""Puzzle game implementations."""

from .binary import BinaryPuzzleGame
from .einstein import EinsteinGame
from .futoshiki import FutoshikiGame
from .kakuro import KakuroGame
from .kenken import KenKenGame
from .killer_sudoku import KillerSudokuGame
from .knapsack import KnapsackGame
from .lights_out import LightsOutGame
from .logic_grid import LogicGridGame
from .mastermind import MastermindGame
from .minesweeper import MinesweeperGame
from .nonogram import NonogramGame
from .nurikabe import NurikabeGame
from .scheduler import SchedulerGame
from .slitherlink import SlitherlinkGame
from .sudoku import SudokuGame

# Registry of available games
AVAILABLE_GAMES = {
    # Classic Logic Puzzles
    "sudoku": SudokuGame,
    "kenken": KenKenGame,
    "kakuro": KakuroGame,
    "binary": BinaryPuzzleGame,
    "futoshiki": FutoshikiGame,
    "nonogram": NonogramGame,
    "logic": LogicGridGame,
    # Advanced CP-SAT Puzzles
    "killer": KillerSudokuGame,
    "lights": LightsOutGame,
    "mastermind": MastermindGame,
    "slither": SlitherlinkGame,
    # Optimization Challenges
    "knapsack": KnapsackGame,
    "scheduler": SchedulerGame,
    # Advanced Reasoning
    "nurikabe": NurikabeGame,
    "einstein": EinsteinGame,
    "minesweeper": MinesweeperGame,
}

__all__ = [
    "SudokuGame",
    "KenKenGame",
    "KakuroGame",
    "BinaryPuzzleGame",
    "FutoshikiGame",
    "NonogramGame",
    "LogicGridGame",
    "KillerSudokuGame",
    "LightsOutGame",
    "MastermindGame",
    "SlitherlinkGame",
    "KnapsackGame",
    "SchedulerGame",
    "NurikabeGame",
    "EinsteinGame",
    "MinesweeperGame",
    "AVAILABLE_GAMES",
]
