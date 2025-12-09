"""Binary Puzzle game implementation."""

import random
from typing import Any

from ..base.puzzle_game import PuzzleGame


class BinaryPuzzleGame(PuzzleGame):
    """Binary Puzzle (also known as Takuzu or Binairo).

    Fill a grid with 0s and 1s following these rules:
    - No more than two consecutive 0s or 1s in any row or column
    - Each row and column must have equal numbers of 0s and 1s
    - No two rows are identical, no two columns are identical
    """

    def __init__(self, difficulty: str = "easy"):
        """Initialize a new Binary Puzzle game.

        Args:
            difficulty: Game difficulty level (easy=6x6, medium=8x8, hard=10x10)
        """
        super().__init__(difficulty)

        # Grid size based on difficulty (must be even)
        self.size = {"easy": 6, "medium": 8, "hard": 10}.get(difficulty, 6)

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

    def generate_puzzle(self) -> None:
        """Generate a new Binary Puzzle."""
        # Start with a simple pattern that satisfies constraints
        # Alternating pattern with some randomness
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Create a simple valid solution
        for row in range(self.size):
            # Create pattern with equal 0s and 1s
            pattern = [0] * (self.size // 2) + [1] * (self.size // 2)
            random.shuffle(pattern)

            # Ensure no three consecutive
            valid = False
            attempts = 0
            while not valid and attempts < 100:
                random.shuffle(pattern)
                self.solution[row] = pattern[:]

                # Check this row doesn't have three consecutive
                has_three = False
                for col in range(self.size - 2):
                    if pattern[col] == pattern[col + 1] == pattern[col + 2]:
                        has_three = True
                        break

                if not has_three:
                    # Check column constraints so far
                    valid = True
                    for col in range(self.size):
                        col_vals = [self.solution[r][col] for r in range(row + 1)]
                        if col_vals.count(0) > self.size // 2 or col_vals.count(1) > self.size // 2:
                            valid = False
                            break

                        # Check no three consecutive in column
                        if row >= 2:
                            if self.solution[row][col] == self.solution[row - 1][col] == self.solution[row - 2][col]:
                                valid = False
                                break

                attempts += 1

        # Remove some cells based on difficulty
        cells_to_remove = {"easy": self.size * 2, "medium": self.size * 3, "hard": self.size * 4}.get(
            self.difficulty, self.size * 2
        )

        # Copy solution to grid
        self.grid = [row[:] for row in self.solution]

        # Randomly remove cells
        cells = [(r, c) for r in range(self.size) for c in range(self.size)]
        random.shuffle(cells)

        for r, c in cells[:cells_to_remove]:
            self.grid[r][c] = -1

        self.initial_grid = [row[:] for row in self.grid]
        self.moves_made = 0
        self.game_started = True

    def validate_move(self, row: int, col: int, num: int) -> tuple[bool, str]:
        """Place a number on the grid.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            num: Number to place (0, 1, or -1 to clear)

        Returns:
            Tuple of (success, message)
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False, f"Invalid coordinates. Use row and column between 1-{self.size}."

        # Check if this cell is part of the initial puzzle
        if self.initial_grid[row][col] != -1:
            return False, "Cannot modify initial puzzle cells."

        # Clear the cell
        if num == -1 or num == 2:  # Accept 2 as clear command for convenience
            self.grid[row][col] = -1
            return True, "Cell cleared."

        # Validate number
        if num not in [0, 1]:
            return False, "Invalid number. Use 0, 1, or 2 to clear."

        # Check if the move is valid
        old_value = self.grid[row][col]
        self.grid[row][col] = num

        # Check no three consecutive
        if not self._check_no_three_consecutive(self.grid):
            self.grid[row][col] = old_value
            return False, "Invalid move! This creates three consecutive identical values."

        # Check count constraints
        row_vals = self.grid[row]
        if not self._check_equal_counts(row_vals):
            self.grid[row][col] = old_value
            return False, "Invalid move! This exceeds the count limit for this row."

        col_vals = [self.grid[r][col] for r in range(self.size)]
        if not self._check_equal_counts(col_vals):
            self.grid[row][col] = old_value
            return False, "Invalid move! This exceeds the count limit for this column."

        self.moves_made += 1
        return True, "Number placed successfully!"

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

    def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        empty_cells = [(r, c) for r in range(self.size) for c in range(self.size) if self.grid[r][c] == -1]
        if not empty_cells:
            return None

        row, col = random.choice(empty_cells)
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
        return f"Moves made: {self.moves_made} | Empty cells: {empty} | Grid size: {self.size}x{self.size}"
