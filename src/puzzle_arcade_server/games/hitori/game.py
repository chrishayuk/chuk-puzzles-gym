"""Hitori puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame


class HitoriGame(PuzzleGame):
    """Hitori puzzle game.

    Shade some cells so that:
    - No number appears more than once in any row or column
    - Shaded cells do not touch horizontally or vertically
    - All unshaded cells form a single connected region
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Hitori game.

        Args:
            difficulty: Game difficulty level (easy, medium, hard)
        """
        super().__init__(difficulty, seed, **kwargs)

        from ...models import DifficultyLevel

        # Set grid size based on difficulty
        self.size = {DifficultyLevel.EASY.value: 5, DifficultyLevel.MEDIUM.value: 7, DifficultyLevel.HARD.value: 9}.get(
            self.difficulty.value, 5
        )

        # Grid stores the numbers
        self.grid: list[list[int]] = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Solution stores which cells should be shaded (True = shaded)
        self.solution: list[list[bool]] = [[False for _ in range(self.size)] for _ in range(self.size)]

        # Player's shading
        self.shaded: list[list[bool]] = [[False for _ in range(self.size)] for _ in range(self.size)]

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Hitori"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Shade cells to eliminate duplicates - no adjacent shaded cells"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["all_different", "connectivity", "adjacency", "partition", "elimination"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["conflict_resolution", "network_connectivity", "resource_elimination", "deduplication"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "medium", "constraint_density": "moderate"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = cells to shade."""
        if not hasattr(self, "solution") or not self.solution:
            return None
        return sum(1 for r in range(self.size) for c in range(self.size) if self.solution[r][c])

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Hitori."""
        from ...models import DifficultyLevel

        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 4,
            DifficultyLevel.HARD.value: 5,
        }.get(self.difficulty.value, 3)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=2.0,  # Shade or not
            state_observability=1.0,
            constraint_density=0.5,
        )

    def _is_connected(self, grid: list[list[bool]]) -> bool:
        """Check if all unshaded cells are connected.

        Args:
            grid: Boolean grid where True = shaded, False = unshaded

        Returns:
            True if all unshaded cells are connected
        """
        # Find first unshaded cell
        start = None
        for r in range(self.size):
            for c in range(self.size):
                if not grid[r][c]:
                    start = (r, c)
                    break
            if start:
                break

        if not start:
            return False  # All cells are shaded

        # BFS to find all connected unshaded cells
        visited = set()
        queue = [start]
        visited.add(start)

        while queue:
            r, c = queue.pop(0)
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if not grid[nr][nc] and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))

        # Count total unshaded cells
        unshaded_count = sum(1 for r in range(self.size) for c in range(self.size) if not grid[r][c])

        return len(visited) == unshaded_count

    def _has_adjacent_shaded(self, row: int, col: int, grid: list[list[bool]]) -> bool:
        """Check if a cell has any adjacent shaded cells.

        Args:
            row: Row index
            col: Column index
            grid: Boolean grid where True = shaded

        Returns:
            True if there's an adjacent shaded cell
        """
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                if grid[nr][nc]:
                    return True
        return False

    async def generate_puzzle(self) -> None:
        """Generate a new Hitori puzzle with retry logic."""
        max_attempts = 50

        for _attempt in range(max_attempts):
            # Step 1: Start with a valid Latin square
            for r in range(self.size):
                for c in range(self.size):
                    self.grid[r][c] = ((r + c) % self.size) + 1

            # Step 2: Randomly swap some rows and columns to create variety
            for _ in range(self.size * 2):
                if self._rng.random() < 0.5:
                    # Swap two rows
                    r1, r2 = self._rng.randint(0, self.size - 1), self._rng.randint(0, self.size - 1)
                    self.grid[r1], self.grid[r2] = self.grid[r2], self.grid[r1]
                else:
                    # Swap two columns
                    c1, c2 = self._rng.randint(0, self.size - 1), self._rng.randint(0, self.size - 1)
                    for r in range(self.size):
                        self.grid[r][c1], self.grid[r][c2] = self.grid[r][c2], self.grid[r][c1]

            # Step 3: Create duplicates strategically
            from ...models import DifficultyLevel

            num_duplicates = {
                DifficultyLevel.EASY.value: self.size,
                DifficultyLevel.MEDIUM.value: self.size * 2,
                DifficultyLevel.HARD.value: self.size * 3,
            }.get(self.difficulty.value, self.size)

            # Track which cells we've modified to avoid over-duplication
            modified_cells = set()

            for _ in range(num_duplicates):
                attempts = 0
                while attempts < 20:
                    r = self._rng.randint(0, self.size - 1)
                    c = self._rng.randint(0, self.size - 1)

                    if (r, c) not in modified_cells:
                        # Find a duplicate value in the same row or column
                        if self._rng.random() < 0.5:
                            # Duplicate in row
                            target_c = self._rng.randint(0, self.size - 1)
                            if target_c != c:
                                self.grid[r][c] = self.grid[r][target_c]
                                modified_cells.add((r, c))
                                break
                        else:
                            # Duplicate in column
                            target_r = self._rng.randint(0, self.size - 1)
                            if target_r != r:
                                self.grid[r][c] = self.grid[target_r][c]
                                modified_cells.add((r, c))
                                break

                    attempts += 1

            # Step 4: Generate solution
            self._generate_solution()

            # Step 5: Validate solution
            if self._validate_solution():
                self.game_started = True
                return

        # Fallback: Generate a simple, always-valid puzzle
        # Reset to a simple latin square with minimal duplicates
        for r in range(self.size):
            for c in range(self.size):
                self.grid[r][c] = ((r + c) % self.size) + 1
                self.solution[r][c] = False

        # Add exactly one duplicate per row that can be safely shaded
        for r in range(self.size):
            # Find a cell where shading won't break connectivity
            # (never shade edge cells or adjacent to already shaded)
            c = r % (self.size - 2) + 1  # Stay away from edges
            if not self._has_adjacent_shaded(r, c, self.solution):
                # Copy a value to create a duplicate
                self.grid[r][c] = self.grid[r][(c + 1) % self.size]
                self.solution[r][c] = True

        # Verify fallback is valid
        if not self._validate_solution():
            # Last resort: no duplicates at all (trivial puzzle)
            for r in range(self.size):
                for c in range(self.size):
                    self.grid[r][c] = ((r + c) % self.size) + 1
                    self.solution[r][c] = False

        self.game_started = True

    def _validate_solution(self) -> bool:
        """Validate that the generated solution is solvable."""
        # Check that solution doesn't have adjacent shaded cells
        for r in range(self.size):
            for c in range(self.size):
                if self.solution[r][c] and self._has_adjacent_shaded(r, c, self.solution):
                    return False

        # Check that unshaded cells are connected
        if not self._is_connected(self.solution):
            return False

        # Check no duplicates in rows (among unshaded cells)
        for r in range(self.size):
            seen = set()
            for c in range(self.size):
                if not self.solution[r][c]:
                    val = self.grid[r][c]
                    if val in seen:
                        return False
                    seen.add(val)

        # Check no duplicates in columns (among unshaded cells)
        for c in range(self.size):
            seen = set()
            for r in range(self.size):
                if not self.solution[r][c]:
                    val = self.grid[r][c]
                    if val in seen:
                        return False
                    seen.add(val)

        return True

    def _generate_solution(self) -> None:
        """Generate a valid solution for the current grid."""
        # Simple greedy approach: shade cells to eliminate duplicates
        # while maintaining constraints

        # For each row, find duplicates
        for r in range(self.size):
            row_seen: dict[int, int] = {}
            for c in range(self.size):
                val = self.grid[r][c]
                if val in row_seen:
                    # We have a duplicate - shade one of them
                    # Choose to shade the current cell if it doesn't violate constraints
                    if not self._has_adjacent_shaded(r, c, self.solution):
                        self.solution[r][c] = True
                    else:
                        # Shade the first occurrence instead
                        prev_c = row_seen[val]
                        if not self._has_adjacent_shaded(r, prev_c, self.solution):
                            self.solution[r][prev_c] = True
                else:
                    row_seen[val] = c

        # For each column, find remaining duplicates
        for c in range(self.size):
            col_seen: dict[int, int] = {}
            for r in range(self.size):
                if self.solution[r][c]:
                    continue  # Already shaded

                val = self.grid[r][c]
                if val in col_seen:
                    # Duplicate - shade if possible
                    if not self._has_adjacent_shaded(r, c, self.solution):
                        self.solution[r][c] = True
                    else:
                        prev_r = col_seen[val]
                        if not self.solution[prev_r][c] and not self._has_adjacent_shaded(prev_r, c, self.solution):
                            self.solution[prev_r][c] = True
                else:
                    col_seen[val] = r

    async def validate_move(self, *args: Any, **kwargs: Any) -> MoveResult:
        """Validate a shading move.

        Args:
            args[0]: Row (1-indexed)
            args[1]: Column (1-indexed)
            args[2]: Action - 'shade', 'unshade', or 's'/'u'

        Returns:
            MoveResult containing success status and message
        """
        if len(args) < 3:
            return MoveResult(success=False, message="Usage: place <row> <col> <shade|unshade>")

        try:
            row, col = int(args[0]) - 1, int(args[1]) - 1
            action = str(args[2]).lower()
        except (ValueError, IndexError):
            return MoveResult(success=False, message="Invalid coordinates or action")

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return MoveResult(success=False, message=f"Coordinates must be between 1 and {self.size}")

        # Process action
        if action in ("shade", "s"):
            # Check if shading would create adjacent shaded cells
            if self._has_adjacent_shaded(row, col, self.shaded):
                return MoveResult(success=False, message="Cannot shade - would create adjacent shaded cells")

            self.shaded[row][col] = True
            self.moves_made += 1
            return MoveResult(success=True, message="Cell shaded")

        elif action in ("unshade", "u", "clear"):
            self.shaded[row][col] = False
            self.moves_made += 1
            return MoveResult(success=True, message="Cell unshaded")

        else:
            return MoveResult(success=False, message="Action must be 'shade' or 'unshade'")

    def is_complete(self) -> bool:
        """Check if the puzzle is completely and correctly solved."""
        # Check no duplicates in rows
        for r in range(self.size):
            seen = set()
            for c in range(self.size):
                if not self.shaded[r][c]:
                    val = self.grid[r][c]
                    if val in seen:
                        return False
                    seen.add(val)

        # Check no duplicates in columns
        for c in range(self.size):
            seen = set()
            for r in range(self.size):
                if not self.shaded[r][c]:
                    val = self.grid[r][c]
                    if val in seen:
                        return False
                    seen.add(val)

        # Check no adjacent shaded cells
        for r in range(self.size):
            for c in range(self.size):
                if self.shaded[r][c] and self._has_adjacent_shaded(r, c, self.shaded):
                    return False

        # Check all unshaded cells are connected
        if not self._is_connected(self.shaded):
            return False

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move."""
        # Find a cell that should be shaded but isn't, or vice versa
        for r in range(self.size):
            for c in range(self.size):
                if self.solution[r][c] and not self.shaded[r][c]:
                    return ((r + 1, c + 1, "shade"), f"Try shading cell at row {r + 1}, column {c + 1}")
                elif not self.solution[r][c] and self.shaded[r][c]:
                    return ((r + 1, c + 1, "unshade"), f"Try unshading cell at row {r + 1}, column {c + 1}")

        return None

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art."""
        lines = []

        # Header
        header = "  |"
        for c in range(self.size):
            header += f" {c + 1}"
        lines.append(header)
        lines.append("  +" + "--" * self.size)

        # Grid rows
        for r in range(self.size):
            row = f"{r + 1:2d}|"
            for c in range(self.size):
                if self.shaded[r][c]:
                    row += f"#{self.grid[r][c]}"
                else:
                    row += f" {self.grid[r][c]}"
            lines.append(row)

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for this puzzle type."""
        return """HITORI RULES:
- Shade some cells so that:
  * No number appears more than once in any row
  * No number appears more than once in any column
  * Shaded cells do not touch horizontally or vertically
  * All unshaded cells form a single connected region
- Shaded cells are shown with # prefix"""

    def get_commands(self) -> str:
        """Get the available commands for this puzzle type."""
        return """HITORI COMMANDS:
  place <row> <col> shade   - Shade a cell
  place <row> <col> unshade - Unshade a cell
  Example: place 1 3 shade
  hint   - Get a hint for the next move
  check  - Check if puzzle is complete
  solve  - Show the solution
  menu   - Return to main menu
  quit   - Exit the game"""
