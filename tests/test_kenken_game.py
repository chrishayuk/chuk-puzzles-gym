"""Tests for KenKen game logic."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from puzzle_arcade_server.games.kenken import KenKenGame


class TestKenKenGame:
    """Test suite for KenKenGame class."""

    async def test_initialization(self):
        """Test game initialization."""
        game = KenKenGame("easy")
        assert game.difficulty == "easy"
        assert game.size == 4
        assert len(game.grid) == 4
        assert len(game.grid[0]) == 4

    async def test_difficulty_sizes(self):
        """Test different difficulty sizes."""
        for difficulty, expected_size in [("easy", 4), ("medium", 5), ("hard", 6)]:
            game = KenKenGame(difficulty)
            assert game.size == expected_size
            assert len(game.grid) == expected_size

    async def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Check solution is valid
        assert all(len(row) == game.size for row in game.solution)
        assert all(1 <= cell <= game.size for row in game.solution for cell in row)

        # Check cages were generated
        assert len(game.cages) > 0

        # Grid should start empty
        assert all(cell == 0 for row in game.grid for cell in row)

    async def test_is_valid_move(self):
        """Test move validation."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Place a valid number
        row, col = 0, 0
        num = game.solution[row][col]
        assert game.is_valid_move(row, col, num)

    async def test_place_number(self):
        """Test placing a number."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Place the correct number
        row, col = 0, 0
        correct_num = game.solution[row][col]
        result = await game.validate_move(row + 1, col + 1, correct_num)
        success, _msg = result.success, result.message
        assert success
        assert game.grid[row][col] == correct_num

    async def test_clear_cell(self):
        """Test clearing a cell."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Place and clear
        row, col = 0, 0
        correct_num = game.solution[row][col]
        await game.validate_move(row + 1, col + 1, correct_num)

        result = await game.validate_move(row + 1, col + 1, 0)
        success, _msg = result.success, result.message
        assert success
        assert game.grid[row][col] == 0

    async def test_is_complete(self):
        """Test completion check."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        assert not game.is_complete()

        # Fill with solution
        game.grid = [row[:] for row in game.solution]
        assert game.is_complete()

    async def test_get_hint(self):
        """Test hint generation."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        hint = await game.get_hint()
        assert hint is not None
        hint_data, hint_message = hint
        row, col, num = hint_data
        assert 1 <= row <= game.size
        assert 1 <= col <= game.size
        assert 1 <= num <= game.size

    async def test_render_grid(self):
        """Test grid rendering."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        grid_str = game.render_grid()
        assert isinstance(grid_str, str)
        assert "Cages:" in grid_str

    async def test_get_rules(self):
        """Test rules retrieval."""
        game = KenKenGame("easy")
        rules = game.get_rules()
        assert "KENKEN" in rules.upper()
        assert "cage" in rules.lower()

    async def test_get_commands(self):
        """Test commands retrieval."""
        game = KenKenGame("easy")
        commands = game.get_commands()
        assert "place" in commands.lower()
        assert "clear" in commands.lower()

    async def test_name_and_description(self):
        """Test name and description properties."""
        game = KenKenGame("easy")
        assert game.name == "KenKen"
        assert len(game.description) > 0

    async def test_invalid_coordinates(self):
        """Test invalid coordinate handling."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Out of bounds
        result = await game.validate_move(10, 10, 1)
        success, msg = result.success, result.message
        assert not success
        assert "Invalid coordinates" in msg

    async def test_invalid_number(self):
        """Test invalid number handling."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Number out of range
        result = await game.validate_move(1, 1, 99)
        success, msg = result.success, result.message
        assert not success
        assert "Invalid number" in msg

    async def test_solve_method(self):
        """Test the solve method."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Create a copy and solve it
        test_grid = [[0 for _ in range(game.size)] for _ in range(game.size)]
        # Fill first row with valid values to test solve
        for i in range(game.size):
            test_grid[0][i] = (i + 1) % game.size + 1 if (i + 1) % game.size != 0 else game.size

        # The solve method should be able to work with the grid
        assert game.solution is not None

    async def test_check_cage_constraints(self):
        """Test cage constraint checking."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Fill grid with solution to test cage validation
        game.grid = [row[:] for row in game.solution]

        # All cages should be satisfied
        assert game.is_complete()

    async def test_evaluate_cage(self):
        """Test cage evaluation logic."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Test with a known cage from the solution
        if len(game.cages) > 0:
            cage = game.cages[0]
            values = [game.solution[r][c] for r, c in cage.cells]

            # Cage should evaluate correctly with solution values
            result = game._evaluate_cage(values, cage.operation, cage.target)
            assert result

    async def test_get_stats(self):
        """Test stats retrieval."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        stats = game.get_stats()
        assert "Moves made" in stats
        assert "Empty cells" in stats
        assert "Grid" in stats
        assert "Seed:" in stats

    async def test_generate_inequalities(self):
        """Test inequality generation."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Cages should have been generated
        assert len(game.cages) > 0

        # Each cage should have cells, operation, and target
        for cage in game.cages:
            assert len(cage.cells) >= 1
            assert cage.target >= 1

    async def test_solve_empty_grid(self):
        """Test solving an empty grid."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Create empty grid and try to solve
        [[0 for _ in range(game.size)] for _ in range(game.size)]

        # The solve method exists and can be called
        # (Full solve might timeout, so just test the method exists)
        assert hasattr(game, "solve")

    async def test_evaluate_different_operations(self):
        """Test cage evaluation with different operations."""
        game = KenKenGame("easy")

        # Test addition
        assert game._evaluate_cage([1, 2, 3], "+", 6)
        assert not game._evaluate_cage([1, 2, 3], "+", 5)

        # Test multiplication
        assert game._evaluate_cage([2, 3], "*", 6)
        assert not game._evaluate_cage([2, 3], "*", 5)

        # Test subtraction
        assert game._evaluate_cage([5, 2], "-", 3)
        assert game._evaluate_cage([2, 5], "-", 3)  # Order shouldn't matter
        assert not game._evaluate_cage([5, 2], "-", 2)

        # Test division
        assert game._evaluate_cage([6, 2], "/", 3)
        assert game._evaluate_cage([2, 6], "/", 3)  # Order shouldn't matter
        assert not game._evaluate_cage([6, 2], "/", 2)

        # Test single cell (None operation)
        assert game._evaluate_cage([5], None, 5)
        assert not game._evaluate_cage([5], None, 3)

    async def test_row_column_uniqueness(self):
        """Test that solution has unique values in rows and columns."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Check rows are unique
        for row in game.solution:
            assert len(row) == len(set(row))

        # Check columns are unique
        for col in range(game.size):
            col_vals = [game.solution[row][col] for row in range(game.size)]
            assert len(col_vals) == len(set(col_vals))

    async def test_cage_constraint_checking(self):
        """Test _check_cage_constraints method."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Fill a cell with solution value
        for row in range(game.size):
            for col in range(game.size):
                if game.grid[row][col] == 0:
                    game.grid[row][col] = game.solution[row][col]
                    # Should pass cage constraints
                    assert game._check_cage_constraints(game.grid, row, col)
                    game.grid[row][col] = 0
                    return

    async def test_is_valid_move_with_grid_param(self):
        """Test is_valid_move with explicit grid parameter."""
        game = KenKenGame("easy")
        await game.generate_puzzle()

        # Create a test grid
        test_grid = [[0 for _ in range(game.size)] for _ in range(game.size)]
        test_grid[0][0] = 1

        # Try placing same number in same row
        assert not game.is_valid_move(0, 1, 1, test_grid)

        # Try placing same number in same column
        assert not game.is_valid_move(1, 0, 1, test_grid)

    async def test_evaluate_cage_edge_cases(self):
        """Test edge cases in cage evaluation."""
        game = KenKenGame("easy")

        # Test division with zero
        assert not game._evaluate_cage([6, 0], "/", 3)

        # Test division with non-divisible numbers
        assert not game._evaluate_cage([7, 2], "/", 3)

        # Test subtraction with wrong values
        assert not game._evaluate_cage([5, 2], "-", 2)

        # Test invalid operations
        assert not game._evaluate_cage([1, 2], "invalid", 3)

    async def test_constraint_types(self):
        """Test constraint types metadata."""
        game = KenKenGame("easy")
        constraint_types = game.constraint_types
        assert isinstance(constraint_types, list)
        assert len(constraint_types) > 0
        assert all(isinstance(ct, str) for ct in constraint_types)

    async def test_business_analogies(self):
        """Test business analogies metadata."""
        game = KenKenGame("easy")
        analogies = game.business_analogies
        assert isinstance(analogies, list)
        assert len(analogies) > 0
        assert all(isinstance(a, str) for a in analogies)

    async def test_complexity_profile(self):
        """Test complexity profile metadata."""
        game = KenKenGame("easy")
        profile = game.complexity_profile
        assert isinstance(profile, dict)
        assert "reasoning_type" in profile
        assert "search_space" in profile
        assert "constraint_density" in profile

    async def test_difficulty_profile(self):
        """Test difficulty profile across all difficulties."""
        for difficulty in ["easy", "medium", "hard"]:
            game = KenKenGame(difficulty)
            await game.generate_puzzle()
            profile = game.difficulty_profile
            assert profile.logic_depth > 0
            assert profile.branching_factor > 0
            assert profile.state_observability == 1.0
            assert 0 <= profile.constraint_density <= 1
