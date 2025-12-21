"""Killer Sudoku puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import KillerSudokuConfig
from .models import Cage


class KillerSudokuGame(PuzzleGame):
    """Killer Sudoku puzzle game.

    Combination of Sudoku and Kakuro - fill grid with 1-9
    where regions sum to target values.
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Killer Sudoku game.

        Args:
            difficulty: Game difficulty level (easy/medium/hard)
        """
        super().__init__(difficulty, seed, **kwargs)

        self.config = KillerSudokuConfig.from_difficulty(self.difficulty)
        self.size = 9
        self.grid = [[0 for _ in range(9)] for _ in range(9)]
        self.solution = [[0 for _ in range(9)] for _ in range(9)]
        self.initial_grid = [[0 for _ in range(9)] for _ in range(9)]

        # Cages: list of Cage objects
        self.cages: list[Cage] = []

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Killer Sudoku"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Sudoku + Kakuro - regions must sum to targets"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["all_different", "cage_sums", "linear_constraints", "uniqueness"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["grouped_constraints", "sum_budgeting", "allocation_with_quotas"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "large", "constraint_density": "dense"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = empty cells to fill."""
        return sum(1 for r in range(9) for c in range(9) if self.grid[r][c] == 0)

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Killer Sudoku."""
        from ...models import DifficultyLevel

        empty = self.optimal_steps or 0
        logic_depth = {
            DifficultyLevel.EASY.value: 3,
            DifficultyLevel.MEDIUM.value: 5,
            DifficultyLevel.HARD.value: 7,
        }.get(self.difficulty.value, 4)
        branching = 2.5 + (empty / 81) * 4
        density = 1.0 - (empty / 81)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=round(branching, 1),
            state_observability=1.0,
            constraint_density=round(density, 2),
        )

    def is_valid_move(self, row: int, col: int, num: int, grid: list[list[int]] | None = None) -> bool:
        """Check if placing num at (row, col) is valid.

        Args:
            row: Row index (0-indexed)
            col: Column index (0-indexed)
            num: Number to place (1-9)
            grid: Grid to check against (defaults to self.grid)

        Returns:
            True if the move is valid, False otherwise
        """
        if grid is None:
            grid = self.grid

        # Check row uniqueness
        for c in range(9):
            if c != col and grid[row][c] == num:
                return False

        # Check column uniqueness
        for r in range(9):
            if r != row and grid[r][col] == num:
                return False

        # Check 3x3 box uniqueness
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for r in range(box_row, box_row + 3):
            for c in range(box_col, box_col + 3):
                if (r != row or c != col) and grid[r][c] == num:
                    return False

        return True

    def solve(self, grid: list[list[int]]) -> bool:
        """Solve the Killer Sudoku puzzle using backtracking.

        Args:
            grid: The Killer Sudoku grid to solve

        Returns:
            True if solved, False otherwise
        """
        for row in range(9):
            for col in range(9):
                if grid[row][col] == 0:
                    for num in range(1, 10):
                        if self.is_valid_move(row, col, num, grid):
                            grid[row][col] = num

                            # Check cage constraints
                            if self._check_cage_constraints(grid, row, col):
                                if self.solve(grid):
                                    return True

                            grid[row][col] = 0

                    return False
        return True

    def _check_cage_constraints(self, grid: list[list[int]], row: int, col: int) -> bool:
        """Check if cage constraints are satisfied.

        Args:
            grid: Current grid state
            row: Row of the cell that was just filled
            col: Column of the cell that was just filled

        Returns:
            True if cage constraints are satisfied or could be satisfied
        """
        # Find which cage contains this cell
        for cage in self.cages:
            if (row, col) not in cage.cells:
                continue

            # Get all values in the cage
            cage_values = []
            filled_count = 0
            for r, c in cage.cells:
                val = grid[r][c]
                if val != 0:
                    cage_values.append(val)
                    filled_count += 1

            # Check for duplicates within cage
            if len(cage_values) != len(set(cage_values)):
                return False

            # If cage is not fully filled, check if we haven't exceeded target
            if filled_count < len(cage.cells):
                current_sum = sum(cage_values)
                if current_sum >= cage.target:
                    return False
            else:
                # All cells filled - check if sum matches target
                if sum(cage_values) != cage.target:
                    return False

        return True

    def _generate_cages(self) -> None:
        """Generate cages for the puzzle.

        In Killer Sudoku, each cage must have unique values.
        """
        used = [[False for _ in range(9)] for _ in range(9)]
        self.cages = []

        for row in range(9):
            for col in range(9):
                if used[row][col]:
                    continue

                # Start a new cage
                cage_size = self._rng.randint(2, 4)  # 2-4 cells per cage
                cells = [(row, col)]
                cage_values = {self.solution[row][col]}
                used[row][col] = True

                # Try to add more cells (must have unique values)
                for _ in range(cage_size - 1):
                    # Find adjacent unused cells with unique values
                    candidates = []
                    for r, c in cells:
                        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 9 and 0 <= nc < 9 and not used[nr][nc]:
                                if (nr, nc) not in candidates:
                                    # Check if value is unique in this cage
                                    if self.solution[nr][nc] not in cage_values:
                                        candidates.append((nr, nc))

                    if candidates:
                        nr, nc = self._rng.choice(candidates)
                        cells.append((nr, nc))
                        cage_values.add(self.solution[nr][nc])
                        used[nr][nc] = True
                    else:
                        # No valid adjacent cells available
                        break

                # If cage is still size 1, try to merge with an adjacent cage
                if len(cells) == 1:
                    r, c = cells[0]
                    cell_value = self.solution[r][c]
                    merged = False
                    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 9 and 0 <= nc < 9:
                            for cage_idx, cage in enumerate(self.cages):
                                if (nr, nc) in cage.cells:
                                    # Check if we can merge without duplicating values
                                    cage_vals = {self.solution[cr][cc] for cr, cc in cage.cells}
                                    if cell_value not in cage_vals:
                                        new_cells = list(cage.cells)
                                        new_cells.append((r, c))
                                        new_sum = sum(self.solution[cr][cc] for cr, cc in new_cells)
                                        self.cages[cage_idx] = Cage(cells=new_cells, operation=None, target=new_sum)
                                        merged = True
                                        break
                        if merged:
                            break

                    if not merged:
                        # Couldn't merge, add as size-1 cage
                        target_sum = self.solution[r][c]
                        self.cages.append(Cage(cells=cells, operation=None, target=target_sum))
                else:
                    # Calculate target sum from solution
                    target_sum = sum(self.solution[r][c] for r, c in cells)
                    self.cages.append(Cage(cells=cells, operation=None, target=target_sum))

    async def generate_puzzle(self) -> None:
        """Generate a new Killer Sudoku puzzle."""
        # Generate a valid Sudoku solution
        self.grid = [[0 for _ in range(9)] for _ in range(9)]

        # Base valid Sudoku pattern
        for row in range(9):
            for col in range(9):
                self.grid[row][col] = (row * 3 + row // 3 + col) % 9 + 1

        # Shuffle rows within bands and columns within stacks to maintain validity
        for band in range(3):
            # Shuffle rows within this band
            rows_in_band = [band * 3, band * 3 + 1, band * 3 + 2]
            shuffled_rows = rows_in_band[:]
            self._rng.shuffle(shuffled_rows)
            # Swap rows
            temp = [self.grid[shuffled_rows[0]][:], self.grid[shuffled_rows[1]][:], self.grid[shuffled_rows[2]][:]]
            for i, r in enumerate(rows_in_band):
                self.grid[r] = temp[i]

        for stack in range(3):
            # Shuffle columns within this stack
            cols_in_stack = [stack * 3, stack * 3 + 1, stack * 3 + 2]
            shuffled_cols = cols_in_stack[:]
            self._rng.shuffle(shuffled_cols)
            # Swap columns
            for row in range(9):
                col_temp = [
                    self.grid[row][shuffled_cols[0]],
                    self.grid[row][shuffled_cols[1]],
                    self.grid[row][shuffled_cols[2]],
                ]
                for i, c in enumerate(cols_in_stack):
                    self.grid[row][c] = col_temp[i]

        # Also shuffle digit mapping for more variety
        digit_map = list(range(1, 10))
        self._rng.shuffle(digit_map)
        for row in range(9):
            for col in range(9):
                self.grid[row][col] = digit_map[self.grid[row][col] - 1]

        self.solution = [row[:] for row in self.grid]

        # Generate cages
        self._generate_cages()

        # Empty the grid (Killer Sudoku starts completely empty)
        self.grid = [[0 for _ in range(9)] for _ in range(9)]
        self.initial_grid = [row[:] for row in self.grid]
        self.moves_made = 0
        self.game_started = True

    async def validate_move(self, row: int, col: int, num: int) -> MoveResult:
        """Place a number on the grid.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            num: Number to place (1-9, or 0 to clear)

        Returns:
            MoveResult indicating success or failure
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < 9 and 0 <= col < 9):
            return MoveResult(success=False, message="Invalid coordinates. Use row and column between 1-9.")

        # Clear the cell
        if num == 0:
            self.grid[row][col] = 0
            return MoveResult(success=True, message="Cell cleared.", state_changed=True)

        # Validate number
        if not (1 <= num <= 9):
            return MoveResult(success=False, message="Invalid number. Use 1-9 or 0 to clear.")

        # Check if the move is valid
        old_value = self.grid[row][col]
        self.grid[row][col] = num

        if not self.is_valid_move(row, col, num):
            self.grid[row][col] = old_value
            return MoveResult(
                success=False, message="Invalid move! This number already exists in the row, column, or box."
            )

        self.moves_made += 1
        return MoveResult(success=True, message="Number placed successfully!", state_changed=True)

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        # Check all cells filled
        for row in range(9):
            for col in range(9):
                if self.grid[row][col] == 0:
                    return False

        # Check Sudoku constraints (rows, columns, boxes)
        for row in range(9):
            if len(set(self.grid[row])) != 9:
                return False

        for col in range(9):
            column = [self.grid[row][col] for row in range(9)]
            if len(set(column)) != 9:
                return False

        for box_row in range(3):
            for box_col in range(3):
                box = []
                for r in range(box_row * 3, box_row * 3 + 3):
                    for c in range(box_col * 3, box_col * 3 + 3):
                        box.append(self.grid[r][c])
                if len(set(box)) != 9:
                    return False

        # Check all cages
        for cage in self.cages:
            cage_values = [self.grid[r][c] for r, c in cage.cells]
            # Check for duplicates
            if len(cage_values) != len(set(cage_values)):
                return False
            # Check sum
            if sum(cage_values) != cage.target:
                return False

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        empty_cells = [(r, c) for r in range(9) for c in range(9) if self.grid[r][c] == 0]
        if not empty_cells:
            return None

        row, col = self._rng.choice(empty_cells)
        hint_data = (row + 1, col + 1, self.solution[row][col])
        hint_message = f"Try placing {self.solution[row][col]} at row {row + 1}, column {col + 1}"
        return hint_data, hint_message

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        Returns:
            String representation of the puzzle grid with cages
        """
        lines = []

        # Create a cage ID map
        cage_map = {}
        for cage_id, cage in enumerate(self.cages):
            for r, c in cage.cells:
                cage_map[(r, c)] = (cage_id, cage.target)

        # Header
        lines.append("  | 1 2 3 | 4 5 6 | 7 8 9 |")
        lines.append("  +" + "-" * 7 + "+" + "-" * 7 + "+" + "-" * 7 + "+")

        for row in range(9):
            if row > 0 and row % 3 == 0:
                lines.append("  +" + "-" * 7 + "+" + "-" * 7 + "+" + "-" * 7 + "+")

            line = f"{row + 1} |"
            for col in range(9):
                if col > 0 and col % 3 == 0:
                    line += " |"

                cell = self.grid[row][col]
                if cell == 0:
                    # Show cage sum in top-left cell of each cage
                    cage_id, target_sum = cage_map.get((row, col), (None, None))
                    if cage_id is not None:
                        cage_cells = self.cages[cage_id].cells
                        if (row, col) == min(cage_cells):
                            line += f" {target_sum:2d}" if target_sum < 100 else f"{target_sum}"
                        else:
                            line += " ."
                    else:
                        line += " ."
                else:
                    line += f" {cell}"
            line += " |"
            lines.append(line)

        lines.append("  +" + "-" * 7 + "+" + "-" * 7 + "+" + "-" * 7 + "+")

        # Show cage info
        lines.append("\nCages (sum targets):")
        for _i, cage in enumerate(self.cages[:10]):  # Show first 10
            cells_str = ", ".join(f"({r + 1},{c + 1})" for r, c in sorted(cage.cells)[:3])
            if len(cage.cells) > 3:
                cells_str += "..."
            lines.append(f"  {cage.target}: {cells_str}")
        if len(self.cages) > 10:
            lines.append(f"  ... and {len(self.cages) - 10} more cages")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Killer Sudoku.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return """KILLER SUDOKU RULES:
- Fill 9×9 grid with digits 1-9
- No repeats in rows, columns, or 3×3 boxes
- Numbers in each cage must sum to the target
- No repeated digits within a cage"""

    def get_commands(self) -> str:
        """Get the available commands for Killer Sudoku.

        Returns:
            Multi-line string describing available commands
        """
        return """KILLER SUDOKU COMMANDS:
  place <row> <col> <num>  - Place a number (e.g., 'place 1 2 4')
  clear <row> <col>        - Clear a cell
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
        empty = sum(1 for r in range(9) for c in range(9) if self.grid[r][c] == 0)
        return (
            f"Moves made: {self.moves_made} | Empty cells: {empty} | Total cages: {len(self.cages)} | Seed: {self.seed}"
        )
