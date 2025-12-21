"""Tents and Trees puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import TentsConfig


class TentsGame(PuzzleGame):
    """Tents and Trees puzzle game.

    Place tents next to trees such that:
    - Each tree has exactly one tent adjacent to it (horizontally or vertically)
    - Each tent is adjacent to exactly one tree
    - Tents cannot touch each other (not even diagonally)
    - Row and column counts show how many tents are in each row/column
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Tents game.

        Args:
            difficulty: Game difficulty level (easy=6x6, medium=8x8, hard=10x10)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Use pydantic config based on difficulty
        self.config = TentsConfig.from_difficulty(self.difficulty)
        self.size = self.config.size

        # Grid: 0 = empty, 1 = tree, 2 = tent (player-placed)
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Trees are fixed at puzzle generation
        self.trees = [[False for _ in range(self.size)] for _ in range(self.size)]

        # Row and column counts
        self.row_counts: list[int] = []
        self.col_counts: list[int] = []

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Tents and Trees"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Match tents to trees while avoiding adjacency conflicts"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["bipartite_matching", "adjacency_avoidance", "counting", "one_to_one_correspondence"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["resource_pairing", "spatial_allocation", "conflict_avoidance", "matching_with_constraints"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "medium", "constraint_density": "moderate"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = tents to place (equals trees)."""
        if not hasattr(self, "solution") or not self.solution:
            return None
        # Solution uses: 0=empty, 1=tent, 2=tree. Count tents only.
        return sum(1 for row in self.solution for cell in row if cell == 1)

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Tents and Trees."""
        from ...models import DifficultyLevel

        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 4,
            DifficultyLevel.HARD.value: 5,
        }.get(self.difficulty.value, 3)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=4.0,  # 4 adjacent positions
            state_observability=1.0,
            constraint_density=0.5,
        )

    def _get_adjacent(self, row: int, col: int) -> list[tuple[int, int]]:
        """Get orthogonally adjacent cells (no diagonals).

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

    async def generate_puzzle(self) -> None:
        """Generate a new Tents and Trees puzzle."""
        # Reset grids
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.trees = [[False for _ in range(self.size)] for _ in range(self.size)]

        # Place trees and tents
        max_attempts = 100
        for _ in range(max_attempts):
            if self._try_generate():
                break

        # Calculate row and column counts from solution
        self.row_counts = [sum(1 for c in range(self.size) if self.solution[r][c] == 2) for r in range(self.size)]
        self.col_counts = [sum(1 for r in range(self.size) if self.solution[r][c] == 2) for c in range(self.size)]

        # Copy trees to player grid
        for r in range(self.size):
            for c in range(self.size):
                if self.trees[r][c]:
                    self.grid[r][c] = 1

        self.moves_made = 0
        self.game_started = True

    def _try_generate(self) -> bool:
        """Try to generate a valid puzzle.

        Returns:
            True if generation succeeded
        """
        # Reset
        self.trees = [[False for _ in range(self.size)] for _ in range(self.size)]
        tent_solution = [[False for _ in range(self.size)] for _ in range(self.size)]

        # Number of tree-tent pairs based on difficulty
        num_pairs = self.config.num_trees

        # Place tree-tent pairs
        placed_pairs = 0
        attempts = 0
        max_attempts = 500

        while placed_pairs < num_pairs and attempts < max_attempts:
            attempts += 1

            # Pick random position for tree
            tree_r = self._rng.randint(0, self.size - 1)
            tree_c = self._rng.randint(0, self.size - 1)

            # Skip if already has tree or tent
            if self.trees[tree_r][tree_c] or tent_solution[tree_r][tree_c]:
                continue

            # Skip if this position is adjacent to an existing tree or tent
            # (would create ambiguous tree-tent associations)
            tree_adjacent = self._get_adjacent(tree_r, tree_c)
            if any(self.trees[ar][ac] for ar, ac in tree_adjacent):
                continue
            if any(tent_solution[ar][ac] for ar, ac in tree_adjacent):
                continue

            # Find valid tent positions (adjacent, not touching other tents)
            valid_tent_positions = []

            for tent_r, tent_c in tree_adjacent:
                # Check if position is empty
                if self.trees[tent_r][tent_c] or tent_solution[tent_r][tent_c]:
                    continue

                # Check if tent would touch another tent (including diagonally)
                all_adj = self._get_all_adjacent(tent_r, tent_c)
                if any(tent_solution[ar][ac] for ar, ac in all_adj):
                    continue

                # Check if this tent position would be adjacent to another tree
                # (would create ambiguous tent-tree associations)
                tent_adj = self._get_adjacent(tent_r, tent_c)
                other_trees = sum(1 for ar, ac in tent_adj if self.trees[ar][ac])
                if other_trees > 0:
                    continue

                valid_tent_positions.append((tent_r, tent_c))

            if valid_tent_positions:
                # Place tree and tent
                tent_r, tent_c = self._rng.choice(valid_tent_positions)
                self.trees[tree_r][tree_c] = True
                tent_solution[tent_r][tent_c] = True
                placed_pairs += 1

        # Transfer to solution grid
        for r in range(self.size):
            for c in range(self.size):
                if self.trees[r][c]:
                    self.solution[r][c] = 1
                elif tent_solution[r][c]:
                    self.solution[r][c] = 2
                else:
                    self.solution[r][c] = 0

        return placed_pairs >= num_pairs

    async def validate_move(self, row: int, col: int, action: str = "place") -> MoveResult:
        """Place or remove a tent.

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

        # Check if it's a tree
        if self.trees[row][col]:
            return MoveResult(success=False, message="Cannot place tent on a tree.")

        action = action.lower()

        if action == "remove":
            if self.grid[row][col] != 2:
                return MoveResult(success=False, message="No tent to remove at this position.")
            self.grid[row][col] = 0
            self.moves_made += 1
            return MoveResult(success=True, message="Tent removed.", state_changed=True)

        elif action == "place":
            if self.grid[row][col] == 2:
                return MoveResult(success=False, message="Tent already placed here.")

            # Check if tent would touch another tent (including diagonally)
            all_adj = self._get_all_adjacent(row, col)
            if any(self.grid[ar][ac] == 2 for ar, ac in all_adj):
                return MoveResult(success=False, message="Tents cannot touch each other (not even diagonally).")

            self.grid[row][col] = 2
            self.moves_made += 1
            return MoveResult(success=True, message="Tent placed!", state_changed=True)

        else:
            return MoveResult(success=False, message="Invalid action. Use 'place' or 'remove'.")

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        # Check row and column counts
        for r in range(self.size):
            count = sum(1 for c in range(self.size) if self.grid[r][c] == 2)
            if count != self.row_counts[r]:
                return False

        for c in range(self.size):
            count = sum(1 for r in range(self.size) if self.grid[r][c] == 2)
            if count != self.col_counts[c]:
                return False

        # Check each tree has exactly one adjacent tent
        for r in range(self.size):
            for c in range(self.size):
                if self.trees[r][c]:
                    adjacent = self._get_adjacent(r, c)
                    tent_count = sum(1 for ar, ac in adjacent if self.grid[ar][ac] == 2)
                    if tent_count != 1:
                        return False

        # Check each tent has exactly one adjacent tree
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 2:
                    adjacent = self._get_adjacent(r, c)
                    tree_count = sum(1 for ar, ac in adjacent if self.trees[ar][ac])
                    if tree_count != 1:
                        return False

        # Check no tents touch
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 2:
                    all_adj = self._get_all_adjacent(r, c)
                    if any(self.grid[ar][ac] == 2 for ar, ac in all_adj):
                        return False

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        # Find a tent location from solution that hasn't been placed
        for r in range(self.size):
            for c in range(self.size):
                if self.solution[r][c] == 2 and self.grid[r][c] != 2:
                    hint_data = (r + 1, c + 1, "place")
                    hint_message = f"Try placing a tent at row {r + 1}, column {c + 1}"
                    return hint_data, hint_message

        # Find incorrectly placed tent
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 2 and self.solution[r][c] != 2:
                    hint_data = (r + 1, c + 1, "remove")
                    hint_message = f"Remove the tent at row {r + 1}, column {c + 1}"
                    return hint_data, hint_message

        return None

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        Returns:
            String representation of the puzzle grid
        """
        lines = []

        # Header with column counts
        header = "   |"
        for c in range(self.size):
            header += f" {self.col_counts[c]}"
        lines.append(header)
        lines.append("   +" + "--" * self.size)

        # Grid rows with row counts
        for r in range(self.size):
            row_str = f" {self.row_counts[r]} |"
            for c in range(self.size):
                if self.trees[r][c]:
                    row_str += " T"
                elif self.grid[r][c] == 2:
                    row_str += " A"  # A for tent (like a triangle)
                else:
                    row_str += " ."
            lines.append(row_str)

        lines.append("\nLegend: T = tree, A = tent (player placed), . = empty")
        lines.append("Numbers on edges = required tents in that row/column")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Tents and Trees.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return """TENTS AND TREES RULES:
- Place tents in empty cells
- Each tree must have exactly one tent adjacent to it (horizontally or vertically)
- Each tent must be adjacent to exactly one tree
- Tents cannot touch each other, not even diagonally
- Row and column numbers show how many tents are in that row/column"""

    def get_commands(self) -> str:
        """Get the available commands for Tents and Trees.

        Returns:
            Multi-line string describing available commands
        """
        return """TENTS AND TREES COMMANDS:
  place <row> <col>    - Place a tent (e.g., 'place 2 3')
  remove <row> <col>   - Remove a tent (e.g., 'remove 2 3')
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
        placed = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 2)
        required = sum(self.row_counts)
        return f"Moves made: {self.moves_made} | Tents placed: {placed}/{required} | Seed: {self.seed}"
