"""Hidato (Number Snake) puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import HidatoConfig


class HidatoGame(PuzzleGame):
    """Hidato (Number Snake) puzzle game.

    Fill the grid with consecutive numbers (1 to N) such that each number
    is adjacent (horizontally, vertically, or diagonally) to the next number.
    Creates a continuous path through all cells.
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Hidato game.

        Args:
            difficulty: Game difficulty level (easy=5x5, medium=7x7, hard=9x9)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Use pydantic config based on difficulty
        self.config = HidatoConfig.from_difficulty(self.difficulty)
        self.size = self.config.size

        # Grid: 0 = empty, 1-N = numbers
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.initial_grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Total numbers to place
        self.total_numbers = self.size * self.size

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Hidato"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Number snake puzzle - connect consecutive numbers via adjacent cells"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["sequential_adjacency", "hamiltonian_path", "all_different", "connectivity"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["route_optimization", "sequential_process_flow", "path_finding", "order_fulfillment"]

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
        """Difficulty characteristics for Hidato."""
        from ...models import DifficultyLevel

        empty = self.optimal_steps or 0
        total = self.size * self.size
        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 4,
            DifficultyLevel.HARD.value: 5,
        }.get(self.difficulty.value, 3)
        branching = 4.0 + (empty / total) * 4  # Up to 8 neighbors
        density = 1.0 - (empty / total) if total > 0 else 0.5
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=round(branching, 1),
            state_observability=1.0,
            constraint_density=round(density, 2),
        )

    def _get_neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        """Get all adjacent cells (including diagonals).

        Args:
            row: Row index
            col: Column index

        Returns:
            List of (row, col) tuples for valid neighbors
        """
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    neighbors.append((nr, nc))
        return neighbors

    def _generate_path(self) -> bool:
        """Generate a valid Hamiltonian path through the grid.

        Returns:
            True if path generation succeeded
        """
        # Use a greedy approach with random walks for efficiency
        # Start from a random position
        row = self._rng.randint(0, self.size - 1)
        col = self._rng.randint(0, self.size - 1)

        visited = set()
        path = []

        # Greedy walk through the grid
        for _ in range(self.total_numbers):
            visited.add((row, col))
            path.append((row, col))

            if len(path) == self.total_numbers:
                break

            # Find unvisited neighbors
            neighbors = self._get_neighbors(row, col)
            unvisited = [(r, c) for r, c in neighbors if (r, c) not in visited]

            if not unvisited:
                # Dead end - this attempt failed
                return False

            # Prefer neighbors with more unvisited neighbors (greedy heuristic)
            def count_unvisited_neighbors(pos: tuple[int, int]) -> int:
                r, c = pos
                neighs = self._get_neighbors(r, c)
                return sum(1 for nr, nc in neighs if (nr, nc) not in visited)

            # Sort by number of unvisited neighbors (descending)
            unvisited.sort(key=count_unvisited_neighbors, reverse=True)

            # Pick one of the best choices (add some randomness)
            if len(unvisited) > 1 and self._rng.random() < 0.3:
                # 30% chance to pick second-best to add variety
                row, col = unvisited[1] if len(unvisited) > 1 else unvisited[0]
            else:
                row, col = unvisited[0]

        # Fill solution grid with the path
        for i, (r, c) in enumerate(path, start=1):
            self.solution[r][c] = i

        return len(path) == self.total_numbers

    def _generate_serpentine_path(self) -> None:
        """Generate a serpentine (snake) path as a fallback.

        This always succeeds and creates a readable pattern.
        """
        num = 1
        for row in range(self.size):
            if row % 2 == 0:
                # Left to right
                for col in range(self.size):
                    self.solution[row][col] = num
                    num += 1
            else:
                # Right to left
                for col in range(self.size - 1, -1, -1):
                    self.solution[row][col] = num
                    num += 1

    async def generate_puzzle(self) -> None:
        """Generate a new Hidato puzzle."""
        # Try greedy generation a few times, then fallback to serpentine
        max_attempts = 50
        success = False
        for _ in range(max_attempts):
            self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]
            if self._generate_path():
                success = True
                break

        # If no success, use serpentine pattern (always works)
        if not success:
            self._generate_serpentine_path()

        # Create the puzzle by revealing some numbers
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Always reveal first and last numbers
        for r in range(self.size):
            for c in range(self.size):
                if self.solution[r][c] == 1:
                    self.grid[r][c] = 1
                elif self.solution[r][c] == self.total_numbers:
                    self.grid[r][c] = self.total_numbers

        # Reveal additional clue numbers based on difficulty
        num_clues = self.config.num_clues
        all_positions = [(r, c) for r in range(self.size) for c in range(self.size)]
        self._rng.shuffle(all_positions)

        revealed = 2  # Already revealed first and last
        for r, c in all_positions:
            if revealed >= num_clues:
                break
            if self.grid[r][c] == 0:  # Not already revealed
                self.grid[r][c] = self.solution[r][c]
                revealed += 1

        # Store initial state
        self.initial_grid = [row[:] for row in self.grid]
        self.moves_made = 0
        self.game_started = True

    async def validate_move(self, row: int, col: int, num: int) -> MoveResult:
        """Place a number on the grid.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            num: Number to place (1 to total_numbers, or 0 to clear)

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
        if not (1 <= num <= self.total_numbers):
            return MoveResult(success=False, message=f"Invalid number. Use 1-{self.total_numbers} or 0 to clear.")

        # Check if number is already used elsewhere
        for r in range(self.size):
            for c in range(self.size):
                if (r, c) != (row, col) and self.grid[r][c] == num:
                    return MoveResult(success=False, message=f"Number {num} is already used at ({r + 1},{c + 1}).")

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
                if self.grid[row][col] != self.solution[row][col]:
                    return False

        # Check adjacency (each number n must be adjacent to n+1)
        for num in range(1, self.total_numbers):
            # Find position of num
            pos_num = None
            pos_next = None

            for r in range(self.size):
                for c in range(self.size):
                    if self.grid[r][c] == num:
                        pos_num = (r, c)
                    if self.grid[r][c] == num + 1:
                        pos_next = (r, c)

            if pos_num is None or pos_next is None:
                return False

            # Check if they're adjacent
            neighbors = self._get_neighbors(pos_num[0], pos_num[1])
            if pos_next not in neighbors:
                return False

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        # Find an empty cell
        empty_cells = [(r, c) for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 0]
        if not empty_cells:
            return None

        # Prefer cells that have known neighbors
        for r, c in empty_cells:
            target_num = self.solution[r][c]
            neighbors = self._get_neighbors(r, c)

            # Check if this cell's number has placed neighbors
            for nr, nc in neighbors:
                if self.grid[nr][nc] in [target_num - 1, target_num + 1]:
                    hint_data = (r + 1, c + 1, target_num)
                    hint_message = f"Try placing {target_num} at row {r + 1}, column {c + 1}"
                    return hint_data, hint_message

        # Otherwise just give any empty cell
        r, c = self._rng.choice(empty_cells)
        target_num = self.solution[r][c]
        hint_data = (r + 1, c + 1, target_num)
        hint_message = f"Try placing {target_num} at row {r + 1}, column {c + 1}"
        return hint_data, hint_message

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        Returns:
            String representation of the puzzle grid
        """
        lines = []

        # Calculate cell width based on total numbers
        cell_width = len(str(self.total_numbers)) + 1

        # Header
        header = "  |"
        for c in range(self.size):
            header += f" {c + 1:^{cell_width}}"
        lines.append(header)
        lines.append("  +" + "-" * (cell_width + 1) * self.size)

        # Grid rows
        for r in range(self.size):
            row_str = f"{r + 1:2}|"
            for c in range(self.size):
                cell = self.grid[r][c]
                if cell == 0:
                    row_str += f" {'.':{cell_width}}"
                else:
                    # Mark initial clues differently
                    if self.initial_grid[r][c] != 0:
                        row_str += f" {cell:{cell_width}}"
                    else:
                        row_str += f" {cell:{cell_width}}"
            lines.append(row_str)

        lines.append("\nLegend: . = empty, numbers = placed/clues")
        lines.append(f"Goal: Fill grid with numbers 1-{self.total_numbers}, each adjacent to the next")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Hidato.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return f"""HIDATO (NUMBER SNAKE) RULES:
- Fill the grid with consecutive numbers from 1 to {self.total_numbers}
- Each number must be adjacent (horizontally, vertically, or diagonally) to the next number
- Some numbers are given as clues
- Create one continuous path through all cells
- Each number appears exactly once"""

    def get_commands(self) -> str:
        """Get the available commands for Hidato.

        Returns:
            Multi-line string describing available commands
        """
        return """HIDATO COMMANDS:
  place <row> <col> <num>  - Place a number (e.g., 'place 1 5 7')
  clear <row> <col>        - Clear a cell you've filled (same as 'place <row> <col> 0')
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
        return f"Moves made: {self.moves_made} | Filled: {filled}/{self.total_numbers} | Seed: {self.seed}"
