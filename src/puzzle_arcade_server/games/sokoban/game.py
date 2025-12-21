"""Sokoban puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
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

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Sokoban game.

        Args:
            difficulty: Game difficulty level (easy=6x6, medium=8x8, hard=10x10)
        """
        super().__init__(difficulty, seed, **kwargs)

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

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps estimate = box pushes + player repositioning moves."""
        if not hasattr(self, "goals") or not self.goals:
            return None
        # Find all boxes in the grid (2 = box, 5 = box on goal)
        boxes = []
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] in (2, 5):
                    boxes.append((r, c))
        if not boxes:
            return None
        # Each box push is 1 move. Player needs to get behind each box.
        # Estimate: sum of box distances + (num_boxes - 1) for repositioning
        total_pushes = 0
        for box in boxes:
            min_dist = min(abs(box[0] - g[0]) + abs(box[1] - g[1]) for g in self.goals)
            total_pushes += min_dist
        # Add repositioning moves between boxes (rough estimate)
        reposition = max(0, len(boxes) - 1) * 2
        return total_pushes + reposition

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Sokoban."""
        from ...models import DifficultyLevel

        logic_depth = {
            DifficultyLevel.EASY.value: 3,
            DifficultyLevel.MEDIUM.value: 5,
            DifficultyLevel.HARD.value: 8,
        }.get(self.difficulty.value, 5)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=4.0,  # 4 directions
            state_observability=1.0,
            constraint_density=0.4,
        )

    def _is_corner(self, r: int, c: int) -> bool:
        """Check if a position is a corner (would trap a box)."""
        # Check all four corner configurations
        corners = [
            [(0, -1), (-1, 0)],  # top-left corner
            [(0, 1), (-1, 0)],  # top-right corner
            [(0, -1), (1, 0)],  # bottom-left corner
            [(0, 1), (1, 0)],  # bottom-right corner
        ]
        for (dr1, dc1), (dr2, dc2) in corners:
            nr1, nc1 = r + dr1, c + dc1
            nr2, nc2 = r + dr2, c + dc2
            # Check if both adjacent cells are walls
            wall1 = not (0 <= nr1 < self.size and 0 <= nc1 < self.size) or self.grid[nr1][nc1] == 1
            wall2 = not (0 <= nr2 < self.size and 0 <= nc2 < self.size) or self.grid[nr2][nc2] == 1
            if wall1 and wall2:
                return True
        return False

    def _can_push_to_goal(self, box_r: int, box_c: int, goal_r: int, goal_c: int) -> bool:
        """Check if a box can be pushed from box position to goal position.

        For simple evaluation, we require box and goal to be on same row or column
        with no walls between them and push space available.
        """
        if box_r == goal_r:
            # Same row - check horizontal push
            if box_c < goal_c:
                # Push right - need empty space to left of box
                if box_c - 1 < 1:
                    return False
                if self.grid[box_r][box_c - 1] != 0:
                    return False
                # Check path is clear
                for c in range(box_c + 1, goal_c + 1):
                    if self.grid[box_r][c] == 1:
                        return False
                return True
            else:
                # Push left - need empty space to right of box
                if box_c + 1 >= self.size - 1:
                    return False
                if self.grid[box_r][box_c + 1] != 0:
                    return False
                # Check path is clear
                for c in range(goal_c, box_c):
                    if self.grid[box_r][c] == 1:
                        return False
                return True
        elif box_c == goal_c:
            # Same column - check vertical push
            if box_r < goal_r:
                # Push down - need empty space above box
                if box_r - 1 < 1:
                    return False
                if self.grid[box_r - 1][box_c] != 0:
                    return False
                # Check path is clear
                for r in range(box_r + 1, goal_r + 1):
                    if self.grid[r][box_c] == 1:
                        return False
                return True
            else:
                # Push up - need empty space below box
                if box_r + 1 >= self.size - 1:
                    return False
                if self.grid[box_r + 1][box_c] != 0:
                    return False
                # Check path is clear
                for r in range(goal_r, box_r):
                    if self.grid[r][box_c] == 1:
                        return False
                return True
        return False

    async def generate_puzzle(self) -> None:
        """Generate a new Sokoban puzzle that is guaranteed solvable.

        Strategy: Place goals first, then place boxes in positions where
        they can be directly pushed to goals in a straight line.
        """
        max_attempts = 50

        for _attempt in range(max_attempts):
            # Create a simple room with walls (only borders, no internal walls for simplicity)
            self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

            # Add border walls
            for i in range(self.size):
                self.grid[0][i] = 1
                self.grid[self.size - 1][i] = 1
                self.grid[i][0] = 1
                self.grid[i][self.size - 1] = 1

            # Place goals in safe positions (not in corners, not on edges next to corners)
            self.goals = []
            goal_attempts = 0
            while len(self.goals) < self.num_boxes and goal_attempts < 100:
                goal_attempts += 1
                # Place goals in the interior, avoiding positions too close to walls
                r = self._rng.randint(2, self.size - 3)
                c = self._rng.randint(2, self.size - 3)
                if self.grid[r][c] == 0 and (r, c) not in self.goals:
                    self.goals.append((r, c))
                    self.grid[r][c] = 3  # Mark as goal

            if len(self.goals) < self.num_boxes:
                continue

            # For each goal, place a box that can be directly pushed to it
            boxes_placed = []
            all_boxes_valid = True

            for goal_r, goal_c in self.goals:
                # Try to place box in a position where it can be pushed to goal
                placed = False

                # Try each direction: place box such that pushing will move it to goal
                # Shuffle directions for variety
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                self._rng.shuffle(directions)

                for dr, dc in directions:
                    # Box position (offset from goal)
                    distance = self._rng.randint(1, 2)  # 1-2 cells away
                    box_r = goal_r - dr * distance
                    box_c = goal_c - dc * distance

                    # Push position (where player needs to be to push)
                    push_r = box_r - dr
                    push_c = box_c - dc

                    # Check all positions are valid
                    if not (1 <= box_r < self.size - 1 and 1 <= box_c < self.size - 1):
                        continue
                    if not (1 <= push_r < self.size - 1 and 1 <= push_c < self.size - 1):
                        continue

                    # Check box position is empty and not a corner
                    if self.grid[box_r][box_c] != 0:
                        continue
                    if (box_r, box_c) in boxes_placed:
                        continue

                    # Check push position is empty
                    if self.grid[push_r][push_c] != 0:
                        continue
                    if (push_r, push_c) in boxes_placed:
                        continue

                    # Check path from box to goal is clear (only goals allowed)
                    path_clear = True
                    if dr != 0:
                        step = 1 if dr > 0 else -1
                        for r in range(box_r + step, goal_r + step, step):
                            if self.grid[r][box_c] not in [0, 3]:
                                path_clear = False
                                break
                            if (r, box_c) in boxes_placed:
                                path_clear = False
                                break
                    else:
                        step = 1 if dc > 0 else -1
                        for c in range(box_c + step, goal_c + step, step):
                            if self.grid[box_r][c] not in [0, 3]:
                                path_clear = False
                                break
                            if (box_r, c) in boxes_placed:
                                path_clear = False
                                break

                    if path_clear:
                        boxes_placed.append((box_r, box_c))
                        placed = True
                        break

                if not placed:
                    all_boxes_valid = False
                    break

            if not all_boxes_valid:
                # Reset and try again
                continue

            # Place all boxes
            for box_r, box_c in boxes_placed:
                self.grid[box_r][box_c] = 2

            # Find a suitable player position
            # Player should be able to reach push positions
            player_placed = False
            player_candidates = []

            for r in range(1, self.size - 1):
                for c in range(1, self.size - 1):
                    if self.grid[r][c] == 0:
                        player_candidates.append((r, c))

            if player_candidates:
                self._rng.shuffle(player_candidates)
                self.player_pos = player_candidates[0]
                self.grid[self.player_pos[0]][self.player_pos[1]] = 4
                player_placed = True

            if player_placed:
                # Store initial state
                self.initial_state = {
                    "grid": [row[:] for row in self.grid],
                    "player_pos": self.player_pos,
                }
                self.moves_made = 0
                self.game_started = True
                return

        # Fallback: create a trivially simple puzzle
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]

        # Add border walls
        for i in range(self.size):
            self.grid[0][i] = 1
            self.grid[self.size - 1][i] = 1
            self.grid[i][0] = 1
            self.grid[i][self.size - 1] = 1

        # Place goals and boxes in a simple line pattern
        self.goals = []
        mid = self.size // 2

        for i in range(self.num_boxes):
            goal_r = mid
            goal_c = 2 + i * 2
            if goal_c < self.size - 2:
                self.goals.append((goal_r, goal_c))
                self.grid[goal_r][goal_c] = 3
                # Box one cell above
                self.grid[goal_r - 1][goal_c] = 2

        # Player at bottom
        self.player_pos = (mid + 1, 2)
        self.grid[self.player_pos[0]][self.player_pos[1]] = 4

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

    def _find_path_to_push_position(self, target_r: int, target_c: int) -> list[str] | None:
        """Use BFS to find path from player to target position.

        Returns list of directions or None if no path exists.
        """
        from collections import deque

        start = self.player_pos
        if start == (target_r, target_c):
            return []

        direction_map = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
        visited = {start}
        queue: deque[tuple[tuple[int, int], list[str]]] = deque([(start, [])])

        while queue:
            (r, c), path = queue.popleft()

            for direction, (dr, dc) in direction_map.items():
                nr, nc = r + dr, c + dc

                if (nr, nc) in visited:
                    continue
                if not (0 <= nr < self.size and 0 <= nc < self.size):
                    continue

                cell = self.grid[nr][nc]
                # Can only move through empty cells and goals
                if cell not in [0, 3]:
                    continue

                if (nr, nc) == (target_r, target_c):
                    return path + [direction]

                visited.add((nr, nc))
                queue.append(((nr, nc), path + [direction]))

        return None

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Uses BFS to find the optimal move to push boxes toward goals.

        Returns:
            Tuple of (hint_data, hint_message) or None
        """
        if self.is_complete():
            return None

        direction_map = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}

        # Find boxes not on goals and unfilled goals
        boxes_not_on_goal = []
        unfilled_goals = []

        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 2:
                    boxes_not_on_goal.append((r, c))

        for gr, gc in self.goals:
            if self.grid[gr][gc] != 5:  # Not box-on-goal
                unfilled_goals.append((gr, gc))

        if not boxes_not_on_goal:
            return None

        # For each box, find the best push direction toward a goal
        best_hint = None
        best_score = float("inf")

        for box_r, box_c in boxes_not_on_goal:
            for goal_r, goal_c in unfilled_goals:
                # Determine push direction needed
                push_dir = None
                if box_r == goal_r:
                    if box_c < goal_c:
                        push_dir = "right"
                    elif box_c > goal_c:
                        push_dir = "left"
                elif box_c == goal_c:
                    if box_r < goal_r:
                        push_dir = "down"
                    elif box_r > goal_r:
                        push_dir = "up"

                if push_dir is None:
                    continue

                dr, dc = direction_map[push_dir]
                # Player needs to be on opposite side of box to push
                push_pos_r = box_r - dr
                push_pos_c = box_c - dc

                # Check if push position is valid
                if not (1 <= push_pos_r < self.size - 1 and 1 <= push_pos_c < self.size - 1):
                    continue
                if self.grid[push_pos_r][push_pos_c] == 1:  # Wall
                    continue

                # Check if we can actually push (destination is clear)
                dest_r, dest_c = box_r + dr, box_c + dc
                if not (0 <= dest_r < self.size and 0 <= dest_c < self.size):
                    continue
                if self.grid[dest_r][dest_c] not in [0, 3]:  # Not empty/goal
                    continue

                # If player is already at push position, push is the hint
                if self.player_pos == (push_pos_r, push_pos_c):
                    score = abs(goal_r - dest_r) + abs(goal_c - dest_c)
                    if score < best_score:
                        best_score = score
                        best_hint = (push_dir, f"Push {push_dir} to move box toward goal")

                # Otherwise, find path to push position
                elif self.grid[push_pos_r][push_pos_c] in [0, 3]:
                    path = self._find_path_to_push_position(push_pos_r, push_pos_c)
                    if path:
                        score = len(path) + abs(goal_r - dest_r) + abs(goal_c - dest_c)
                        if score < best_score:
                            best_score = score
                            best_hint = (path[0], f"Move {path[0]} to get into push position")

        if best_hint:
            return best_hint

        # Fallback: try any valid move
        curr_r, curr_c = self.player_pos
        for direction, (dr, dc) in direction_map.items():
            new_r, new_c = curr_r + dr, curr_c + dc
            if 0 <= new_r < self.size and 0 <= new_c < self.size:
                cell = self.grid[new_r][new_c]
                if cell in [0, 3]:  # Empty or goal
                    return direction, f"Try moving {direction}"
                elif cell in [2, 5]:  # Box
                    push_r, push_c = new_r + dr, new_c + dc
                    if 0 <= push_r < self.size and 0 <= push_c < self.size:
                        if self.grid[push_r][push_c] in [0, 3]:
                            return direction, f"Try pushing {direction}"

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
