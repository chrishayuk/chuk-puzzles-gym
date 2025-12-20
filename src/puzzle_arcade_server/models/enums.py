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
    RESET = "reset"
    MENU = "menu"
    M = "m"
    MODE = "mode"
    SEED = "seed"
    # Game-specific commands (kept here for server command parsing)
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
    GUESS = "guess"
    SET = "set"
    SHADE = "shade"
    BRIDGE = "bridge"
    MOVE = "move"


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
