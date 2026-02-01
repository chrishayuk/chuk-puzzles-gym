"""Graph Coloring puzzle game."""

from .commands import GraphColoringCommandHandler
from .config import GraphColoringConfig
from .game import GraphColoringGame

__all__ = ["GraphColoringGame", "GraphColoringConfig", "GraphColoringCommandHandler"]
