"""Kakuro puzzle game implementation."""

import random
from typing import Any

from ..base.puzzle_game import PuzzleGame


class KakuroGame(PuzzleGame):
    """Kakuro (Cross Sums) puzzle game.

    Like a crossword puzzle but with numbers. Each run (horizontal or vertical
    sequence of white cells) must sum to the clue number, and no digit can repeat
    within a run.
    """

    def __init__(self, difficulty: str = "easy"):
        """Initialize a new Kakuro game.

        Args:
            difficulty: Game difficulty level (easy=5x5, medium=7x7, hard=9x9)
        """
        super().__init__(difficulty)

        # Grid size based on difficulty
        self.size = {"easy": 5, "medium": 7, "hard": 9}.get(difficulty, 5)

        # Grid: 0 = empty/playable, -1 = black cell
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.initial_grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Clues: list of (row, col, direction, sum, length)
        # direction: 'h' for horizontal, 'v' for vertical
        self.clues: list[tuple[int, int, str, int, int]] = []

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Kakuro"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Crossword math puzzle - fill runs with unique digits that sum to clues"

    def _create_pattern(self) -> None:
        """Create a pattern of black and white cells."""
        # Simple pattern: create some black cells
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Make diagonal black cells
        for i in range(min(2, self.size)):
            self.grid[i][i] = -1

        # Add some random black cells to create runs
        num_black = self.size // 2
        for _ in range(num_black):
            row = random.randint(0, self.size - 1)
            col = random.randint(0, self.size - 1)
            if self.grid[row][col] == 0:
                self.grid[row][col] = -1

    def _find_runs(self) -> list[tuple[int, int, str, list[tuple[int, int]]]]:
        """Find all runs (sequences of white cells) in the grid.

        Returns:
            List of (start_row, start_col, direction, cells) where cells is list of (row, col)
        """
        runs = []

        # Find horizontal runs
        for row in range(self.size):
            col = 0
            while col < self.size:
                if self.grid[row][col] != -1:
                    # Start of a run
                    start_col = col
                    cells = []
                    while col < self.size and self.grid[row][col] != -1:
                        cells.append((row, col))
                        col += 1

                    if len(cells) >= 2:  # Only count runs of length 2+
                        runs.append((row, start_col, "h", cells))
                else:
                    col += 1

        # Find vertical runs
        for col in range(self.size):
            row = 0
            while row < self.size:
                if self.grid[row][col] != -1:
                    # Start of a run
                    start_row = row
                    cells = []
                    while row < self.size and self.grid[row][col] != -1:
                        cells.append((row, col))
                        row += 1

                    if len(cells) >= 2:  # Only count runs of length 2+
                        runs.append((start_row, col, "v", cells))
                else:
                    row += 1

        return runs

    def generate_puzzle(self) -> None:
        """Generate a new Kakuro puzzle."""
        # Create pattern
        self._create_pattern()

        # Find all runs
        runs = self._find_runs()

        # Generate solution for each run
        self.solution = [row[:] for row in self.grid]
        self.clues = []

        for start_row, start_col, direction, cells in runs:
            # Generate unique random digits for this run
            run_length = len(cells)
            digits = random.sample(range(1, 10), run_length)

            for (r, c), digit in zip(cells, digits, strict=True):
                self.solution[r][c] = digit

            # Create clue
            clue_sum = sum(digits)
            self.clues.append((start_row, start_col, direction, clue_sum, run_length))

        # Empty the playable cells
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] != -1:
                    self.grid[row][col] = 0

        self.initial_grid = [row[:] for row in self.grid]
        self.moves_made = 0
        self.game_started = True

    def validate_move(self, row: int, col: int, num: int) -> tuple[bool, str]:
        """Place a number on the grid.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            num: Number to place (1-9, or 0 to clear)

        Returns:
            Tuple of (success, message)
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False, f"Invalid coordinates. Use row and column between 1-{self.size}."

        # Check if this is a black cell
        if self.initial_grid[row][col] == -1:
            return False, "Cannot place numbers in black cells."

        # Clear the cell
        if num == 0:
            self.grid[row][col] = 0
            return True, "Cell cleared."

        # Validate number
        if not (1 <= num <= 9):
            return False, "Invalid number. Use 1-9 or 0 to clear."

        self.grid[row][col] = num
        self.moves_made += 1
        return True, "Number placed successfully!"

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        # Check all white cells filled
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] == 0:  # Empty white cell
                    return False
                if self.grid[row][col] != -1 and self.grid[row][col] != self.solution[row][col]:
                    return False

        return True

    def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        empty_cells = [
            (r, c)
            for r in range(self.size)
            for c in range(self.size)
            if self.grid[r][c] == 0  # Empty white cell
        ]
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

        # Header - align with row format "N |"
        header = "  |"
        for i in range(self.size):
            header += f" {i + 1} |"
        lines.append(header)
        lines.append("  +" + "---+" * self.size)

        for row in range(self.size):
            line = f"{row + 1} |"
            for col in range(self.size):
                if self.grid[row][col] == -1:
                    line += " ■ |"
                else:
                    cell = self.grid[row][col]
                    cell_str = str(cell) if cell != 0 else "."
                    line += f" {cell_str} |"
            lines.append(line)
            lines.append("  +" + "---+" * self.size)

        # Show clues
        lines.append("\nClues:")
        for start_row, start_col, direction, clue_sum, length in self.clues:
            dir_str = "→" if direction == "h" else "↓"
            lines.append(f"  ({start_row + 1},{start_col + 1}) {dir_str} {clue_sum} ({length} cells)")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Kakuro.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return """KAKURO RULES:
- Fill white cells with 1-9
- Runs must sum to clue (→ horizontal, ↓ vertical)
- No repeats within a run
- Black cells (■) stay empty"""

    def get_commands(self) -> str:
        """Get the available commands for Kakuro.

        Returns:
            Multi-line string describing available commands
        """
        return """KAKURO COMMANDS:
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
        total_white = sum(1 for r in range(self.size) for c in range(self.size) if self.initial_grid[r][c] != -1)
        return f"Moves made: {self.moves_made} | Empty cells: {empty}/{total_white}"
