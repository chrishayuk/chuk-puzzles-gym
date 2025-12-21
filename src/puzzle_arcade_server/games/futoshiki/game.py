"""Futoshiki puzzle game implementation."""

from typing import Any

from ...models import DifficultyLevel, DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import FutoshikiConfig


class FutoshikiGame(PuzzleGame):
    """Futoshiki (inequality constraints) puzzle game.

    Similar to Sudoku but uses inequality constraints between adjacent cells.
    Each row and column must contain unique numbers from 1 to N.
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Futoshiki game.

        Args:
            difficulty: Game difficulty level (easy=4x4, medium=5x5, hard=6x6)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Use pydantic config based on difficulty
        self.config = FutoshikiConfig.from_difficulty(self.difficulty)
        self.size = self.config.size

        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.initial_grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Inequalities: list of ((row1, col1), (row2, col2))
        # Meaning: cell1 > cell2
        self.inequalities: list[tuple[tuple[int, int], tuple[int, int]]] = []

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Futoshiki"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Inequality number puzzle - fill grid with constraints"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["all_different", "linear_inequality", "ordering", "comparison_constraints"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["priority_ranking", "ordering_with_constraints", "relative_positioning", "inequality_systems"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "medium", "constraint_density": "moderate"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = empty cells to fill."""
        return sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 0)

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Futoshiki."""

        empty = self.optimal_steps or 0
        total = self.size * self.size
        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 3,
            DifficultyLevel.HARD.value: 5,
        }.get(self.difficulty.value, 3)
        branching = 2.0 + (empty / total) * 2
        density = 1.0 - (empty / total) if total > 0 else 0.5
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=round(branching, 1),
            state_observability=1.0,
            constraint_density=round(density, 2),
        )

    def is_valid_move(self, row: int, col: int, num: int, grid: list[list[int]] | None = None) -> bool:
        """Check if placing num at (row, col) is valid.

        Args:
            row: Row index (0-indexed)
            col: Column index (0-indexed)
            num: Number to place (1 to self.size)
            grid: Grid to check against (defaults to self.grid)

        Returns:
            True if the move is valid, False otherwise
        """
        if grid is None:
            grid = self.grid

        # Check row uniqueness
        for c in range(self.size):
            if c != col and grid[row][c] == num:
                return False

        # Check column uniqueness
        for r in range(self.size):
            if r != row and grid[r][col] == num:
                return False

        # Check inequality constraints involving this cell
        for (r1, c1), (r2, c2) in self.inequalities:
            # Check if this cell is involved
            if (r1, c1) == (row, col):
                # This cell should be > cell2
                if grid[r2][c2] != 0 and num <= grid[r2][c2]:
                    return False
            elif (r2, c2) == (row, col):
                # Cell1 should be > this cell
                if grid[r1][c1] != 0 and grid[r1][c1] <= num:
                    return False

        return True

    def solve(self, grid: list[list[int]]) -> bool:
        """Solve the Futoshiki puzzle using backtracking.

        Args:
            grid: The Futoshiki grid to solve

        Returns:
            True if solved, False otherwise
        """
        for row in range(self.size):
            for col in range(self.size):
                if grid[row][col] == 0:
                    for num in range(1, self.size + 1):
                        grid[row][col] = num

                        if self.is_valid_move(row, col, num, grid) and self.solve(grid):
                            return True

                        grid[row][col] = 0

                    return False
        return True

    def _generate_inequalities(self) -> None:
        """Generate inequality constraints from the solution."""
        self.inequalities = []

        # Determine number of inequalities based on difficulty
        num_inequalities_map = {
            DifficultyLevel.EASY: self.size * 2,
            DifficultyLevel.MEDIUM: self.size * 3,
            DifficultyLevel.HARD: self.size * 4,
        }
        num_inequalities = num_inequalities_map[self.difficulty]

        # Collect all possible adjacent pairs
        possible_pairs = []

        # Horizontal pairs
        for row in range(self.size):
            for col in range(self.size - 1):
                possible_pairs.append(((row, col), (row, col + 1)))

        # Vertical pairs
        for row in range(self.size - 1):
            for col in range(self.size):
                possible_pairs.append(((row, col), (row + 1, col)))

        # Randomly select inequalities
        self._rng.shuffle(possible_pairs)

        for (r1, c1), (r2, c2) in possible_pairs[:num_inequalities]:
            val1 = self.solution[r1][c1]
            val2 = self.solution[r2][c2]

            if val1 > val2:
                self.inequalities.append(((r1, c1), (r2, c2)))
            else:
                self.inequalities.append(((r2, c2), (r1, c1)))

    async def generate_puzzle(self) -> None:
        """Generate a new Futoshiki puzzle."""
        # Generate a valid Latin square as solution
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Simple solution generation: shifted rows
        for row in range(self.size):
            for col in range(self.size):
                self.grid[row][col] = (row + col) % self.size + 1

        # Shuffle rows and columns to make it more random
        row_order = list(range(self.size))
        col_order = list(range(self.size))
        self._rng.shuffle(row_order)
        self._rng.shuffle(col_order)

        shuffled = [[self.grid[row_order[r]][col_order[c]] for c in range(self.size)] for r in range(self.size)]
        self.solution = shuffled

        # Generate inequalities
        self._generate_inequalities()

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
            self.grid[r][c] = 0

        self.initial_grid = [row[:] for row in self.grid]
        self.moves_made = 0
        self.game_started = True

    async def validate_move(self, row: int, col: int, num: int) -> MoveResult:
        """Place a number on the grid.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            num: Number to place (1 to self.size, or 0 to clear)

        Returns:
            MoveResult with success status and message
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return MoveResult(success=False, message=f"Invalid coordinates. Use row and column between 1-{self.size}.")

        # Check if this cell is part of the initial puzzle
        if self.initial_grid[row][col] != 0:
            return MoveResult(success=False, message="Cannot modify initial puzzle cells.")

        # Clear the cell
        if num == 0:
            self.grid[row][col] = 0
            return MoveResult(success=True, message="Cell cleared.", state_changed=True)

        # Validate number
        if not (1 <= num <= self.size):
            return MoveResult(success=False, message=f"Invalid number. Use 1-{self.size} or 0 to clear.")

        # Check if the move is valid
        old_value = self.grid[row][col]
        self.grid[row][col] = num

        if not self.is_valid_move(row, col, num):
            self.grid[row][col] = old_value
            return MoveResult(
                success=False, message="Invalid move! This violates uniqueness or inequality constraints."
            )

        self.moves_made += 1
        return MoveResult(success=True, message="Number placed successfully!", state_changed=True)

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] == 0:
                    return False
                if self.grid[row][col] != self.solution[row][col]:
                    return False
        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        empty_cells = [(r, c) for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 0]
        if not empty_cells:
            return None

        row, col = self._rng.choice(empty_cells)
        hint_data = (row + 1, col + 1, self.solution[row][col])
        hint_message = f"Try placing {self.solution[row][col]} at row {row + 1}, column {col + 1}"
        return hint_data, hint_message

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        Returns:
            String representation of the puzzle grid with inequalities
        """
        lines = []

        # Build a map of horizontal and vertical inequalities
        h_ineq = {}  # (row, col) -> '>' or '<' between col and col+1
        v_ineq = {}  # (row, col) -> '^' or 'v' between row and row+1

        for (r1, c1), (r2, c2) in self.inequalities:
            if r1 == r2:  # Horizontal
                if c1 < c2:
                    h_ineq[(r1, c1)] = ">"
                else:
                    h_ineq[(r1, c2)] = "<"
            else:  # Vertical
                if r1 < r2:
                    v_ineq[(r1, c1)] = "v"
                else:
                    v_ineq[(r2, c1)] = "^"

        # Header - align with row format "N | ..."
        header = "  | " + "   ".join(str(i + 1) for i in range(self.size)) + " |"
        lines.append(header)

        for row in range(self.size):
            # Main row
            line = f"{row + 1} | "
            for col in range(self.size):
                cell = self.grid[row][col]
                cell_str = str(cell) if cell != 0 else "."
                line += cell_str

                # Add horizontal inequality
                if col < self.size - 1:
                    ineq = h_ineq.get((row, col), " ")
                    line += f" {ineq} "

            line += " |"
            lines.append(line)

            # Vertical inequality row
            if row < self.size - 1:
                line = "  | "
                for col in range(self.size):
                    ineq = v_ineq.get((row, col), " ")
                    line += ineq
                    if col < self.size - 1:
                        line += "   "
                line += " |"
                lines.append(line)

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Futoshiki.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return f"""FUTOSHIKI RULES:
- Fill {self.size}x{self.size} grid with 1-{self.size}
- No repeats in rows or columns
- Satisfy inequality signs (>, <, ^, v)"""

    def get_commands(self) -> str:
        """Get the available commands for Futoshiki.

        Returns:
            Multi-line string describing available commands
        """
        return """FUTOSHIKI COMMANDS:
  place <row> <col> <num>  - Place a number (e.g., 'place 1 2 4')
  clear <row> <col>        - Clear a cell
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
        empty = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 0)
        return f"Moves made: {self.moves_made} | Empty cells: {empty} | Inequalities: {len(self.inequalities)} | Seed: {self.seed}"
