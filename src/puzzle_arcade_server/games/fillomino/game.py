"""Fillomino puzzle game implementation."""

from typing import Any

from ...models import MoveResult
from .._base import PuzzleGame
from .config import FillominoConfig


class FillominoGame(PuzzleGame):
    """Fillomino puzzle game.

    Fill the grid with numbers such that:
    - The grid is divided into polyomino regions
    - Each region contains cells with the same number
    - The number in each region equals the size of that region
    - No two regions of the same size can share an edge
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None):
        """Initialize a new Fillomino game.

        Args:
            difficulty: Game difficulty level (easy=6x6, medium=8x8, hard=10x10)
        """
        super().__init__(difficulty, seed)

        # Use pydantic config based on difficulty
        self.config = FillominoConfig.from_difficulty(self.difficulty)
        self.size = self.config.size

        # Grid: 0 = empty, 1-9 = number
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.initial_grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Fillomino"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Region growth puzzle - divide grid into numbered polyominoes"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["region_growth", "self_referential_constraints", "partition", "adjacency_exclusion"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["territory_expansion", "cluster_formation", "resource_grouping", "zoning"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "large", "constraint_density": "dense"}

    def _get_adjacent(self, row: int, col: int) -> list[tuple[int, int]]:
        """Get orthogonally adjacent cells.

        Args:
            row: Row index
            col: Column index

        Returns:
            List of (row, col) tuples for valid adjacent cells
        """
        adjacent = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                adjacent.append((nr, nc))
        return adjacent

    def _find_region(
        self, grid: list[list[int]], row: int, col: int, visited: set[tuple[int, int]]
    ) -> list[tuple[int, int]]:
        """Find all cells in the same region using flood fill.

        Args:
            grid: Grid to search
            row: Starting row
            col: Starting column
            visited: Set of already visited cells

        Returns:
            List of (row, col) tuples in the region
        """
        if (row, col) in visited:
            return []

        target_value = grid[row][col]
        if target_value == 0:
            return []

        region = []
        stack = [(row, col)]

        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            if grid[r][c] != target_value:
                continue

            visited.add((r, c))
            region.append((r, c))

            for nr, nc in self._get_adjacent(r, c):
                if (nr, nc) not in visited and grid[nr][nc] == target_value:
                    stack.append((nr, nc))

        return region

    async def generate_puzzle(self) -> None:
        """Generate a new Fillomino puzzle."""
        # Create a valid solution using random region placement
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Fill the grid with regions
        for _ in range(100):  # Try to fill completely
            # Find an empty cell
            empty_cells = [(r, c) for r in range(self.size) for c in range(self.size) if self.solution[r][c] == 0]
            if not empty_cells:
                break

            # Pick a random empty cell
            r, c = self._rng.choice(empty_cells)

            # Choose a random region size (1-5)
            size = self._rng.randint(1, min(5, len(empty_cells)))

            # Try to create a region of this size
            region = [(r, c)]
            self.solution[r][c] = size

            # Grow the region
            while len(region) < size:
                # Find cells adjacent to the current region
                candidates = []
                for rr, cc in region:
                    for nr, nc in self._get_adjacent(rr, cc):
                        if self.solution[nr][nc] == 0 and (nr, nc) not in region:
                            candidates.append((nr, nc))

                if not candidates:
                    # Can't grow further, adjust size
                    size = len(region)
                    for rr, cc in region:
                        self.solution[rr][cc] = size
                    break

                # Add a random candidate to the region
                nr, nc = self._rng.choice(candidates)
                region.append((nr, nc))
                self.solution[nr][nc] = size

        # Fill any remaining cells with size 1
        for r in range(self.size):
            for c in range(self.size):
                if self.solution[r][c] == 0:
                    self.solution[r][c] = 1

        # Create the puzzle by revealing some numbers
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        num_clues = self.config.num_clues

        # Reveal one number from each region
        visited = set()
        clue_count = 0
        for r in range(self.size):
            for c in range(self.size):
                if (r, c) not in visited and clue_count < num_clues:
                    region = self._find_region(self.solution, r, c, set())
                    if region:
                        # Reveal one cell from this region
                        reveal_r, reveal_c = self._rng.choice(region)
                        self.grid[reveal_r][reveal_c] = self.solution[reveal_r][reveal_c]
                        clue_count += 1
                        visited.update(region)

        self.initial_grid = [row[:] for row in self.grid]
        self.moves_made = 0
        self.game_started = True

    async def validate_move(self, row: int, col: int, num: int) -> MoveResult:
        """Place a number on the grid.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            num: Number to place (1-9, or 0 to clear)

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
            return MoveResult(success=False, message="Cannot modify initial clue cells.")

        # Clear the cell
        if num == 0:
            self.grid[row][col] = 0
            return MoveResult(success=True, message="Cell cleared.", state_changed=True)

        # Validate number range
        if not (1 <= num <= 9):
            return MoveResult(success=False, message="Invalid number. Use 1-9 or 0 to clear.")

        # Place the number
        self.grid[row][col] = num
        self.moves_made += 1
        return MoveResult(success=True, message="Number placed successfully!", state_changed=True)

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        # Check all cells are filled
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] == 0:
                    return False

        # Check each region
        visited = set()
        for r in range(self.size):
            for c in range(self.size):
                if (r, c) in visited:
                    continue

                region = self._find_region(self.grid, r, c, set())
                if not region:
                    return False

                # Check region size matches the number
                size = len(region)
                number = self.grid[r][c]
                if size != number:
                    return False

                # Check no adjacent region has the same size
                for rr, cc in region:
                    for nr, nc in self._get_adjacent(rr, cc):
                        if (nr, nc) not in region and self.grid[nr][nc] == number:
                            return False

                visited.update(region)

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        # Find an empty cell
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 0:
                    correct_num = self.solution[r][c]
                    hint_data = (r + 1, c + 1, correct_num)
                    hint_message = f"Try placing {correct_num} at row {r + 1}, column {c + 1}"
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
        for c in range(self.size):
            header += f" {c + 1}"
        lines.append(header)
        lines.append("  +" + "--" * self.size)

        # Grid rows
        for r in range(self.size):
            row_str = f"{r + 1:2}|"
            for c in range(self.size):
                cell = self.grid[r][c]
                if cell == 0:
                    row_str += " ."
                else:
                    row_str += f" {cell}"
            lines.append(row_str)

        lines.append("\nLegend: . = empty, 1-9 = numbers forming regions")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Fillomino.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return """FILLOMINO RULES:
- Fill the grid with numbers to form regions
- Each region contains cells with the same number
- The number in each region equals the size (area) of that region
- No two regions of the same size can share an edge
- Some numbers are given as clues"""

    def get_commands(self) -> str:
        """Get the available commands for Fillomino.

        Returns:
            Multi-line string describing available commands
        """
        return """FILLOMINO COMMANDS:
  place <row> <col> <num>  - Place a number (e.g., 'place 1 5 3')
  clear <row> <col>        - Clear a cell (same as 'place <row> <col> 0')
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
        return f"Moves made: {self.moves_made} | Filled: {filled}/{total} | Seed: {self.seed}"
