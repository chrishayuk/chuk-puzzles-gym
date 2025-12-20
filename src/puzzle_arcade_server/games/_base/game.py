"""Abstract base class for all puzzle games."""

import random
from abc import ABC, abstractmethod
from typing import Any

from ...models import DifficultyLevel, MoveResult


class PuzzleGame(ABC):
    """Base class for all puzzle games in the arcade.

    This defines the common interface that all puzzle types must implement.
    Games are pure puzzle generators - they don't solve, they just validate.
    The solving happens client-side (LLMs with MCP solver access).

    All games support deterministic seeding for reproducibility:
    - Pass a seed to __init__ to get the same puzzle every time
    - Use self._rng for all random operations in subclasses
    - The seed is exposed so players can share puzzles
    """

    def __init__(
        self,
        difficulty: DifficultyLevel | str = DifficultyLevel.EASY,
        seed: int | None = None,
    ):
        """Initialize a new puzzle game.

        Args:
            difficulty: Game difficulty level (easy, medium, hard)
            seed: Random seed for reproducible puzzle generation.
                  If None, a random seed is generated.
        """
        # Convert string to enum if needed (for backwards compatibility)
        if isinstance(difficulty, str):
            self.difficulty = DifficultyLevel(difficulty)
        else:
            self.difficulty = difficulty

        # Initialize deterministic random number generator
        self.seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        self._rng = random.Random(self.seed)

        self.moves_made = 0
        self.game_started = False

    @abstractmethod
    async def generate_puzzle(self) -> None:
        """Generate a new puzzle with a unique solution.

        This should create the puzzle grid, store the solution,
        and prepare the initial state for play.

        This is async to allow for non-blocking generation of complex puzzles.
        """
        pass

    @abstractmethod
    async def validate_move(self, *args: Any, **kwargs: Any) -> MoveResult:
        """Validate a player's move.

        Args:
            *args: Move parameters (game-specific)
            **kwargs: Additional move parameters (game-specific)

        Returns:
            MoveResult containing success status and message
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
    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if no hints available

        This is async to allow for complex hint computation.
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
        return f"Moves made: {self.moves_made} | Seed: {self.seed}"

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

    @property
    def constraint_types(self) -> list[str]:
        """The types of constraints this puzzle demonstrates.

        Examples: all_different, linear_sum, boolean_sat, optimization,
                  connectivity, global_loop, feedback, probabilistic
        """
        return []

    @property
    def business_analogies(self) -> list[str]:
        """Real-world business problems this puzzle models.

        Examples: scheduling, resource_allocation, portfolio_selection,
                  routing, capacity_planning, constraint_satisfaction
        """
        return []

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity characteristics of this puzzle.

        Returns dict with:
        - reasoning_type: deductive, probabilistic, optimization, hybrid
        - search_space: small, medium, large, exponential
        - constraint_density: sparse, moderate, dense
        """
        return {"reasoning_type": "deductive", "search_space": "medium", "constraint_density": "moderate"}
