"""Slitherlink puzzle game implementation."""

from typing import Any

from ...models import DifficultyLevel, DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import SlitherlinkConfig


class SlitherlinkGame(PuzzleGame):
    """Slitherlink puzzle game.

    Draw a single continuous loop by connecting dots.
    Numbers indicate how many edges around that cell are part of the loop.
    The loop must not branch or cross itself.
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Slitherlink game.

        Args:
            difficulty: Game difficulty level (easy/medium/hard)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Grid configuration
        self.config = SlitherlinkConfig.from_difficulty(self.difficulty)
        self.size = self.config.size

        # Clue grid: -1 = no clue, 0-3 = number of edges
        self.clues = [[-1 for _ in range(self.size)] for _ in range(self.size)]

        # Edge states: 0 = unknown, 1 = line, 2 = no line (X)
        # Horizontal edges: (size+1) rows x size columns
        self.h_edges = [[0 for _ in range(self.size)] for _ in range(self.size + 1)]
        # Vertical edges: size rows x (size+1) columns
        self.v_edges = [[0 for _ in range(self.size + 1)] for _ in range(self.size)]

        # Solution edges
        self.solution_h_edges = [[0 for _ in range(self.size)] for _ in range(self.size + 1)]
        self.solution_v_edges = [[0 for _ in range(self.size + 1)] for _ in range(self.size)]

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Slitherlink"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Draw a single loop - numbers show edge counts"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["global_loop", "local_counting", "topological", "uniqueness"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["circuit_design", "routing", "loop_detection"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "exponential", "constraint_density": "moderate"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = line segments to draw."""
        if not hasattr(self, "solution_h_edges") or not hasattr(self, "solution_v_edges"):
            return None
        h_lines = sum(sum(row) for row in self.solution_h_edges)
        v_lines = sum(sum(row) for row in self.solution_v_edges)
        return h_lines + v_lines

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Slitherlink."""

        logic_depth = {
            DifficultyLevel.EASY.value: 3,
            DifficultyLevel.MEDIUM.value: 5,
            DifficultyLevel.HARD.value: 7,
        }.get(self.difficulty.value, 4)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=4.0,  # 4 edges per cell
            state_observability=1.0,
            constraint_density=0.6,
        )

    def _generate_simple_loop(self) -> None:
        """Generate a simple rectangular loop as the solution."""
        # Create a simple rectangular loop for testing
        # This is a simplified generator - a full implementation would
        # use more sophisticated loop generation algorithms

        # For a simple version, create a border loop
        for col in range(self.size):
            self.solution_h_edges[0][col] = 1  # Top edge
            self.solution_h_edges[self.size][col] = 1  # Bottom edge

        for row in range(self.size):
            self.solution_v_edges[row][0] = 1  # Left edge
            self.solution_v_edges[row][self.size] = 1  # Right edge

    def _count_edges_around_cell(self, row: int, col: int, h_edges: list[list[int]], v_edges: list[list[int]]) -> int:
        """Count edges around a cell in the given edge configuration.

        Args:
            row: Cell row
            col: Cell column
            h_edges: Horizontal edges grid
            v_edges: Vertical edges grid

        Returns:
            Number of edges around the cell (0-4)
        """
        count = 0
        # Top edge
        if h_edges[row][col] == 1:
            count += 1
        # Bottom edge
        if h_edges[row + 1][col] == 1:
            count += 1
        # Left edge
        if v_edges[row][col] == 1:
            count += 1
        # Right edge
        if v_edges[row][col + 1] == 1:
            count += 1
        return count

    async def generate_puzzle(self) -> None:
        """Generate a new Slitherlink puzzle."""
        # Generate solution loop
        self._generate_simple_loop()

        # Generate clues based on solution
        # Place clues based on difficulty
        num_clues_map = {
            DifficultyLevel.EASY: self.size * 2,
            DifficultyLevel.MEDIUM: self.size * 3,
            DifficultyLevel.HARD: self.size * 4,
        }
        num_clues = num_clues_map[self.difficulty]

        placed = 0
        attempts = 0
        max_attempts = num_clues * 10

        while placed < num_clues and attempts < max_attempts:
            row = self._rng.randint(0, self.size - 1)
            col = self._rng.randint(0, self.size - 1)

            if self.clues[row][col] == -1:  # No clue yet
                edge_count = self._count_edges_around_cell(row, col, self.solution_h_edges, self.solution_v_edges)
                # Place clue
                self.clues[row][col] = edge_count
                placed += 1

            attempts += 1

        # Reset player edges
        self.h_edges = [[0 for _ in range(self.size)] for _ in range(self.size + 1)]
        self.v_edges = [[0 for _ in range(self.size + 1)] for _ in range(self.size)]

        self.moves_made = 0
        self.game_started = True

    async def validate_move(self, edge_type: str, row: int, col: int, state: int) -> MoveResult:
        """Set an edge state.

        Args:
            edge_type: 'h' for horizontal, 'v' for vertical
            row: Row index (1-indexed, user-facing)
            col: Column index (1-indexed, user-facing)
            state: 0=unknown, 1=line, 2=no line (X)

        Returns:
            MoveResult with success status and message
        """
        # Convert to 0-indexed
        row -= 1
        col -= 1

        # Validate state
        if state not in [0, 1, 2]:
            return MoveResult(success=False, message="Invalid state. Use 0=clear, 1=line, 2=X")

        # Validate edge type and coordinates
        if edge_type.lower() == "h":
            if not (0 <= row <= self.size and 0 <= col < self.size):
                return MoveResult(
                    success=False, message=f"Invalid horizontal edge. Row: 1-{self.size + 1}, Col: 1-{self.size}"
                )
            self.h_edges[row][col] = state
            edge_name = "horizontal"
        elif edge_type.lower() == "v":
            if not (0 <= row < self.size and 0 <= col <= self.size):
                return MoveResult(
                    success=False, message=f"Invalid vertical edge. Row: 1-{self.size}, Col: 1-{self.size + 1}"
                )
            self.v_edges[row][col] = state
            edge_name = "vertical"
        else:
            return MoveResult(success=False, message="Invalid edge type. Use 'h' or 'v'")

        self.moves_made += 1

        state_name = {0: "cleared", 1: "set to line", 2: "marked as X"}[state]
        return MoveResult(
            success=True,
            message=f"{edge_name.capitalize()} edge ({row + 1},{col + 1}) {state_name}",
            state_changed=True,
        )

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        # Check all clues are satisfied
        for row in range(self.size):
            for col in range(self.size):
                if self.clues[row][col] != -1:
                    edge_count = self._count_edges_around_cell(row, col, self.h_edges, self.v_edges)
                    if edge_count != self.clues[row][col]:
                        return False

        # Check that we have a valid loop (simplified check)
        # Count total edges - should be > 0 and even
        total_edges = sum(sum(1 for e in row if e == 1) for row in self.h_edges)
        total_edges += sum(sum(1 for e in row if e == 1) for row in self.v_edges)

        if total_edges == 0:
            return False

        # Check each vertex has 0 or 2 edges (no branches)
        for dot_row in range(self.size + 1):
            for dot_col in range(self.size + 1):
                edges = 0

                # Count edges connected to this dot
                # Horizontal edge to the left (row=dot_row, col=dot_col-1)
                if dot_col > 0:
                    if self.h_edges[dot_row][dot_col - 1] == 1:
                        edges += 1

                # Horizontal edge to the right (row=dot_row, col=dot_col)
                if dot_col < self.size:
                    if self.h_edges[dot_row][dot_col] == 1:
                        edges += 1

                # Vertical edge above (row=dot_row-1, col=dot_col)
                if dot_row > 0:
                    if self.v_edges[dot_row - 1][dot_col] == 1:
                        edges += 1

                # Vertical edge below (row=dot_row, col=dot_col)
                if dot_row < self.size:
                    if self.v_edges[dot_row][dot_col] == 1:
                        edges += 1

                # Each vertex must have exactly 0 or 2 edges (part of loop or not)
                if edges != 0 and edges != 2:
                    return False

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None
        """
        # Find an edge that's in the solution but not set by player
        for row in range(self.size + 1):
            for col in range(self.size):
                if self.solution_h_edges[row][col] == 1 and self.h_edges[row][col] != 1:
                    hint_data = ("h", row + 1, col + 1, 1)
                    hint_message = f"Try setting horizontal edge at ({row + 1},{col + 1}) to line"
                    return hint_data, hint_message

        for row in range(self.size):
            for col in range(self.size + 1):
                if self.solution_v_edges[row][col] == 1 and self.v_edges[row][col] != 1:
                    hint_data = ("v", row + 1, col + 1, 1)
                    hint_message = f"Try setting vertical edge at ({row + 1},{col + 1}) to line"
                    return hint_data, hint_message

        return None

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        Returns:
            String representation of the puzzle grid
        """
        lines = []

        # Render grid with dots and edges
        for row in range(self.size + 1):
            # Horizontal edges row
            if row <= self.size:
                h_line = "  "
                for col in range(self.size):
                    h_line += "+"
                    # Horizontal edge
                    if row < self.size + 1:
                        edge = self.h_edges[row][col]
                        if edge == 1:
                            h_line += "---"
                        elif edge == 2:
                            h_line += " X "
                        else:
                            h_line += "   "
                h_line += "+"
                lines.append(h_line)

            # Vertical edges and cells row
            if row < self.size:
                v_line = "  "
                for col in range(self.size + 1):
                    # Vertical edge
                    if col <= self.size:
                        edge = self.v_edges[row][col]
                        if edge == 1:
                            v_line += "|"
                        elif edge == 2:
                            v_line += "X"
                        else:
                            v_line += " "

                    # Cell content (clue)
                    if col < self.size:
                        clue = self.clues[row][col]
                        if clue == -1:
                            v_line += "   "
                        else:
                            v_line += f" {clue} "

                lines.append(v_line)

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Slitherlink.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return """SLITHERLINK RULES:
- Draw a single continuous loop by connecting dots
- Numbers show how many edges around that cell are part of the loop
- The loop must not branch or cross itself
- Each dot connects to exactly 0 or 2 edges
- Empty cells have no constraint on edge count"""

    def get_commands(self) -> str:
        """Get the available commands for Slitherlink.

        Returns:
            Multi-line string describing available commands
        """
        return """SLITHERLINK COMMANDS:
  set h <row> <col> <state>  - Set horizontal edge (e.g., 'set h 1 2 1')
  set v <row> <col> <state>  - Set vertical edge (e.g., 'set v 2 1 1')
    state: 0=clear, 1=line, 2=X (not part of loop)
  show                       - Display current grid
  hint                       - Get a hint for the next move
  check                      - Check if puzzle is complete
  solve                      - Show solution (ends game)
  menu                       - Return to game selection
  quit                       - Exit the server"""

    def get_stats(self) -> str:
        """Get current game statistics.

        Returns:
            String with game stats
        """
        total_lines = sum(sum(1 for e in row if e == 1) for row in self.h_edges)
        total_lines += sum(sum(1 for e in row if e == 1) for row in self.v_edges)

        total_clues = sum(sum(1 for c in row if c != -1) for row in self.clues)

        return f"Moves made: {self.moves_made} | Lines drawn: {total_lines} | Clues: {total_clues} | Grid: {self.size}×{self.size} | Seed: {self.seed}"
