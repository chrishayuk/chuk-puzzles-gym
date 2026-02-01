"""Rush Hour puzzle game implementation."""

from collections import deque
from typing import Any

from ...models import DifficultyLevel, DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import RushHourConfig
from .models import Vehicle

VEHICLE_IDS = "ABCDEFGHIJKLMNOPQRSTUVWYZ"  # Skip X (reserved for target)


class RushHourGame(PuzzleGame):
    """Rush Hour puzzle - slide vehicles to let the target car exit.

    Rules:
    - Vehicles occupy 2 or 3 cells and can only move along their orientation
    - Horizontal vehicles move left/right, vertical vehicles move up/down
    - Vehicles cannot pass through each other
    - Move the target car (X) to the right edge to win
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        super().__init__(difficulty, seed, **kwargs)
        self.config = RushHourConfig.from_difficulty(self.difficulty)
        self.size = self.config.size
        self.vehicles: dict[str, Vehicle] = {}
        self.grid: list[list[str]] = []
        self.initial_grid: list[list[str]] = []
        self.exit_row = 2  # Target car always on row 2 (0-indexed)
        self.min_solution_moves: int | None = None

    @property
    def name(self) -> str:
        return "Rush Hour"

    @property
    def description(self) -> str:
        return "Slide vehicles to free the target car (X) to the exit"

    @property
    def constraint_types(self) -> list[str]:
        return ["sequential_planning", "spatial_blocking", "search", "irreversible_actions"]

    @property
    def business_analogies(self) -> list[str]:
        return ["traffic_management", "warehouse_logistics", "deadlock_resolution"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        return {
            "reasoning_type": "planning",
            "search_space": "large",
            "constraint_density": "moderate",
        }

    @property
    def complexity_metrics(self) -> dict[str, int | float]:
        return {
            "variable_count": len(self.vehicles),
            "constraint_count": len(self.vehicles) * 2,
            "domain_size": self.size,
            "branching_factor": len(self.vehicles) * 2.0,
            "empty_cells": sum(1 for row in self.grid for cell in row if cell == "."),
        }

    @property
    def difficulty_profile(self) -> DifficultyProfile:
        profiles = {
            DifficultyLevel.EASY: DifficultyProfile(
                logic_depth=3, branching_factor=6.0, state_observability=1.0, constraint_density=0.4
            ),
            DifficultyLevel.MEDIUM: DifficultyProfile(
                logic_depth=6, branching_factor=10.0, state_observability=1.0, constraint_density=0.5
            ),
            DifficultyLevel.HARD: DifficultyProfile(
                logic_depth=10, branching_factor=15.0, state_observability=1.0, constraint_density=0.6
            ),
        }
        return profiles[self.difficulty]

    @property
    def optimal_steps(self) -> int | None:
        return self.min_solution_moves

    def _build_grid(self) -> list[list[str]]:
        """Build the grid from current vehicle positions."""
        grid = [["." for _ in range(self.size)] for _ in range(self.size)]
        for vid, v in self.vehicles.items():
            for i in range(v.length):
                if v.orientation == "h":
                    grid[v.row][v.col + i] = vid
                else:
                    grid[v.row + i][v.col] = vid
        return grid

    def _can_place_vehicle(self, grid: list[list[str]], row: int, col: int, length: int, orientation: str) -> bool:
        """Check if a vehicle can be placed at the given position."""
        for i in range(length):
            if orientation == "h":
                r, c = row, col + i
            else:
                r, c = row + i, col
            if not (0 <= r < self.size and 0 <= c < self.size):
                return False
            if grid[r][c] != ".":
                return False
        return True

    def _get_state_tuple(self) -> tuple:
        """Get a hashable state representation for BFS."""
        return tuple((v.id, v.row, v.col) for v in sorted(self.vehicles.values(), key=lambda x: x.id))

    def _solve_bfs(self) -> int | None:
        """Find minimum moves to solve using BFS.

        Returns:
            Minimum number of moves, or None if unsolvable.
        """
        initial_state = self._get_state_tuple()
        queue: deque[tuple[tuple, int, dict[str, Vehicle]]] = deque()
        queue.append((initial_state, 0, dict(self.vehicles)))
        visited: set[tuple] = {initial_state}

        while queue:
            state, moves, vehicles = queue.popleft()

            # Check if target car reached exit
            target = vehicles["X"]
            if target.col + target.length - 1 >= self.size - 1:
                return moves

            # Limit search depth
            if moves >= 60:
                continue

            # Build grid for this state
            grid = [["." for _ in range(self.size)] for _ in range(self.size)]
            for vid, v in vehicles.items():
                for i in range(v.length):
                    if v.orientation == "h":
                        grid[v.row][v.col + i] = vid
                    else:
                        grid[v.row + i][v.col] = vid

            # Try all possible moves
            for vid, v in vehicles.items():
                if v.orientation == "h":
                    # Try moving left
                    if v.col > 0 and grid[v.row][v.col - 1] == ".":
                        new_vehicles = dict(vehicles)
                        new_vehicles[vid] = Vehicle(id=vid, row=v.row, col=v.col - 1, length=v.length, orientation="h")
                        new_state = tuple(
                            (vv.id, vv.row, vv.col) for vv in sorted(new_vehicles.values(), key=lambda x: x.id)
                        )
                        if new_state not in visited:
                            visited.add(new_state)
                            queue.append((new_state, moves + 1, new_vehicles))
                    # Try moving right
                    if v.col + v.length < self.size and grid[v.row][v.col + v.length] == ".":
                        new_vehicles = dict(vehicles)
                        new_vehicles[vid] = Vehicle(id=vid, row=v.row, col=v.col + 1, length=v.length, orientation="h")
                        new_state = tuple(
                            (vv.id, vv.row, vv.col) for vv in sorted(new_vehicles.values(), key=lambda x: x.id)
                        )
                        if new_state not in visited:
                            visited.add(new_state)
                            queue.append((new_state, moves + 1, new_vehicles))
                else:  # vertical
                    # Try moving up
                    if v.row > 0 and grid[v.row - 1][v.col] == ".":
                        new_vehicles = dict(vehicles)
                        new_vehicles[vid] = Vehicle(id=vid, row=v.row - 1, col=v.col, length=v.length, orientation="v")
                        new_state = tuple(
                            (vv.id, vv.row, vv.col) for vv in sorted(new_vehicles.values(), key=lambda x: x.id)
                        )
                        if new_state not in visited:
                            visited.add(new_state)
                            queue.append((new_state, moves + 1, new_vehicles))
                    # Try moving down
                    if v.row + v.length < self.size and grid[v.row + v.length][v.col] == ".":
                        new_vehicles = dict(vehicles)
                        new_vehicles[vid] = Vehicle(id=vid, row=v.row + 1, col=v.col, length=v.length, orientation="v")
                        new_state = tuple(
                            (vv.id, vv.row, vv.col) for vv in sorted(new_vehicles.values(), key=lambda x: x.id)
                        )
                        if new_state not in visited:
                            visited.add(new_state)
                            queue.append((new_state, moves + 1, new_vehicles))

        return None

    async def generate_puzzle(self) -> None:
        """Generate a Rush Hour puzzle."""
        size = self.size
        num_vehicles = self.config.num_vehicles
        min_moves = self.config.min_moves
        max_moves = self.config.max_moves

        best_puzzle: dict[str, Vehicle] | None = None
        best_moves: int | None = None

        for _ in range(100):
            self.vehicles = {}

            # Place target car (X) on exit row, random starting column
            max_start_col = size - 3  # Leave room to not already be at exit
            start_col = self._rng.randint(0, max(0, max_start_col))
            self.vehicles["X"] = Vehicle(id="X", row=self.exit_row, col=start_col, length=2, orientation="h")

            grid = self._build_grid()

            # Place blocking vehicles
            placed = 0
            attempts = 0
            while placed < num_vehicles and attempts < 200:
                attempts += 1
                vid = VEHICLE_IDS[placed] if placed < len(VEHICLE_IDS) else chr(ord("a") + placed - len(VEHICLE_IDS))
                orientation = self._rng.choice(["h", "v"])
                length = self._rng.choice([2, 2, 3])  # More 2-length vehicles
                row = self._rng.randint(0, size - 1)
                col = self._rng.randint(0, size - 1)

                if self._can_place_vehicle(grid, row, col, length, orientation):
                    self.vehicles[vid] = Vehicle(id=vid, row=row, col=col, length=length, orientation=orientation)
                    for i in range(length):
                        if orientation == "h":
                            grid[row][col + i] = vid
                        else:
                            grid[row + i][col] = vid
                    placed += 1

            # Verify solvability and difficulty
            solution_moves = self._solve_bfs()
            if solution_moves is not None and min_moves <= solution_moves <= max_moves:
                best_puzzle = dict(self.vehicles)
                best_moves = solution_moves
                break
            elif solution_moves is not None:
                # Keep the best puzzle found so far
                if best_puzzle is None or (
                    best_moves is not None and abs(solution_moves - min_moves) < abs(best_moves - min_moves)
                ):
                    best_puzzle = dict(self.vehicles)
                    best_moves = solution_moves

        if best_puzzle is not None:
            self.vehicles = best_puzzle
            self.min_solution_moves = best_moves
        else:
            # Minimal fallback: just target car, no blockers, already solvable
            self.vehicles = {"X": Vehicle(id="X", row=self.exit_row, col=0, length=2, orientation="h")}
            self.min_solution_moves = self.size - 2

        self.grid = self._build_grid()
        self.initial_grid = [row[:] for row in self.grid]
        self.game_started = True

    async def validate_move(self, vehicle_id: str, direction: str) -> MoveResult:
        """Validate sliding a vehicle.

        Args:
            vehicle_id: Vehicle letter (e.g., 'X', 'A')
            direction: 'up', 'down', 'left', 'right'
        """
        vehicle_id = vehicle_id.upper()
        direction = direction.lower()

        if vehicle_id not in self.vehicles:
            self.record_move((vehicle_id,), False)
            available = ", ".join(sorted(self.vehicles.keys()))
            return MoveResult(success=False, message=f"No vehicle '{vehicle_id}'. Available: {available}")

        vehicle = self.vehicles[vehicle_id]
        valid_directions = {"h": {"left", "right"}, "v": {"up", "down"}}

        if direction not in valid_directions[vehicle.orientation]:
            self.record_move((vehicle_id,), False)
            orient_name = "horizontal" if vehicle.orientation == "h" else "vertical"
            valid = " or ".join(valid_directions[vehicle.orientation])
            return MoveResult(
                success=False,
                message=f"Vehicle {vehicle_id} is {orient_name}. Use: {valid}",
            )

        # Calculate new position
        new_row, new_col = vehicle.row, vehicle.col
        if direction == "left":
            new_col -= 1
        elif direction == "right":
            new_col += 1
        elif direction == "up":
            new_row -= 1
        elif direction == "down":
            new_row += 1

        # Check bounds
        if vehicle.orientation == "h":
            if new_col < 0 or new_col + vehicle.length > self.size:
                self.record_move((vehicle_id,), False)
                return MoveResult(success=False, message=f"Vehicle {vehicle_id} cannot move {direction} - wall.")
        else:
            if new_row < 0 or new_row + vehicle.length > self.size:
                self.record_move((vehicle_id,), False)
                return MoveResult(success=False, message=f"Vehicle {vehicle_id} cannot move {direction} - wall.")

        # Check for collisions
        # First, clear current vehicle from grid
        temp_grid = [row[:] for row in self.grid]
        for i in range(vehicle.length):
            if vehicle.orientation == "h":
                temp_grid[vehicle.row][vehicle.col + i] = "."
            else:
                temp_grid[vehicle.row + i][vehicle.col] = "."

        # Check new position
        for i in range(vehicle.length):
            if vehicle.orientation == "h":
                r, c = new_row, new_col + i
            else:
                r, c = new_row + i, new_col
            if temp_grid[r][c] != ".":
                self.record_move((vehicle_id,), False)
                return MoveResult(
                    success=False,
                    message=f"Vehicle {vehicle_id} blocked by {temp_grid[r][c]}.",
                )

        # Apply move
        new_vehicle = Vehicle(
            id=vehicle_id,
            row=new_row,
            col=new_col,
            length=vehicle.length,
            orientation=vehicle.orientation,
        )
        self.vehicles[vehicle_id] = new_vehicle
        self.grid = self._build_grid()
        self.record_move((vehicle_id,), True)

        msg = f"Moved {vehicle_id} {direction}."
        game_over = self.is_complete()
        if game_over:
            msg += " Vehicle X has reached the exit!"

        return MoveResult(success=True, message=msg, state_changed=True, game_over=game_over)

    def is_complete(self) -> bool:
        """Check if target car has reached the exit."""
        target = self.vehicles.get("X")
        if target is None:
            return False
        return target.col + target.length >= self.size

    async def get_hint(self) -> tuple[Any, str] | None:
        """Suggest a move by running BFS from current state."""
        if not self.can_use_hint():
            return None

        # Run BFS to find next move
        initial_state = self._get_state_tuple()
        queue: deque[tuple[tuple, list[tuple[str, str]], dict[str, Vehicle]]] = deque()
        queue.append((initial_state, [], dict(self.vehicles)))
        visited: set[tuple] = {initial_state}

        while queue:
            state, moves_list, vehicles = queue.popleft()

            target = vehicles["X"]
            if target.col + target.length >= self.size:
                if moves_list:
                    vid, direction = moves_list[0]
                    return ((vid, direction), f"Try moving vehicle {vid} {direction}.")
                return None

            if len(moves_list) >= 30:
                continue

            grid = [["." for _ in range(self.size)] for _ in range(self.size)]
            for vid, v in vehicles.items():
                for i in range(v.length):
                    if v.orientation == "h":
                        grid[v.row][v.col + i] = vid
                    else:
                        grid[v.row + i][v.col] = vid

            for vid, v in vehicles.items():
                for direction, dr, dc in [("left", 0, -1), ("right", 0, 1), ("up", -1, 0), ("down", 1, 0)]:
                    if v.orientation == "h" and direction in ("up", "down"):
                        continue
                    if v.orientation == "v" and direction in ("left", "right"):
                        continue

                    new_row, new_col = v.row + dr, v.col + dc
                    if v.orientation == "h" and (new_col < 0 or new_col + v.length > self.size):
                        continue
                    if v.orientation == "v" and (new_row < 0 or new_row + v.length > self.size):
                        continue

                    blocked = False
                    for i in range(v.length):
                        if v.orientation == "h":
                            r, c = new_row, new_col + i
                        else:
                            r, c = new_row + i, new_col
                        if grid[r][c] != "." and grid[r][c] != vid:
                            blocked = True
                            break
                    if blocked:
                        continue

                    new_vehicles = dict(vehicles)
                    new_vehicles[vid] = Vehicle(
                        id=vid, row=new_row, col=new_col, length=v.length, orientation=v.orientation
                    )
                    new_state = tuple(
                        (vv.id, vv.row, vv.col) for vv in sorted(new_vehicles.values(), key=lambda x: x.id)
                    )
                    if new_state not in visited:
                        visited.add(new_state)
                        queue.append((new_state, moves_list + [(vid, direction)], new_vehicles))

        return None

    def render_grid(self) -> str:
        """Render the Rush Hour board."""
        lines = []
        lines.append(f"Rush Hour ({self.size}x{self.size})")
        if self.min_solution_moves is not None:
            lines.append(f"Minimum solution: {self.min_solution_moves} moves")
        lines.append("")

        # Column headers
        header = "    " + " ".join(str(c + 1) for c in range(self.size))
        lines.append(header)
        lines.append("   " + "+" + "--" * self.size + "+")

        for r in range(self.size):
            cells = " ".join(self.grid[r])
            exit_marker = " >" if r == self.exit_row else "  "
            lines.append(f" {r + 1} | {cells} |{exit_marker}")

        lines.append("   " + "+" + "--" * self.size + "+")

        # Vehicle legend
        lines.append("")
        lines.append("Vehicles:")
        for vid in sorted(self.vehicles.keys()):
            v = self.vehicles[vid]
            orient = "horizontal" if v.orientation == "h" else "vertical"
            target = " (TARGET)" if vid == "X" else ""
            lines.append(f"  {vid}: {orient}, length {v.length}{target}")

        return "\n".join(lines)

    def get_stats(self) -> str:
        """Get current game statistics."""
        return f"Moves: {self.moves_made} | Vehicles: {len(self.vehicles)} | Grid: {self.size}x{self.size} | Seed: {self.seed}"

    def get_rules(self) -> str:
        return (
            f"RUSH HOUR ({self.size}x{self.size})\n"
            "Slide vehicles to let the target car (X) reach the exit (>).\n"
            "Horizontal vehicles move left/right only.\n"
            "Vertical vehicles move up/down only.\n"
            "Vehicles cannot pass through each other.\n"
            "Move X to the right edge to win."
        )

    def get_commands(self) -> str:
        return (
            "Commands:\n"
            "  move <vehicle> <direction>  - Slide a vehicle (left/right/up/down)\n"
            "  hint                        - Get a hint\n"
            "  check                       - Check if solved\n"
            "  show                        - Show current state\n"
            "  menu                        - Return to menu"
        )
