"""Numberlink (Flow) puzzle game implementation."""

from collections import deque
from typing import Any

from ...models import DifficultyLevel, DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import NumberlinkConfig


class NumberlinkGame(PuzzleGame):
    """Numberlink puzzle - connect numbered pairs with non-crossing paths.

    Rules:
    - The grid contains pairs of numbered endpoints
    - Connect each pair with a continuous path
    - Paths cannot cross or overlap
    - Every cell must be part of exactly one path
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        super().__init__(difficulty, seed, **kwargs)
        self.config = NumberlinkConfig.from_difficulty(self.difficulty)
        self.size = self.config.size
        self.num_pairs = self.config.num_pairs
        self.grid: list[list[int]] = []
        self.solution: list[list[int]] = []
        self.initial_grid: list[list[int]] = []
        self.endpoints: dict[int, list[tuple[int, int]]] = {}

    @property
    def name(self) -> str:
        return "Numberlink"

    @property
    def description(self) -> str:
        return "Connect numbered pairs with non-crossing paths"

    @property
    def constraint_types(self) -> list[str]:
        return ["path_connectivity", "non_crossing", "space_filling"]

    @property
    def business_analogies(self) -> list[str]:
        return ["cable_routing", "circuit_layout", "network_design", "logistics_routing"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        return {
            "reasoning_type": "deductive",
            "search_space": "large",
            "constraint_density": "dense",
        }

    @property
    def complexity_metrics(self) -> dict[str, int | float]:
        empty = sum(1 for row in self.grid for cell in row if cell == 0)
        return {
            "variable_count": self.size * self.size,
            "constraint_count": self.num_pairs * 2 + self.size * self.size,
            "domain_size": self.num_pairs,
            "branching_factor": 3.0,
            "empty_cells": empty,
        }

    @property
    def difficulty_profile(self) -> DifficultyProfile:
        profiles = {
            DifficultyLevel.EASY: DifficultyProfile(
                logic_depth=3, branching_factor=3.0, state_observability=1.0, constraint_density=0.6
            ),
            DifficultyLevel.MEDIUM: DifficultyProfile(
                logic_depth=5, branching_factor=3.5, state_observability=1.0, constraint_density=0.5
            ),
            DifficultyLevel.HARD: DifficultyProfile(
                logic_depth=7, branching_factor=4.0, state_observability=1.0, constraint_density=0.4
            ),
        }
        return profiles[self.difficulty]

    def _neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        """Get valid orthogonal neighbors."""
        result = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                result.append((nr, nc))
        return result

    def _generate_hamiltonian_path(self) -> list[tuple[int, int]] | None:
        """Generate a space-filling path that visits all cells.

        Uses a randomized DFS approach to create a Hamiltonian path.
        """
        n = self.size
        total = n * n
        visited = [[False] * n for _ in range(n)]

        # Start from a random cell
        start_r = self._rng.randint(0, n - 1)
        start_c = self._rng.randint(0, n - 1)

        path: list[tuple[int, int]] = [(start_r, start_c)]
        visited[start_r][start_c] = True

        def _count_reachable(r: int, c: int) -> int:
            """Count cells reachable from (r,c) without using visited cells."""
            seen = set()
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                cr, cc = queue.popleft()
                for nr, nc in self._neighbors(cr, cc):
                    if not visited[nr][nc] and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            return len(seen)

        while len(path) < total:
            r, c = path[-1]
            neighbors = self._neighbors(r, c)
            unvisited = [(nr, nc) for nr, nc in neighbors if not visited[nr][nc]]

            if not unvisited:
                return None  # Dead end

            # Warnsdorff's rule: prefer cells with fewer unvisited neighbors
            # (with random tie-breaking)
            def sort_key(pos: tuple[int, int]) -> tuple[int, int]:
                nr, nc = pos
                count = sum(1 for nnr, nnc in self._neighbors(nr, nc) if not visited[nnr][nnc])
                return (count, self._rng.randint(0, 1000))

            unvisited.sort(key=sort_key)
            nr, nc = unvisited[0]
            path.append((nr, nc))
            visited[nr][nc] = True

        return path

    async def generate_puzzle(self) -> None:
        """Generate a Numberlink puzzle by partitioning a Hamiltonian path."""
        n = self.size
        num_pairs = self.num_pairs

        # Try to generate a valid Hamiltonian path
        path = None
        for _ in range(50):
            path = self._generate_hamiltonian_path()
            if path and len(path) == n * n:
                break
            path = None

        if path is None:
            # Fallback: simpler snake path
            path = []
            for r in range(n):
                cols = range(n) if r % 2 == 0 else range(n - 1, -1, -1)
                for c in cols:
                    path.append((r, c))

        total = len(path)

        # Partition the path into num_pairs segments
        # Calculate segment lengths that sum to total
        min_len = 2  # Each segment must have at least 2 cells
        remaining = total - num_pairs * min_len
        if remaining < 0:
            # Reduce pairs if grid is too small
            num_pairs = total // min_len
            self.num_pairs = num_pairs
            remaining = total - num_pairs * min_len

        # Distribute extra cells randomly
        extras = [0] * num_pairs
        for _ in range(remaining):
            idx = self._rng.randint(0, num_pairs - 1)
            extras[idx] += 1

        lengths = [min_len + e for e in extras]

        # Build solution grid from path segments
        self.solution = [[0] * n for _ in range(n)]
        self.endpoints = {}
        pos = 0
        for pair_id in range(1, num_pairs + 1):
            seg_len = lengths[pair_id - 1]
            segment = path[pos : pos + seg_len]
            start = segment[0]
            end = segment[-1]
            self.endpoints[pair_id] = [start, end]
            for r, c in segment:
                self.solution[r][c] = pair_id
            pos += seg_len

        # Initial grid: only endpoints are shown
        self.initial_grid = [[0] * n for _ in range(n)]
        for pair_id, pts in self.endpoints.items():
            for r, c in pts:
                self.initial_grid[r][c] = pair_id

        self.grid = [row[:] for row in self.initial_grid]
        self.game_started = True

    def _is_endpoint(self, r: int, c: int) -> bool:
        """Check if (r, c) is an endpoint cell."""
        return self.initial_grid[r][c] != 0

    async def validate_move(self, row: int, col: int, num: int) -> MoveResult:
        """Validate placing a path segment.

        Args:
            row: 1-indexed row
            col: 1-indexed column
            num: Pair number (1-N) or 0 to clear
        """
        n = self.size
        r, c = row - 1, col - 1

        if not (0 <= r < n and 0 <= c < n):
            self.record_move((row, col), False)
            return MoveResult(success=False, message=f"Position ({row}, {col}) is out of bounds.")

        if self._is_endpoint(r, c):
            self.record_move((row, col), False)
            return MoveResult(success=False, message="Cannot modify an endpoint cell.")

        if num == 0:
            if self.grid[r][c] == 0:
                self.record_move((row, col), False)
                return MoveResult(success=False, message="Cell is already empty.")
            self.grid[r][c] = 0
            self.record_move((row, col), True)
            return MoveResult(success=True, message=f"Cleared cell ({row}, {col}).", state_changed=True)

        if not (1 <= num <= self.num_pairs):
            self.record_move((row, col), False)
            return MoveResult(success=False, message=f"Pair number must be between 1 and {self.num_pairs}.")

        self.grid[r][c] = num
        self.record_move((row, col), True)
        return MoveResult(success=True, message=f"Placed {num} at ({row}, {col}).", state_changed=True)

    def is_complete(self) -> bool:
        """Check if all paths are correctly connected."""
        return self.grid == self.solution

    def _check_paths_valid(self) -> bool:
        """Verify each pair forms a valid connected path."""
        for pair_id, pts in self.endpoints.items():
            start, end = pts
            # BFS from start following cells with this pair_id
            visited = set()
            queue = deque([start])
            visited.add(start)
            while queue:
                r, c = queue.popleft()
                for nr, nc in self._neighbors(r, c):
                    if (nr, nc) not in visited and self.grid[nr][nc] == pair_id:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            if end not in visited:
                return False
            # Check all cells of this pair_id are connected
            total = sum(1 for row in self.grid for cell in row if cell == pair_id)
            if len(visited) != total:
                return False
        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Suggest a cell to fill from the solution."""
        if not self.can_use_hint():
            return None
        n = self.size
        for r in range(n):
            for c in range(n):
                if self.grid[r][c] == 0 and self.solution[r][c] != 0:
                    val = self.solution[r][c]
                    return (
                        (r + 1, c + 1, val),
                        f"Try placing {val} at row {r + 1}, column {c + 1}.",
                    )
        return None

    def render_grid(self) -> str:
        """Render the grid showing paths and endpoints."""
        n = self.size
        lines = []

        # Column headers
        header = "    " + "  ".join(str(c + 1) for c in range(n))
        lines.append(header)
        lines.append("   " + "+" + "---" * n + "+")

        for r in range(n):
            cells = []
            for c in range(n):
                val = self.grid[r][c]
                if val == 0:
                    cells.append(".")
                elif self._is_endpoint(r, c):
                    # Show endpoints in uppercase/bold style
                    if val < 10:
                        cells.append(str(val))
                    else:
                        cells.append(chr(ord("A") + val - 10))
                else:
                    if val < 10:
                        cells.append(str(val))
                    else:
                        cells.append(chr(ord("a") + val - 10))
            line = f" {r + 1} | " + "  ".join(cells) + " |"
            lines.append(line)

        lines.append("   " + "+" + "---" * n + "+")
        lines.append(f"Pairs: {self.num_pairs}")

        return "\n".join(lines)

    def get_stats(self) -> str:
        """Get current game statistics."""
        filled = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] != 0)
        total = self.size * self.size
        return f"Moves: {self.moves_made} | Filled: {filled}/{total} | Pairs: {self.num_pairs} | Seed: {self.seed}"

    def get_rules(self) -> str:
        return (
            f"NUMBERLINK ({self.size}x{self.size}, {self.num_pairs} pairs)\n"
            "Connect each pair of matching numbers with a continuous path.\n"
            "Paths travel horizontally or vertically (not diagonally).\n"
            "Paths cannot cross or overlap.\n"
            "Every cell must be part of exactly one path."
        )

    def get_commands(self) -> str:
        return (
            "Commands:\n"
            f"  place <row> <col> <pair>  - Place a path segment (1-{self.num_pairs})\n"
            "  clear <row> <col>         - Clear a cell\n"
            "  hint                      - Get a hint\n"
            "  check                     - Check if solved\n"
            "  show                      - Show current state\n"
            "  menu                      - Return to menu"
        )
