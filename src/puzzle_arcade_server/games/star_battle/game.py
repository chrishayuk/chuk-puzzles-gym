"""Star Battle puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import StarBattleConfig


class StarBattleGame(PuzzleGame):
    """Star Battle puzzle game.

    Place stars in the grid such that:
    - Each row contains exactly N stars
    - Each column contains exactly N stars
    - Each region contains exactly N stars
    - Stars cannot touch each other (not even diagonally)
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Star Battle game.

        Args:
            difficulty: Game difficulty level (easy=6x6/1star, medium=8x8/2stars, hard=10x10/2stars)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Use pydantic config based on difficulty
        self.config = StarBattleConfig.from_difficulty(self.difficulty)
        self.size = self.config.size
        self.stars_per_row = self.config.stars_per_row

        # Grid: 0 = empty, 1 = star (player-placed)
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Regions: each cell belongs to a region (0 to num_regions-1)
        self.regions = [[0 for _ in range(self.size)] for _ in range(self.size)]

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Star Battle"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return f"Place {self.stars_per_row} star(s) in each row, column, and region without touching"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["placement_limits", "multi_region_constraints", "adjacency_avoidance", "counting"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["resource_distribution", "conflict_avoidance", "quota_management", "spatial_planning"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "large", "constraint_density": "dense"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = stars to place."""
        if not hasattr(self, "solution") or not self.solution:
            return None
        return sum(sum(row) for row in self.solution)

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Star Battle."""
        from ...models import DifficultyLevel

        logic_depth = {
            DifficultyLevel.EASY.value: 3,
            DifficultyLevel.MEDIUM.value: 5,
            DifficultyLevel.HARD.value: 6,
        }.get(self.difficulty.value, 4)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=3.0,
            state_observability=1.0,
            constraint_density=0.6,
        )

    def _get_all_adjacent(self, row: int, col: int) -> list[tuple[int, int]]:
        """Get all adjacent cells including diagonals.

        Args:
            row: Row index
            col: Column index

        Returns:
            List of (row, col) tuples for all adjacent cells
        """
        adjacent = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    adjacent.append((nr, nc))
        return adjacent

    def _generate_regions(self) -> None:
        """Generate regions for the puzzle."""
        # Simple region generation: create rectangular-ish regions
        # Create a simple grid division
        if self.size == 6:
            # 6x6: create 6 regions of 6 cells each
            patterns = [
                [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
                [(0, 2), (0, 3), (1, 2), (1, 3), (2, 2), (2, 3)],
                [(0, 4), (0, 5), (1, 4), (1, 5), (2, 4), (2, 5)],
                [(3, 0), (3, 1), (4, 0), (4, 1), (5, 0), (5, 1)],
                [(3, 2), (3, 3), (4, 2), (4, 3), (5, 2), (5, 3)],
                [(3, 4), (3, 5), (4, 4), (4, 5), (5, 4), (5, 5)],
            ]
            for region_id, cells in enumerate(patterns):
                for r, c in cells:
                    self.regions[r][c] = region_id
        else:
            # For other sizes, use row-based regions
            for r in range(self.size):
                for c in range(self.size):
                    self.regions[r][c] = r

    async def generate_puzzle(self) -> None:
        """Generate a new Star Battle puzzle."""
        # Generate regions
        self._generate_regions()

        # Reset grids
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Try to place stars that satisfy all constraints
        max_attempts = 100
        for _ in range(max_attempts):
            if self._try_place_stars():
                break

        # If failed, create a simple valid solution
        if sum(sum(row) for row in self.solution) < self.size * self.stars_per_row:
            self._create_simple_solution()

        self.moves_made = 0
        self.game_started = True

    def _try_place_stars(self) -> bool:
        """Try to place stars that satisfy all constraints.

        Returns:
            True if successful
        """
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Place stars row by row
        for row in range(self.size):
            stars_placed = 0
            attempts = 0
            max_attempts_per_row = 100

            while stars_placed < self.stars_per_row and attempts < max_attempts_per_row:
                attempts += 1
                col = self._rng.randint(0, self.size - 1)

                # Check if we can place a star here
                if self.solution[row][col] == 1:
                    continue

                # Check column constraint
                col_count = sum(self.solution[r][col] for r in range(self.size))
                if col_count >= self.stars_per_row:
                    continue

                # Check region constraint
                region_id = self.regions[row][col]
                region_count = sum(
                    self.solution[r][c]
                    for r in range(self.size)
                    for c in range(self.size)
                    if self.regions[r][c] == region_id
                )
                if region_count >= self.stars_per_row:
                    continue

                # Check adjacency (no touching stars)
                adjacent = self._get_all_adjacent(row, col)
                if any(self.solution[ar][ac] == 1 for ar, ac in adjacent):
                    continue

                # Place the star
                self.solution[row][col] = 1
                stars_placed += 1

            if stars_placed < self.stars_per_row:
                return False

        return True

    def _create_simple_solution(self) -> None:
        """Create a simple valid solution as fallback."""
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Place stars in a diagonal pattern with spacing
        spacing = max(2, self.size // self.stars_per_row)
        for i in range(self.stars_per_row):
            for row in range(self.size):
                col = (row * spacing + i * (self.size // self.stars_per_row)) % self.size
                if self.solution[row][col] == 0:
                    # Check adjacency
                    adjacent = self._get_all_adjacent(row, col)
                    if not any(self.solution[ar][ac] == 1 for ar, ac in adjacent):
                        self.solution[row][col] = 1

    async def validate_move(self, row: int, col: int, action: str = "place") -> MoveResult:
        """Place or remove a star.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            action: "place" or "remove" (default: "place")

        Returns:
            MoveResult with success status and message
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return MoveResult(success=False, message=f"Invalid coordinates. Use row and column between 1-{self.size}.")

        action = action.lower()

        if action == "remove":
            if self.grid[row][col] != 1:
                return MoveResult(success=False, message="No star to remove at this position.")
            self.grid[row][col] = 0
            self.moves_made += 1
            return MoveResult(success=True, message="Star removed.", state_changed=True)

        elif action == "place":
            if self.grid[row][col] == 1:
                return MoveResult(success=False, message="Star already placed here.")

            # Check if star would touch another star
            adjacent = self._get_all_adjacent(row, col)
            if any(self.grid[ar][ac] == 1 for ar, ac in adjacent):
                return MoveResult(success=False, message="Stars cannot touch each other (not even diagonally).")

            self.grid[row][col] = 1
            self.moves_made += 1
            return MoveResult(success=True, message="Star placed!", state_changed=True)

        else:
            return MoveResult(success=False, message="Invalid action. Use 'place' or 'remove'.")

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        # Check row counts
        for row in range(self.size):
            count = sum(self.grid[row])
            if count != self.stars_per_row:
                return False

        # Check column counts
        for col in range(self.size):
            count = sum(self.grid[row][col] for row in range(self.size))
            if count != self.stars_per_row:
                return False

        # Check region counts
        num_regions = max(max(row) for row in self.regions) + 1
        for region_id in range(num_regions):
            count = sum(
                self.grid[r][c] for r in range(self.size) for c in range(self.size) if self.regions[r][c] == region_id
            )
            if count != self.stars_per_row:
                return False

        # Check no stars touch
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 1:
                    adjacent = self._get_all_adjacent(r, c)
                    if any(self.grid[ar][ac] == 1 for ar, ac in adjacent):
                        return False

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        # Find a star location from solution that hasn't been placed
        for r in range(self.size):
            for c in range(self.size):
                if self.solution[r][c] == 1 and self.grid[r][c] != 1:
                    hint_data = (r + 1, c + 1, "place")
                    hint_message = f"Try placing a star at row {r + 1}, column {c + 1}"
                    return hint_data, hint_message

        # Find incorrectly placed star
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 1 and self.solution[r][c] != 1:
                    hint_data = (r + 1, c + 1, "remove")
                    hint_message = f"Remove the star at row {r + 1}, column {c + 1}"
                    return hint_data, hint_message

        return None

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        Returns:
            String representation of the puzzle grid
        """
        lines = []

        # Header
        header = "   |"
        for c in range(self.size):
            header += f" {c + 1}"
        lines.append(header)
        lines.append("   +" + "--" * self.size)

        # Grid rows
        for r in range(self.size):
            row_str = f" {r + 1} |"
            for c in range(self.size):
                if self.grid[r][c] == 1:
                    row_str += " *"
                else:
                    # Show region boundaries
                    row_str += " ."
            lines.append(row_str)

        lines.append("\nLegend: * = star, . = empty")
        lines.append(f"Goal: Place {self.stars_per_row} star(s) in each row, column, and region")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Star Battle.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return f"""STAR BATTLE RULES:
- Place {self.stars_per_row} star(s) in each row
- Place {self.stars_per_row} star(s) in each column
- Place {self.stars_per_row} star(s) in each region
- Stars cannot touch each other, not even diagonally
- All stars must be placed according to these constraints"""

    def get_commands(self) -> str:
        """Get the available commands for Star Battle.

        Returns:
            Multi-line string describing available commands
        """
        return """STAR BATTLE COMMANDS:
  place <row> <col>    - Place a star (e.g., 'place 2 3')
  remove <row> <col>   - Remove a star (e.g., 'remove 2 3')
  show                 - Display the current grid
  hint                 - Get a hint for the next move
  check                - Check your progress
  solve                - Show the solution (ends game)
  menu                 - Return to game selection
  quit                 - Exit the server"""

    def get_stats(self) -> str:
        """Get current game statistics.

        Returns:
            String with game stats
        """
        placed = sum(sum(row) for row in self.grid)
        required = self.size * self.stars_per_row
        return f"Moves made: {self.moves_made} | Stars placed: {placed}/{required} | Seed: {self.seed}"
