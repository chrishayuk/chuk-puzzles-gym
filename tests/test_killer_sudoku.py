"""Tests for Killer Sudoku puzzle game."""

from puzzle_arcade_server.games.killer_sudoku import KillerSudokuGame


class TestKillerSudokuGame:
    """Test suite for Killer Sudoku game."""

    async def test_initialization(self):
        """Test game initialization."""
        game = KillerSudokuGame("easy")
        assert game.difficulty == "easy"
        assert game.size == 9
        assert game.name == "Killer Sudoku"
        assert "Kakuro" in game.description

    async def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        assert game.game_started is True
        assert game.moves_made == 0
        assert len(game.grid) == 9
        assert len(game.grid[0]) == 9
        assert len(game.solution) == 9
        assert len(game.cages) > 0

        # Grid should start empty
        assert all(cell == 0 for row in game.grid for cell in row)

    async def test_generate_cages(self):
        """Test cage generation."""
        game = KillerSudokuGame("easy")
        game.solution = [[1, 2, 3, 4, 5, 6, 7, 8, 9] for _ in range(9)]
        game._generate_cages()

        # Should have cages
        assert len(game.cages) > 0

        # Each cage should have cells and target sum
        for cage in game.cages:
            assert len(cage.cells) >= 1  # At least 1 cell per cage
            assert cage.target > 0

            # Target sum should match solution
            actual_sum = sum(game.solution[r][c] for r, c in cage.cells)
            assert actual_sum == cage.target

    async def test_is_valid_move_row_conflict(self):
        """Test move validation with row conflict."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        game.grid[0][0] = 5
        assert game.is_valid_move(0, 1, 5) is False  # Same row

    async def test_is_valid_move_column_conflict(self):
        """Test move validation with column conflict."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        game.grid[0][0] = 5
        assert game.is_valid_move(1, 0, 5) is False  # Same column

    async def test_is_valid_move_box_conflict(self):
        """Test move validation with 3x3 box conflict."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        game.grid[0][0] = 5
        assert game.is_valid_move(1, 1, 5) is False  # Same 3x3 box

    async def test_is_valid_move_success(self):
        """Test successful move validation."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        game.grid[0][0] = 5
        assert game.is_valid_move(0, 4, 1) is True  # Different box, row, col

    async def test_check_cage_constraints_duplicate(self):
        """Test cage constraint with duplicate values."""
        from puzzle_arcade_server.games.killer_sudoku.models import Cage

        game = KillerSudokuGame("easy")
        game.cages = [
            Cage(cells=[(0, 0), (0, 1), (0, 2)], operation=None, target=6),  # Target sum 6
        ]
        game.grid = [[0 for _ in range(9)] for _ in range(9)]

        # Place duplicate in cage
        game.grid[0][0] = 2
        game.grid[0][1] = 2

        assert game._check_cage_constraints(game.grid, 0, 1) is False

    async def test_check_cage_constraints_exceed_sum(self):
        """Test cage constraint when sum is exceeded."""
        from puzzle_arcade_server.games.killer_sudoku.models import Cage

        game = KillerSudokuGame("easy")
        game.cages = [
            Cage(cells=[(0, 0), (0, 1)], operation=None, target=5),  # Target sum 5
        ]
        game.grid = [[0 for _ in range(9)] for _ in range(9)]

        # Place values that exceed target
        game.grid[0][0] = 3
        game.grid[0][1] = 3  # Total would be 6 > 5

        assert game._check_cage_constraints(game.grid, 0, 1) is False

    async def test_check_cage_constraints_correct(self):
        """Test cage constraint with correct values."""
        from puzzle_arcade_server.games.killer_sudoku.models import Cage

        game = KillerSudokuGame("easy")
        game.cages = [
            Cage(cells=[(0, 0), (0, 1)], operation=None, target=5),  # Target sum 5
        ]
        game.grid = [[0 for _ in range(9)] for _ in range(9)]

        # Place values that match target
        game.grid[0][0] = 2
        game.grid[0][1] = 3  # Total 5

        assert game._check_cage_constraints(game.grid, 0, 1) is True

    async def test_validate_move_success(self):
        """Test successful move placement."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(1, 1, 5)
        success, message = result.success, result.message
        assert success is True
        assert "successfully" in message.lower()

    async def test_validate_move_invalid_coordinates(self):
        """Test move with invalid coordinates."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(0, 0, 5)
        success, message = result.success, result.message
        assert success is False
        assert "Invalid coordinates" in message

        result = await game.validate_move(10, 10, 5)
        success, message = result.success, result.message
        assert success is False
        assert "Invalid coordinates" in message

    async def test_validate_move_clear_cell(self):
        """Test clearing a cell."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        game.grid[0][0] = 5
        result = await game.validate_move(1, 1, 0)
        success, message = result.success, result.message
        assert success is True
        assert "cleared" in message.lower()

    async def test_validate_move_invalid_number(self):
        """Test move with invalid number."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(1, 1, 10)
        success, message = result.success, result.message
        assert success is False
        assert "Invalid number" in message

    async def test_is_complete_empty_grid(self):
        """Test completion check with empty grid."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        assert game.is_complete() is False

    async def test_is_complete_filled_correct(self):
        """Test completion check with correctly filled grid."""
        from puzzle_arcade_server.games.killer_sudoku.models import Cage

        game = KillerSudokuGame("easy")
        # Create a simple valid grid
        game.grid = [[0 for _ in range(9)] for _ in range(9)]
        for row in range(9):
            for col in range(9):
                game.grid[row][col] = (row * 3 + row // 3 + col) % 9 + 1

        # Create cages that match this grid (no duplicates within cages)
        game.cages = [
            Cage(cells=[(0, 0), (0, 1)], operation=None, target=game.grid[0][0] + game.grid[0][1]),
            Cage(cells=[(1, 0), (1, 1)], operation=None, target=game.grid[1][0] + game.grid[1][1]),
            Cage(cells=[(2, 0), (2, 1)], operation=None, target=game.grid[2][0] + game.grid[2][1]),
        ]
        # Add more cages to cover all cells
        for row in range(9):
            for col in range(2, 9):
                game.cages.append(Cage(cells=[(row, col)], operation=None, target=game.grid[row][col]))

        assert game.is_complete() is True

    async def test_is_complete_cage_wrong_sum(self):
        """Test completion check with wrong cage sum."""
        game = KillerSudokuGame("easy")
        game.cages = [
            ([(0, 0), (0, 1)], 5),
        ]
        game.grid = [[1, 2, 3, 4, 5, 6, 7, 8, 9] for _ in range(9)]

        # This grid has 1+2=3, but cage expects 5
        assert game.is_complete() is False

    async def test_get_hint(self):
        """Test hint generation."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        hint_data, hint_message = await game.get_hint()
        assert hint_data is not None
        assert len(hint_data) == 3  # (row, col, num)
        assert "placing" in hint_message.lower()

    async def test_get_hint_solved(self):
        """Test hint when puzzle is solved."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()
        game.grid = [row[:] for row in game.solution]

        result = await game.get_hint()
        assert result is None

    async def test_render_grid(self):
        """Test grid rendering."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        grid_str = game.render_grid()
        assert "|" in grid_str
        assert "+" in grid_str
        assert "Cages" in grid_str

    async def test_get_rules(self):
        """Test rules retrieval."""
        game = KillerSudokuGame("easy")
        rules = game.get_rules()

        assert "KILLER SUDOKU" in rules
        assert "9×9" in rules
        assert "cage" in rules.lower()

    async def test_get_commands(self):
        """Test commands retrieval."""
        game = KillerSudokuGame("easy")
        commands = game.get_commands()

        assert "place" in commands.lower()
        assert "clear" in commands.lower()
        assert "hint" in commands.lower()

    async def test_get_stats(self):
        """Test statistics retrieval."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        stats = game.get_stats()
        assert "Moves:" in stats or "Moves made:" in stats
        assert "Empty" in stats
        assert "cages" in stats.lower()
        assert "Seed:" in stats

    async def test_solve(self):
        """Test puzzle solving."""
        game = KillerSudokuGame("easy")
        game.grid = [[0 for _ in range(9)] for _ in range(9)]

        # Simple valid grid
        for row in range(9):
            for col in range(9):
                game.grid[row][col] = (row * 3 + row // 3 + col) % 9 + 1

        # Create simple cages that match
        game.cages = [
            ([(0, 0), (0, 1)], game.grid[0][0] + game.grid[0][1]),
        ]

        # Grid should already be a valid solution
        test_grid = [row[:] for row in game.grid]
        assert game.solve(test_grid) is True

    async def test_moves_counter(self):
        """Test that moves are counted correctly."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        initial_moves = game.moves_made
        await game.validate_move(1, 1, 5)
        assert game.moves_made == initial_moves + 1

    async def test_all_cells_covered_by_cages(self):
        """Test that all cells are covered by exactly one cage."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        # Count cells in cages
        covered_cells = set()
        for cage in game.cages:
            for cell in cage.cells:
                assert cell not in covered_cells, "Cell covered by multiple cages"
                covered_cells.add(cell)

        # All cells should be covered
        assert len(covered_cells) == 81

    async def test_cage_sizes(self):
        """Test that cages are reasonable sizes."""
        game = KillerSudokuGame("easy")
        await game.generate_puzzle()

        for cage in game.cages:
            assert 1 <= len(cage.cells), "Cage must have at least 1 cell"

    async def test_constraint_types(self):
        """Test constraint types metadata."""
        game = KillerSudokuGame("easy")
        constraint_types = game.constraint_types
        assert isinstance(constraint_types, list)
        assert len(constraint_types) > 0
        assert all(isinstance(ct, str) for ct in constraint_types)

    async def test_business_analogies(self):
        """Test business analogies metadata."""
        game = KillerSudokuGame("easy")
        analogies = game.business_analogies
        assert isinstance(analogies, list)
        assert len(analogies) > 0
        assert all(isinstance(a, str) for a in analogies)

    async def test_complexity_profile(self):
        """Test complexity profile metadata."""
        game = KillerSudokuGame("easy")
        profile = game.complexity_profile
        assert isinstance(profile, dict)
        assert "reasoning_type" in profile
        assert "search_space" in profile
        assert "constraint_density" in profile

    async def test_difficulty_profile(self):
        """Test difficulty profile across all difficulties."""
        for difficulty in ["easy", "medium", "hard"]:
            game = KillerSudokuGame(difficulty)
            await game.generate_puzzle()
            profile = game.difficulty_profile
            assert profile.logic_depth > 0
            assert profile.branching_factor > 0
            assert profile.state_observability == 1.0
            assert 0 <= profile.constraint_density <= 1
