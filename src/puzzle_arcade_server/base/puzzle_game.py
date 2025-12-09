"""Abstract base class for all puzzle games."""

from abc import ABC, abstractmethod
from typing import Any


class PuzzleGame(ABC):
    """Base class for all puzzle games in the arcade.

    This defines the common interface that all puzzle types must implement.
    Games are pure puzzle generators - they don't solve, they just validate.
    The solving happens client-side (LLMs with MCP solver access).
    """

    def __init__(self, difficulty: str = "easy"):
        """Initialize a new puzzle game.

        Args:
            difficulty: Game difficulty level (easy, medium, hard)
        """
        self.difficulty = difficulty
        self.moves_made = 0
        self.game_started = False

    @abstractmethod
    def generate_puzzle(self) -> None:
        """Generate a new puzzle with a unique solution.

        This should create the puzzle grid, store the solution,
        and prepare the initial state for play.
        """
        pass

    @abstractmethod
    def validate_move(self, *args: Any) -> tuple[bool, str]:
        """Validate a player's move.

        Args:
            *args: Move parameters (game-specific)

        Returns:
            Tuple of (success: bool, message: str)
        """
        pass

    @abstractmethod
    def is_complete(self) -> bool:
        """Check if the puzzle is completely and correctly solved.

        Returns:
            True if puzzle is solved correctly, False otherwise
        """
        pass

    @abstractmethod
    def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if no hints available
        """
        pass

    @abstractmethod
    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        This should be clean and parseable for LLM clients.

        Returns:
            String representation of the puzzle grid
        """
        pass

    @abstractmethod
    def get_rules(self) -> str:
        """Get the rules description for this puzzle type.

        Returns:
            Multi-line string describing the puzzle rules
        """
        pass

    @abstractmethod
    def get_commands(self) -> str:
        """Get the available commands for this puzzle type.

        Returns:
            Multi-line string describing available commands
        """
        pass

    def get_stats(self) -> str:
        """Get current game statistics.

        Returns:
            String with game stats (moves, completion, etc.)
        """
        return f"Moves made: {self.moves_made}"

    @property
    @abstractmethod
    def name(self) -> str:
        """The display name of this puzzle type."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        pass
