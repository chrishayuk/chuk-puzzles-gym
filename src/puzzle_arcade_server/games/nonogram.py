"""Nonogram (Picross) puzzle game implementation."""

import random
from typing import Any

from ..base.puzzle_game import PuzzleGame


class NonogramGame(PuzzleGame):
    """Nonogram (also known as Picross, Griddlers, or Hanjie) puzzle game.

    Fill cells to reveal a picture based on number clues for each row and column.
    Clues indicate consecutive filled cells in that row/column.
    """

    def __init__(self, difficulty: str = "easy"):
        """Initialize a new Nonogram game.

        Args:
            difficulty: Game difficulty level (easy=5x5, medium=8x8, hard=10x10)
        """
        super().__init__(difficulty)

        # Grid size based on difficulty
        self.size = {"easy": 5, "medium": 8, "hard": 10}.get(difficulty, 5)

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
        density = {"easy": 0.4, "medium": 0.5, "hard": 0.6}.get(self.difficulty, 0.4)

        for row in range(self.size):
            for col in range(self.size):
                self.solution[row][col] = 1 if random.random() < density else 0

    def generate_puzzle(self) -> None:
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

    def validate_move(self, row: int, col: int, value: int) -> tuple[bool, str]:
        """Mark a cell on the grid.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            value: Value to place (0=empty/X, 1=filled/■, -1=unknown/clear)

        Returns:
            Tuple of (success, message)
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False, f"Invalid coordinates. Use row and column between 1-{self.size}."

        # Validate value
        if value not in [-1, 0, 1]:
            return False, "Invalid value. Use 1 (filled), 0 (empty), or -1 (clear)."

        self.grid[row][col] = value
        self.moves_made += 1
        return True, "Cell marked successfully!"

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

    def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        unknown_cells = [(r, c) for r in range(self.size) for c in range(self.size) if self.grid[r][c] == -1]
        if not unknown_cells:
            return None

        row, col = random.choice(unknown_cells)
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
        return f"Moves made: {self.moves_made} | Unknown: {unknown} | Filled: {filled}/{self.size * self.size}"
