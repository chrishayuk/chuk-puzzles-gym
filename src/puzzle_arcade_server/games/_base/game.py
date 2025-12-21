"""Abstract base class for all puzzle games."""

import random
from abc import ABC, abstractmethod
from typing import Any

from ...models import DifficultyLevel, DifficultyProfile, MoveResult, SolverConfig


class PuzzleGame(ABC):
    """Base class for all puzzle games in the arcade.

    This defines the common interface that all puzzle types must implement.
    Games are pure puzzle generators - they don't solve, they just validate.
    The solving happens client-side (LLMs with MCP solver access).

    All games support deterministic seeding for reproducibility:
    - Pass a seed to __init__ to get the same puzzle every time
    - Use self._rng for all random operations in subclasses
    - The seed is exposed so players can share puzzles

    Metrics tracked for evaluation:
    - moves_made: Valid moves (state-changing actions)
    - invalid_moves: Rejected/invalid move attempts
    - hints_used: Solver hints consumed
    - retries: Attempts on same cell (backtracking indicator)
    """

    def __init__(
        self,
        difficulty: DifficultyLevel | str = DifficultyLevel.EASY,
        seed: int | None = None,
        solver_config: SolverConfig | None = None,
    ):
        """Initialize a new puzzle game.

        Args:
            difficulty: Game difficulty level (easy, medium, hard)
            seed: Random seed for reproducible puzzle generation.
                  If None, a random seed is generated.
            solver_config: Configuration for solver/hint usage.
                          If None, uses default (solver allowed, no penalty).
        """
        # Convert string to enum if needed (for backwards compatibility)
        if isinstance(difficulty, str):
            self.difficulty = DifficultyLevel(difficulty)
        else:
            self.difficulty = difficulty

        # Initialize deterministic random number generator
        self.seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        self._rng = random.Random(self.seed)

        # Solver configuration
        self.solver_config = solver_config or SolverConfig()

        # Core metrics
        self.moves_made = 0
        self.invalid_moves = 0
        self.hints_used = 0
        self.retries = 0  # Attempts on same cell

        # State tracking
        self.game_started = False
        self._last_move_position: tuple[Any, ...] | None = None  # For retry detection

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
        parts = [f"Moves: {self.moves_made}"]
        if self.invalid_moves > 0:
            parts.append(f"Invalid: {self.invalid_moves}")
        if self.hints_used > 0:
            parts.append(f"Hints: {self.hints_used}")
        parts.append(f"Seed: {self.seed}")
        return " | ".join(parts)

    def record_move(self, position: tuple[Any, ...], success: bool) -> None:
        """Record a move attempt for metrics tracking.

        Call this from validate_move() implementations to track metrics.

        Args:
            position: The position/target of the move (for retry detection)
            success: Whether the move was valid
        """
        if success:
            self.moves_made += 1
        else:
            self.invalid_moves += 1

        # Detect retries (same position attempted again)
        if self._last_move_position == position:
            self.retries += 1
        self._last_move_position = position

    def record_hint(self) -> bool:
        """Record a hint request and check if allowed.

        Returns:
            True if hint is allowed, False if budget exceeded or solver disabled.
        """
        if not self.solver_config.solver_allowed:
            return False
        if self.hints_used >= self.solver_config.hint_budget:
            return False
        self.hints_used += 1
        return True

    def can_use_hint(self) -> bool:
        """Check if hints are available without consuming one.

        Returns:
            True if solver is allowed and budget not exceeded.
        """
        if not self.solver_config.solver_allowed:
            return False
        return self.hints_used < self.solver_config.hint_budget

    @property
    def hints_remaining(self) -> int:
        """Number of hints remaining in budget."""
        if not self.solver_config.solver_allowed:
            return 0
        return max(0, self.solver_config.hint_budget - self.hints_used)

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

    @property
    def complexity_metrics(self) -> dict[str, int | float]:
        """Quantified complexity metrics for this puzzle instance.

        Returns dict with:
        - variable_count: Number of decision variables (cells to fill)
        - constraint_count: Number of constraints
        - domain_size: Average domain size per variable
        - branching_factor: Estimated branching factor
        - empty_cells: Number of cells still to be filled

        Override in subclasses for accurate values.
        """
        return {
            "variable_count": 0,
            "constraint_count": 0,
            "domain_size": 0,
            "branching_factor": 0.0,
            "empty_cells": 0,
        }

    @property
    def difficulty_profile(self) -> DifficultyProfile:
        """Detailed difficulty characteristics for curriculum learning.

        Goes beyond simple easy/medium/hard to enable:
        - Curriculum learning with skill ladders
        - Fair comparisons across identical difficulty profiles
        - Automated training runs with reproducible difficulty scaling

        Override in subclasses for accurate values based on puzzle instance.
        """
        # Default values based on difficulty level
        base_logic = {DifficultyLevel.EASY.value: 2, DifficultyLevel.MEDIUM.value: 4, DifficultyLevel.HARD.value: 6}
        base_branching = {
            DifficultyLevel.EASY.value: 2.0,
            DifficultyLevel.MEDIUM.value: 4.0,
            DifficultyLevel.HARD.value: 6.0,
        }
        base_density = {
            DifficultyLevel.EASY.value: 0.6,
            DifficultyLevel.MEDIUM.value: 0.5,
            DifficultyLevel.HARD.value: 0.4,
        }

        diff_str = self.difficulty.value
        return DifficultyProfile(
            logic_depth=base_logic.get(diff_str, 3),
            branching_factor=base_branching.get(diff_str, 3.0),
            state_observability=1.0,  # Most puzzles are fully observable
            constraint_density=base_density.get(diff_str, 0.5),
        )

    @property
    def optimal_steps(self) -> int | None:
        """Minimum number of steps to solve this puzzle (from solver).

        Returns None if not computed or not applicable.
        Override in subclasses that can compute optimal solutions.

        For grid-based puzzles, this is typically the number of empty cells.
        For optimization puzzles, this may be the number of decisions.
        """
        # Default: estimate from complexity metrics
        metrics = self.complexity_metrics
        empty_cells = metrics.get("empty_cells", 0)
        if empty_cells > 0:
            return int(empty_cells)
        return None

    @property
    def canonical_solution(self) -> list[tuple[Any, ...]] | None:
        """Optimal solution trace as a list of moves.

        Returns None if not available.
        Override in subclasses that can provide solution traces.

        Each move is a tuple of (row, col, value) or game-specific format.
        """
        return None

    def get_solution_efficiency(self, steps_taken: int) -> float:
        """Calculate efficiency score compared to optimal solution.

        Args:
            steps_taken: Actual steps taken to solve

        Returns:
            Efficiency score from 0.0 to 1.0 (1.0 = optimal)
        """
        optimal = self.optimal_steps
        if optimal is None or steps_taken == 0:
            return 0.0
        return min(1.0, optimal / steps_taken)
