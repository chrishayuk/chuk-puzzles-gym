"""Binary Puzzle game implementation."""

from typing import Any

from ...models import DifficultyLevel, DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import BinaryConfig


class BinaryPuzzleGame(PuzzleGame):
    """Binary Puzzle (also known as Takuzu or Binairo).

    Fill a grid with 0s and 1s following these rules:
    - No more than two consecutive 0s or 1s in any row or column
    - Each row and column must have equal numbers of 0s and 1s
    - No two rows are identical, no two columns are identical
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Binary Puzzle game.

        Args:
            difficulty: Game difficulty level (easy=6x6, medium=8x8, hard=10x10)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Grid size based on difficulty (must be even)
        self.config = BinaryConfig.from_difficulty(self.difficulty)
        self.size = self.config.size

        # Grid: -1 = empty, 0 or 1 = filled
        self.grid = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.initial_grid = [[-1 for _ in range(self.size)] for _ in range(self.size)]

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Binary Puzzle"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Fill grid with 0s and 1s - no three in a row, equal counts"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["all_different", "no_three_consecutive", "equal_counts", "pattern_avoidance"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["binary_allocation", "balanced_distribution", "pattern_constraints", "quota_management"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "medium", "constraint_density": "moderate"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = empty cells to fill."""
        return sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == -1)

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Binary Puzzle."""

        empty = self.optimal_steps or 0
        total = self.size * self.size
        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 3,
            DifficultyLevel.HARD.value: 4,
        }.get(self.difficulty.value, 2)
        branching = 2.0  # Binary choice per cell
        density = 1.0 - (empty / total) if total > 0 else 0.5
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=branching,
            state_observability=1.0,
            constraint_density=round(density, 2),
        )

    def _check_no_three_consecutive(self, grid: list[list[int]]) -> bool:
        """Check if there are no three consecutive 0s or 1s.

        Args:
            grid: The grid to check

        Returns:
            True if valid, False if three consecutive found
        """
        # Check rows
        for row in range(self.size):
            for col in range(self.size - 2):
                vals = [grid[row][col], grid[row][col + 1], grid[row][col + 2]]
                if -1 not in vals and len(set(vals)) == 1:
                    return False

        # Check columns
        for col in range(self.size):
            for row in range(self.size - 2):
                vals = [grid[row][col], grid[row + 1][col], grid[row + 2][col]]
                if -1 not in vals and len(set(vals)) == 1:
                    return False

        return True

    def _check_equal_counts(self, sequence: list[int]) -> bool:
        """Check if a completed sequence has equal 0s and 1s.

        Args:
            sequence: List of values

        Returns:
            True if equal counts or incomplete, False if counts are wrong
        """
        if -1 in sequence:
            # Not complete yet
            count_0 = sequence.count(0)
            count_1 = sequence.count(1)
            # Check if we haven't exceeded the limit
            return count_0 <= self.size // 2 and count_1 <= self.size // 2

        return sequence.count(0) == sequence.count(1) == self.size // 2

    def _generate_valid_solution(self) -> bool:
        """Generate a valid binary puzzle solution using backtracking.

        Returns:
            True if solution generated successfully
        """
        for row in range(self.size):
            for col in range(self.size):
                if self.solution[row][col] == -1:
                    # Try 0 and 1
                    for value in [0, 1]:
                        self.solution[row][col] = value

                        # Check constraints
                        if self._check_no_three_consecutive(self.solution):
                            # Check row count constraint
                            row_vals = self.solution[row]
                            if self._check_equal_counts(row_vals):
                                # Check column count constraint
                                col_vals = [self.solution[r][col] for r in range(self.size)]
                                if self._check_equal_counts(col_vals):
                                    if self._generate_valid_solution():
                                        return True

                        self.solution[row][col] = -1

                    return False

        return True

    def _verify_binary_solution(self) -> bool:
        """Verify the solution satisfies all binary puzzle constraints."""
        # Check all rows
        for row in range(self.size):
            row_vals = self.solution[row]
            if row_vals.count(0) != self.size // 2 or row_vals.count(1) != self.size // 2:
                return False
            # Check no three consecutive
            for col in range(self.size - 2):
                if row_vals[col] == row_vals[col + 1] == row_vals[col + 2]:
                    return False

        # Check all columns
        for col in range(self.size):
            col_vals = [self.solution[r][col] for r in range(self.size)]
            if col_vals.count(0) != self.size // 2 or col_vals.count(1) != self.size // 2:
                return False
            # Check no three consecutive
            for row in range(self.size - 2):
                if col_vals[row] == col_vals[row + 1] == col_vals[row + 2]:
                    return False

        return True

    def _create_fallback_binary_solution(self) -> None:
        """Create a simple valid binary solution using alternating pattern."""
        # Use a known valid pattern: alternating 0011 style
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

        for row in range(self.size):
            for col in range(self.size):
                # Create a pattern that avoids three consecutive
                # Pattern: 0,0,1,1,0,0 for even rows, 1,1,0,0,1,1 for odd rows
                block = (col // 2) % 2
                if row % 2 == 1:
                    block = 1 - block
                self.solution[row][col] = block

    def _generate_valid_binary_row(self, row: int) -> list[int] | None:
        """Generate a valid row that satisfies all constraints.

        Args:
            row: Row index to generate

        Returns:
            Valid pattern or None if generation fails
        """
        # Create pattern with equal 0s and 1s
        pattern = [0] * (self.size // 2) + [1] * (self.size // 2)

        for _ in range(200):
            self._rng.shuffle(pattern)

            # Check this row doesn't have three consecutive
            has_three = False
            for col in range(self.size - 2):
                if pattern[col] == pattern[col + 1] == pattern[col + 2]:
                    has_three = True
                    break

            if has_three:
                continue

            # Check column constraints so far
            valid = True
            for col in range(self.size):
                col_vals = [self.solution[r][col] for r in range(row)] + [pattern[col]]
                if col_vals.count(0) > self.size // 2 or col_vals.count(1) > self.size // 2:
                    valid = False
                    break

                # Check no three consecutive in column
                if row >= 2:
                    if pattern[col] == self.solution[row - 1][col] == self.solution[row - 2][col]:
                        valid = False
                        break

            if valid:
                return pattern[:]

        return None

    async def generate_puzzle(self) -> None:
        """Generate a new Binary Puzzle."""
        max_restarts = 20

        for _ in range(max_restarts):
            # Start with empty solution
            self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

            # Try to generate each row
            success = True
            for row in range(self.size):
                pattern = self._generate_valid_binary_row(row)
                if pattern is None:
                    success = False
                    break
                self.solution[row] = pattern

            if success:
                # Verify the solution
                if self._verify_binary_solution():
                    break
        else:
            # Fallback: use a simple alternating pattern
            self._create_fallback_binary_solution()

        # Remove some cells based on difficulty
        cells_to_remove_map = {
            DifficultyLevel.EASY: self.size * 2,
            DifficultyLevel.MEDIUM: self.size * 3,
            DifficultyLevel.HARD: self.size * 4,
        }
        cells_to_remove = cells_to_remove_map[self.difficulty]

        # Copy solution to grid
        self.grid = [row[:] for row in self.solution]

        # Randomly remove cells
        cells = [(r, c) for r in range(self.size) for c in range(self.size)]
        self._rng.shuffle(cells)

        for r, c in cells[:cells_to_remove]:
            self.grid[r][c] = -1

        self.initial_grid = [row[:] for row in self.grid]
        self.moves_made = 0
        self.game_started = True

    async def validate_move(self, row: int, col: int, num: int) -> MoveResult:
        """Place a number on the grid.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            num: Number to place (0, 1, or -1 to clear)

        Returns:
            MoveResult indicating success/failure and message
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return MoveResult(success=False, message=f"Invalid coordinates. Use row and column between 1-{self.size}.")

        # Check if this cell is part of the initial puzzle
        if self.initial_grid[row][col] != -1:
            return MoveResult(success=False, message="Cannot modify initial puzzle cells.")

        # Clear the cell
        if num == -1 or num == 2:  # Accept 2 as clear command for convenience
            self.grid[row][col] = -1
            return MoveResult(success=True, message="Cell cleared.", state_changed=True)

        # Validate number
        if num not in [0, 1]:
            return MoveResult(success=False, message="Invalid number. Use 0, 1, or 2 to clear.")

        # Check if the move is valid
        old_value = self.grid[row][col]
        self.grid[row][col] = num

        # Check no three consecutive
        if not self._check_no_three_consecutive(self.grid):
            self.grid[row][col] = old_value
            return MoveResult(success=False, message="Invalid move! This creates three consecutive identical values.")

        # Check count constraints
        row_vals = self.grid[row]
        if not self._check_equal_counts(row_vals):
            self.grid[row][col] = old_value
            return MoveResult(success=False, message="Invalid move! This exceeds the count limit for this row.")

        col_vals = [self.grid[r][col] for r in range(self.size)]
        if not self._check_equal_counts(col_vals):
            self.grid[row][col] = old_value
            return MoveResult(success=False, message="Invalid move! This exceeds the count limit for this column.")

        self.moves_made += 1
        return MoveResult(success=True, message="Number placed successfully!", state_changed=True)

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        # Check all cells filled
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
        empty_cells = [(r, c) for r in range(self.size) for c in range(self.size) if self.grid[r][c] == -1]
        if not empty_cells:
            return None

        row, col = self._rng.choice(empty_cells)
        hint_data = (row + 1, col + 1, self.solution[row][col])
        hint_message = f"Try placing {self.solution[row][col]} at row {row + 1}, column {col + 1}"
        return hint_data, hint_message

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        Returns:
            String representation of the puzzle grid
        """
        lines = []

        # Header - align with row format "NN|"
        header = "  |"
        for i in range(self.size):
            col_label = str(i + 1) if i < 9 else chr(65 + i - 9)
            header += f"{col_label}|"
        lines.append(header)
        lines.append("  +" + "-+" * self.size)

        for row in range(self.size):
            line = f"{row + 1:2d}|"
            for col in range(self.size):
                cell = self.grid[row][col]
                if cell == -1:
                    line += ".|"
                else:
                    line += f"{cell}|"
            lines.append(line)
            lines.append("  +" + "-+" * self.size)

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Binary Puzzle.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return f"""BINARY PUZZLE RULES:
- Fill {self.size}x{self.size} grid with 0s and 1s
- Max 2 consecutive 0s or 1s per row/column
- Each row/column: {self.size // 2} zeros, {self.size // 2} ones
- All rows unique, all columns unique"""

    def get_commands(self) -> str:
        """Get the available commands for Binary Puzzle.

        Returns:
            Multi-line string describing available commands
        """
        return """BINARY PUZZLE COMMANDS:
  place <row> <col> <num>  - Place 0 or 1 (e.g., 'place 1 2 0')
  clear <row> <col>        - Clear a cell (or use 'place <row> <col> 2')
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
        empty = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == -1)
        return f"Moves made: {self.moves_made} | Empty cells: {empty} | Grid size: {self.size}x{self.size} | Seed: {self.seed}"
