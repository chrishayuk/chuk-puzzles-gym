"""Sokoban puzzle game implementation."""

from typing import Any

from ...models import MoveResult
from .._base import PuzzleGame
from .config import SokobanConfig


class SokobanGame(PuzzleGame):
    """Sokoban puzzle game.

    Push boxes to goal positions:
    - Player can move in 4 directions
    - Player can push boxes (but not pull them)
    - Boxes cannot be pushed through walls or other boxes
    - Goal: Get all boxes onto goal positions
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None):
        """Initialize a new Sokoban game.

        Args:
            difficulty: Game difficulty level (easy=6x6, medium=8x8, hard=10x10)
        """
        super().__init__(difficulty, seed)

        # Use pydantic config based on difficulty
        self.config = SokobanConfig.from_difficulty(self.difficulty)
        self.size = self.config.size
        self.num_boxes = self.config.num_boxes

        # Grid: 0 = empty, 1 = wall, 2 = box, 3 = goal, 4 = player
        # Box on goal = 5, Player on goal = 6
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.goals: list[tuple[int, int]] = []
        self.player_pos: tuple[int, int] = (0, 0)
        self.initial_state: dict[str, Any] = {}

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Sokoban"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Push boxes to goal positions - planning and spatial reasoning"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["irreversible_actions", "spatial_planning", "goal_states", "path_finding"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["warehouse_logistics", "movement_planning", "resource_positioning", "sequential_operations"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "optimization", "search_space": "exponential", "constraint_density": "sparse"}

    async def generate_puzzle(self) -> None:
        """Generate a new Sokoban puzzle."""
        # Create a simple room with walls
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Add border walls
        for i in range(self.size):
            self.grid[0][i] = 1
            self.grid[self.size - 1][i] = 1
            self.grid[i][0] = 1
            self.grid[i][self.size - 1] = 1

        # Add some internal walls
        for _ in range(self.size // 2):
            r = self._rng.randint(2, self.size - 3)
            c = self._rng.randint(2, self.size - 3)
            self.grid[r][c] = 1

        # Place goals
        self.goals = []
        for _ in range(self.num_boxes):
            while True:
                r = self._rng.randint(1, self.size - 2)
                c = self._rng.randint(1, self.size - 2)
                if self.grid[r][c] == 0 and (r, c) not in self.goals:
                    self.goals.append((r, c))
                    self.grid[r][c] = 3
                    break

        # Place boxes near goals
        for goal_r, goal_c in self.goals:
            placed = False
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                r, c = goal_r + dr, goal_c + dc
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.grid[r][c] == 0:
                        self.grid[r][c] = 2
                        placed = True
                        break
            if not placed:
                # Place box on empty space
                for r in range(1, self.size - 1):
                    for c in range(1, self.size - 1):
                        if self.grid[r][c] == 0:
                            self.grid[r][c] = 2
                            placed = True
                            break
                    if placed:
                        break

        # Place player
        for r in range(1, self.size - 1):
            for c in range(1, self.size - 1):
                if self.grid[r][c] == 0:
                    self.player_pos = (r, c)
                    self.grid[r][c] = 4
                    break

        # Store initial state
        self.initial_state = {
            "grid": [row[:] for row in self.grid],
            "player_pos": self.player_pos,
        }

        self.moves_made = 0
        self.game_started = True

    async def validate_move(self, direction: str) -> MoveResult:
        """Move the player in a direction.

        Args:
            direction: Direction to move ("up", "down", "left", "right")

        Returns:
            MoveResult with success status and message
        """
        direction = direction.lower()

        # Map direction to delta
        direction_map = {
            "up": (-1, 0),
            "down": (1, 0),
            "left": (0, -1),
            "right": (0, 1),
            "u": (-1, 0),
            "d": (1, 0),
            "l": (0, -1),
            "r": (0, 1),
        }

        if direction not in direction_map:
            return MoveResult(success=False, message="Invalid direction. Use: up, down, left, right")

        dr, dc = direction_map[direction]
        curr_r, curr_c = self.player_pos
        new_r, new_c = curr_r + dr, curr_c + dc

        # Check bounds
        if not (0 <= new_r < self.size and 0 <= new_c < self.size):
            return MoveResult(success=False, message="Cannot move outside the grid.")

        # Check what's at the new position
        target_cell = self.grid[new_r][new_c]

        # Wall
        if target_cell == 1:
            return MoveResult(success=False, message="Cannot move into a wall.")

        # Empty or goal
        if target_cell in [0, 3]:
            # Move player
            # Clear current position
            on_goal = any(curr_r == gr and curr_c == gc for gr, gc in self.goals)
            self.grid[curr_r][curr_c] = 3 if on_goal else 0

            # Set new position
            on_goal = any(new_r == gr and new_c == gc for gr, gc in self.goals)
            self.grid[new_r][new_c] = 6 if on_goal else 4

            self.player_pos = (new_r, new_c)
            self.moves_made += 1
            return MoveResult(success=True, message=f"Moved {direction}.", state_changed=True)

        # Box or box on goal
        if target_cell in [2, 5]:
            # Try to push the box
            push_r, push_c = new_r + dr, new_c + dc

            # Check push destination
            if not (0 <= push_r < self.size and 0 <= push_c < self.size):
                return MoveResult(success=False, message="Cannot push box outside the grid.")

            push_target = self.grid[push_r][push_c]

            # Can only push into empty or goal
            if push_target not in [0, 3]:
                return MoveResult(success=False, message="Cannot push box into wall or another box.")

            # Push the box
            # Clear current position
            on_goal = any(curr_r == gr and curr_c == gc for gr, gc in self.goals)
            self.grid[curr_r][curr_c] = 3 if on_goal else 0

            # Move player to box position
            box_on_goal = any(new_r == gr and new_c == gc for gr, gc in self.goals)
            self.grid[new_r][new_c] = 6 if box_on_goal else 4

            # Move box to push position
            push_on_goal = any(push_r == gr and push_c == gc for gr, gc in self.goals)
            self.grid[push_r][push_c] = 5 if push_on_goal else 2

            self.player_pos = (new_r, new_c)
            self.moves_made += 1
            return MoveResult(success=True, message=f"Pushed box {direction}.", state_changed=True)

        return MoveResult(success=False, message="Unknown cell type.")

    def is_complete(self) -> bool:
        """Check if the puzzle is complete (all boxes on goals)."""
        # Check if all goals have boxes
        for gr, gc in self.goals:
            cell = self.grid[gr][gc]
            # Box on goal (5) or player on goal with box (not possible in standard rules)
            if cell != 5 and cell != 6:  # Goal must have box
                # Check if there's a box here
                if cell != 5:
                    return False
        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None
        """
        # Simple hint: suggest moving toward nearest box not on goal
        curr_r, curr_c = self.player_pos

        # Find boxes not on goals
        boxes_not_on_goal = []
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 2:  # Box not on goal
                    boxes_not_on_goal.append((r, c))

        if not boxes_not_on_goal:
            return None

        # Find closest box
        min_dist = float("inf")
        closest_box = None
        for br, bc in boxes_not_on_goal:
            dist = abs(br - curr_r) + abs(bc - curr_c)
            if dist < min_dist:
                min_dist = dist
                closest_box = (br, bc)

        if closest_box:
            br, bc = closest_box
            # Suggest direction toward box
            if br < curr_r:
                direction = "up"
            elif br > curr_r:
                direction = "down"
            elif bc < curr_c:
                direction = "left"
            else:
                direction = "right"

            hint_data = direction
            hint_message = f"Try moving {direction} toward a box"
            return hint_data, hint_message

        return None

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        Returns:
            String representation of the puzzle grid
        """
        lines = []

        for r in range(self.size):
            row_str = ""
            for c in range(self.size):
                cell = self.grid[r][c]
                if cell == 0:
                    row_str += " ."
                elif cell == 1:
                    row_str += " #"
                elif cell == 2:
                    row_str += " $"
                elif cell == 3:
                    row_str += " ○"
                elif cell == 4:
                    row_str += " @"
                elif cell == 5:
                    row_str += " ☒"
                elif cell == 6:
                    row_str += " Θ"
                else:
                    row_str += " ?"
            lines.append(row_str)

        lines.append("\nLegend: @ = player, $ = box, ○ = goal, # = wall")
        lines.append("        ☒ = box on goal, Θ = player on goal")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Sokoban.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return """SOKOBAN RULES:
- Move the player (@) to push boxes ($) onto goals (○)
- You can only push boxes, not pull them
- You cannot push a box into a wall or another box
- Goal: Get all boxes onto goal positions
- Moves are irreversible - plan carefully!"""

    def get_commands(self) -> str:
        """Get the available commands for Sokoban.

        Returns:
            Multi-line string describing available commands
        """
        return """SOKOBAN COMMANDS:
  up (or u)       - Move player up
  down (or d)     - Move player down
  left (or l)     - Move player left
  right (or r)    - Move player right
  show            - Display the current grid
  hint            - Get a hint
  check           - Check if puzzle is solved
  reset           - Reset to initial state
  menu            - Return to game selection
  quit            - Exit the server"""

    def get_stats(self) -> str:
        """Get current game statistics.

        Returns:
            String with game stats
        """
        boxes_on_goals = sum(1 for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 5)
        return f"Moves made: {self.moves_made} | Boxes on goals: {boxes_on_goals}/{self.num_boxes} | Seed: {self.seed}"
