"""Lights Out puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import LightsOutConfig


class LightsOutGame(PuzzleGame):
    """Lights Out puzzle game.

    Click lights to toggle them and their neighbors.
    Goal: Turn all lights off.
    Perfect demonstration of boolean XOR constraints.
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Lights Out game.

        Args:
            difficulty: Game difficulty level (easy=5x5, medium=6x6, hard=7x7)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Use pydantic config based on difficulty
        self.config = LightsOutConfig.from_difficulty(self.difficulty)
        self.size = self.config.size

        # Grid: 0 = off, 1 = on
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.initial_grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Track which cells need to be pressed (solution)
        self.presses = [[0 for _ in range(self.size)] for _ in range(self.size)]

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Lights Out"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Toggle lights to turn all off - XOR constraint puzzle"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["boolean_sat", "xor_constraints", "parity", "linear_algebra"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["toggle_systems", "parity_checking", "state_synchronization"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "exponential", "constraint_density": "dense"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = presses needed."""
        if not hasattr(self, "presses") or not self.presses:
            return None
        return sum(1 for r in range(self.size) for c in range(self.size) if self.presses[r][c] == 1)

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Lights Out."""
        from ...models import DifficultyLevel

        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 3,
            DifficultyLevel.HARD.value: 4,
        }.get(self.difficulty.value, 3)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=2.0,  # Press or not
            state_observability=1.0,
            constraint_density=0.7,
        )

    def _toggle_cell(self, row: int, col: int, grid: list[list[int]]) -> None:
        """Toggle a cell and its neighbors.

        Args:
            row: Row index
            col: Column index
            grid: Grid to modify
        """
        # Toggle the cell itself
        grid[row][col] = 1 - grid[row][col]

        # Toggle neighbors (up, down, left, right)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < self.size and 0 <= new_col < self.size:
                grid[new_row][new_col] = 1 - grid[new_row][new_col]

    async def generate_puzzle(self) -> None:
        """Generate a new Lights Out puzzle."""
        # Start with all lights off
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Generate a random solution pattern (which cells to press)
        num_presses = self.config.num_presses

        # Randomly select cells to press
        pressed_cells: set[tuple[int, int]] = set()
        attempts = 0
        while len(pressed_cells) < num_presses and attempts < 100:
            row = self._rng.randint(0, self.size - 1)
            col = self._rng.randint(0, self.size - 1)
            pressed_cells.add((row, col))
            attempts += 1

        # Apply these presses to create the puzzle
        for row, col in pressed_cells:
            self.presses[row][col] = 1
            self._toggle_cell(row, col, self.grid)

        # Store initial state
        self.initial_grid = [row[:] for row in self.grid]
        self.moves_made = 0
        self.game_started = True

    async def validate_move(self, row: int, col: int) -> MoveResult:
        """Toggle a cell (press it).

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)

        Returns:
            MoveResult with success status and message
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return MoveResult(success=False, message=f"Invalid coordinates. Use row and column between 1-{self.size}.")

        # Toggle the cell and neighbors
        self._toggle_cell(row, col, self.grid)

        # Update solution tracking - XOR the press state
        # (pressing a cell twice cancels out)
        self.presses[row][col] = 1 - self.presses[row][col]

        self.moves_made += 1

        return MoveResult(success=True, message=f"Toggled light at ({row + 1}, {col + 1})", state_changed=True)

    def is_complete(self) -> bool:
        """Check if the puzzle is complete (all lights off)."""
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] == 1:
                    return False
        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        # Find a cell in the solution that should be pressed
        for row in range(self.size):
            for col in range(self.size):
                if self.presses[row][col] == 1:
                    hint_data = (row + 1, col + 1)
                    hint_message = f"Try pressing the light at row {row + 1}, column {col + 1}"
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
                cell = self.grid[row][col]
                # ● = on, ○ = off
                symbol = "●" if cell == 1 else "○"
                line += f"{symbol}|"
            lines.append(line)
            lines.append("  +" + "-+" * self.size)

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Lights Out.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return f"""LIGHTS OUT RULES:
- Click a light to toggle it and its neighbors
- Neighbors = up, down, left, right (not diagonal)
- Goal: Turn ALL lights off (○)
- ● = light ON, ○ = light OFF
- Grid size: {self.size}×{self.size}"""

    def get_commands(self) -> str:
        """Get the available commands for Lights Out.

        Returns:
            Multi-line string describing available commands
        """
        return """LIGHTS OUT COMMANDS:
  press <row> <col>  - Press a light (e.g., 'press 2 3')
  show               - Display the current grid
  hint               - Get a hint for the next move
  check              - Check if all lights are off
  reset              - Reset to initial state
  menu               - Return to game selection
  quit               - Exit the server"""

    def get_stats(self) -> str:
        """Get current game statistics.

        Returns:
            String with game stats
        """
        lights_on = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 1)
        return f"Moves made: {self.moves_made} | Lights ON: {lights_on} | Grid size: {self.size}×{self.size} | Seed: {self.seed}"
