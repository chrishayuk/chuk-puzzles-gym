"""Nonogram (Picross) puzzle game implementation."""

from typing import Any

from ...models import DifficultyLevel, DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import NonogramConfig


class NonogramGame(PuzzleGame):
    """Nonogram (also known as Picross, Griddlers, or Hanjie) puzzle game.

    Fill cells to reveal a picture based on number clues for each row and column.
    Clues indicate consecutive filled cells in that row/column.
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Nonogram game.

        Args:
            difficulty: Game difficulty level (easy=5x5, medium=7x7, hard=10x10)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Use pydantic config based on difficulty
        self.config = NonogramConfig.from_difficulty(self.difficulty)
        self.size = self.config.size

        # Grid: -1 = unknown, 0 = empty (marked X), 1 = filled (marked ■)
        self.grid = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.initial_grid = [[-1 for _ in range(self.size)] for _ in range(self.size)]

        # Clues: row_clues[i] = list of consecutive filled counts for row i
        self.row_clues: list[list[int]] = []
        self.col_clues: list[list[int]] = []

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Nonogram"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Picture logic puzzle - reveal image from number clues"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["run_length_encoding", "linear_constraints", "cross_referencing", "pattern_completion"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["data_reconstruction", "pattern_recognition", "image_recovery", "constraint_propagation"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "large", "constraint_density": "dense"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = all cells to mark (filled=1 and empty=0)."""
        if not hasattr(self, "solution") or not self.solution:
            return None
        # Count both filled (1) and empty (0) cells - all need to be marked
        return sum(
            1 for r in range(len(self.solution)) for c in range(len(self.solution[0])) if self.solution[r][c] in (0, 1)
        )

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Nonogram."""

        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 4,
            DifficultyLevel.HARD.value: 5,
        }.get(self.difficulty.value, 3)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=2.0,
            state_observability=1.0,
            constraint_density=0.5,
        )

    def _calculate_clues(self, line: list[int]) -> list[int]:
        """Calculate clues for a line (row or column).

        Args:
            line: List of 0s and 1s

        Returns:
            List of consecutive filled cell counts
        """
        clues = []
        count = 0

        for cell in line:
            if cell == 1:
                count += 1
            elif count > 0:
                clues.append(count)
                count = 0

        if count > 0:
            clues.append(count)

        return clues if clues else [0]

    def _generate_pattern(self) -> None:
        """Generate a random pattern for the solution."""
        # Create a simple random pattern
        density_map = {
            DifficultyLevel.EASY: 0.4,
            DifficultyLevel.MEDIUM: 0.5,
            DifficultyLevel.HARD: 0.6,
        }
        density = density_map[self.difficulty]

        for row in range(self.size):
            for col in range(self.size):
                self.solution[row][col] = 1 if self._rng.random() < density else 0

    async def generate_puzzle(self) -> None:
        """Generate a new Nonogram puzzle."""
        # Generate a random pattern
        self._generate_pattern()

        # Calculate clues from the solution
        self.row_clues = []
        for row in range(self.size):
            clues = self._calculate_clues(self.solution[row])
            self.row_clues.append(clues)

        self.col_clues = []
        for col in range(self.size):
            column = [self.solution[row][col] for row in range(self.size)]
            clues = self._calculate_clues(column)
            self.col_clues.append(clues)

        # Start with empty grid
        self.grid = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        self.initial_grid = [row[:] for row in self.grid]
        self.moves_made = 0
        self.game_started = True

    async def validate_move(self, row: int, col: int, value: int) -> MoveResult:
        """Mark a cell on the grid.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            value: Value to place (0=empty/X, 1=filled/■, -1=unknown/clear)

        Returns:
            MoveResult with success status and message
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return MoveResult(success=False, message=f"Invalid coordinates. Use row and column between 1-{self.size}.")

        # Validate value
        if value not in [-1, 0, 1]:
            return MoveResult(success=False, message="Invalid value. Use 1 (filled), 0 (empty), or -1 (clear).")

        self.grid[row][col] = value
        self.moves_made += 1
        return MoveResult(success=True, message="Cell marked successfully!", state_changed=True)

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        # Check all cells marked
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] == -1:
                    return False
                if self.grid[row][col] != self.solution[row][col]:
                    return False

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        unknown_cells = [(r, c) for r in range(self.size) for c in range(self.size) if self.grid[r][c] == -1]
        if not unknown_cells:
            return None

        row, col = self._rng.choice(unknown_cells)
        value = self.solution[row][col]
        value_str = "filled (■)" if value == 1 else "empty (X)"
        hint_data = (row + 1, col + 1, value)
        hint_message = f"Try marking row {row + 1}, column {col + 1} as {value_str}"
        return hint_data, hint_message

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        Returns:
            String representation of the puzzle grid with clues
        """
        lines = []

        # Determine max clue length for formatting
        max_row_clues = max(len(clues) for clues in self.row_clues)
        max_col_clues = max(len(clues) for clues in self.col_clues)

        # Render column clues
        for clue_idx in range(max_col_clues):
            line = " " * (max_row_clues * 2 + 2)
            for col in range(self.size):
                clues = self.col_clues[col]
                # Pad clues from the top
                padded_idx = clue_idx - (max_col_clues - len(clues))
                if padded_idx >= 0:
                    line += f"{clues[padded_idx]:2d} "
                else:
                    line += "   "
            lines.append(line)

        lines.append(" " * (max_row_clues * 2 + 2) + "+" + "--+" * self.size)

        # Render grid with row clues
        for row in range(self.size):
            # Row clues
            clues = self.row_clues[row]
            clue_str = " ".join(f"{c:2d}" for c in clues)
            clue_str = clue_str.rjust(max_row_clues * 3)

            # Grid row
            line = clue_str + " |"
            for col in range(self.size):
                cell = self.grid[row][col]
                if cell == -1:
                    line += " ? |"
                elif cell == 0:
                    line += " X |"
                else:  # cell == 1
                    line += " ■ |"
            lines.append(line)
            lines.append(" " * (max_row_clues * 2 + 2) + "+" + "--+" * self.size)

        lines.append("\nLegend: ? = unknown, X = empty, ■ = filled")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Nonogram.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return f"""NONOGRAM RULES:
- Fill cells to reveal a picture
- Numbers on the left show consecutive filled cells in each row
- Numbers on the top show consecutive filled cells in each column
- Multiple numbers mean multiple groups with at least one empty cell between
- For example: [3, 1] means 3 filled, gap, 1 filled
- Mark cells as: 1 (filled/■), 0 (empty/X), or -1 (unknown/?)
- Grid size: {self.size}x{self.size}"""

    def get_commands(self) -> str:
        """Get the available commands for Nonogram.

        Returns:
            Multi-line string describing available commands
        """
        return """NONOGRAM COMMANDS:
  place <row> <col> <val>  - Mark cell: 1=filled(■), 0=empty(X), -1=clear(?)
                             Example: 'place 1 2 1' marks (1,2) as filled
  show                     - Display the current grid
  hint                     - Get a hint for the next move
  check                    - Check your progress
  solve                    - Show the solution (ends game)
  menu                     - Return to game selection
  quit                     - Exit the server"""

    def get_stats(self) -> str:
        """Get current game statistics.

        Returns:
            String with game stats
        """
        unknown = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == -1)
        filled = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 1)
        return f"Moves made: {self.moves_made} | Unknown: {unknown} | Filled: {filled}/{self.size * self.size} | Seed: {self.seed}"
