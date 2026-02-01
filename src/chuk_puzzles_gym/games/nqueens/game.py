"""N-Queens puzzle game implementation."""

from typing import Any

from ...models import DifficultyLevel, DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import NQueensConfig


class NQueensGame(PuzzleGame):
    """N-Queens puzzle - place N queens on an NxN board with no conflicts.

    Rules:
    - Place exactly N queens on an NxN chessboard
    - No two queens may share the same row, column, or diagonal
    - Some queens may be pre-placed as hints
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        super().__init__(difficulty, seed, **kwargs)
        self.config = NQueensConfig.from_difficulty(self.difficulty)
        self.size = self.config.size
        self.grid: list[list[int]] = []
        self.solution: list[list[int]] = []
        self.initial_grid: list[list[int]] = []
        self._queen_cols: list[int] = []  # Solution: queen_cols[row] = col

    @property
    def name(self) -> str:
        return "N-Queens"

    @property
    def description(self) -> str:
        return f"Place {self.size} queens on a {self.size}x{self.size} board with no conflicts"

    @property
    def constraint_types(self) -> list[str]:
        return ["placement", "attack_avoidance", "all_different", "diagonal_constraint"]

    @property
    def business_analogies(self) -> list[str]:
        return ["non_conflicting_placement", "resource_allocation", "antenna_placement"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        return {
            "reasoning_type": "deductive",
            "search_space": "exponential",
            "constraint_density": "moderate",
        }

    @property
    def complexity_metrics(self) -> dict[str, int | float]:
        queens_placed = sum(1 for row in self.grid for cell in row if cell == 1)
        return {
            "variable_count": self.size,
            "constraint_count": self.size * 3,  # row + col + diag constraints
            "domain_size": self.size,
            "branching_factor": self.size / 2.0,
            "empty_cells": self.size - queens_placed,
        }

    @property
    def difficulty_profile(self) -> DifficultyProfile:
        profiles = {
            DifficultyLevel.EASY: DifficultyProfile(
                logic_depth=2, branching_factor=3.0, state_observability=1.0, constraint_density=0.5
            ),
            DifficultyLevel.MEDIUM: DifficultyProfile(
                logic_depth=4, branching_factor=4.0, state_observability=1.0, constraint_density=0.4
            ),
            DifficultyLevel.HARD: DifficultyProfile(
                logic_depth=6, branching_factor=6.0, state_observability=1.0, constraint_density=0.3
            ),
        }
        return profiles[self.difficulty]

    @property
    def optimal_steps(self) -> int | None:
        """Number of queens left to place."""
        initial_queens = sum(1 for row in self.initial_grid for cell in row if cell == 1)
        return self.size - initial_queens

    def _solve_nqueens(self) -> list[int] | None:
        """Find a valid N-Queens solution using randomized backtracking.

        Returns:
            List of column positions for each row, or None if no solution.
        """
        n = self.size
        result: list[int] = [-1] * n
        used_cols: set[int] = set()
        diag1: set[int] = set()  # row - col
        diag2: set[int] = set()  # row + col

        # Create shuffled column order for each row (for randomization)
        col_orders = []
        for _ in range(n):
            cols = list(range(n))
            self._rng.shuffle(cols)
            col_orders.append(cols)

        def backtrack(row: int) -> bool:
            if row == n:
                return True
            for col in col_orders[row]:
                if col in used_cols:
                    continue
                d1 = row - col
                d2 = row + col
                if d1 in diag1 or d2 in diag2:
                    continue
                result[row] = col
                used_cols.add(col)
                diag1.add(d1)
                diag2.add(d2)
                if backtrack(row + 1):
                    return True
                used_cols.discard(col)
                diag1.discard(d1)
                diag2.discard(d2)
            return False

        if backtrack(0):
            return result
        return None

    def _has_conflicts(self) -> bool:
        """Check if current grid has any queen conflicts."""
        n = self.size
        queens = []
        for r in range(n):
            for c in range(n):
                if self.grid[r][c] == 1:
                    queens.append((r, c))

        for i in range(len(queens)):
            for j in range(i + 1, len(queens)):
                r1, c1 = queens[i]
                r2, c2 = queens[j]
                if r1 == r2 or c1 == c2 or abs(r1 - r2) == abs(c1 - c2):
                    return True
        return False

    async def generate_puzzle(self) -> None:
        """Generate an N-Queens puzzle."""
        n = self.size
        queen_cols = self._solve_nqueens()
        if queen_cols is None:
            raise RuntimeError(f"Failed to find N-Queens solution for N={n}")

        self._queen_cols = queen_cols

        # Build solution grid
        self.solution = [[0] * n for _ in range(n)]
        for r in range(n):
            self.solution[r][queen_cols[r]] = 1

        # Pre-place some queens as hints
        self.grid = [[0] * n for _ in range(n)]
        rows = list(range(n))
        self._rng.shuffle(rows)
        for r in rows[: self.config.pre_placed]:
            self.grid[r][queen_cols[r]] = 1

        self.initial_grid = [row[:] for row in self.grid]
        self.game_started = True

    async def validate_move(self, row: int, col: int, num: int) -> MoveResult:
        """Validate placing or removing a queen.

        Args:
            row: 1-indexed row
            col: 1-indexed column
            num: 1 to place queen, 0 to clear
        """
        n = self.size
        r, c = row - 1, col - 1

        if not (0 <= r < n and 0 <= c < n):
            self.record_move((row, col), False)
            return MoveResult(success=False, message=f"Position ({row}, {col}) is out of bounds.")

        if self.initial_grid[r][c] == 1 and num == 0:
            self.record_move((row, col), False)
            return MoveResult(success=False, message="Cannot remove a pre-placed queen.")

        if num == 0:
            if self.grid[r][c] == 0:
                self.record_move((row, col), False)
                return MoveResult(success=False, message="No queen at that position.")
            self.grid[r][c] = 0
            self.record_move((row, col), True)
            return MoveResult(success=True, message=f"Removed queen from ({row}, {col}).", state_changed=True)

        if num != 1:
            self.record_move((row, col), False)
            return MoveResult(success=False, message="Use 1 to place a queen or 0 to clear.")

        if self.grid[r][c] == 1:
            self.record_move((row, col), False)
            return MoveResult(success=False, message="A queen is already at that position.")

        # Check conflicts with existing queens
        for rr in range(n):
            for cc in range(n):
                if self.grid[rr][cc] == 1:
                    if rr == r:
                        self.record_move((row, col), False)
                        return MoveResult(
                            success=False,
                            message=f"Conflicts with queen at ({rr + 1}, {cc + 1}) - same row.",
                        )
                    if cc == c:
                        self.record_move((row, col), False)
                        return MoveResult(
                            success=False,
                            message=f"Conflicts with queen at ({rr + 1}, {cc + 1}) - same column.",
                        )
                    if abs(rr - r) == abs(cc - c):
                        self.record_move((row, col), False)
                        return MoveResult(
                            success=False,
                            message=f"Conflicts with queen at ({rr + 1}, {cc + 1}) - same diagonal.",
                        )

        self.grid[r][c] = 1
        self.record_move((row, col), True)
        return MoveResult(success=True, message=f"Placed queen at ({row}, {col}).", state_changed=True)

    def is_complete(self) -> bool:
        """Check if N queens are placed with no conflicts."""
        n = self.size
        queens = []
        for r in range(n):
            for c in range(n):
                if self.grid[r][c] == 1:
                    queens.append((r, c))

        if len(queens) != n:
            return False

        # Verify no conflicts
        cols = set()
        diag1 = set()
        diag2 = set()
        for r, c in queens:
            if c in cols or (r - c) in diag1 or (r + c) in diag2:
                return False
            cols.add(c)
            diag1.add(r - c)
            diag2.add(r + c)

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Suggest the next queen to place from the solution."""
        if not self.can_use_hint():
            return None
        n = self.size
        for r in range(n):
            c = self._queen_cols[r]
            if self.grid[r][c] == 0:
                return (
                    (r + 1, c + 1, 1),
                    f"Try placing a queen at row {r + 1}, column {c + 1}.",
                )
        return None

    def render_grid(self) -> str:
        """Render the chessboard with queens."""
        n = self.size
        lines = []

        # Column headers
        header = "    " + "  ".join(str(c + 1) for c in range(n))
        lines.append(header)
        lines.append("   " + "+" + "---" * n + "+")

        for r in range(n):
            cells = []
            for c in range(n):
                if self.grid[r][c] == 1:
                    if self.initial_grid[r][c] == 1:
                        cells.append("Q")  # Pre-placed queen
                    else:
                        cells.append("Q")  # Player-placed queen
                else:
                    cells.append(".")
            line = f" {r + 1} | " + "  ".join(cells) + " |"
            lines.append(line)

        lines.append("   " + "+" + "---" * n + "+")
        queens_placed = sum(1 for row in self.grid for cell in row if cell == 1)
        lines.append(f"Queens: {queens_placed}/{n}")

        return "\n".join(lines)

    def get_stats(self) -> str:
        """Get current game statistics."""
        placed = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 1)
        return f"Moves: {self.moves_made} | Queens: {placed}/{self.size} | Board: {self.size}x{self.size} | Seed: {self.seed}"

    def get_rules(self) -> str:
        return (
            f"N-QUEENS ({self.size}x{self.size})\n"
            f"Place {self.size} queens on the board.\n"
            "No two queens may share the same row, column, or diagonal.\n"
            "Pre-placed queens (Q) cannot be removed."
        )

    def get_commands(self) -> str:
        return (
            "Commands:\n"
            "  place <row> <col> 1  - Place a queen\n"
            "  clear <row> <col>    - Remove a queen\n"
            "  hint                 - Get a hint\n"
            "  check                - Check if solved\n"
            "  show                 - Show current state\n"
            "  menu                 - Return to menu"
        )
