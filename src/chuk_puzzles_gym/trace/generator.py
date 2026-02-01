"""
Trace generator for puzzle games.

Generates step-by-step solution traces compatible with chuk-gym-core.
"""

from typing import Any

from chuk_gym_core import Step, StepOperation, Trace

from chuk_puzzles_gym.games._base import PuzzleGame


class TraceGenerator:
    """
    Generates solution traces for puzzle games.

    Traces are machine-verifiable sequences of steps that transform
    the initial puzzle state into the solved state.

    Usage:
        game = SudokuGame(difficulty="medium", seed=42)
        await game.generate_puzzle()

        generator = TraceGenerator()
        trace = generator.generate(game)

        # Trace contains step-by-step solution
        for step in trace.steps:
            print(f"{step.explanation}")
    """

    def generate(self, game: PuzzleGame) -> Trace:
        """
        Generate a solution trace for a puzzle game.

        Args:
            game: A puzzle game instance with a generated puzzle

        Returns:
            Trace with step-by-step solution
        """
        # Normalize game name: lowercase, spaces to underscores, remove special chars
        game_name = game.name.lower().replace(" ", "_")
        # Remove apostrophes and other non-alphanumeric chars (except underscore)
        game_name = "".join(c for c in game_name if c.isalnum() or c == "_")

        # Dispatch to game-specific generator
        if hasattr(self, f"_generate_{game_name}"):
            return getattr(self, f"_generate_{game_name}")(game)

        # Fall back to generic grid-based generator
        if hasattr(game, "grid") and hasattr(game, "solution"):
            return self._generate_grid_puzzle(game)

        # Last resort: generate from canonical solution
        if game.canonical_solution:
            return self._generate_from_canonical(game)

        # Empty trace if nothing else works
        return Trace(
            problem_id=f"{game_name}_{game.difficulty.value}_{game.seed}",
            steps=[],
        )

    def _generate_grid_puzzle(self, game: PuzzleGame) -> Trace:
        """Generate trace for a grid-based puzzle with solution."""
        problem_id = f"{game.name.lower().replace(' ', '_')}_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        # Get initial and solution grids (dynamically accessed attributes)
        grid = getattr(game, "grid", None)
        initial = getattr(game, "initial_grid", grid)
        solution = getattr(game, "solution", None)

        if solution is None:
            return Trace(problem_id=problem_id, steps=[])

        # Find all cells that need to be filled
        # Handle both 0 and -1 as empty values (different games use different conventions)
        moves: list[tuple[int, int, Any]] = []
        for row in range(len(solution)):
            for col in range(len(solution[row])):
                initial_val = initial[row][col]
                solution_val = solution[row][col]
                # Check if cell needs to be filled: initial is empty (0 or -1) and differs from solution
                is_empty = initial_val == 0 or initial_val == -1
                needs_fill = is_empty and solution_val != initial_val
                if needs_fill:
                    moves.append((row, col, solution_val))

        # Generate steps for each move
        for i, (row, col, value) in enumerate(moves):
            step = Step(
                index=i,
                operation=StepOperation.PLACE,
                before_state=self._format_cell_state(row, col, None, is_empty=True),
                after_state=self._format_cell_state(row, col, value, is_empty=False),
                output_value=value,
                position=(row + 1, col + 1),  # 1-indexed for user display
                rule_applied=self._infer_rule(game, row, col, value),
                explanation=self._generate_explanation(game, row, col, value),
            )
            steps.append(step)

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_from_canonical(self, game: PuzzleGame) -> Trace:
        """Generate trace from canonical solution list."""
        problem_id = f"{game.name.lower().replace(' ', '_')}_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        canonical = game.canonical_solution
        if not canonical:
            return Trace(problem_id=problem_id, steps=[])

        for i, move in enumerate(canonical):
            if isinstance(move, tuple) and len(move) >= 3:
                row, col, value = move[0], move[1], move[2]
                step = Step(
                    index=i,
                    operation=StepOperation.PLACE,
                    before_state=f"cell({row},{col})=empty",
                    after_state=f"cell({row},{col})={value}",
                    output_value=value,
                    position=(row, col),
                    explanation=f"Place {value} at position ({row}, {col})",
                )
            else:
                step = Step(
                    index=i,
                    operation=StepOperation.DEDUCE,
                    before_state=str(move),
                    after_state=str(move),
                    explanation=f"Move {i + 1}: {move}",
                )
            steps.append(step)

        return Trace(problem_id=problem_id, steps=steps)

    def _format_cell_state(self, row: int, col: int, value: Any, is_empty: bool = False) -> str:
        """Format cell state for step display."""
        if is_empty or value is None or value == -1:
            return f"cell(r{row + 1},c{col + 1})=empty"
        return f"cell(r{row + 1},c{col + 1})={value}"

    def _infer_rule(self, game: PuzzleGame, row: int, col: int, value: Any) -> str:
        """Infer the logical rule used to determine this value."""
        game_name = game.name.lower()

        # Game-specific rules
        if "sudoku" in game_name:
            return self._infer_sudoku_rule(game, row, col, value)
        elif "kenken" in game_name or "kakuro" in game_name:
            return "arithmetic_constraint"
        elif "nonogram" in game_name:
            return "line_constraint"
        elif "binary" in game_name:
            return "balance_constraint"

        return "constraint_propagation"

    def _infer_sudoku_rule(self, game: PuzzleGame, row: int, col: int, value: Any) -> str:
        """Infer the Sudoku-specific rule used."""
        # Get solution grid dynamically
        solution = getattr(game, "solution", None)
        if solution is None:
            return "elimination"

        # Check if this is the only candidate in the row
        row_vals = set(solution[row]) - {0}
        if len(row_vals) == 9:
            return "naked_single_row"

        # Check column
        col_vals = {solution[r][col] for r in range(9)} - {0}
        if len(col_vals) == 9:
            return "naked_single_column"

        # Check box
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        box_vals = set()
        for r in range(box_row, box_row + 3):
            for c in range(box_col, box_col + 3):
                if solution[r][c] != 0:
                    box_vals.add(solution[r][c])
        if len(box_vals) == 9:
            return "naked_single_box"

        return "elimination"

    def _generate_explanation(self, game: PuzzleGame, row: int, col: int, value: Any) -> str:
        """Generate a natural language explanation for the step."""
        game_name = game.name.lower()

        if "sudoku" in game_name:
            box_num = 3 * (row // 3) + (col // 3) + 1
            return (
                f"Place {value} at row {row + 1}, column {col + 1}. "
                f"This is the only valid digit for this cell considering "
                f"row {row + 1}, column {col + 1}, and box {box_num} constraints."
            )
        elif "binary" in game_name:
            v = "1" if value == 1 else "0"
            return (
                f"Place {v} at row {row + 1}, column {col + 1}. "
                f"This maintains the balance and avoids three consecutive same digits."
            )
        elif "futoshiki" in game_name:
            return f"Place {value} at row {row + 1}, column {col + 1}. This satisfies the inequality constraints."
        elif "kenken" in game_name:
            return f"Place {value} at row {row + 1}, column {col + 1}. This satisfies the cage arithmetic constraint."
        else:
            return f"Place {value} at row {row + 1}, column {col + 1}."

    def _identify_checkpoints(self, steps: list[Step]) -> list[int]:
        """Identify key milestone steps for partial credit."""
        if not steps:
            return []

        checkpoints = []
        total = len(steps)

        # Add checkpoints at 25%, 50%, 75%, 100%
        for pct in [0.25, 0.5, 0.75, 1.0]:
            idx = min(int(total * pct), total - 1)
            if idx not in checkpoints:
                checkpoints.append(idx)

        return checkpoints

    # Game-specific generators

    def _generate_sudoku(self, game: PuzzleGame) -> Trace:
        """Generate trace specifically for Sudoku."""
        return self._generate_grid_puzzle(game)

    def _generate_binary(self, game: PuzzleGame) -> Trace:
        """Generate trace for Binary puzzle."""
        return self._generate_grid_puzzle(game)

    def _generate_futoshiki(self, game: PuzzleGame) -> Trace:
        """Generate trace for Futoshiki puzzle."""
        return self._generate_grid_puzzle(game)

    def _generate_kenken(self, game: PuzzleGame) -> Trace:
        """Generate trace for KenKen puzzle."""
        return self._generate_grid_puzzle(game)

    def _generate_kakuro(self, game: PuzzleGame) -> Trace:
        """Generate trace for Kakuro puzzle."""
        return self._generate_grid_puzzle(game)

    def _generate_nonogram(self, game: PuzzleGame) -> Trace:
        """Generate trace for Nonogram puzzle."""
        problem_id = f"nonogram_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        if hasattr(game, "grid") and hasattr(game, "solution"):
            initial = game.grid
            solution = game.solution

            step_idx = 0
            for row in range(len(solution)):
                for col in range(len(solution[row])):
                    if solution[row][col] != initial[row][col]:
                        is_filled = solution[row][col] == 1
                        step = Step(
                            index=step_idx,
                            operation=StepOperation.PLACE if is_filled else StepOperation.ELIMINATE,
                            before_state=f"cell(r{row + 1},c{col + 1})=unknown",
                            after_state=f"cell(r{row + 1},c{col + 1})={'filled' if is_filled else 'empty'}",
                            output_value=is_filled,
                            position=(row + 1, col + 1),
                            rule_applied="line_logic",
                            explanation=f"{'Fill' if is_filled else 'Mark empty'} cell at row {row + 1}, column {col + 1} based on row/column clues.",
                        )
                        steps.append(step)
                        step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_mastermind(self, game: PuzzleGame) -> Trace:
        """Generate trace for Mastermind (code-breaking)."""
        problem_id = f"mastermind_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        if hasattr(game, "secret_code") and game.secret_code:
            # For Mastermind, the solution is discovering the code
            secret = game.secret_code
            code_str = " ".join(str(c) for c in secret)
            step = Step(
                index=0,
                operation=StepOperation.DEDUCE,
                before_state="secret_code=unknown",
                after_state=f"secret_code={code_str}",
                output_value=secret,
                rule_applied="deductive_elimination",
                explanation=f"The secret code is {code_str}. Discovered through systematic guessing and feedback analysis.",
            )
            steps.append(step)

        return Trace(problem_id=problem_id, steps=steps)

    def _generate_einstein(self, game: PuzzleGame) -> Trace:
        """Generate trace for Einstein puzzle."""
        problem_id = f"einstein_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        if hasattr(game, "solution") and game.solution:
            # Einstein has assignments: list of HouseAssignment objects
            solution = game.solution
            step_idx = 0
            attributes = ["color", "nationality", "drink", "smoke", "pet"]

            for house_idx, house_data in enumerate(solution):
                for attr in attributes:
                    value = getattr(house_data, attr, None)
                    if value:
                        step = Step(
                            index=step_idx,
                            operation=StepOperation.DEDUCE,
                            before_state=f"house{house_idx + 1}.{attr}=unknown",
                            after_state=f"house{house_idx + 1}.{attr}={value}",
                            output_value=value,
                            position=(house_idx + 1,),
                            rule_applied="logical_deduction",
                            explanation=f"House {house_idx + 1} has {attr}={value}, deduced from the clues.",
                        )
                        steps.append(step)
                        step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_logic(self, game: PuzzleGame) -> Trace:
        """Generate trace for Logic Grid puzzle."""
        problem_id = f"logic_grid_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        if hasattr(game, "solution") and game.solution:
            # Logic Grid has solution: dict[person -> PersonAttributes]
            solution = game.solution
            step_idx = 0
            attributes = ["color", "pet", "drink"]

            for person, attrs in solution.items():
                for category in attributes:
                    value = getattr(attrs, category, None)
                    if value:
                        step = Step(
                            index=step_idx,
                            operation=StepOperation.DEDUCE,
                            before_state=f"{person}.{category}=unknown",
                            after_state=f"{person}.{category}={value}",
                            output_value=value,
                            rule_applied="logical_elimination",
                            explanation=f"{person} is associated with {category}={value}.",
                        )
                        steps.append(step)
                        step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_logic_grid(self, game: PuzzleGame) -> Trace:
        """Generate trace for Logic Grid puzzle (alias for _generate_logic)."""
        return self._generate_logic(game)

    def _generate_hitori(self, game: PuzzleGame) -> Trace:
        """Generate trace for Hitori puzzle."""
        problem_id = f"hitori_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        if hasattr(game, "solution") and game.solution:
            # Hitori has solution: 2D bool grid (True = shaded)
            solution = game.solution
            step_idx = 0

            for row in range(len(solution)):
                for col in range(len(solution[row])):
                    if solution[row][col]:  # Cell should be shaded
                        step = Step(
                            index=step_idx,
                            operation=StepOperation.ELIMINATE,
                            before_state=f"cell(r{row + 1},c{col + 1})=unshaded",
                            after_state=f"cell(r{row + 1},c{col + 1})=shaded",
                            output_value=True,
                            position=(row + 1, col + 1),
                            rule_applied="duplicate_elimination",
                            explanation=f"Shade cell at row {row + 1}, column {col + 1} to eliminate duplicate.",
                        )
                        steps.append(step)
                        step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_bridges(self, game: PuzzleGame) -> Trace:
        """Generate trace for Bridges puzzle."""
        problem_id = f"bridges_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        if hasattr(game, "solution") and game.solution:
            # Bridges has solution: dict[(r1,c1,r2,c2) -> bridge_count]
            solution = game.solution
            step_idx = 0

            for (r1, c1, r2, c2), count in solution.items():
                if count > 0:
                    step = Step(
                        index=step_idx,
                        operation=StepOperation.PLACE,
                        before_state=f"bridge({r1 + 1},{c1 + 1})-({r2 + 1},{c2 + 1})=0",
                        after_state=f"bridge({r1 + 1},{c1 + 1})-({r2 + 1},{c2 + 1})={count}",
                        output_value=count,
                        position=(r1 + 1, c1 + 1, r2 + 1, c2 + 1),
                        rule_applied="connectivity_constraint",
                        explanation=f"Place {count} bridge(s) between islands at ({r1 + 1},{c1 + 1}) and ({r2 + 1},{c2 + 1}).",
                    )
                    steps.append(step)
                    step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_knapsack(self, game: PuzzleGame) -> Trace:
        """Generate trace for Knapsack puzzle."""
        problem_id = f"knapsack_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        if hasattr(game, "optimal_selection") and game.optimal_selection:
            # Knapsack has optimal_selection: list[bool]
            items = getattr(game, "items", [])
            step_idx = 0

            for i, selected in enumerate(game.optimal_selection):
                if selected:
                    item_name = items[i].name if i < len(items) else f"Item {i + 1}"
                    item_weight = items[i].weight if i < len(items) else 0
                    item_value = items[i].value if i < len(items) else 0
                    step = Step(
                        index=step_idx,
                        operation=StepOperation.PLACE,
                        before_state=f"item({item_name})=not_selected",
                        after_state=f"item({item_name})=selected",
                        output_value=True,
                        position=(i + 1,),
                        rule_applied="optimization",
                        explanation=f"Select {item_name} (weight: {item_weight}, value: {item_value}) for optimal value.",
                    )
                    steps.append(step)
                    step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_lights_out(self, game: PuzzleGame) -> Trace:
        """Generate trace for Lights Out puzzle."""
        problem_id = f"lights_out_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        if hasattr(game, "presses") and game.presses:
            # Lights Out has presses: 2D int grid (1 = press needed)
            presses = game.presses
            step_idx = 0
            size = len(presses)

            for row in range(size):
                for col in range(len(presses[row])):
                    if presses[row][col] == 1:
                        step = Step(
                            index=step_idx,
                            operation=StepOperation.PLACE,
                            before_state=f"cell(r{row + 1},c{col + 1})=not_pressed",
                            after_state=f"cell(r{row + 1},c{col + 1})=pressed",
                            output_value=True,
                            position=(row + 1, col + 1),
                            rule_applied="xor_toggle",
                            explanation=f"Press light at row {row + 1}, column {col + 1} to toggle it and neighbors.",
                        )
                        steps.append(step)
                        step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_minesweeper(self, game: PuzzleGame) -> Trace:
        """Generate trace for Minesweeper puzzle."""
        problem_id = f"minesweeper_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        if hasattr(game, "mines") and game.mines:
            # Minesweeper has mines: 2D bool grid (True = mine)
            mines = game.mines
            size = len(mines)
            step_idx = 0

            # First, mark all mines as flagged
            for row in range(size):
                for col in range(len(mines[row])):
                    if mines[row][col]:
                        step = Step(
                            index=step_idx,
                            operation=StepOperation.ELIMINATE,
                            before_state=f"cell(r{row + 1},c{col + 1})=unknown",
                            after_state=f"cell(r{row + 1},c{col + 1})=mine",
                            output_value=True,
                            position=(row + 1, col + 1),
                            rule_applied="mine_identification",
                            explanation=f"Flag cell at row {row + 1}, column {col + 1} as a mine.",
                        )
                        steps.append(step)
                        step_idx += 1

            # Then, reveal all safe cells
            for row in range(size):
                for col in range(len(mines[row])):
                    if not mines[row][col]:
                        counts = getattr(game, "counts", None)
                        count = counts[row][col] if counts else 0
                        step = Step(
                            index=step_idx,
                            operation=StepOperation.DEDUCE,
                            before_state=f"cell(r{row + 1},c{col + 1})=unknown",
                            after_state=f"cell(r{row + 1},c{col + 1})={count}",
                            output_value=count,
                            position=(row + 1, col + 1),
                            rule_applied="safe_reveal",
                            explanation=f"Reveal cell at row {row + 1}, column {col + 1} ({count} adjacent mines).",
                        )
                        steps.append(step)
                        step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_scheduler(self, game: PuzzleGame) -> Trace:
        """Generate trace for Scheduler puzzle."""
        problem_id = f"scheduler_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        if hasattr(game, "optimal_schedule") and game.optimal_schedule:
            # Scheduler has optimal_schedule: dict[task_id -> (worker_id, start_time)]
            tasks = getattr(game, "tasks", [])
            step_idx = 0

            # Sort by start time for logical ordering
            sorted_schedule = sorted(game.optimal_schedule.items(), key=lambda x: (x[1][1], x[0]))

            for task_id, (worker_id, start_time) in sorted_schedule:
                task = tasks[task_id] if task_id < len(tasks) else None
                task_name = task.name if task else f"Task {task_id + 1}"
                duration = task.duration if task else 0
                end_time = start_time + duration

                step = Step(
                    index=step_idx,
                    operation=StepOperation.PLACE,
                    before_state=f"task({task_name})=unscheduled",
                    after_state=f"task({task_name})=worker{worker_id}@{start_time}-{end_time}",
                    output_value=(worker_id, start_time),
                    position=(task_id + 1,),
                    rule_applied="scheduling_constraint",
                    explanation=f"Schedule {task_name} on Worker {worker_id} from time {start_time} to {end_time}.",
                )
                steps.append(step)
                step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_task_scheduler(self, game: PuzzleGame) -> Trace:
        """Generate trace for Task Scheduler (alias for _generate_scheduler)."""
        return self._generate_scheduler(game)

    def _generate_slitherlink(self, game: PuzzleGame) -> Trace:
        """Generate trace for Slitherlink puzzle."""
        problem_id = f"slitherlink_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        step_idx = 0

        # Horizontal edges
        if hasattr(game, "solution_h_edges") and game.solution_h_edges:
            for row in range(len(game.solution_h_edges)):
                for col in range(len(game.solution_h_edges[row])):
                    if game.solution_h_edges[row][col] == 1:
                        step = Step(
                            index=step_idx,
                            operation=StepOperation.PLACE,
                            before_state=f"h_edge(r{row + 1},c{col + 1})=unknown",
                            after_state=f"h_edge(r{row + 1},c{col + 1})=line",
                            output_value=1,
                            position=(row + 1, col + 1),
                            rule_applied="loop_constraint",
                            explanation=f"Draw horizontal edge at row {row + 1}, column {col + 1}.",
                        )
                        steps.append(step)
                        step_idx += 1

        # Vertical edges
        if hasattr(game, "solution_v_edges") and game.solution_v_edges:
            for row in range(len(game.solution_v_edges)):
                for col in range(len(game.solution_v_edges[row])):
                    if game.solution_v_edges[row][col] == 1:
                        step = Step(
                            index=step_idx,
                            operation=StepOperation.PLACE,
                            before_state=f"v_edge(r{row + 1},c{col + 1})=unknown",
                            after_state=f"v_edge(r{row + 1},c{col + 1})=line",
                            output_value=1,
                            position=(row + 1, col + 1),
                            rule_applied="loop_constraint",
                            explanation=f"Draw vertical edge at row {row + 1}, column {col + 1}.",
                        )
                        steps.append(step)
                        step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_sokoban(self, game: PuzzleGame) -> Trace:
        """Generate trace for Sokoban puzzle."""
        problem_id = f"sokoban_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        if hasattr(game, "goals") and game.goals:
            # For Sokoban, the trace shows the goal state
            # Each box needs to reach a goal position
            step_idx = 0

            # Find boxes in the initial grid (2 = box, 5 = box on goal)
            grid = getattr(game, "grid", [])
            boxes = []
            for r in range(len(grid)):
                for c in range(len(grid[r])):
                    if grid[r][c] in (2, 5):
                        boxes.append((r, c))

            # Match boxes to goals (simplified - assumes 1:1 mapping)
            for i, goal in enumerate(game.goals):
                goal_r, goal_c = goal
                box_pos = boxes[i] if i < len(boxes) else None

                if box_pos:
                    box_r, box_c = box_pos
                    step = Step(
                        index=step_idx,
                        operation=StepOperation.PLACE,
                        before_state=f"box{i + 1}=({box_r + 1},{box_c + 1})",
                        after_state=f"box{i + 1}=({goal_r + 1},{goal_c + 1})",
                        output_value=(goal_r + 1, goal_c + 1),
                        position=(goal_r + 1, goal_c + 1),
                        rule_applied="goal_placement",
                        explanation=f"Push box {i + 1} from ({box_r + 1},{box_c + 1}) to goal at ({goal_r + 1},{goal_c + 1}).",
                    )
                    steps.append(step)
                    step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_einstein_s_puzzle(self, game: PuzzleGame) -> Trace:
        """Generate trace for Einstein's Puzzle (alias with different name format)."""
        return self._generate_einstein(game)

    def _generate_einstein_puzzle(self, game: PuzzleGame) -> Trace:
        """Generate trace for Einstein's Puzzle (handles 'einstein's puzzle' -> 'einstein_puzzle')."""
        return self._generate_einstein(game)

    def _generate_einsteins_puzzle(self, game: PuzzleGame) -> Trace:
        """Generate trace for Einstein's Puzzle (handles 'einstein's puzzle' -> 'einsteins_puzzle')."""
        return self._generate_einstein(game)

    def _generate_graph_coloring(self, game: PuzzleGame) -> Trace:
        """Generate trace for Graph Coloring puzzle."""
        problem_id = f"graph_coloring_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        solution = getattr(game, "solution", {})
        initial_coloring = getattr(game, "initial_coloring", {})
        step_idx = 0

        for node in sorted(solution.keys()):
            if node not in initial_coloring:
                color = solution[node]
                step = Step(
                    index=step_idx,
                    operation=StepOperation.PLACE,
                    before_state=f"node({node})=uncolored",
                    after_state=f"node({node})=color{color}",
                    output_value=color,
                    position=(node,),
                    rule_applied="graph_coloring_constraint",
                    explanation=f"Color node {node} with color {color}, avoiding conflicts with adjacent nodes.",
                )
                steps.append(step)
                step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_cryptarithmetic(self, game: PuzzleGame) -> Trace:
        """Generate trace for Cryptarithmetic puzzle."""
        problem_id = f"cryptarithmetic_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        letter_mapping = getattr(game, "letter_mapping", {})
        initial_mapping = getattr(game, "initial_mapping", {})
        step_idx = 0

        for letter in sorted(letter_mapping.keys()):
            if letter not in initial_mapping:
                digit = letter_mapping[letter]
                step = Step(
                    index=step_idx,
                    operation=StepOperation.DEDUCE,
                    before_state=f"letter({letter})=unknown",
                    after_state=f"letter({letter})={digit}",
                    output_value=digit,
                    rule_applied="arithmetic_constraint",
                    explanation=f"Assign digit {digit} to letter {letter} to satisfy the equation.",
                )
                steps.append(step)
                step_idx += 1

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )

    def _generate_rush_hour(self, game: PuzzleGame) -> Trace:
        """Generate trace for Rush Hour puzzle."""
        problem_id = f"rush_hour_{game.difficulty.value}_{game.seed}"
        steps: list[Step] = []

        # Rush Hour traces are move sequences; generate from hint system
        vehicles = getattr(game, "vehicles", {})
        if vehicles:
            step = Step(
                index=0,
                operation=StepOperation.DEDUCE,
                before_state="target_car=blocked",
                after_state="target_car=exit",
                output_value="solve",
                rule_applied="sequential_planning",
                explanation=f"Slide vehicles to clear a path for car X to reach the exit. "
                f"Minimum solution: {getattr(game, 'min_solution_moves', '?')} moves.",
            )
            steps.append(step)

        return Trace(
            problem_id=problem_id,
            steps=steps,
            checkpoints=self._identify_checkpoints(steps),
        )


def generate_trace(game: PuzzleGame) -> Trace:
    """
    Convenience function to generate a trace for a puzzle game.

    Args:
        game: A puzzle game instance with a generated puzzle

    Returns:
        Trace with step-by-step solution
    """
    generator = TraceGenerator()
    return generator.generate(game)
