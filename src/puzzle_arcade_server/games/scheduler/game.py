"""Task Scheduler optimization puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import SchedulerConfig
from .constants import TASK_NAMES
from .enums import SchedulerAction
from .models import Task


class SchedulerGame(PuzzleGame):
    """Task Scheduler optimization puzzle game.

    Schedule tasks with dependencies and resource constraints
    to minimize total completion time (makespan).
    Demonstrates temporal reasoning and optimization.
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Scheduler game.

        Args:
            difficulty: Game difficulty level (easy/medium/hard)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Configuration using Pydantic model
        self.config = SchedulerConfig.from_difficulty(self.difficulty)
        self.num_tasks: int = self.config.num_tasks
        self.num_workers: int = self.config.num_workers

        # Task properties - using Task model
        self.tasks: list[Task] = []
        self.dependencies: list[tuple[int, int]] = []  # (task_a, task_b) means A must finish before B starts

        # Player's schedule: task_id -> (worker_id, start_time)
        self.schedule: dict[int, tuple[int, int]] = {}

        # Optimal solution
        self.optimal_makespan = 0
        self.optimal_schedule: dict[int, tuple[int, int]] = {}

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Task Scheduler"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Schedule tasks with dependencies to minimize completion time"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["optimization", "precedence", "resource_allocation", "makespan_minimization"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["project_scheduling", "sprint_planning", "team_allocation", "workflow_optimization"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "optimization", "search_space": "exponential", "constraint_density": "moderate"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = tasks to schedule."""
        return len(self.tasks) if hasattr(self, "tasks") else None

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Task Scheduler."""
        from ...models import DifficultyLevel

        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 4,
            DifficultyLevel.HARD.value: 5,
        }.get(self.difficulty.value, 3)
        n_workers = self.num_workers if hasattr(self, "num_workers") else 3
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=float(n_workers),
            state_observability=1.0,
            constraint_density=0.5,
        )

    async def generate_puzzle(self) -> None:
        """Generate a new Scheduler puzzle."""
        # Generate tasks with random durations using constants
        self.tasks = []
        for i in range(self.num_tasks):
            name = TASK_NAMES[i] if i < len(TASK_NAMES) else f"Task {chr(65 + i)}"
            duration = self._rng.randint(2, 8)
            dependencies: list[int] = []
            task = Task(id=i, name=name, duration=duration, dependencies=dependencies)
            self.tasks.append(task)

        # Generate dependencies (DAG - no cycles)
        self.dependencies = []
        for i in range(self.num_tasks):
            for j in range(i + 1, self.num_tasks):
                if self._rng.random() < self.config.dependency_prob:
                    # Task i must complete before task j can start
                    self.dependencies.append((i, j))

        # Calculate optimal solution
        self._solve_optimal()

        # Initialize empty schedule
        self.schedule = {}
        self.moves_made = 0
        self.game_started = True

    def _solve_optimal(self) -> None:
        """Solve the scheduling problem optimally using greedy approach with topological sort."""
        # Build dependency graph
        in_degree = [0] * self.num_tasks
        adj_list: list[list[int]] = [[] for _ in range(self.num_tasks)]

        for task_a, task_b in self.dependencies:
            adj_list[task_a].append(task_b)
            in_degree[task_b] += 1

        # Topological sort with earliest start times
        earliest_start = [0] * self.num_tasks
        queue = [i for i in range(self.num_tasks) if in_degree[i] == 0]

        # Calculate earliest start times
        while queue:
            task = queue.pop(0)
            for dependent in adj_list[task]:
                # Dependent can't start until current task finishes
                earliest_start[dependent] = max(
                    earliest_start[dependent], earliest_start[task] + self.tasks[task].duration
                )
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Schedule tasks greedily with proper dependency handling
        worker_available = [0] * self.num_workers
        self.optimal_schedule = {}

        # Sort tasks by earliest start time
        sorted_tasks = sorted(range(self.num_tasks), key=lambda t: earliest_start[t])

        for task_id in sorted_tasks:
            # Calculate actual earliest start based on scheduled dependencies
            actual_earliest_start = 0
            for dep_task, dependent in self.dependencies:
                if dependent == task_id and dep_task in self.optimal_schedule:
                    dep_worker, dep_start = self.optimal_schedule[dep_task]
                    dep_end = dep_start + self.tasks[dep_task].duration
                    actual_earliest_start = max(actual_earliest_start, dep_end)

            # Find the worker that can start this task earliest
            # considering both worker availability and actual dependency finish times
            best_worker = 0
            best_start_time = max(worker_available[0], actual_earliest_start)

            for worker_id in range(1, self.num_workers):
                # This task can't start before its dependencies finish
                # and can't start before the worker is available
                candidate_start = max(worker_available[worker_id], actual_earliest_start)

                if candidate_start < best_start_time:
                    best_start_time = candidate_start
                    best_worker = worker_id

            # Store 1-indexed worker_id for consistency
            self.optimal_schedule[task_id] = (best_worker + 1, best_start_time)
            worker_available[best_worker] = best_start_time + self.tasks[task_id].duration

        # Calculate makespan
        self.optimal_makespan = max(worker_available) if worker_available else 0

    async def validate_move(self, task_id: int | str, worker_id: int, start_time: int) -> MoveResult:
        """Assign a task to a worker at a specific start time, or unassign a task.

        Args:
            task_id: Task number (1-indexed) or "unassign" action
            worker_id: Worker number (1-indexed) when assigning, or task number when unassigning
            start_time: Start time (0 or positive integer) when assigning, unused when unassigning

        Returns:
            MoveResult with success status and message
        """
        # Handle unassign action
        if isinstance(task_id, str) and task_id.lower() == SchedulerAction.UNASSIGN.value:
            return await self._unassign_task(worker_id)

        # Convert to 0-indexed
        task_id = int(task_id) - 1
        worker_id -= 1

        # Validate inputs
        if not (0 <= task_id < self.num_tasks):
            return MoveResult(success=False, message=f"Invalid task number. Use 1-{self.num_tasks}.")

        if not (0 <= worker_id < self.num_workers):
            return MoveResult(success=False, message=f"Invalid worker number. Use 1-{self.num_workers}.")

        if start_time < 0:
            return MoveResult(success=False, message="Start time must be non-negative.")

        # Check if task is already scheduled - allow reassignment
        is_reassignment = task_id in self.schedule

        # Check dependencies
        for dep_task, dependent in self.dependencies:
            if dependent == task_id:
                # This task depends on dep_task
                if dep_task not in self.schedule:
                    return MoveResult(
                        success=False,
                        message=f"Cannot schedule - {self.tasks[dep_task].name} must be scheduled first.",
                    )

                dep_worker, dep_start = self.schedule[dep_task]
                dep_end = dep_start + self.tasks[dep_task].duration

                if start_time < dep_end:
                    return MoveResult(
                        success=False,
                        message=f"Cannot start at {start_time} - {self.tasks[dep_task].name} finishes at {dep_end}.",
                    )

        # Check worker availability (no overlap)
        task_duration = self.tasks[task_id].duration
        task_end = start_time + task_duration

        for other_task_id, (other_worker, other_start) in self.schedule.items():
            if other_worker == worker_id + 1:  # other_worker is 1-indexed in schedule
                other_end = other_start + self.tasks[other_task_id].duration
                # Check for overlap
                if not (task_end <= other_start or start_time >= other_end):
                    return MoveResult(
                        success=False,
                        message=f"Worker {worker_id + 1} is busy with {self.tasks[other_task_id].name} from {other_start} to {other_end}.",
                    )

        # Schedule the task (store 1-indexed worker_id for consistency with user input)
        self.schedule[task_id] = (worker_id + 1, start_time)
        self.moves_made += 1

        task_name = self.tasks[task_id].name
        if is_reassignment:
            return MoveResult(
                success=True,
                message=f"Reassigned {task_name} to Worker {worker_id + 1} at time {start_time}",
                state_changed=True,
            )
        else:
            return MoveResult(
                success=True,
                message=f"Scheduled {task_name} on Worker {worker_id + 1} at time {start_time}",
                state_changed=True,
            )

    async def _unassign_task(self, task_id: int) -> MoveResult:
        """Unassign a task from the schedule.

        Args:
            task_id: Task number (1-indexed)

        Returns:
            MoveResult with success status and message
        """
        task_id -= 1

        if task_id not in self.schedule:
            return MoveResult(success=False, message=f"{self.tasks[task_id].name} is not currently assigned.")

        # Check if any scheduled task depends on this one
        for dep_task, dependent in self.dependencies:
            if dep_task == task_id and dependent in self.schedule:
                return MoveResult(
                    success=False,
                    message=f"Cannot unassign - {self.tasks[dependent].name} depends on {self.tasks[task_id].name}.",
                )

        del self.schedule[task_id]
        self.moves_made += 1
        return MoveResult(success=True, message=f"Unassigned {self.tasks[task_id].name}", state_changed=True)

    def _get_makespan(self) -> int:
        """Calculate the makespan (total completion time) of current schedule."""
        if not self.schedule:
            return 0

        max_end = 0
        for task_id, (_worker, start_time) in self.schedule.items():
            end_time = start_time + self.tasks[task_id].duration
            max_end = max(max_end, end_time)

        return max_end

    def is_complete(self) -> bool:
        """Check if all tasks are scheduled optimally."""
        # All tasks must be scheduled
        if len(self.schedule) != self.num_tasks:
            return False

        # Check if makespan is optimal
        return self._get_makespan() == self.optimal_makespan

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None
        """
        # Find an unscheduled task that's in the optimal solution
        for task_id in range(self.num_tasks):
            if task_id not in self.schedule and task_id in self.optimal_schedule:
                worker, start_time = self.optimal_schedule[task_id]
                # worker is already 1-indexed in optimal_schedule
                hint_data = (task_id + 1, worker, start_time)
                hint_message = f"Try scheduling {self.tasks[task_id].name} on Worker {worker} at time {start_time}"
                return hint_data, hint_message

        return None

    def render_grid(self) -> str:
        """Render the current schedule as ASCII art.

        Returns:
            String representation of the schedule
        """
        lines = []

        lines.append("Task Scheduler")
        lines.append(f"Workers: {self.num_workers} | Tasks: {self.num_tasks}")
        lines.append(f"Current Makespan: {self._get_makespan()}")
        lines.append(f"Optimal Makespan: {self.optimal_makespan}")
        lines.append("")

        # Tasks table
        lines.append("Tasks:")
        lines.append("  # | Name   | Duration | Status")
        lines.append("  --+--------+----------+----------------------------------")

        for task in self.tasks:
            task_id = task.id
            status = "Not scheduled"

            if task_id in self.schedule:
                worker, start_time = self.schedule[task_id]
                end_time = start_time + task.duration
                status = f"Worker {worker}, time {start_time}-{end_time}"

            lines.append(f"  {task_id + 1:2d} | {task.name:<6s} | {task.duration:4d}hrs  | {status}")

        # Dependencies
        if self.dependencies:
            lines.append("")
            lines.append("Dependencies:")
            for task_a, task_b in self.dependencies:
                lines.append(f"  {self.tasks[task_a].name} → {self.tasks[task_b].name}")

        # Timeline visualization
        if self.schedule:
            lines.append("")
            lines.append("Timeline:")
            makespan = self._get_makespan()

            for worker_id in range(self.num_workers):
                timeline = ["."] * (makespan + 1)

                for task_id, (w, start) in self.schedule.items():
                    if w == worker_id + 1:
                        duration = self.tasks[task_id].duration
                        task_letter = chr(65 + task_id)  # A, B, C...

                        for t in range(start, start + duration):
                            if t <= makespan:
                                timeline[t] = task_letter

                timeline_str = "".join(timeline)
                lines.append(f"  Worker {worker_id + 1}: {timeline_str}")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Scheduler.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return f"""TASK SCHEDULER RULES:
