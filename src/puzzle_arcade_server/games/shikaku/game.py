"""Shikaku (Rectangles) puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame


class ShikakuGame(PuzzleGame):
    """Shikaku (Rectangles) puzzle game.

    Divide the grid into rectangles such that:
    - Each rectangle contains exactly one number
    - The number indicates the area of that rectangle
    - All cells must be covered by rectangles
    - Rectangles cannot overlap
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Shikaku game.

        Args:
            difficulty: Game difficulty level (easy, medium, hard)
        """
        super().__init__(difficulty, seed, **kwargs)

        from ...models import DifficultyLevel

        # Set grid size based on difficulty
        self.size = {
            DifficultyLevel.EASY.value: 6,
            DifficultyLevel.MEDIUM.value: 8,
            DifficultyLevel.HARD.value: 10,
        }.get(self.difficulty.value, 6)

        # Grid stores the clue numbers (0 = no clue)
        self.grid: list[list[int]] = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Solution stores rectangle IDs (each rectangle has a unique ID)
        self.solution: list[list[int]] = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Player's rectangles (rectangle_id -> list of (row, col) cells)
        self.rectangles: dict[int, list[tuple[int, int]]] = {}
        self.next_rect_id = 1

        # Store clue positions for validation
        self.clues: dict[tuple[int, int], int] = {}

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Shikaku"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Divide grid into rectangles matching the given areas"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["partition", "area_constraints", "rectangle_tiling", "non_overlapping", "coverage"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["space_allocation", "territory_division", "resource_partitioning", "layout_optimization"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "large", "constraint_density": "moderate"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = rectangles to create."""
        if not hasattr(self, "solution") or not self.solution:
            return None
        return max(max(row) for row in self.solution) if self.solution else None

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Shikaku."""
        from ...models import DifficultyLevel

        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 4,
            DifficultyLevel.HARD.value: 5,
        }.get(self.difficulty.value, 3)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=5.0,  # Many rectangle possibilities
            state_observability=1.0,
            constraint_density=0.5,
        )

    async def generate_puzzle(self) -> None:
        """Generate a new Shikaku puzzle with retry logic."""
        max_attempts = 50

        for _attempt in range(max_attempts):
            # Reset state
            self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
            self.solution = [[0 for _ in range(self.size)] for _ in range(self.size)]
            self.clues = {}

            # Step 1: Generate solution by creating rectangles
            if self._generate_rectangles():
                # Step 2: Validate puzzle
                if self._validate_puzzle():
                    self.game_started = True
                    return

        # Fallback: use last attempt
        self.game_started = True

    def _generate_rectangles(self) -> bool:
        """Generate rectangles to fill the grid."""
        rect_id = 1
        remaining_cells = {(r, c) for r in range(self.size) for c in range(self.size)}

        # Use strategic starting points (grid positions) for better coverage
        start_positions = []
        step = max(2, self.size // 3)
        for r in range(0, self.size, step):
            for c in range(0, self.size, step):
                start_positions.append((r, c))
        self._rng.shuffle(start_positions)

        attempts = 0
        max_rect_attempts = 100

        while remaining_cells and attempts < max_rect_attempts:
            attempts += 1

            # Try strategic positions first, then random
            if start_positions:
                # Filter start positions to only uncovered cells
                valid_starts = [pos for pos in start_positions if pos in remaining_cells]
                if valid_starts:
                    r, c = self._rng.choice(valid_starts)
                else:
                    r, c = self._rng.choice(list(remaining_cells))
            else:
                r, c = self._rng.choice(list(remaining_cells))

            # Determine maximum rectangle size
            max_width = 1
            while c + max_width < self.size and (r, c + max_width) in remaining_cells:
                max_width += 1

            max_height = 1
            while r + max_height < self.size and (r + max_height, c) in remaining_cells:
                max_height += 1

            # Choose dimensions (prefer reasonable sizes)
            max_dim = 4
            width = self._rng.randint(1, min(max_width, max_dim))
            height = self._rng.randint(1, min(max_height, max_dim))

            # Ensure the rectangle fits
            valid = True
            rect_cells = []
            for dr in range(height):
                for dc in range(width):
                    nr, nc = r + dr, c + dc
                    if nr >= self.size or nc >= self.size or (nr, nc) not in remaining_cells:
                        valid = False
                        break
                    rect_cells.append((nr, nc))
                if not valid:
                    break

            if valid and rect_cells:
                # Mark these cells with the rectangle ID
                for nr, nc in rect_cells:
                    self.solution[nr][nc] = rect_id
                    remaining_cells.remove((nr, nc))

                # Place the clue number in a random cell within the rectangle
                clue_r, clue_c = self._rng.choice(rect_cells)
                area = width * height
                self.grid[clue_r][clue_c] = area
                self.clues[(clue_r, clue_c)] = area

                rect_id += 1
            else:
                # If we can't create a valid rectangle, just use a single cell
                self.solution[r][c] = rect_id
                self.grid[r][c] = 1
                self.clues[(r, c)] = 1
                remaining_cells.remove((r, c))
                rect_id += 1

        return len(remaining_cells) == 0

    def _validate_puzzle(self) -> bool:
        """Validate that the generated puzzle is valid."""
        # Check all cells are covered
        for r in range(self.size):
            for c in range(self.size):
                if self.solution[r][c] == 0:
                    return False

        # Check each clue matches its rectangle area
        for (clue_r, clue_c), area in self.clues.items():
            rect_id = self.solution[clue_r][clue_c]
            rect_cells = sum(1 for r in range(self.size) for c in range(self.size) if self.solution[r][c] == rect_id)

            if rect_cells != area:
                return False

        # Check no rectangle has multiple clues
        rect_clue_count: dict[int, int] = {}
        for (r, c), _area in self.clues.items():
            rect_id = self.solution[r][c]
            rect_clue_count[rect_id] = rect_clue_count.get(rect_id, 0) + 1

        for count in rect_clue_count.values():
            if count != 1:
                return False

        return True

    async def validate_move(self, *args: Any, **kwargs: Any) -> MoveResult:
        """Validate a rectangle placement move.

        Args:
            args[0]: Top-left row (1-indexed)
            args[1]: Top-left column (1-indexed)
            args[2]: Bottom-right row (1-indexed)
            args[3]: Bottom-right column (1-indexed)

        Returns:
            MoveResult containing success status and message
        """
        if len(args) < 4:
            return MoveResult(success=False, message="Usage: place <top_row> <top_col> <bottom_row> <bottom_col>")

        try:
            r1, c1, r2, c2 = int(args[0]) - 1, int(args[1]) - 1, int(args[2]) - 1, int(args[3]) - 1
        except (ValueError, IndexError):
            return MoveResult(success=False, message="Invalid coordinates")

        # Normalize coordinates
        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1

        # Validate coordinates
        if not (0 <= r1 <= r2 < self.size and 0 <= c1 <= c2 < self.size):
            return MoveResult(success=False, message="Coordinates out of range")

        # Check if cells are already covered
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                for rect_id, cells in self.rectangles.items():
                    if (r, c) in cells:
                        return MoveResult(
                            success=False,
                            message=f"Cell ({r + 1},{c + 1}) is already covered by rectangle {rect_id}",
                        )

        # Find if rectangle contains exactly one clue
        clue_count = 0
        clue_value = 0
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if (r, c) in self.clues:
                    clue_count += 1
                    clue_value = self.clues[(r, c)]

        if clue_count == 0:
            return MoveResult(success=False, message="Rectangle must contain exactly one clue number")
        if clue_count > 1:
            return MoveResult(success=False, message="Rectangle contains multiple clue numbers")

        # Check if area matches the clue
        width = c2 - c1 + 1
        height = r2 - r1 + 1
        area = width * height

        if area != clue_value:
            return MoveResult(success=False, message=f"Rectangle area ({area}) doesn't match clue ({clue_value})")

        # Place the rectangle
        cells = [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]
        self.rectangles[self.next_rect_id] = cells
        self.next_rect_id += 1
        self.moves_made += 1

        return MoveResult(success=True, message=f"Rectangle placed (area {area})")

    def is_complete(self) -> bool:
        """Check if the puzzle is completely and correctly solved."""
        # Check that all cells are covered
        covered_cells = set()
        for cells in self.rectangles.values():
            for cell in cells:
                if cell in covered_cells:
                    return False  # Overlapping rectangles
                covered_cells.add(cell)

        # Check if all cells are covered
        total_cells = self.size * self.size
        if len(covered_cells) != total_cells:
            return False

        # Check that each rectangle contains exactly one clue with matching area
        for cells in self.rectangles.values():
            clue_count = 0
            clue_value = 0
            for r, c in cells:
                if (r, c) in self.clues:
                    clue_count += 1
                    clue_value = self.clues[(r, c)]

            if clue_count != 1:
                return False

            if len(cells) != clue_value:
                return False

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move."""
        # Find a rectangle from the solution that hasn't been placed yet
        solution_rects: dict[int, list[tuple[int, int]]] = {}
        for r in range(self.size):
            for c in range(self.size):
                rect_id = self.solution[r][c]
                if rect_id not in solution_rects:
                    solution_rects[rect_id] = []
                solution_rects[rect_id].append((r, c))

        # Check which solution rectangles haven't been placed
        for cells in solution_rects.values():
            # Check if any cell in this rectangle is not yet covered
            is_placed = False
            for r, c in cells:
                for placed_cells in self.rectangles.values():
                    if (r, c) in placed_cells:
                        is_placed = True
                        break
                if is_placed:
                    break

            if not is_placed:
                # Found an unplaced rectangle
                min_r = min(r for r, c in cells)
                max_r = max(r for r, c in cells)
                min_c = min(c for r, c in cells)
                max_c = max(c for r, c in cells)

                return (
                    (min_r + 1, min_c + 1, max_r + 1, max_c + 1),
                    f"Try rectangle from ({min_r + 1},{min_c + 1}) to ({max_r + 1},{max_c + 1})",
                )

        return None

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art."""
        lines = []

        # Create a display grid showing rectangles
        display = [[" . " for _ in range(self.size)] for _ in range(self.size)]

        # Place clue numbers
        for (r, c), value in self.clues.items():
            display[r][c] = f" {value:2d}"

        # Mark placed rectangles with letters
        rect_ids = sorted(self.rectangles.keys())
        for idx, rect_id in enumerate(rect_ids):
            letter = chr(65 + (idx % 26))  # A, B, C, ...
            for r, c in self.rectangles[rect_id]:
                if (r, c) not in self.clues:
                    display[r][c] = f" {letter} "

        # Header
        header = "  |"
        for c in range(self.size):
            header += f" {c + 1:2d}"
        lines.append(header)
        lines.append("  +" + "---" * self.size)

        # Grid rows
        for r in range(self.size):
            row = f"{r + 1:2d}|"
            for c in range(self.size):
                row += display[r][c]
            lines.append(row)

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for this puzzle type."""
        return """SHIKAKU (RECTANGLES) RULES:
- Divide the grid into rectangles
- Each rectangle must contain exactly one number
- The number shows the area (width × height) of that rectangle
- All cells must be covered by rectangles
- Rectangles cannot overlap
- Placed rectangles are marked with letters (A, B, C, ...)"""

    def get_commands(self) -> str:
        """Get the available commands for this puzzle type."""
        return """SHIKAKU COMMANDS:
  place <r1> <c1> <r2> <c2> - Draw rectangle from top-left to bottom-right
  Example: place 1 1 2 3  (creates 2×3 rectangle)
  hint   - Get a hint for the next move
  check  - Check if puzzle is complete
  solve  - Show the solution
  menu   - Return to main menu
  quit   - Exit the game"""
