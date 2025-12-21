"""Fillomino puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
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

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Fillomino game.

        Args:
            difficulty: Game difficulty level (easy=6x6, medium=8x8, hard=10x10)
        """
        super().__init__(difficulty, seed, **kwargs)

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

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = empty cells to fill."""
        return sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 0)

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Fillomino."""
        from ...models import DifficultyLevel

        empty = self.optimal_steps or 0
        total = self.size * self.size
        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 4,
            DifficultyLevel.HARD.value: 5,
        }.get(self.difficulty.value, 3)
        branching = 3.0 + (empty / total) * 3
        density = 1.0 - (empty / total) if total > 0 else 0.5
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=round(branching, 1),
            state_observability=1.0,
            constraint_density=round(density, 2),
        )

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

    def _create_fallback_solution(self) -> None:
        """Create a simple valid Fillomino solution.

        Uses a greedy approach: for each empty cell, try to create the largest
        valid region possible (up to size 4), then fill remaining with 1s.
        """
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Process cells in order, trying to create valid regions
        for r in range(self.size):
            for c in range(self.size):
                if self.solution[r][c] != 0:
                    continue

                # Try to create a region of size 2, 3, or 4
                placed = False
                for target_size in [3, 2, 4]:
                    region = self._try_grow_region(r, c, target_size)
                    if region and len(region) == target_size:
                        for rr, cc in region:
                            self.solution[rr][cc] = target_size
                        placed = True
                        break

                if not placed:
                    # Can't form a larger region, use size 1
                    # But check it won't merge with adjacent 1s
                    can_use_one = True
                    for nr, nc in self._get_adjacent(r, c):
                        if self.solution[nr][nc] == 1:
                            can_use_one = False
                            break

                    if can_use_one:
                        self.solution[r][c] = 1
                    else:
                        # Try size 2 with any adjacent empty cell
                        for nr, nc in self._get_adjacent(r, c):
                            if self.solution[nr][nc] == 0:
                                self.solution[r][c] = 2
                                self.solution[nr][nc] = 2
                                placed = True
                                break
                        if not placed:
                            # Last resort
                            self.solution[r][c] = 1

    def _try_grow_region(self, start_r: int, start_c: int, target_size: int) -> list[tuple[int, int]] | None:
        """Try to grow a region of exactly target_size from start position."""
        region = [(start_r, start_c)]

        while len(region) < target_size:
            candidates = []
            for r, c in region:
                for nr, nc in self._get_adjacent(r, c):
                    if self.solution[nr][nc] == 0 and (nr, nc) not in region:
                        # Check this wouldn't create adjacency with same-size region
                        test_region = region + [(nr, nc)]
                        valid = True
                        for tr, tc in test_region:
                            for ar, ac in self._get_adjacent(tr, tc):
                                if (ar, ac) not in test_region and self.solution[ar][ac] == target_size:
                                    valid = False
                                    break
                            if not valid:
                                break
                        if valid:
                            candidates.append((nr, nc))

            if not candidates:
                return None

            # Pick the first candidate
            region.append(candidates[0])

        return region

    def _is_valid_region_placement(self, grid: list[list[int]], region: list[tuple[int, int]], size: int) -> bool:
        """Check if placing a region with given size would be valid.

        A region is valid if no adjacent cell outside the region has the same number.
        """
        for r, c in region:
            for nr, nc in self._get_adjacent(r, c):
                if (nr, nc) not in region and grid[nr][nc] == size:
                    return False
        return True

    async def generate_puzzle(self) -> None:
        """Generate a new Fillomino puzzle with valid solution."""
        max_attempts = 50

        for _attempt in range(max_attempts):
            self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

            # Fill the grid with regions
            success = True
            for _ in range(self.size * self.size):
                # Find empty cells
                empty_cells = [(r, c) for r in range(self.size) for c in range(self.size) if self.solution[r][c] == 0]
                if not empty_cells:
                    break

                # Pick a random empty cell
                r, c = self._rng.choice(empty_cells)

                # Try different region sizes, starting from larger
                placed = False
                for target_size in self._rng.sample(range(1, 6), min(5, len(empty_cells))):
                    region = [(r, c)]

                    # Grow the region
                    temp_solution = [row[:] for row in self.solution]
                    temp_solution[r][c] = target_size

                    while len(region) < target_size:
                        # Find valid candidates
                        candidates = []
                        for rr, cc in region:
                            for nr, nc in self._get_adjacent(rr, cc):
                                if temp_solution[nr][nc] == 0 and (nr, nc) not in region:
                                    # Check if adding this cell would create adjacent same-size regions
                                    test_region = region + [(nr, nc)]
                                    if self._is_valid_region_placement(temp_solution, test_region, target_size):
                                        candidates.append((nr, nc))

                        if not candidates:
                            break

                        nr, nc = self._rng.choice(candidates)
                        region.append((nr, nc))
                        temp_solution[nr][nc] = target_size

                    # Check if we achieved the target size and the region is valid
                    if len(region) == target_size and self._is_valid_region_placement(
                        temp_solution, region, target_size
                    ):
                        # Apply the region
                        for rr, cc in region:
                            self.solution[rr][cc] = target_size
                        placed = True
                        break

                if not placed:
                    # Try size 1 as fallback
                    if self._is_valid_region_placement(self.solution, [(r, c)], 1):
                        self.solution[r][c] = 1
                    else:
                        # Can't place anything valid here
                        success = False
                        break

            if success:
                # Verify the solution is complete and valid
                if self._verify_solution():
                    break

        # If no valid solution found, create a simple valid fallback
        if not self._verify_solution():
            self._create_fallback_solution()

        # Create the puzzle by revealing some numbers
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        num_clues = self.config.num_clues

        # Reveal one number from each region
        visited: set[tuple[int, int]] = set()
        clue_count = 0
        for r in range(self.size):
            for c in range(self.size):
                if (r, c) not in visited and clue_count < num_clues:
                    region = self._find_region(self.solution, r, c, set())
                    if region:
                        reveal_r, reveal_c = self._rng.choice(region)
                        self.grid[reveal_r][reveal_c] = self.solution[reveal_r][reveal_c]
                        clue_count += 1
                        visited.update(region)

        self.initial_grid = [row[:] for row in self.grid]
        self.moves_made = 0
        self.game_started = True

    def _verify_solution(self) -> bool:
        """Verify the solution is complete and valid."""
        # Check all cells are filled
        for r in range(self.size):
            for c in range(self.size):
                if self.solution[r][c] == 0:
                    return False

        # Check each region
        visited: set[tuple[int, int]] = set()
        for r in range(self.size):
            for c in range(self.size):
                if (r, c) in visited:
                    continue

                region = self._find_region(self.solution, r, c, set())
                if not region:
                    return False

                # Check region size matches the number
                size = len(region)
                number = self.solution[r][c]
                if size != number:
                    return False

                # Check no adjacent region has the same size
                if not self._is_valid_region_placement(self.solution, region, number):
                    return False

                visited.update(region)

        return True

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
