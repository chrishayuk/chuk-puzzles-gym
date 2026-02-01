"""Skyscrapers puzzle game implementation."""

from typing import Any

from ...models import DifficultyLevel, DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import SkyscrapersConfig


class SkyscrapersGame(PuzzleGame):
    """Skyscrapers puzzle - fill a Latin square with visibility clues.

    Rules:
    - Fill an NxN grid with numbers 1 to N
    - Each row and column must contain each number exactly once (Latin square)
    - Numbers represent building heights
    - Clues around the border indicate how many buildings are visible from that direction
    - A taller building hides all shorter buildings behind it
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        super().__init__(difficulty, seed, **kwargs)
        self.config = SkyscrapersConfig.from_difficulty(self.difficulty)
        self.size = self.config.size
        self.grid: list[list[int]] = []
        self.solution: list[list[int]] = []
        self.initial_grid: list[list[int]] = []
        self.clues: dict[str, list[int]] = {"top": [], "bottom": [], "left": [], "right": []}

    @property
    def name(self) -> str:
        return "Skyscrapers"

    @property
    def description(self) -> str:
        return "Fill the grid with building heights using visibility clues"

    @property
    def constraint_types(self) -> list[str]:
        return ["all_different", "visibility", "ordering", "boundary_clues"]

    @property
    def business_analogies(self) -> list[str]:
        return ["urban_planning", "line_of_sight_analysis", "signal_visibility"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        return {
            "reasoning_type": "deductive",
            "search_space": "medium",
            "constraint_density": "dense",
        }

    @property
    def complexity_metrics(self) -> dict[str, int | float]:
        empty = sum(1 for row in self.grid for cell in row if cell == 0)
        return {
            "variable_count": self.size * self.size,
            "constraint_count": 2 * self.size + 4 * self.size,
            "domain_size": self.size,
            "branching_factor": self.size / 2.0,
            "empty_cells": empty,
        }

    @property
    def difficulty_profile(self) -> DifficultyProfile:
        profiles = {
            DifficultyLevel.EASY: DifficultyProfile(
                logic_depth=2, branching_factor=2.0, state_observability=1.0, constraint_density=0.7
            ),
            DifficultyLevel.MEDIUM: DifficultyProfile(
                logic_depth=4, branching_factor=3.0, state_observability=1.0, constraint_density=0.6
            ),
            DifficultyLevel.HARD: DifficultyProfile(
                logic_depth=6, branching_factor=4.0, state_observability=1.0, constraint_density=0.5
            ),
        }
        return profiles[self.difficulty]

    def _compute_visibility(self, line: list[int]) -> int:
        """Count how many buildings are visible from the start of a line."""
        count = 0
        max_height = 0
        for h in line:
            if h > max_height:
                count += 1
                max_height = h
        return count

    def _generate_latin_square(self) -> list[list[int]]:
        """Generate a random NxN Latin square."""
        n = self.size
        # Start with a shifted-row construction
        base = list(range(1, n + 1))
        grid = []
        for r in range(n):
            row = [(base[(r + c) % n]) for c in range(n)]
            grid.append(row)

        # Shuffle rows
        rows = list(range(n))
        self._rng.shuffle(rows)
        grid = [grid[r] for r in rows]

        # Shuffle columns
        cols = list(range(n))
        self._rng.shuffle(cols)
        grid = [[row[c] for c in cols] for row in grid]

        # Shuffle values (relabel)
        perm = list(range(1, n + 1))
        self._rng.shuffle(perm)
        mapping = {i + 1: perm[i] for i in range(n)}
        grid = [[mapping[cell] for cell in row] for row in grid]

        return grid

    def _compute_all_clues(self, grid: list[list[int]]) -> dict[str, list[int]]:
        """Compute visibility clues from all 4 directions."""
        n = self.size
        clues: dict[str, list[int]] = {"top": [], "bottom": [], "left": [], "right": []}

        for c in range(n):
            col = [grid[r][c] for r in range(n)]
            clues["top"].append(self._compute_visibility(col))
            clues["bottom"].append(self._compute_visibility(col[::-1]))

        for r in range(n):
            clues["left"].append(self._compute_visibility(grid[r]))
            clues["right"].append(self._compute_visibility(grid[r][::-1]))

        return clues

    async def generate_puzzle(self) -> None:
        """Generate a Skyscrapers puzzle."""
        self.solution = self._generate_latin_square()
        self.clues = self._compute_all_clues(self.solution)

        # Copy solution to grid, then remove cells based on difficulty
        self.grid = [row[:] for row in self.solution]

        # Determine cells to remove
        n = self.size
        total_cells = n * n
        remove_map = {
            DifficultyLevel.EASY: int(total_cells * 0.45),
            DifficultyLevel.MEDIUM: int(total_cells * 0.60),
            DifficultyLevel.HARD: int(total_cells * 0.75),
        }
        cells_to_remove = remove_map[self.difficulty]

        # Randomly remove cells
        all_cells = [(r, c) for r in range(n) for c in range(n)]
        self._rng.shuffle(all_cells)
        for r, c in all_cells[:cells_to_remove]:
            self.grid[r][c] = 0

        self.initial_grid = [row[:] for row in self.grid]
        self.game_started = True

    async def validate_move(self, row: int, col: int, num: int) -> MoveResult:
        """Validate placing a height value.

        Args:
            row: 1-indexed row
            col: 1-indexed column
            num: Height value (1-N) or 0 to clear
        """
        n = self.size
        r, c = row - 1, col - 1

        if not (0 <= r < n and 0 <= c < n):
            self.record_move((row, col), False)
            return MoveResult(success=False, message=f"Position ({row}, {col}) is out of bounds.")

        if self.initial_grid[r][c] != 0:
            self.record_move((row, col), False)
            return MoveResult(success=False, message="Cannot modify an initial cell.")

        if num == 0:
            self.grid[r][c] = 0
            self.record_move((row, col), True)
            return MoveResult(success=True, message=f"Cleared cell ({row}, {col}).", state_changed=True)

        if not (1 <= num <= n):
            self.record_move((row, col), False)
            return MoveResult(success=False, message=f"Value must be between 1 and {n}.")

        # Check row uniqueness
        for cc in range(n):
            if cc != c and self.grid[r][cc] == num:
                self.record_move((row, col), False)
                return MoveResult(
                    success=False,
                    message=f"Value {num} already exists in row {row}.",
                )

        # Check column uniqueness
        for rr in range(n):
            if rr != r and self.grid[rr][c] == num:
                self.record_move((row, col), False)
                return MoveResult(
                    success=False,
                    message=f"Value {num} already exists in column {col}.",
                )

        self.grid[r][c] = num
        self.record_move((row, col), True)
        return MoveResult(
            success=True,
            message=f"Placed {num} at ({row}, {col}).",
            state_changed=True,
        )

    def is_complete(self) -> bool:
        """Check if the puzzle is solved correctly."""
        return self.grid == self.solution

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint - suggest a cell to fill."""
        if not self.can_use_hint():
            return None
        n = self.size
        for r in range(n):
            for c in range(n):
                if self.grid[r][c] == 0:
                    val = self.solution[r][c]
                    return (
                        (r + 1, c + 1, val),
                        f"Try placing {val} at row {r + 1}, column {c + 1}.",
                    )
        return None

    def render_grid(self) -> str:
        """Render the puzzle with visibility clues."""
        n = self.size
        lines = []

        # Top clues
        top_clues = "    " + "  ".join(str(c) if c > 0 else " " for c in self.clues["top"])
        lines.append(top_clues)
        lines.append("   " + "+" + "---" * n + "+")

        # Grid rows with left/right clues
        for r in range(n):
            left = str(self.clues["left"][r]) if self.clues["left"][r] > 0 else " "
            right = str(self.clues["right"][r]) if self.clues["right"][r] > 0 else " "
            cells = "  ".join(str(v) if v != 0 else "." for v in self.grid[r])
            lines.append(f" {left} | {cells} | {right}")

        # Bottom border and clues
        lines.append("   " + "+" + "---" * n + "+")
        bot_clues = "    " + "  ".join(str(c) if c > 0 else " " for c in self.clues["bottom"])
        lines.append(bot_clues)

        return "\n".join(lines)

    def get_stats(self) -> str:
        """Get current game statistics."""
        empty = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 0)
        return f"Moves: {self.moves_made} | Empty cells: {empty} | Grid: {self.size}x{self.size} | Seed: {self.seed}"

    def get_rules(self) -> str:
        return (
            f"SKYSCRAPERS ({self.size}x{self.size})\n"
            f"Fill the grid with numbers 1 to {self.size}.\n"
            "Each row and column must contain each number exactly once.\n"
            "Numbers represent building heights.\n"
            "Clues around the border show how many buildings are visible from that direction.\n"
            "A taller building hides all shorter ones behind it."
        )

    def get_commands(self) -> str:
        return (
            "Commands:\n"
            f"  place <row> <col> <height>  - Place a height (1-{self.size})\n"
            "  clear <row> <col>           - Clear a cell\n"
            "  hint                        - Get a hint\n"
            "  check                       - Check if solved\n"
            "  show                        - Show current state\n"
            "  menu                        - Return to menu"
        )
