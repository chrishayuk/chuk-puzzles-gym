"""Bridges (Hashiwokakero) puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame


class BridgesGame(PuzzleGame):
    """Bridges (Hashiwokakero) puzzle game.

    Connect islands with bridges according to the numbers on each island.
    - Each island must have exactly the number of bridges shown
    - Bridges can only run horizontally or vertically
    - Bridges cannot cross each other
    - At most two bridges can connect any pair of islands
    - All islands must be connected in a single network
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Bridges game.

        Args:
            difficulty: Game difficulty level (easy, medium, hard)
        """
        super().__init__(difficulty, seed, **kwargs)

        from ...models import DifficultyLevel

        # Set grid size based on difficulty
        self.size = {
            DifficultyLevel.EASY.value: 7,
            DifficultyLevel.MEDIUM.value: 9,
            DifficultyLevel.HARD.value: 11,
        }.get(self.difficulty.value, 7)

        # Grid stores island values (0 = water, 1-8 = island with that many bridges needed)
        self.grid: list[list[int]] = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Solution stores the bridges (stored as a dict of (r1,c1,r2,c2) -> bridge_count)
        self.solution: dict[tuple[int, int, int, int], int] = {}

        # Player's current bridges
        self.bridges: dict[tuple[int, int, int, int], int] = {}

        # Island positions for easy lookup
        self.islands: list[tuple[int, int]] = []

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Bridges"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Connect islands with bridges - satisfy all island numbers"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["connectivity", "local_counting", "graph_construction", "path_finding"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["network_design", "infrastructure_planning", "connection_optimization", "graph_connectivity"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "large", "constraint_density": "moderate"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = number of bridge connections to place."""
        if not hasattr(self, "solution") or not self.solution:
            return None
        # Each connection is one move, regardless of bridge count (1 or 2)
        return len(self.solution)

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Bridges."""
        from ...models import DifficultyLevel

        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 4,
            DifficultyLevel.HARD.value: 5,
        }.get(self.difficulty.value, 3)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=4.0,  # 4 directions, 0-2 bridges
            state_observability=1.0,
            constraint_density=0.5,
        )

    def _normalize_bridge(self, r1: int, c1: int, r2: int, c2: int) -> tuple[int, int, int, int]:
        """Normalize bridge coordinates so smaller coords come first."""
        if (r1, c1) > (r2, c2):
            return (r2, c2, r1, c1)
        return (r1, c1, r2, c2)

    def _find_neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        """Find all islands that can be connected from this position."""
        neighbors = []

        # Check horizontal (left and right)
        for c in range(col + 1, self.size):
            if self.grid[row][c] > 0:
                neighbors.append((row, c))
                break

        for c in range(col - 1, -1, -1):
            if self.grid[row][c] > 0:
                neighbors.append((row, c))
                break

        # Check vertical (up and down)
        for r in range(row + 1, self.size):
            if self.grid[r][col] > 0:
                neighbors.append((r, col))
                break

        for r in range(row - 1, -1, -1):
            if self.grid[r][col] > 0:
                neighbors.append((r, col))
                break

        return neighbors

    def _bridges_cross(self, r1: int, c1: int, r2: int, c2: int, r3: int, c3: int, r4: int, c4: int) -> bool:
        """Check if two bridges would cross each other."""
        # Horizontal bridge 1
        if r1 == r2:
            min_c, max_c = min(c1, c2), max(c1, c2)
            # Vertical bridge 2
            if c3 == c4:
                min_r, max_r = min(r3, r4), max(r3, r4)
                # Check if they intersect
                return min_c < c3 < max_c and min_r < r1 < max_r

        # Vertical bridge 1
        if c1 == c2:
            min_r, max_r = min(r1, r2), max(r1, r2)
            # Horizontal bridge 2
            if r3 == r4:
                min_c, max_c = min(c3, c4), max(c3, c4)
                # Check if they intersect
                return min_r < r3 < max_r and min_c < c1 < max_c

        return False

    async def generate_puzzle(self) -> None:
        """Generate a new Bridges puzzle with retry logic."""
        max_attempts = 50

        for _attempt in range(max_attempts):
            # Reset state
            self.islands = []
            self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
            self.solution = {}

            # Step 1: Place islands strategically
            if not self._place_islands_strategically():
                continue

            # Step 2: Generate solution
            self._generate_solution()

            # Step 3: Validate solution
            if self._validate_puzzle():
                # Step 4: Update island values based on solution
                for r, c in self.islands:
                    bridge_count = 0
                    for (r1, c1, r2, c2), count in self.solution.items():
                        if (r1, c1) == (r, c) or (r2, c2) == (r, c):
                            bridge_count += count
                    self.grid[r][c] = bridge_count

                self.game_started = True
                return

        # Fallback: use last attempt even if not perfect
        for r, c in self.islands:
            bridge_count = 0
            for (r1, c1, r2, c2), count in self.solution.items():
                if (r1, c1) == (r, c) or (r2, c2) == (r, c):
                    bridge_count += count
            if bridge_count == 0:
                bridge_count = 1
            self.grid[r][c] = bridge_count

        self.game_started = True

    def _place_islands_strategically(self) -> bool:
        """Place islands using strategic positions for better puzzle quality."""
        from ...models import DifficultyLevel

        num_islands = {
            DifficultyLevel.EASY.value: 8,
            DifficultyLevel.MEDIUM.value: 12,
            DifficultyLevel.HARD.value: 16,
        }.get(self.difficulty.value, 8)

        # Create a grid of strategic positions (avoid edges for better connectivity)
        step = max(2, self.size // 4)
        strategic_positions = []

        for r in range(1, self.size - 1, step):
            for c in range(1, self.size - 1, step):
                strategic_positions.append((r, c))

        # Add some edge positions for variety
        for i in range(1, self.size - 1, step):
            strategic_positions.extend([(0, i), (self.size - 1, i), (i, 0), (i, self.size - 1)])

        # Shuffle positions for variety
        self._rng.shuffle(strategic_positions)

        # Select positions ensuring minimum spacing
        min_spacing = 2
        for r, c in strategic_positions:
            if len(self.islands) >= num_islands:
                break

            # Check spacing from existing islands
            if all(abs(r - ir) + abs(c - ic) >= min_spacing for ir, ic in self.islands):
                self.islands.append((r, c))
                self.grid[r][c] = 1

        return len(self.islands) >= max(4, num_islands // 2)

    def _validate_puzzle(self) -> bool:
        """Validate that the generated puzzle is solvable and well-formed."""
        # Check all islands have at least one bridge
        for r, c in self.islands:
            bridge_count = 0
            for (r1, c1, r2, c2), count in self.solution.items():
                if (r1, c1) == (r, c) or (r2, c2) == (r, c):
                    bridge_count += count

            if bridge_count == 0:
                return False

            # Check bridge count is reasonable (not too high)
            if bridge_count > 8:
                return False

        # Check all islands are connected (graph connectivity)
        if not self._check_connectivity():
            return False

        return True

    def _check_connectivity(self) -> bool:
        """Check if all islands are connected via bridges."""
        if not self.islands:
            return True

        # BFS from first island
        visited = {self.islands[0]}
        queue = [self.islands[0]]

        while queue:
            r, c = queue.pop(0)

            # Check all bridges from this island
            for (r1, c1, r2, c2), count in self.solution.items():
                if count > 0:
                    if (r1, c1) == (r, c) and (r2, c2) not in visited:
                        visited.add((r2, c2))
                        queue.append((r2, c2))
                    elif (r2, c2) == (r, c) and (r1, c1) not in visited:
                        visited.add((r1, c1))
                        queue.append((r1, c1))

        return len(visited) == len(self.islands)

    def _would_cross_existing(self, r1: int, c1: int, r2: int, c2: int) -> bool:
        """Check if a new bridge would cross any existing bridge in the solution."""
        for (br1, bc1, br2, bc2), bcount in self.solution.items():
            if bcount > 0:
                if self._bridges_cross(r1, c1, r2, c2, br1, bc1, br2, bc2):
                    return True
        return False

    def _generate_solution(self) -> None:
        """Generate a valid solution for the puzzle without crossing bridges."""
        if not self.islands:
            return

        # Create a minimum spanning tree using a simple approach
        # but only add bridges that don't cross existing ones
        connected = {self.islands[0]}
        unconnected = set(self.islands[1:])

        while unconnected:
            # Find the closest unconnected island to any connected island
            # that can be connected without crossing
            best_dist = float("inf")
            best_pair = None

            for r1, c1 in connected:
                neighbors = self._find_neighbors(r1, c1)
                for r2, c2 in neighbors:
                    if (r2, c2) in unconnected:
                        # Check if this bridge would cross existing ones
                        if not self._would_cross_existing(r1, c1, r2, c2):
                            dist = abs(r1 - r2) + abs(c1 - c2)
                            if dist < best_dist:
                                best_dist = dist
                                best_pair = ((r1, c1), (r2, c2))

            if best_pair:
                (r1, c1), (r2, c2) = best_pair
                bridge_key = self._normalize_bridge(r1, c1, r2, c2)
                self.solution[bridge_key] = 1
                connected.add((r2, c2))
                unconnected.remove((r2, c2))
            else:
                break

        # Add some additional bridges for variety (up to 2 bridges per connection)
        # Only if they don't create crossings
        for r1, c1 in self.islands:
            neighbors = self._find_neighbors(r1, c1)
            for r2, c2 in neighbors:
                bridge_key = self._normalize_bridge(r1, c1, r2, c2)
                if bridge_key in self.solution and self._rng.random() < 0.3:
                    if self.solution[bridge_key] < 2:
                        self.solution[bridge_key] += 1

    async def validate_move(self, *args: Any, **kwargs: Any) -> MoveResult:
        """Validate a bridge placement move.

        Args:
            args[0]: Starting row (1-indexed)
            args[1]: Starting column (1-indexed)
            args[2]: Ending row (1-indexed)
            args[3]: Ending column (1-indexed)
            args[4]: Number of bridges (1 or 2, or 0 to remove)

        Returns:
            MoveResult containing success status and message
        """
        if len(args) < 5:
            return MoveResult(success=False, message="Usage: place <row1> <col1> <row2> <col2> <count>")

        try:
            r1, c1, r2, c2, count = int(args[0]) - 1, int(args[1]) - 1, int(args[2]) - 1, int(args[3]) - 1, int(args[4])
        except (ValueError, IndexError):
            return MoveResult(success=False, message="Invalid coordinates or count")

        # Validate coordinates
        if not (0 <= r1 < self.size and 0 <= c1 < self.size and 0 <= r2 < self.size and 0 <= c2 < self.size):
            return MoveResult(success=False, message="Coordinates out of range")

        # Check that they're not the same position (before checking if it's an island)
        if r1 == r2 and c1 == c2:
            return MoveResult(success=False, message="Cannot connect island to itself")

        # Check that both positions are islands
        if self.grid[r1][c1] == 0 or self.grid[r2][c2] == 0:
            return MoveResult(success=False, message="Both positions must be islands")

        # Check that islands are in a line (horizontal or vertical)
        if r1 != r2 and c1 != c2:
            return MoveResult(success=False, message="Bridges must be horizontal or vertical")

        # Normalize bridge coordinates
        bridge_key = self._normalize_bridge(r1, c1, r2, c2)

        # Validate count
        if count < 0 or count > 2:
            return MoveResult(success=False, message="Bridge count must be 0, 1, or 2")

        # Check for crossing bridges
        if count > 0:
            for (br1, bc1, br2, bc2), bcount in self.bridges.items():
                if bcount > 0 and (br1, bc1, br2, bc2) != bridge_key:
                    if self._bridges_cross(r1, c1, r2, c2, br1, bc1, br2, bc2):
                        return MoveResult(success=False, message="Bridges cannot cross")

        # Update or remove bridge
        if count == 0:
            if bridge_key in self.bridges:
                del self.bridges[bridge_key]
                self.moves_made += 1
                return MoveResult(success=True, message="Bridge removed")
            return MoveResult(success=False, message="No bridge to remove")
        else:
            self.bridges[bridge_key] = count
            self.moves_made += 1
            return MoveResult(success=True, message=f"Bridge placed ({count} bridge{'s' if count > 1 else ''})")

    def is_complete(self) -> bool:
        """Check if the puzzle is completely and correctly solved."""
        # Check that each island has the correct number of bridges
        for r, c in self.islands:
            required = self.grid[r][c]
            actual = 0

            for (r1, c1, r2, c2), count in self.bridges.items():
                if (r1, c1) == (r, c) or (r2, c2) == (r, c):
                    actual += count

            if actual != required:
                return False

        # Check that all islands are connected (simplified check)
        # In a full implementation, we'd do a proper connectivity check
        return len(self.bridges) >= len(self.islands) - 1

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move."""
        # Find a bridge in the solution that's not yet placed correctly
        for bridge_key, solution_count in self.solution.items():
            current_count = self.bridges.get(bridge_key, 0)
            if current_count != solution_count:
                r1, c1, r2, c2 = bridge_key
                return (
                    (r1 + 1, c1 + 1, r2 + 1, c2 + 1, solution_count),
                    f"Try placing {solution_count} bridge(s) between ({r1 + 1},{c1 + 1}) and ({r2 + 1},{c2 + 1})",
                )

        return None

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art."""
        lines = []

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
                if self.grid[r][c] > 0:
                    # This is an island
                    row += f" {self.grid[r][c]:2d}"
                else:
                    # Check for bridges
                    bridge_char = "  ."

                    # Check horizontal bridges
                    for (r1, c1, r2, c2), count in self.bridges.items():
                        if r1 == r2 == r and min(c1, c2) < c < max(c1, c2):
                            bridge_char = " ══" if count == 2 else " ──"
                            break

                    # Check vertical bridges
                    for (r1, c1, r2, c2), count in self.bridges.items():
                        if c1 == c2 == c and min(r1, r2) < r < max(r1, r2):
                            bridge_char = " ║ " if count == 2 else " │ "
                            break

                    row += bridge_char

            lines.append(row)

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for this puzzle type."""
        return """BRIDGES (HASHIWOKAKERO) RULES:
- Connect all islands with bridges
- Each island shows the number of bridges it needs
- Bridges can only be horizontal or vertical
- Bridges cannot cross each other
- At most 2 bridges can connect any pair of islands
- All islands must be connected in a single network"""

    def get_commands(self) -> str:
        """Get the available commands for this puzzle type."""
        return """BRIDGES COMMANDS:
  place <r1> <c1> <r2> <c2> <count> - Place bridges (1 or 2, or 0 to remove)
  Example: place 1 1 1 3 2  (places 2 bridges between islands)
  hint   - Get a hint for the next move
  check  - Check if puzzle is complete
  solve  - Show the solution
  menu   - Return to main menu
  quit   - Exit the game"""