- Schedule all {self.num_tasks} tasks across {self.num_workers} workers
- Each task has a duration in hours
- Tasks with dependencies must wait for predecessors
- Workers can only do one task at a time
- Goal: Minimize makespan (total completion time)
- Optimal makespan: {self.optimal_makespan} hours
- This is an OPTIMIZATION problem!"""

    def get_commands(self) -> str:
        """Get the available commands for Scheduler.

        Returns:
            Multi-line string describing available commands
        """
        return """TASK SCHEDULER COMMANDS:
  assign <task> <worker> <time>  - Schedule a task (e.g., 'assign 1 2 5')
  unassign <task>                - Remove task from schedule
  show                           - Display current schedule
  hint                           - Get scheduling hint
  check                          - Check if schedule is optimal
  solve                          - Show optimal schedule (ends game)
  menu                           - Return to game selection
  quit                           - Exit the server"""

    def get_stats(self) -> str:
        """Get current game statistics.

        Returns:
            String with game stats
        """
        scheduled = len(self.schedule)
        makespan = self._get_makespan()
        optimality = (self.optimal_makespan / makespan * 100) if makespan > 0 else 0

        return f"Moves: {self.moves_made} | Scheduled: {scheduled}/{self.num_tasks} | Makespan: {makespan}/{self.optimal_makespan}hrs ({optimality:.0f}%) | Seed: {self.seed}"
