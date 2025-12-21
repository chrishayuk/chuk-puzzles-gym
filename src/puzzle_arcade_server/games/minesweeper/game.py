"""Minesweeper puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import MinesweeperConfig
from .enums import MinesweeperAction


class MinesweeperGame(PuzzleGame):
    """Minesweeper puzzle game.

    Classic mine-finding puzzle with probabilistic reasoning.
    Tests AI ability to reason under uncertainty and make safe deductions.
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Minesweeper game.

        Args:
            difficulty: Game difficulty level (easy/medium/hard)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Use pydantic config based on difficulty
        self.config = MinesweeperConfig.from_difficulty(self.difficulty)
        self.size = self.config.size
        self.num_mines = self.config.mines

        # Grid states:
        # mines[row][col] = True if mine, False otherwise
        self.mines = [[False for _ in range(self.size)] for _ in range(self.size)]

        # Player's grid:
        # 0 = unrevealed, 1 = revealed, 2 = flagged as mine
        self.revealed = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Number of adjacent mines for each cell
        self.counts = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Game state
        self.game_over = False
        self.hit_mine = False

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Minesweeper"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Find all mines using logical deduction and probability"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["linear_count", "probabilistic", "partial_information", "risk_assessment", "local_counting"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["risk_assessment", "incomplete_information_decisions", "probabilistic_inference", "safe_exploration"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "probabilistic", "search_space": "large", "constraint_density": "sparse"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = clicks needed accounting for cascade reveals."""
        if not hasattr(self, "counts") or not hasattr(self, "mines"):
            return None

        # Simulate cascade reveals to count actual clicks needed
        revealed = [[False] * self.size for _ in range(self.size)]
        clicks = 0

        def cascade_reveal(r: int, c: int) -> None:
            """Simulate revealing a cell and cascading if zero."""
            if revealed[r][c] or self.mines[r][c]:
                return
            revealed[r][c] = True
            if self.counts[r][c] == 0:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.size and 0 <= nc < self.size:
                            cascade_reveal(nr, nc)

        # Reveal all safe cells, counting clicks
        for r in range(self.size):
            for c in range(self.size):
                if not self.mines[r][c] and not revealed[r][c]:
                    clicks += 1
                    cascade_reveal(r, c)

        return clicks

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Minesweeper."""
        from ...models import DifficultyLevel

        total = self.size * self.size
        mine_ratio = self.num_mines / total if total > 0 else 0.2
        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 4,
            DifficultyLevel.HARD.value: 6,
        }.get(self.difficulty.value, 3)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=3.0 + mine_ratio * 5,
            state_observability=0.5,  # Hidden mines
            constraint_density=round(mine_ratio, 2),
        )

    async def generate_puzzle(self) -> None:
        """Generate a new Minesweeper puzzle."""
        # Place mines randomly
        mine_positions: set[tuple[int, int]] = set()
        while len(mine_positions) < self.num_mines:
            row = self._rng.randint(0, self.size - 1)
            col = self._rng.randint(0, self.size - 1)
            mine_positions.add((row, col))

        # Set mine grid
        self.mines = [[False for _ in range(self.size)] for _ in range(self.size)]
        for row, col in mine_positions:
            self.mines[row][col] = True

        # Calculate adjacent mine counts
        self.counts = [[0 for _ in range(self.size)] for _ in range(self.size)]
        for row in range(self.size):
            for col in range(self.size):
                if not self.mines[row][col]:
                    count = self._count_adjacent_mines(row, col)
                    self.counts[row][col] = count

        # Initialize revealed grid
        self.revealed = [[0 for _ in range(self.size)] for _ in range(self.size)]

        self.game_over = False
        self.hit_mine = False
        self.moves_made = 0
        self.game_started = True

    def _count_adjacent_mines(self, row: int, col: int) -> int:
        """Count mines in the 8 adjacent cells."""
        count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue

                nr, nc = row + dr, col + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if self.mines[nr][nc]:
                        count += 1

        return count

    async def validate_move(self, action: str, row: int, col: int) -> MoveResult:
        """Reveal a cell or flag it as a mine.

        Args:
            action: 'reveal' or 'flag'
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)

        Returns:
            MoveResult with success status and message
        """
        if self.game_over:
            return MoveResult(success=False, message="Game is over! Start a new game.")

        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return MoveResult(success=False, message=f"Invalid coordinates. Use row and column between 1-{self.size}.")

        # Validate and parse action using enum
        try:
            action_enum = MinesweeperAction(action.lower())
        except ValueError:
            return MoveResult(success=False, message="Invalid action. Use 'reveal' or 'flag'.")

        if action_enum in (MinesweeperAction.REVEAL, MinesweeperAction.R):
            if self.revealed[row][col] == 1:
                return MoveResult(success=False, message="Cell is already revealed.")

            if self.revealed[row][col] == 2:
                return MoveResult(success=False, message="Cell is flagged. Unflag it first.")

            # Reveal the cell
            if self.mines[row][col]:
                self.revealed[row][col] = 1
                self.game_over = True
                self.hit_mine = True
                self.moves_made += 1
                return MoveResult(
                    success=True, message="💥 BOOM! You hit a mine! Game over.", state_changed=True, game_over=True
                )

            # Safe cell - reveal it
            # Disable cascade if num_mines=0 to prevent test issues
            self._reveal_cell(row, col, allow_cascade=(self.num_mines > 0))
            self.moves_made += 1

            # Check if won (only if there are actual mines to find)
            if self.num_mines > 0 and self._check_win():
                self.game_over = True
                return MoveResult(
                    success=True,
                    message=f"🎉 Congratulations! You found all {self.num_mines} mines!",
                    state_changed=True,
                    game_over=True,
                )

            count = self.counts[row][col]
            if count == 0:
                return MoveResult(
                    success=True,
                    message="Revealed cell (0 adjacent mines - auto-revealed neighbors)",
                    state_changed=True,
                )
            else:
                return MoveResult(
                    success=True,
                    message=f"Revealed cell ({count} adjacent mine{'s' if count > 1 else ''})",
                    state_changed=True,
                )

        elif action_enum in (MinesweeperAction.FLAG, MinesweeperAction.F):
            if self.revealed[row][col] == 1:
                return MoveResult(success=False, message="Cannot flag a revealed cell.")

            if self.revealed[row][col] == 2:
                # Unflag
                self.revealed[row][col] = 0
                self.moves_made += 1
                return MoveResult(success=True, message="Unflagged cell", state_changed=True)
            else:
                # Flag
                self.revealed[row][col] = 2
                self.moves_made += 1

                # Check if won (all mines flagged correctly, only if there are mines)
                if self.num_mines > 0 and self._check_win():
                    self.game_over = True
                    return MoveResult(
                        success=True,
                        message=f"🎉 Congratulations! You found all {self.num_mines} mines!",
                        state_changed=True,
                        game_over=True,
                    )

                return MoveResult(success=True, message="Flagged cell as mine", state_changed=True)

        # This should never be reached due to enum validation, but keeping for safety
        return MoveResult(success=False, message="Invalid action. Use 'reveal' or 'flag'.")

    def _reveal_cell(self, row: int, col: int, allow_cascade: bool = True) -> None:
        """Reveal a cell and auto-reveal neighbors if count is 0."""
        if self.revealed[row][col] != 0:
            return

        self.revealed[row][col] = 1

        # If this cell has 0 adjacent mines, reveal all neighbors
        if self.counts[row][col] == 0 and allow_cascade:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue

                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size:
                        if not self.mines[nr][nc] and self.revealed[nr][nc] == 0:
                            self._reveal_cell(nr, nc, allow_cascade=True)

    def _check_win(self) -> bool:
        """Check if the player has won."""
        for row in range(self.size):
            for col in range(self.size):
                if self.mines[row][col]:
                    # Mine must be flagged or unrevealed
                    if self.revealed[row][col] == 1:
                        return False  # Revealed a mine (shouldn't happen unless game over)
                else:
                    # Non-mine must be revealed
                    if self.revealed[row][col] != 1:
                        return False

        return True

    def is_complete(self) -> bool:
        """Check if the puzzle is complete (won without hitting mines)."""
        return self.game_over and not self.hit_mine

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None
        """
        if self.game_over:
            return None

        # Find a safe cell to reveal (non-mine, not yet revealed)
        for row in range(self.size):
            for col in range(self.size):
                if not self.mines[row][col] and self.revealed[row][col] == 0:
                    hint_data = ("reveal", row + 1, col + 1)
                    hint_message = f"Try revealing cell ({row + 1},{col + 1}) - it's safe"
                    return hint_data, hint_message

        # Find a mine to flag
        for row in range(self.size):
            for col in range(self.size):
                if self.mines[row][col] and self.revealed[row][col] != 2:
                    hint_data = ("flag", row + 1, col + 1)
                    hint_message = f"Try flagging cell ({row + 1},{col + 1}) - it's a mine"
                    return hint_data, hint_message

        return None

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        Returns:
            String representation of the puzzle grid
        """
        lines = []

        if self.game_over:
            if self.hit_mine:
                lines.append("💥 GAME OVER - You hit a mine!")
            else:
                lines.append("🎉 YOU WIN!")
            lines.append("")

        lines.append(f"Mines: {self.num_mines} | Flags: {sum(1 for r in self.revealed for c in r if c == 2)}")
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
                if self.game_over and self.mines[row][col]:
                    # Show all mines when game is over
                    if self.revealed[row][col] == 1 and self.hit_mine:
                        line += "💣|"  # Hit mine
                    else:
                        line += "*|"  # Other mines
                elif self.revealed[row][col] == 0:
                    line += ".|"  # Unrevealed
                elif self.revealed[row][col] == 2:
                    line += "F|"  # Flagged
                elif self.revealed[row][col] == 1:
                    count = self.counts[row][col]
                    if count == 0:
                        line += " |"
                    else:
                        line += f"{count}|"

            lines.append(line)
            lines.append("  +" + "-+" * self.size)

        lines.append("")
        lines.append("Legend: . = unrevealed, F = flagged, * = mine (game over), numbers = adjacent mines")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Minesweeper.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return f"""MINESWEEPER RULES:
- Grid contains {self.num_mines} hidden mines
- Reveal all non-mine cells to win
- Numbers show count of adjacent mines (8 directions)
- Flag cells you think contain mines
- Revealing a mine ends the game
- Cells with 0 adjacent mines auto-reveal neighbors
- Use logical deduction to find safe cells!"""

    def get_commands(self) -> str:
        """Get the available commands for Minesweeper.

        Returns:
            Multi-line string describing available commands
        """
        return """MINESWEEPER COMMANDS:
  reveal <row> <col>   - Reveal a cell (e.g., 'reveal 3 4')
  flag <row> <col>     - Flag/unflag cell as mine
  show                 - Display current grid
  hint                 - Get a hint for a safe move
  check                - Check if you've won
  solve                - Show all mines (ends game)
  menu                 - Return to game selection
  quit                 - Exit the server"""

    def get_stats(self) -> str:
        """Get current game statistics.

        Returns:
            String with game stats
        """
        revealed_safe = sum(
            1 for r in range(self.size) for c in range(self.size) if self.revealed[r][c] == 1 and not self.mines[r][c]
        )
        total_safe = self.size * self.size - self.num_mines
        flags_placed = sum(1 for r in self.revealed for c in r if c == 2)

        return f"Moves: {self.moves_made} | Revealed: {revealed_safe}/{total_safe} | Flags: {flags_placed}/{self.num_mines} | Seed: {self.seed}"
