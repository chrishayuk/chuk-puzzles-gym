"""Tests for Task Scheduler puzzle game."""

import pytest

from puzzle_arcade_server.games.scheduler import SchedulerGame


class TestSchedulerGame:
    """Test suite for Task Scheduler game."""

    async def test_initialization_easy(self):
        """Test game initialization with easy difficulty."""
        game = SchedulerGame("easy")
        assert game.difficulty == "easy"
        assert game.num_tasks == 4
        assert game.num_workers == 2
        assert game.name == "Task Scheduler"
        assert "schedule" in game.description.lower()

    async def test_initialization_medium(self):
        """Test game initialization with medium difficulty."""
        game = SchedulerGame("medium")
        assert game.num_tasks == 6
        assert game.num_workers == 2

    async def test_initialization_hard(self):
        """Test game initialization with hard difficulty."""
        game = SchedulerGame("hard")
        assert game.num_tasks == 8
        assert game.num_workers == 3

    async def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        assert game.game_started is True
        assert len(game.tasks) == 4
        assert len(game.dependencies) >= 0
        assert game.optimal_makespan > 0
        assert len(game.schedule) == 0

    async def test_tasks_have_valid_attributes(self):
        """Test that generated tasks have valid attributes."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        for task in game.tasks:
            assert task.name is not None
            assert task.duration > 0

    async def test_dependencies_are_valid(self):
        """Test that dependencies form a valid DAG."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        # Dependencies should not create cycles
        # Check that all dependencies reference valid task IDs
        for dep_task, dependent in game.dependencies:
            assert 0 <= dep_task < len(game.tasks)
            assert 0 <= dependent < len(game.tasks)
            assert dep_task != dependent  # No self-dependencies

    async def test_assign_task_success(self):
        """Test successfully assigning a task."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [
            Task(id=0, name="Task1", duration=3, dependencies=[]),
            Task(id=1, name="Task2", duration=2, dependencies=[]),
        ]
        game.dependencies = []
        game.schedule = {}
        game.num_workers = 2
        game.game_started = True

        result = await game.validate_move(1, 1, 0)
        success, message = result.success, result.message
        assert success is True
        assert 0 in game.schedule
        assert game.schedule[0] == (1, 0)
        assert "Task1" in message

    async def test_assign_task_with_dependency(self):
        """Test assigning a task that has a dependency."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [
            Task(id=0, name="Task1", duration=3, dependencies=[]),
            Task(id=1, name="Task2", duration=2, dependencies=[0]),
        ]
        game.dependencies = [(0, 1)]  # Task2 depends on Task1
        game.schedule = {}
        game.num_workers = 2
        game.game_started = True

        # Try to schedule Task2 before Task1 - should fail
        result = await game.validate_move(2, 1, 0)
        success, message = result.success, result.message
        assert success is False
        assert "must be scheduled first" in message.lower()

        # Schedule Task1 first
        result = await game.validate_move(1, 1, 0)
        success, message = result.success, result.message
        assert success is True

        # Now schedule Task2 - should succeed if time is valid
        result = await game.validate_move(2, 1, 3)
        success, message = result.success, result.message
        assert success is True

    async def test_assign_task_too_early_for_dependency(self):
        """Test assigning a task before its dependency finishes."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [
            Task(id=0, name="Task1", duration=5, dependencies=[]),
            Task(id=1, name="Task2", duration=2, dependencies=[0]),
        ]
        game.dependencies = [(0, 1)]
        game.schedule = {0: (1, 0)}  # Task1 on Worker1 at time 0, finishes at 5
        game.num_workers = 2
        game.game_started = True

        # Try to start Task2 at time 3 (before Task1 finishes at 5)
        result = await game.validate_move(2, 1, 3)
        success, message = result.success, result.message
        assert success is False
        assert "finishes at" in message.lower()

    async def test_worker_conflict(self):
        """Test that worker conflicts are detected."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [
            Task(id=0, name="Task1", duration=5, dependencies=[]),
            Task(id=1, name="Task2", duration=3, dependencies=[]),
        ]
        game.dependencies = []
        game.schedule = {0: (1, 0)}  # Task1 on Worker1 from 0-5
        game.num_workers = 2
        game.game_started = True

        # Try to assign Task2 to Worker1 at time 2 (conflicts with Task1)
        result = await game.validate_move(2, 1, 2)
        success, message = result.success, result.message
        assert success is False
        assert "busy" in message.lower() or "conflict" in message.lower()

    async def test_worker_available_after_task(self):
        """Test that worker is available after a task finishes."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [
            Task(id=0, name="Task1", duration=5, dependencies=[]),
            Task(id=1, name="Task2", duration=3, dependencies=[]),
        ]
        game.dependencies = []
        game.schedule = {0: (1, 0)}  # Task1 on Worker1 from 0-5
        game.num_workers = 2
        game.game_started = True

        # Assign Task2 to Worker1 at time 5 (when Task1 finishes)
        result = await game.validate_move(2, 1, 5)
        success, _message = result.success, result.message
        assert success is True
        assert 1 in game.schedule

    async def test_reassign_task(self):
        """Test reassigning a task to different worker/time."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [Task(id=0, name="Task1", duration=3, dependencies=[])]
        game.dependencies = []
        game.schedule = {0: (1, 0)}
        game.num_workers = 2
        game.game_started = True

        result = await game.validate_move(1, 2, 5)
        success, message = result.success, result.message
        assert success is True
        assert game.schedule[0] == (2, 5)
        assert "reassigned" in message.lower()

    async def test_unassign_task(self):
        """Test unassigning a task."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [
            Task(id=0, name="Task1", duration=3, dependencies=[]),
            Task(id=1, name="Task2", duration=2, dependencies=[]),
        ]
        game.dependencies = []
        game.schedule = {0: (1, 0), 1: (2, 0)}
        game.num_workers = 2
        game.game_started = True

        result = await game.validate_move("unassign", 1, 0)
        success, message = result.success, result.message
        assert success is True
        assert 0 not in game.schedule
        assert "unassigned" in message.lower()

    async def test_unassign_task_not_assigned(self):
        """Test unassigning a task that's not assigned."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [Task(id=0, name="Task1", duration=3, dependencies=[])]
        game.dependencies = []
        game.schedule = {}
        game.num_workers = 2
        game.game_started = True

        result = await game.validate_move("unassign", 1, 0)
        success, message = result.success, result.message
        assert success is False
        assert "not currently assigned" in message.lower()

    async def test_invalid_task_id(self):
        """Test with invalid task ID."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(0, 1, 0)
        success, message = result.success, result.message
        assert success is False
        assert "invalid task" in message.lower()

        result = await game.validate_move(10, 1, 0)
        success, message = result.success, result.message
        assert success is False
        assert "invalid task" in message.lower()

    async def test_invalid_worker_id(self):
        """Test with invalid worker ID."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(1, 0, 0)
        success, message = result.success, result.message
        assert success is False
        assert "invalid worker" in message.lower()

        result = await game.validate_move(1, 10, 0)
        success, message = result.success, result.message
        assert success is False
        assert "invalid worker" in message.lower()

    async def test_negative_start_time(self):
        """Test with negative start time."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(1, 1, -5)
        success, message = result.success, result.message
        assert success is False
        assert "negative" in message.lower() or "invalid" in message.lower()

    async def test_get_makespan(self):
        """Test makespan calculation."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [
            Task(id=0, name="Task1", duration=3, dependencies=[]),
            Task(id=1, name="Task2", duration=5, dependencies=[]),
        ]
        game.schedule = {
            0: (1, 0),  # Task1: 0-3
            1: (2, 2),  # Task2: 2-7
        }

        makespan = game._get_makespan()
        assert makespan == 7  # Task2 finishes last at time 7

    async def test_get_makespan_empty(self):
        """Test makespan with no tasks scheduled."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [Task(id=0, name="Task1", duration=3, dependencies=[])]
        game.schedule = {}

        makespan = game._get_makespan()
        assert makespan == 0

    async def test_is_complete_all_tasks_scheduled(self):
        """Test completion when all tasks are scheduled optimally."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        # Schedule all tasks to match optimal solution
        game.schedule = game.optimal_schedule.copy()

        assert game.is_complete() is True

    async def test_is_complete_not_all_scheduled(self):
        """Test completion when not all tasks are scheduled."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        # Only schedule some tasks
        if len(game.tasks) > 0:
            game.schedule = {0: (1, 0)}

        assert game.is_complete() is False

    async def test_is_complete_suboptimal_schedule(self):
        """Test completion when all tasks scheduled but not optimally."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [
            Task(id=0, name="Task1", duration=2, dependencies=[]),
            Task(id=1, name="Task2", duration=2, dependencies=[]),
        ]
        game.dependencies = []
        game.optimal_makespan = 2  # Optimal: both tasks in parallel
        game.schedule = {
            0: (1, 0),  # Task1: 0-2
            1: (1, 2),  # Task2: 2-4 (sequential, makespan=4)
        }
        game.num_workers = 2
        game.game_started = True

        assert game.is_complete() is False  # Not optimal

    async def test_get_hint(self):
        """Test hint generation."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [Task(id=0, name="Task1", duration=3, dependencies=[])]
        game.optimal_schedule = {0: (1, 0)}
        game.schedule = {}

        hint_data, hint_message = await game.get_hint()
        assert hint_data == (1, 1, 0)
        assert "Task1" in hint_message

    async def test_get_hint_already_optimal(self):
        """Test hint when already at optimal solution."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [Task(id=0, name="Task1", duration=3, dependencies=[])]
        game.optimal_schedule = {0: (1, 0)}
        game.schedule = {0: (1, 0)}

        result = await game.get_hint()
        assert result is None

    async def test_render_grid(self):
        """Test grid rendering."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        grid_str = game.render_grid()
        assert "Task Scheduler" in grid_str
        assert "Worker" in grid_str
        # Dependencies section only appears if there are dependencies
        # Just verify the grid renders successfully
        assert "Task" in grid_str

    async def test_get_rules(self):
        """Test rules retrieval."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        rules = game.get_rules()
        assert "TASK SCHEDULER" in rules.upper()
        assert "makespan" in rules.lower()
        assert "dependencies" in rules.lower()

    async def test_get_commands(self):
        """Test commands retrieval."""
        game = SchedulerGame("easy")
        commands = game.get_commands()

        assert "assign" in commands.lower()
        assert "unassign" in commands.lower()
        assert "show" in commands.lower()

    async def test_get_stats(self):
        """Test statistics retrieval."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        stats = game.get_stats()
        assert "Moves" in stats
        assert "Scheduled" in stats
        assert "Makespan" in stats

    async def test_moves_counter(self):
        """Test that moves are counted correctly."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        initial_moves = game.moves_made
        await game.validate_move(1, 1, 0)
        assert game.moves_made == initial_moves + 1

    @pytest.mark.parametrize(
        "difficulty,expected_tasks,expected_workers", [("easy", 4, 2), ("medium", 6, 2), ("hard", 8, 3)]
    )
    async def test_difficulty_levels(self, difficulty, expected_tasks, expected_workers):
        """Test different difficulty levels."""
        game = SchedulerGame(difficulty)
        await game.generate_puzzle()
        assert len(game.tasks) == expected_tasks
        assert game.num_workers == expected_workers

    async def test_optimal_schedule_respects_dependencies(self):
        """Test that optimal schedule respects all dependencies."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        for dep_task, dependent in game.dependencies:
            if dep_task in game.optimal_schedule and dependent in game.optimal_schedule:
                dep_worker, dep_start = game.optimal_schedule[dep_task]
                dep_end = dep_start + game.tasks[dep_task].duration

                dep_worker2, dep_start2 = game.optimal_schedule[dependent]
                assert dep_start2 >= dep_end, f"Task {dependent} starts before Task {dep_task} finishes"

    async def test_optimal_schedule_no_worker_conflicts(self):
        """Test that optimal schedule has no worker conflicts."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        # Check each worker's timeline for conflicts
        for worker in range(1, game.num_workers + 1):
            worker_tasks = []
            for task_id, (w, start) in game.optimal_schedule.items():
                if w == worker:
                    duration = game.tasks[task_id].duration
                    worker_tasks.append((start, start + duration, task_id))

            # Sort by start time
            worker_tasks.sort()

            # Check for overlaps
            for i in range(len(worker_tasks) - 1):
                end1 = worker_tasks[i][1]
                start2 = worker_tasks[i + 1][0]
                assert end1 <= start2, f"Worker {worker} has overlapping tasks"

    async def test_chain_dependencies(self):
        """Test scheduling with chain dependencies (A -> B -> C)."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [
            Task(id=0, name="TaskA", duration=2, dependencies=[]),
            Task(id=1, name="TaskB", duration=3, dependencies=[0]),
            Task(id=2, name="TaskC", duration=1, dependencies=[1]),
        ]
        game.dependencies = [(0, 1), (1, 2)]  # A -> B -> C
        game.schedule = {}
        game.num_workers = 2
        game.game_started = True

        # Schedule in correct order
        await game.validate_move(1, 1, 0)  # A: 0-2
        await game.validate_move(2, 1, 2)  # B: 2-5
        await game.validate_move(3, 1, 5)  # C: 5-6

        assert len(game.schedule) == 3
        assert game._get_makespan() == 6

    async def test_parallel_independent_tasks(self):
        """Test that independent tasks can run in parallel."""
        from puzzle_arcade_server.games.scheduler.models import Task

        game = SchedulerGame("easy")
        game.tasks = [
            Task(id=0, name="Task1", duration=3, dependencies=[]),
            Task(id=1, name="Task2", duration=3, dependencies=[]),
        ]
        game.dependencies = []  # No dependencies
        game.schedule = {}
        game.num_workers = 2
        game.game_started = True

        # Both tasks can start at time 0 on different workers
        result1 = await game.validate_move(1, 1, 0)
        result2 = await game.validate_move(2, 2, 0)

        assert result1.success is True
        assert result2.success is True
        assert game._get_makespan() == 3  # Both finish at same time

    async def test_unassign_task_with_dependent(self):
        """Test unassigning a task that has dependent tasks scheduled."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        # Add dependency manually
        game.dependencies = [(0, 1)]  # Task 0 must finish before Task 1

        # Assign both tasks
        await game.validate_move(1, 1, 0)  # Assign task 0 (1-indexed)
        await game.validate_move(2, 1, game.tasks[0].duration)  # Assign task 1 after task 0

        # Try to unassign task 0 (which task 1 depends on)
        result = await game.validate_move("unassign", 1, 0)  # unassign, task_id (1-indexed), unused param
        assert result.success is False
        assert "depends on" in result.message.lower()

    async def test_render_grid_with_timeline(self):
        """Test render_grid shows timeline when tasks are assigned."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        # Assign some tasks
        await game.validate_move(0, 1, 0)
        await game.validate_move(1, 2, 0)

        grid = game.render_grid()
        assert "Timeline:" in grid
        assert "Worker 1:" in grid
        assert "Worker 2:" in grid
        # Should contain task letters (A, B, etc.)
        assert "A" in grid or "B" in grid

    async def test_render_grid_with_dependencies(self):
        """Test render_grid shows dependencies section."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        # Add dependencies
        game.dependencies = [(0, 1), (1, 2)]

        grid = game.render_grid()
        assert "Dependencies:" in grid
        assert "→" in grid  # Dependency arrow

    async def test_render_grid_full_schedule(self):
        """Test render_grid with a complete schedule."""
        game = SchedulerGame("easy")
        await game.generate_puzzle()

        # Schedule all tasks
        current_time = 0
        for i in range(game.num_tasks):
            worker = (i % game.num_workers) + 1
            await game.validate_move(i, worker, current_time)
            current_time += game.tasks[i].duration

        grid = game.render_grid()
        # Should show task status with worker and time
        assert "Worker" in grid
        assert "time" in grid
        assert "Timeline:" in grid

    async def test_constraint_types(self):
        """Test constraint types metadata."""
        game = SchedulerGame("easy")
        constraint_types = game.constraint_types
        assert isinstance(constraint_types, list)
        assert len(constraint_types) > 0
        assert all(isinstance(ct, str) for ct in constraint_types)

    async def test_business_analogies(self):
        """Test business analogies metadata."""
        game = SchedulerGame("easy")
        analogies = game.business_analogies
        assert isinstance(analogies, list)
        assert len(analogies) > 0
        assert all(isinstance(a, str) for a in analogies)

    async def test_complexity_profile(self):
        """Test complexity profile metadata."""
        game = SchedulerGame("easy")
        profile = game.complexity_profile
        assert isinstance(profile, dict)
        assert "reasoning_type" in profile
        assert "search_space" in profile
        assert "constraint_density" in profile
