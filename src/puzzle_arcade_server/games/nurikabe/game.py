"""Nurikabe puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import NurikabeConfig
from .enums import NurikabeColor


class NurikabeGame(PuzzleGame):
    """Nurikabe puzzle game.

    Create islands (white cells) and sea (black cells) where:
    - Each numbered cell is part of a white island of that size
    - All black cells are connected
    - No 2×2 blocks of black cells
    - All white cells in an island are connected
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Nurikabe game.

        Args:
            difficulty: Game difficulty level (easy/medium/hard)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Load config from difficulty
        self.config = NurikabeConfig.from_difficulty(self.difficulty)
        self.size = self.config.size
        self.num_islands = self.config.num_islands

        # Grid: 0 = unknown, 1 = white (island), 2 = black (sea)
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Clues: (row, col, size) - this cell is part of an island of this size
        self.clues: list[tuple[int, int, int]] = []

        # Islands: list of ((row, col), size) tuples
        self.islands: list[tuple[tuple[int, int], int]] = []

        # Given cells: set of (row, col) positions that show clue numbers
        self.given_cells: set[tuple[int, int]] = set()

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Nurikabe"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Create islands and sea - test connectivity reasoning"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["connectivity", "partition", "all_different_regions", "no_pools"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["network_segmentation", "zone_planning", "cluster_analysis"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "large", "constraint_density": "dense"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = all cells to mark (excluding clue cells)."""
        if not hasattr(self, "solution") or not self.solution:
            return None
        # Solution has 1=island, 2=sea. Count all cells except we need to
        # subtract clue cells which are already given
        # Clues are stored separately, so count from solution
        total_cells = self.size * self.size
        # Count clue cells (they're integers > 0 in the clues dict or initial grid)
        if hasattr(self, "clues") and self.clues:
            num_clues = len(self.clues)
        else:
            num_clues = 0
        return total_cells - num_clues

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Nurikabe."""
        from ...models import DifficultyLevel

        logic_depth = {
            DifficultyLevel.EASY.value: 3,
            DifficultyLevel.MEDIUM.value: 5,
            DifficultyLevel.HARD.value: 6,
        }.get(self.difficulty.value, 4)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=2.0,  # Island or sea
            state_observability=1.0,
            constraint_density=0.6,
        )

    async def generate_puzzle(self) -> None:
        """Generate a new Nurikabe puzzle with sophisticated algorithm."""
        max_attempts = 100

        for _attempt in range(max_attempts):
            # Start with all black cells (sea)
            self.solution = [[2 for _ in range(self.size)] for _ in range(self.size)]

            self.clues = []
            self.islands = []
            self.given_cells = set()

            # Step 1: Place islands strategically
            placed_islands = self._place_separated_islands_v2()

            # Step 2: Mark island cells as white in solution
            for island_cells in placed_islands:
                for r, c in island_cells:
                    self.solution[r][c] = 1

            # Step 3: Fix any 2x2 black blocks iteratively
            self._fix_2x2_blocks()

            # Step 4: Validate the solution
            if self._validate_solution():
                break

        # Initialize player grid
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Place clue numbers
        for row, col, _size in self.clues:
            self.grid[row][col] = 1  # Mark as white

        self.moves_made = 0
        self.game_started = True

    def _place_separated_islands_v2(self) -> list[list[tuple[int, int]]]:
        """Place islands at well-separated positions (simple version)."""
        placed_islands = []

        # Define island sizes
        island_sizes = []
        for i in range(self.num_islands):
            if i == 0:
                island_sizes.append(3)  # First island is size 3
            else:
                island_sizes.append(2)  # Others are size 2

        # Use simple corner/center positions with good spacing
        positions = [
            (0, 0),  # Top-left
            (0, self.size - 1),  # Top-right
            (self.size - 1, 0),  # Bottom-left
            (self.size - 1, self.size - 1),  # Bottom-right
            (self.size // 2, self.size // 2),  # Center
        ]

        for i, size in enumerate(island_sizes):
            if i >= len(positions):
                break

            start_row, start_col = positions[i]
            island_cells = [(start_row, start_col)]

            # Add adjacent cells to form island
            neighbors = [
                (start_row - 1, start_col),
                (start_row + 1, start_col),
                (start_row, start_col - 1),
                (start_row, start_col + 1),
            ]

            for nr, nc in neighbors:
                if len(island_cells) >= size:
                    break
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    island_cells.append((nr, nc))

            # Trim to exact size
            island_cells = island_cells[:size]

            if len(island_cells) >= 2:  # Only add if we have at least 2 cells
                placed_islands.append(island_cells)
                clue_cell = island_cells[0]
                self.clues.append((clue_cell[0], clue_cell[1], len(island_cells)))
                self.islands.append((clue_cell, len(island_cells)))
                self.given_cells.add(clue_cell)

        return placed_islands

    def _fix_2x2_blocks(self) -> None:
        """Iteratively fix any 2x2 black blocks."""
        # Track which cells belong to which island and the max sizes
        island_map = {}  # (row, col) -> island_id
        island_sizes = {}  # island_id -> (current_size, max_size)

        for island_id, (clue_pos, max_size) in enumerate(self.islands):
            clue_r, clue_c = clue_pos
            island = self._get_island_from_cell_in_solution(clue_r, clue_c)
            for r, c in island:
                island_map[(r, c)] = island_id
            island_sizes[island_id] = (len(island), max_size)

        max_iterations = 100
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            found_2x2 = False

            # Scan for 2x2 black blocks
            for row in range(self.size - 1):
                for col in range(self.size - 1):
                    if (
                        self.solution[row][col] == 2
                        and self.solution[row][col + 1] == 2
                        and self.solution[row + 1][col] == 2
                        and self.solution[row + 1][col + 1] == 2
                    ):
                        found_2x2 = True

                        # Try to convert one cell to white without merging islands
                        # Prefer cells that are not part of given islands
                        candidates = [(row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1)]

                        converted = False
                        for r, c in candidates:
                            if (r, c) not in self.given_cells:
                                # Check neighbor islands
                                neighbor_islands = set()
                                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                    nr, nc = r + dr, c + dc
                                    if 0 <= nr < self.size and 0 <= nc < self.size:
                                        if self.solution[nr][nc] == 1 and (nr, nc) in island_map:
                                            neighbor_islands.add(island_map[(nr, nc)])

                                # Only convert if it won't merge different islands
                                # AND won't make an island too large
                                # AND won't disconnect the black sea
                                can_add = True
                                if len(neighbor_islands) == 1:
                                    island_id = list(neighbor_islands)[0]
                                    current_size, max_size = island_sizes[island_id]
                                    if current_size >= max_size:
                                        can_add = False  # Island is already full
                                elif len(neighbor_islands) > 1:
                                    can_add = False  # Would merge islands

                                if can_add:
                                    # Temporarily convert and check black connectivity
                                    self.solution[r][c] = 1
                                    temp_grid = self.grid
                                    self.grid = self.solution
                                    black_connected = self._check_black_connected()
                                    self.grid = temp_grid

                                    if black_connected:
                                        # Update island map if this extends an existing island
                                        if len(neighbor_islands) == 1:
                                            island_id = list(neighbor_islands)[0]
                                            island_map[(r, c)] = island_id
                                            current_size, max_size = island_sizes[island_id]
                                            island_sizes[island_id] = (current_size + 1, max_size)
                                        converted = True
                                        break
                                    else:
                                        # Revert the change
                                        self.solution[r][c] = 2

                        # If we couldn't convert safely, this generation attempt failed
                        # The outer loop will retry with a new random arrangement
                        if not converted:
                            # Mark this as invalid by returning early
                            # The validation will fail and trigger a retry
                            pass

            if not found_2x2:
                break

    def _get_island_from_cell_in_solution(self, row: int, col: int) -> set[tuple[int, int]]:
        """Get all white cells connected to the given cell in solution."""
        if self.solution[row][col] != 1:
            return set()

        island = set()
        queue = [(row, col)]
        island.add((row, col))

        while queue:
            r, c = queue.pop(0)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if (nr, nc) not in island and self.solution[nr][nc] == 1:
                        island.add((nr, nc))
                        queue.append((nr, nc))

        return island

    def _validate_solution(self) -> bool:
        """Validate that the generated solution meets all Nurikabe rules."""
        # Temporarily use solution as grid for validation
        temp_grid = self.grid
        self.grid = self.solution

        # Check that each clue cell has an island of the correct size
        for clue_row, clue_col, expected_size in self.clues:
            island_cells = self._get_island_from_cell(clue_row, clue_col)
            if len(island_cells) != expected_size:
                self.grid = temp_grid
                return False

        # Check that black cells are connected
        if not self._check_black_connected():
            self.grid = temp_grid
            return False

        # Check no 2x2 black blocks
        if self._has_2x2_black():
            self.grid = temp_grid
            return False

        self.grid = temp_grid
        return True

    async def validate_move(self, row: int, col: int, color: str) -> MoveResult:
        """Mark a cell as black or white.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            color: 'white' or 'black'

        Returns:
            MoveResult with success status and message
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return MoveResult(success=False, message=f"Invalid coordinates. Use row and column between 1-{self.size}.")

        # Validate color with enum
        try:
            color_enum = NurikabeColor(color.lower())
        except ValueError:
            return MoveResult(success=False, message="Invalid color. Use 'white', 'black', or 'clear'.")

        # Check if this is a clue cell
        for clue_row, clue_col, _size in self.clues:
            if row == clue_row and col == clue_col:
                return MoveResult(success=False, message="Cannot modify clue cells.")

        if color_enum in (NurikabeColor.WHITE, NurikabeColor.W):
            self.grid[row][col] = 1
            self.moves_made += 1
            return MoveResult(success=True, message="Cell marked as white (island).", state_changed=True)
        elif color_enum in (NurikabeColor.BLACK, NurikabeColor.B):
            self.grid[row][col] = 2
            self.moves_made += 1
            return MoveResult(success=True, message="Cell marked as black (sea).", state_changed=True)
        elif color_enum in (NurikabeColor.CLEAR, NurikabeColor.C):
            # Don't clear clue cells
            for clue_row, clue_col, _size in self.clues:
                if row == clue_row and col == clue_col:
                    return MoveResult(success=False, message="Cannot clear clue cells.")
            # Check if cell is already unmarked
            if self.grid[row][col] == 0:
                return MoveResult(success=False, message="Cell is already unmarked.")
            self.grid[row][col] = 0
            self.moves_made += 1
            return MoveResult(success=True, message="Cell cleared.", state_changed=True)

        return MoveResult(success=False, message="Invalid color. Use 'white', 'black', or 'clear'.")

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

    async def get_hint(self) -> tuple[Any, str] | None:
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

        lines.append("Nurikabe")
        lines.append(f"Islands: {len(self.islands)}")
        lines.append("")

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
        marked = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] != 0)
        total = self.size * self.size

        return f"Moves made: {self.moves_made} | Marked: {marked}/{total} cells | Islands: {len(self.islands)} | Seed: {self.seed}"
