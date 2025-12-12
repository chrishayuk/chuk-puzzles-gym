"""Puzzle game implementations."""

from .binary import BinaryPuzzleGame
from .bridges import BridgesGame
from .einstein import EinsteinGame
from .fillomino import FillominoGame
from .futoshiki import FutoshikiGame
from .hidato import HidatoGame
from .hitori import HitoriGame
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
from .shikaku import ShikakuGame
from .slitherlink import SlitherlinkGame
from .sokoban import SokobanGame
from .star_battle import StarBattleGame
from .sudoku import SudokuGame
from .tents import TentsGame

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
    "bridges": BridgesGame,
    "hitori": HitoriGame,
    "shikaku": ShikakuGame,
    # Specialized Constraint Puzzles
    "hidato": HidatoGame,
    "tents": TentsGame,
    "fillomino": FillominoGame,
    "star_battle": StarBattleGame,
    "sokoban": SokobanGame,
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
    "BridgesGame",
    "FillominoGame",
    "FutoshikiGame",
    "HidatoGame",
    "HitoriGame",
    "NonogramGame",
    "LogicGridGame",
    "KillerSudokuGame",
    "LightsOutGame",
    "MastermindGame",
    "ShikakuGame",
    "SlitherlinkGame",
    "SokobanGame",
    "StarBattleGame",
    "TentsGame",
    "KnapsackGame",
    "SchedulerGame",
    "NurikabeGame",
    "EinsteinGame",
    "MinesweeperGame",
    "AVAILABLE_GAMES",
]
