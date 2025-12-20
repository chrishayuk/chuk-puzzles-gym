"""Base classes for puzzle games."""

from .commands import CommandResult, GameCommandHandler
from .game import PuzzleGame

__all__ = ["PuzzleGame", "GameCommandHandler", "CommandResult"]
