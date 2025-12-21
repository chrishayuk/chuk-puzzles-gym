"""Pydantic models and enums for the Puzzle Arcade server.

Game-specific models and enums have been moved to their respective game folders.
"""

from .base import GridPosition, MoveResult
from .config import GameConfig
from .enums import (
    CellState,
    ConnectionState,
    DifficultyLevel,
    EpisodeStatus,
    GameCommand,
    OutputMode,
)
from .evaluation import (
    DifficultyProfile,
    EpisodeResult,
    EpisodeTracer,
    EvaluationSummary,
    MoveRecord,
    SolverConfig,
    TraceEvent,
)

__all__ = [
    # Enums
    "CellState",
    "ConnectionState",
    "DifficultyLevel",
    "EpisodeStatus",
    "GameCommand",
    "OutputMode",
    # Base models
    "MoveResult",
    "GridPosition",
    "GameConfig",
    # Evaluation models
    "DifficultyProfile",
    "EpisodeResult",
    "EpisodeTracer",
    "EvaluationSummary",
    "MoveRecord",
    "SolverConfig",
    "TraceEvent",
]
