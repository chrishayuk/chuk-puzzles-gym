"""KenKen puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import KenKenConfig
from .enums import ArithmeticOperation
from .models import Cage


class KenKenGame(PuzzleGame):
    """KenKen (also known as Calcudoku or Mathdoku) puzzle game.

    Similar to Sudoku but uses arithmetic cages with operations.
    Each cage has a target number and an operation (+, -, *, /).
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new KenKen game.

        Args:
            difficulty: Game difficulty level (easy=4x4, medium=5x5, hard=6x6)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Grid size based on difficulty
        self.config = KenKenConfig.from_difficulty(self.difficulty)
        self.size = self.config.size

        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.initial_grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Cages: list of Cage objects
        self.cages: list[Cage] = []

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "KenKen"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Arithmetic cage puzzle - combine math and logic"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["all_different", "arithmetic_cages", "operations", "multi_operation_constraints"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["resource_groups", "operational_constraints", "mathematical_relationships", "grouped_calculations"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "medium", "constraint_density": "moderate"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = empty cells to fill."""
        return sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 0)

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for KenKen."""
        from ...models import DifficultyLevel

        empty = self.optimal_steps or 0
        total = self.size * self.size
        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 4,
            DifficultyLevel.HARD.value: 5,
        }.get(self.difficulty.value, 3)
        branching = 2.0 + (empty / total) * 3
        density = 1.0 - (empty / total) if total > 0 else 0.5
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
            num: Number to place (1 to self.size)
            grid: Grid to check against (defaults to self.grid)

        Returns:
            True if the move is valid, False otherwise
        """
        if grid is None:
            grid = self.grid

        # Check row uniqueness
        for c in range(self.size):
            if c != col and grid[row][c] == num:
                return False

        # Check column uniqueness
        for r in range(self.size):
            if r != row and grid[r][col] == num:
                return False

        return True

    def solve(self, grid: list[list[int]]) -> bool:
        """Solve the KenKen puzzle using backtracking.

        Args:
            grid: The KenKen grid to solve

        Returns:
            True if solved, False otherwise
        """
        for row in range(self.size):
            for col in range(self.size):
                if grid[row][col] == 0:
                    for num in range(1, self.size + 1):
                        grid[row][col] = num

                        if self.is_valid_move(row, col, num, grid) and self._check_cage_constraints(grid, row, col):
                            if self.solve(grid):
                                return True

                        grid[row][col] = 0

                    return False
        return True

    def _check_cage_constraints(self, grid: list[list[int]], row: int, col: int) -> bool:
        """Check if the cage containing (row, col) is still valid.

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
            cage_values = [grid[r][c] for r, c in cage.cells]

            # If cage is not fully filled, we can only do partial checking
            if 0 in cage_values:
                # For now, allow partial fills (optimistic checking)
                # More sophisticated pruning could be added here
                continue

            # All cells filled - check if operation gives target
            if not self._evaluate_cage(cage_values, cage.operation, cage.target):
                return False

        return True

    def _evaluate_cage(self, values: list[int], operation: ArithmeticOperation | None, target: int) -> bool:
        """Check if the cage operation evaluates to the target.

        Args:
            values: List of values in the cage
            operation: Operation to perform
            target: Target value

        Returns:
            True if operation on values equals target
        """
        if operation is None or operation == ArithmeticOperation.NONE:
            # Single cell cage
            return len(values) == 1 and values[0] == target

        if operation == ArithmeticOperation.ADD:
            return sum(values) == target

        if operation == ArithmeticOperation.MULTIPLY:
            result = 1
            for v in values:
                result *= v
            return result == target

        if operation == ArithmeticOperation.SUBTRACT:
            # Subtraction: target = larger - smaller (for 2 cells)
            if len(values) != 2:
                return False
            return abs(values[0] - values[1]) == target

        if operation == ArithmeticOperation.DIVIDE:
            # Division: target = larger / smaller (for 2 cells)
            if len(values) != 2:
                return False
            a, b = sorted(values, reverse=True)
            return b != 0 and a % b == 0 and a // b == target

        return False

    def _generate_cages(self) -> None:
        """Generate cages for the puzzle."""
        # Simple cage generation: create random connected regions
        used = [[False for _ in range(self.size)] for _ in range(self.size)]
        self.cages = []

        for row in range(self.size):
            for col in range(self.size):
                if used[row][col]:
                    continue

                # Start a new cage
                cage_size = self._rng.randint(1, 3)  # 1-3 cells per cage
                cells = [(row, col)]
                used[row][col] = True

                # Try to add more cells
                for _ in range(cage_size - 1):
                    # Find adjacent unused cells
                    candidates = []
                    for r, c in cells:
                        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.size and 0 <= nc < self.size and not used[nr][nc]:
                                candidates.append((nr, nc))

                    if candidates:
                        nr, nc = self._rng.choice(candidates)
                        cells.append((nr, nc))
                        used[nr][nc] = True

                # Determine operation and target from solution
                cage_values = [self.solution[r][c] for r, c in cells]

                if len(cells) == 1:
                    operation = None
                    target = cage_values[0]
                else:
                    # Choose operation based on cage size
                    if len(cells) == 2:
                        operations = [
                            ArithmeticOperation.ADD,
                            ArithmeticOperation.SUBTRACT,
                            ArithmeticOperation.MULTIPLY,
                            ArithmeticOperation.DIVIDE,
                        ]
                    else:
                        operations = [ArithmeticOperation.ADD, ArithmeticOperation.MULTIPLY]

                    operation = self._rng.choice(operations)

                    if operation == ArithmeticOperation.ADD:
                        target = sum(cage_values)
                    elif operation == ArithmeticOperation.MULTIPLY:
                        target = 1
                        for v in cage_values:
                            target *= v
                    elif operation == ArithmeticOperation.SUBTRACT:
                        target = abs(cage_values[0] - cage_values[1])
                    elif operation == ArithmeticOperation.DIVIDE:
                        a, b = sorted(cage_values, reverse=True)
                        if b == 0 or a % b != 0:
                            # Fallback to addition if division doesn't work
                            operation = ArithmeticOperation.ADD
                            target = sum(cage_values)
                        else:
                            target = a // b

                self.cages.append(Cage(cells=cells, operation=operation, target=target))

    async def generate_puzzle(self) -> None:
        """Generate a new KenKen puzzle."""
        # Generate a valid Latin square as solution
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Simple solution generation: shifted rows
        for row in range(self.size):
            for col in range(self.size):
                self.grid[row][col] = (row + col) % self.size + 1

        # Shuffle rows and columns to make it more random
        row_order = list(range(self.size))
        col_order = list(range(self.size))
        self._rng.shuffle(row_order)
        self._rng.shuffle(col_order)

        shuffled = [[self.grid[row_order[r]][col_order[c]] for c in range(self.size)] for r in range(self.size)]
        self.solution = shuffled

        # Generate cages
        self._generate_cages()

        # Empty the grid (KenKen starts completely empty)
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.initial_grid = [row[:] for row in self.grid]
        self.moves_made = 0
        self.game_started = True

    async def validate_move(self, row: int, col: int, num: int) -> MoveResult:
        """Place a number on the grid.

        Args:
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            num: Number to place (1 to self.size, or 0 to clear)

        Returns:
            MoveResult indicating success/failure and message
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate coordinates
        if not (0 <= row < self.size and 0 <= col < self.size):
            return MoveResult(success=False, message=f"Invalid coordinates. Use row and column between 1-{self.size}.")

        # Clear the cell
        if num == 0:
            self.grid[row][col] = 0
            return MoveResult(success=True, message="Cell cleared.", state_changed=True)

        # Validate number
        if not (1 <= num <= self.size):
            return MoveResult(success=False, message=f"Invalid number. Use 1-{self.size} or 0 to clear.")

        # Check if the move is valid
        old_value = self.grid[row][col]
        self.grid[row][col] = num

        if not self.is_valid_move(row, col, num):
            self.grid[row][col] = old_value
            return MoveResult(success=False, message="Invalid move! This number already exists in the row or column.")

        self.moves_made += 1
        return MoveResult(success=True, message="Number placed successfully!", state_changed=True)

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        # Check all cells filled
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] == 0:
                    return False

        # Check all cages
        for cage in self.cages:
            cage_values = [self.grid[r][c] for r, c in cage.cells]
            if not self._evaluate_cage(cage_values, cage.operation, cage.target):
                return False

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        empty_cells = [(r, c) for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 0]
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

        # Create a cage ID map for rendering
        cage_map = {}
        for cage_id, cage in enumerate(self.cages):
            for r, c in cage.cells:
                cage_map[(r, c)] = (cage_id, cage.operation, cage.target)

        # Determine cell width needed (accommodate cage labels)
        max_label_len = 0
        for cage in self.cages:
            op_str = cage.operation.value if cage.operation else ""
            label_len = len(f"{cage.target}{op_str}")
            max_label_len = max(max_label_len, label_len)

        # Cell width: 1 (space) + 1 (digit/.) + max_label_len, minimum 4
        cell_width = max(4, 2 + max_label_len)

        # Header - center column numbers within each cell width
        # Row format is "N |..." so header should be "  |..." to align pipes
        header = "  |"  # 2 spaces + pipe to match row format "N |"
        for i in range(self.size):
            col_num = str(i + 1)
            # Center the column number in the cell width
            padding_left = (cell_width - len(col_num)) // 2
            padding_right = cell_width - len(col_num) - padding_left
            cell_header = " " * padding_left + col_num + " " * padding_right
            header += cell_header + "|"
        lines.append(header)

        lines.append("  +" + ("-" * cell_width + "+") * self.size)

        for row in range(self.size):
            line = f"{row + 1} |"
            for col in range(self.size):
                cell = self.grid[row][col]

                # Start with the cell value
                if cell != 0:
                    cell_content = str(cell)
                else:
                    cell_content = "."
                    # Show cage info in first cell of cage (only if cell is empty)
                    cage_id, operation, target = cage_map.get((row, col), (None, None, None))
                    if cage_id is not None:
                        # Check if this is the first cell of the cage
                        cage_cells = self.cages[cage_id].cells
                        if (row, col) == min(cage_cells):
                            op_str = operation.value if operation else ""
                            cage_label = f"{target}{op_str}"
                            cell_content = f"{cell_content}{cage_label}"

                # Pad to fixed width (cell_width includes the border spacing)
                padded_content = f" {cell_content}".ljust(cell_width)
                line += f"{padded_content}|"
            lines.append(line)
            lines.append("  +" + ("-" * cell_width + "+") * self.size)

        # Show cage legend
        lines.append("\nCages:")
        for _cage_id, cage in enumerate(self.cages):
            op_str = cage.operation.value if cage.operation else ""
            cells_str = ", ".join(f"({r + 1},{c + 1})" for r, c in sorted(cage.cells))
            lines.append(f"  {cage.target}{op_str}: {cells_str}")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for KenKen.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return f"""KENKEN RULES:
- Fill {self.size}x{self.size} grid with 1-{self.size}
- No repeats in rows or columns
- Satisfy cage arithmetic constraints
- Operations: + - * /"""

    def get_commands(self) -> str:
        """Get the available commands for KenKen.

        Returns:
            Multi-line string describing available commands
        """
        return """KENKEN COMMANDS:
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
        empty = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 0)
        return f"Moves made: {self.moves_made} | Empty cells: {empty} | Grid size: {self.size}x{self.size} | Seed: {self.seed}"
