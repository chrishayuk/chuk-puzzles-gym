"""Sudoku puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import SudokuConfig


class SudokuGame(PuzzleGame):
    """Classic 9x9 Sudoku puzzle game."""

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Sudoku game.

        Args:
            difficulty: Game difficulty level (easy, medium, hard)
            seed: Random seed for reproducible puzzle generation
        """
        super().__init__(difficulty, seed, **kwargs)
        self.config = SudokuConfig.from_difficulty(self.difficulty)
        self.grid = [[0 for _ in range(9)] for _ in range(9)]
        self.solution = [[0 for _ in range(9)] for _ in range(9)]
        self.initial_grid = [[0 for _ in range(9)] for _ in range(9)]

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Sudoku"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Classic logic puzzle - fill 9x9 grid with digits 1-9"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["all_different", "regional_uniqueness", "grid_constraints", "multi_level_constraints"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["resource_assignment", "unique_allocation", "multi_constraint_satisfaction", "grid_scheduling"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "large", "constraint_density": "moderate"}

    @property
    def complexity_metrics(self) -> dict[str, int | float]:
        """Quantified complexity metrics for this Sudoku puzzle."""
        empty_cells = sum(1 for r in range(9) for c in range(9) if self.grid[r][c] == 0)
        # Sudoku has 27 AllDifferent constraints: 9 rows + 9 cols + 9 boxes
        constraint_count = 27
        # 81 cells total, domain is 1-9
        variable_count = 81
        domain_size = 9
        # Branching factor depends on how constrained each cell is
        # For a well-formed puzzle, average is around 2-3
        branching_factor = 2.5 if empty_cells > 0 else 0.0
        return {
            "variable_count": variable_count,
            "constraint_count": constraint_count,
            "domain_size": domain_size,
            "branching_factor": branching_factor,
            "empty_cells": empty_cells,
        }

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps to solve = number of empty cells to fill."""
        return sum(1 for r in range(9) for c in range(9) if self.grid[r][c] == 0)

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Detailed difficulty characteristics for Sudoku."""
        from ...models import DifficultyLevel

        empty = self.optimal_steps or 0
        # Logic depth: easy puzzles need simple elimination, hard need chains
        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 4,
            DifficultyLevel.HARD.value: 6,
        }.get(self.difficulty.value, 3)
        # Branching factor increases with empty cells
        branching = 2.0 + (empty / 81) * 4  # 2-6 range
        # Constraint density is inverse of empty cells ratio
        density = 1.0 - (empty / 81)

        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=round(branching, 1),
            state_observability=1.0,
            constraint_density=round(density, 2),
        )

    def is_valid_move(self, row: int, col: int, num: int, grid: list[list[int]] | None = None) -> bool:
        """Check if placing num at (row, col) is valid according to sudoku rules.

        Args:
            row: Row index (0-8)
            col: Column index (0-8)
            num: Number to place (1-9)
            grid: Grid to check against (defaults to self.grid)

        Returns:
            True if the move is valid, False otherwise
        """
        if grid is None:
            grid = self.grid

        # Check row
        for c in range(9):
            if c != col and grid[row][c] == num:
                return False

        # Check column
        for r in range(9):
            if r != row and grid[r][col] == num:
                return False

        # Check 3x3 box
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for r in range(box_row, box_row + 3):
            for c in range(box_col, box_col + 3):
                if (r != row or c != col) and grid[r][c] == num:
                    return False

        return True

    def solve(self, grid: list[list[int]]) -> bool:
        """Solve the sudoku puzzle using backtracking.

        Args:
            grid: The sudoku grid to solve

        Returns:
            True if solved, False otherwise
        """
        for row in range(9):
            for col in range(9):
                if grid[row][col] == 0:
                    for num in range(1, 10):
                        # Temporarily place the number
                        grid[row][col] = num

                        # Check if it's valid (check against the grid being solved)
                        if self.is_valid_move(row, col, num, grid) and self.solve(grid):
                            return True

                        # Backtrack
                        grid[row][col] = 0

                    return False
        return True

    async def generate_puzzle(self) -> None:
        """Generate a new sudoku puzzle."""
        # Start with an empty grid
        self.grid = [[0 for _ in range(9)] for _ in range(9)]

        # Fill diagonal 3x3 boxes (they don't interfere with each other)
        for box in range(3):
            nums = list(range(1, 10))
            self._rng.shuffle(nums)
            for i in range(3):
                for j in range(3):
                    self.grid[box * 3 + i][box * 3 + j] = nums[i * 3 + j]

        # Solve the complete grid
        self.solution = [row[:] for row in self.grid]
        self.solve(self.solution)
        self.grid = [row[:] for row in self.solution]

        # Remove numbers based on difficulty
        cells_to_remove = self.config.cells_to_remove

        # Randomly remove numbers
        cells = [(r, c) for r in range(9) for c in range(9)]
        self._rng.shuffle(cells)

        for r, c in cells[:cells_to_remove]:
            self.grid[r][c] = 0

        # Store the initial state
        self.initial_grid = [row[:] for row in self.grid]
        self.moves_made = 0
        self.game_started = True

    async def validate_move(self, row: int, col: int, num: int) -> MoveResult:
        """Place a number on the grid.

        Args:
            row: Row index (1-9, user-facing)
            col: Column index (1-9, user-facing)
            num: Number to place (1-9, or 0 to clear)

        Returns:
            MoveResult with success status and message
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < 9 and 0 <= col < 9):
            return MoveResult(success=False, message="Invalid coordinates. Use row and column between 1-9.")

        # Check if this cell is part of the initial puzzle
        if self.initial_grid[row][col] != 0:
            return MoveResult(success=False, message="Cannot modify initial puzzle cells.")

        # Clear the cell
        if num == 0:
            self.grid[row][col] = 0
            return MoveResult(success=True, message="Cell cleared.", state_changed=True)

        # Validate number
        if not (1 <= num <= 9):
            return MoveResult(success=False, message="Invalid number. Use 1-9 or 0 to clear.")

        # Check if the move is valid
        old_value = self.grid[row][col]
        self.grid[row][col] = num

        if not self.is_valid_move(row, col, num):
            self.grid[row][col] = old_value
            return MoveResult(success=False, message="Invalid move! This number conflicts with sudoku rules.")

        self.moves_made += 1
        return MoveResult(success=True, message="Number placed successfully!", state_changed=True)

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        for row in range(9):
            for col in range(9):
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
        empty_cells = [(r, c) for r in range(9) for c in range(9) if self.grid[r][c] == 0]
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
        lines.append("  | 1 2 3 | 4 5 6 | 7 8 9 |")
        lines.append("  " + "-" * 25)

        for row in range(9):
            if row > 0 and row % 3 == 0:
                lines.append("  " + "-" * 25)

            line = f"{row + 1} |"
            for col in range(9):
                if col > 0 and col % 3 == 0:
                    line += " |"

                cell = self.grid[row][col]
                if cell == 0:
                    line += " ."
                else:
                    line += f" {cell}"

            line += " |"
            lines.append(line)

        lines.append("  " + "-" * 25)
        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Sudoku.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return """SUDOKU RULES:
- Fill the 9x9 grid with numbers 1-9
- Each row must contain 1-9 without repeats
- Each column must contain 1-9 without repeats
- Each 3x3 box must contain 1-9 without repeats
- Some cells are pre-filled and cannot be modified"""

    def get_commands(self) -> str:
        """Get the available commands for Sudoku.

        Returns:
            Multi-line string describing available commands
        """
        return """SUDOKU COMMANDS:
  place <row> <col> <num>  - Place a number (e.g., 'place 1 5 7')
  clear <row> <col>        - Clear a cell you've filled
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
        empty = sum(1 for r in range(9) for c in range(9) if self.grid[r][c] == 0)
        return f"Moves made: {self.moves_made} | Empty cells: {empty} | Seed: {self.seed}"
