"""Puzzle game implementations."""

from .binary import BinaryPuzzleGame
from .bridges import BridgesGame
from .cryptarithmetic import CryptarithmeticCommandHandler, CryptarithmeticGame
from .einstein import EinsteinGame
from .fillomino import FillominoGame
from .futoshiki import FutoshikiGame
from .graph_coloring import GraphColoringCommandHandler, GraphColoringGame
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
from .nqueens import NQueensGame
from .numberlink import NumberlinkGame
from .nurikabe import NurikabeGame
from .rush_hour import RushHourCommandHandler, RushHourGame
from .scheduler import SchedulerGame
from .shikaku import ShikakuGame
from .skyscrapers import SkyscrapersGame
from .slitherlink import SlitherlinkGame
from .sokoban import SokobanGame
from .star_battle import StarBattleGame
from .sudoku import SudokuGame
from .sudoku.commands import SudokuCommandHandler
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
    # New Games
    "skyscrapers": SkyscrapersGame,
    "nqueens": NQueensGame,
    "numberlink": NumberlinkGame,
    "graph_coloring": GraphColoringGame,
    "cryptarithmetic": CryptarithmeticGame,
    "rush_hour": RushHourGame,
}

# Registry of game command handlers (games that have moved command handling out of server)
GAME_COMMAND_HANDLERS = {
    "sudoku": SudokuCommandHandler,
    "graph_coloring": GraphColoringCommandHandler,
    "cryptarithmetic": CryptarithmeticCommandHandler,
    "rush_hour": RushHourCommandHandler,
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
    "SkyscrapersGame",
    "NQueensGame",
    "NumberlinkGame",
    "GraphColoringGame",
    "CryptarithmeticGame",
    "RushHourGame",
    "AVAILABLE_GAMES",
    "GAME_COMMAND_HANDLERS",
]
