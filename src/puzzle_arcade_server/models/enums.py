"""Enums for the Puzzle Arcade server."""

from enum import Enum, IntEnum


class DifficultyLevel(str, Enum):
    """Difficulty levels for all games."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GameCommand(str, Enum):
    """Commands available in game mode."""

    QUIT = "quit"
    EXIT = "exit"
    Q = "q"
    HELP = "help"
    H = "h"
    SHOW = "show"
    S = "s"
    HINT = "hint"
    CHECK = "check"
    SOLVE = "solve"
    MENU = "menu"
    M = "m"
    MODE = "mode"
    # Game-specific commands
    PLACE = "place"
    CLEAR = "clear"
    PRESS = "press"
    CONNECT = "connect"
    EXCLUDE = "exclude"
    REVEAL = "reveal"
    FLAG = "flag"
    SELECT = "select"
    DESELECT = "deselect"
    ASSIGN = "assign"
    UNASSIGN = "unassign"
    MARK = "mark"


class MinesweeperAction(str, Enum):
    """Actions for Minesweeper game."""

    REVEAL = "reveal"
    R = "r"
    FLAG = "flag"
    F = "f"


class KnapsackAction(str, Enum):
    """Actions for Knapsack game."""

    SELECT = "select"
    DESELECT = "deselect"


class SchedulerAction(str, Enum):
    """Actions for Scheduler game."""

    ASSIGN = "assign"
    UNASSIGN = "unassign"


class NurikabeColor(str, Enum):
    """Colors for Nurikabe cells."""

    WHITE = "white"
    W = "w"
    BLACK = "black"
    B = "b"
    CLEAR = "clear"
    C = "c"


class ArithmeticOperation(str, Enum):
    """Arithmetic operations for KenKen cages."""

    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    NONE = ""  # For single-cell cages


class CellState(IntEnum):
    """State of a cell in grid-based games."""

    EMPTY = 0
    UNREVEALED = 0
    FILLED = 1
    REVEALED = 1
    FLAGGED = 2
    MARKED = 2


class ConnectionState(IntEnum):
    """Connection state in logic grid puzzles."""

    UNKNOWN = 0
    DISCONNECTED = 1
    CONNECTED = 2


class OutputMode(str, Enum):
    """Output mode for the server."""

    NORMAL = "normal"
    AGENT = "agent"
    COMPACT = "compact"
