"""Nurikabe puzzle game implementation."""

import random
from typing import Any

from ..base.puzzle_game import PuzzleGame


class NurikabeGame(PuzzleGame):
    """Nurikabe puzzle game.

    Create islands (white cells) and sea (black cells) where:
    - Each numbered cell is part of a white island of that size
    - All black cells are connected
    - No 2×2 blocks of black cells
    - All white cells in an island are connected
    """

    def __init__(self, difficulty: str = "easy"):
        """Initialize a new Nurikabe game.

        Args:
            difficulty: Game difficulty level (easy/medium/hard)
        """
        super().__init__(difficulty)

        # Grid size based on difficulty
        self.size = {"easy": 6, "medium": 8, "hard": 10}.get(difficulty, 6)

        # Grid: 0 = unknown, 1 = white (island), 2 = black (sea)
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Clues: (row, col, size) - this cell is part of an island of this size
        self.clues: list[tuple[int, int, int]] = []

        # Islands: list of ((row, col), size) tuples
        self.islands: list[tuple[tuple[int, int], int]] = []

        # Given cells: set of (row, col) positions that show clue numbers
        self.given_cells: set[tuple[int, int]] = set()

        # Number of islands for difficulty
        self.num_islands = {"easy": 3, "medium": 4, "hard": 5}.get(difficulty, 3)

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Nurikabe"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Create islands and sea - test connectivity reasoning"

    def generate_puzzle(self) -> None:
        """Generate a new Nurikabe puzzle."""
        # For simplicity, we'll create a basic puzzle with predefined patterns
        # A full implementation would use more sophisticated generation

        # Start with all black
        self.solution = [[2 for _ in range(self.size)] for _ in range(self.size)]

        # Create some islands
        self.clues = []
        self.islands = []
        self.given_cells = set()
        placed_islands: list[list[tuple[int, int]]] = []

        for _ in range(self.num_islands):
            attempts = 0
            while attempts < 50:
                # Random position for island
                row = random.randint(0, self.size - 1)
                col = random.randint(0, self.size - 1)

                # Random island size
                island_size = random.randint(2, 4)

                # Try to place island
                island_cells = self._try_place_island(row, col, island_size, placed_islands)

                if island_cells:
                    # Mark cells as white
                    for r, c in island_cells:
                        self.solution[r][c] = 1

                    # Add clue (use first cell of island)
                    clue_cell = island_cells[0]
                    self.clues.append((clue_cell[0], clue_cell[1], island_size))
                    self.islands.append((clue_cell, island_size))
                    self.given_cells.add(clue_cell)
                    placed_islands.append(island_cells)
                    break

                attempts += 1

        # Initialize player grid
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Place clue numbers
        for row, col, _size in self.clues:
            self.grid[row][col] = 1  # Mark as white

        self.moves_made = 0
        self.game_started = True

    def _try_place_island(
        self, start_row: int, start_col: int, size: int, existing_islands: list[list[tuple[int, int]]]
    ) -> list[tuple[int, int]] | None:
        """Try to place an island of given size starting from position.

        Returns:
            List of cells in the island, or None if placement failed
        """
        island = [(start_row, start_col)]
        candidates = [(start_row, start_col)]

        while len(island) < size and candidates:
            # Pick random cell from candidates
            cell = random.choice(candidates)
            candidates.remove(cell)

            # Try to expand from this cell
            row, col = cell
            neighbors = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]

            random.shuffle(neighbors)

            for nr, nc in neighbors:
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if (nr, nc) not in island:
                        # Check if adding this cell would overlap with existing islands
                        overlap = False
                        for existing in existing_islands:
                            if (nr, nc) in existing:
                                overlap = True
                                break

                            # Also check if adjacent to existing island
                            for er, ec in existing:
                                if abs(nr - er) + abs(nc - ec) == 1:
                                    overlap = True
                                    break

                            if overlap:
                                break

                        if not overlap:
                            island.append((nr, nc))
                            candidates.append((nr, nc))

                            if len(island) >= size:
                                return island

        return island if len(island) == size else None

    def validate_move(self, row: int, col: int, color: str) -> tuple[bool, str]:
        """Mark a cell as black or white.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            color: 'white' or 'black'

        Returns:
            Tuple of (success, message)
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False, f"Invalid coordinates. Use row and column between 1-{self.size}."

        # Check if this is a clue cell
        for clue_row, clue_col, _size in self.clues:
            if row == clue_row and col == clue_col:
                return False, "Cannot modify clue cells."

        color = color.lower()

        if color == "white" or color == "w":
            self.grid[row][col] = 1
            self.moves_made += 1
            return True, "Cell marked as white (island)."
        elif color == "black" or color == "b":
            self.grid[row][col] = 2
            self.moves_made += 1
            return True, "Cell marked as black (sea)."
        elif color == "clear" or color == "c":
            # Don't clear clue cells
            for clue_row, clue_col, _size in self.clues:
                if row == clue_row and col == clue_col:
                    return False, "Cannot clear clue cells."
            # Check if cell is already unmarked
            if self.grid[row][col] == 0:
                return False, "Cell is already unmarked."
            self.grid[row][col] = 0
            self.moves_made += 1
            return True, "Cell cleared."
        else:
            return False, "Invalid color. Use 'white', 'black', or 'clear'."

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        # All cells must be filled
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] == 0:
                    return False

        # Check each clue has an island of correct size
        for clue_row, clue_col, island_size in self.clues:
            island = self._get_island_from_cell(clue_row, clue_col)
            if len(island) != island_size:
                return False

        # Check all black cells are connected
        if not self._check_black_connected():
            return False

        # Check no 2×2 blocks of black
        if self._has_2x2_black():
            return False

        return True

    def _get_island_from_cell(self, row: int, col: int) -> set[tuple[int, int]]:
        """Get all cells in the white island containing this cell using BFS."""
        if self.grid[row][col] != 1:
            return set()

        island = set()
        queue = [(row, col)]
        island.add((row, col))

        while queue:
            r, c = queue.pop(0)

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc

                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if (nr, nc) not in island and self.grid[nr][nc] == 1:
                        island.add((nr, nc))
                        queue.append((nr, nc))

        return island

    def _check_black_connected(self) -> bool:
        """Check if all black cells form a single connected component."""
        # Find first black cell
        first_black = None
        black_count = 0

        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] == 2:
                    black_count += 1
                    if first_black is None:
                        first_black = (row, col)

        if black_count == 0:
            return True  # No black cells is technically connected

        # BFS from first black cell
        visited = set()
        queue = [first_black]
        visited.add(first_black)

        while queue:
            row, col = queue.pop(0)

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc

                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if (nr, nc) not in visited and self.grid[nr][nc] == 2:
                        visited.add((nr, nc))
                        queue.append((nr, nc))

        return len(visited) == black_count

    def _has_2x2_black(self) -> bool:
        """Check if there are any 2×2 blocks of black cells."""
        for row in range(self.size - 1):
            for col in range(self.size - 1):
                if (
                    self.grid[row][col] == 2
                    and self.grid[row][col + 1] == 2
                    and self.grid[row + 1][col] == 2
                    and self.grid[row + 1][col + 1] == 2
                ):
                    return True
        return False

    def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None
        """
        # Find a cell that differs from solution
        for row in range(self.size):
            for col in range(self.size):
                # Skip clue cells
                is_clue = any(r == row and c == col for r, c, _ in self.clues)
                if is_clue:
                    continue

                if self.grid[row][col] != self.solution[row][col]:
                    color = "white" if self.solution[row][col] == 1 else "black"
                    hint_data = (row + 1, col + 1, color)
                    hint_message = f"Try marking ({row + 1},{col + 1}) as {color}"
                    return hint_data, hint_message

        return None

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        Returns:
            String representation of the puzzle grid
        """
        lines = []

        # Header
        header = "  |"
        for i in range(self.size):
            header += f"{i + 1}|"
        lines.append(header)
        lines.append("  +" + "-+" * self.size)

        # Grid rows
        for row in range(self.size):
            line = f"{row + 1} |"

            for col in range(self.size):
                # Check if this is a clue cell
                clue_value = None
                for clue_row, clue_col, size in self.clues:
                    if row == clue_row and col == clue_col:
                        clue_value = size
                        break

                if clue_value is not None:
                    line += f"{clue_value}|"
                elif self.grid[row][col] == 0:
                    line += ".|"
                elif self.grid[row][col] == 1:
                    line += "○|"  # White (island)
                elif self.grid[row][col] == 2:
                    line += "●|"  # Black (sea)

            lines.append(line)
            lines.append("  +" + "-+" * self.size)

        lines.append("")
        lines.append("Legend: Numbers = island size, ○ = white (island), ● = black (sea), . = unknown")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Nurikabe.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return """NURIKABE RULES:
- Numbers indicate island sizes (connected white cells)
- Each number must be part of an island of that size
- All black cells (sea) must be connected
- No 2×2 blocks of black cells allowed
- White cells in same island must be connected
- All cells must be either white (island) or black (sea)"""

    def get_commands(self) -> str:
        """Get the available commands for Nurikabe.

        Returns:
            Multi-line string describing available commands
        """
        return """NURIKABE COMMANDS:
  mark <row> <col> white   - Mark cell as white/island (e.g., 'mark 2 3 white')
  mark <row> <col> black   - Mark cell as black/sea
  mark <row> <col> clear   - Clear a cell
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
        filled = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] != 0)
        total = self.size * self.size

        return f"Moves made: {self.moves_made} | Filled: {filled}/{total} cells | Clues: {len(self.clues)}"
