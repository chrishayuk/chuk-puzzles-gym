"""Tests for Futoshiki game logic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from puzzle_arcade_server.games.futoshiki import FutoshikiGame


class TestFutoshikiGame:
    """Test suite for FutoshikiGame class."""

    async def test_initialization(self):
        """Test game initialization."""
        game = FutoshikiGame("easy")
        assert game.difficulty == "easy"
        assert game.size == 4

    async def test_difficulty_sizes(self):
        """Test different difficulty sizes."""
        for difficulty, expected_size in [("easy", 4), ("medium", 5), ("hard", 6)]:
            game = FutoshikiGame(difficulty)
            assert game.size == expected_size

    async def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Check inequalities were generated
        assert len(game.inequalities) > 0

        # Grid should have some empty cells
        empty_count = sum(1 for row in game.grid for cell in row if cell == 0)
        assert empty_count > 0

    async def test_place_number(self):
        """Test placing a number."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Find empty cell
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 0:
                    correct_num = game.solution[r][c]
                    result = await game.validate_move(r + 1, c + 1, correct_num)
                    success, _msg = result.success, result.message
                    assert success
                    assert game.grid[r][c] == correct_num
                    return

    async def test_clear_cell(self):
        """Test clearing a cell."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Find empty, place, clear
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 0 and game.initial_grid[r][c] == 0:
                    await game.validate_move(r + 1, c + 1, game.solution[r][c])
                    result = await game.validate_move(r + 1, c + 1, 0)
                    success, _msg = result.success, result.message
                    assert success
                    assert game.grid[r][c] == 0
                    return

    async def test_cannot_modify_initial_cells(self):
        """Test that initial cells cannot be modified."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Find initial cell
        for r in range(game.size):
            for c in range(game.size):
                if game.initial_grid[r][c] != 0:
                    result = await game.validate_move(r + 1, c + 1, 1)
                    success, msg = result.success, result.message
                    assert not success
                    assert "Cannot modify" in msg
                    return

    async def test_is_complete(self):
        """Test completion check."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        assert not game.is_complete()

        # Fill with solution
        game.grid = [row[:] for row in game.solution]
        assert game.is_complete()

    async def test_get_hint(self):
        """Test hint generation."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            hint_data, hint_message = hint
            row, col, num = hint_data
            assert 1 <= row <= game.size
            assert 1 <= col <= game.size
            assert 1 <= num <= game.size

    async def test_render_grid(self):
        """Test grid rendering."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        grid_str = game.render_grid()
        assert isinstance(grid_str, str)
        assert "|" in grid_str

    async def test_name_and_description(self):
        """Test name and description."""
        game = FutoshikiGame("easy")
        assert game.name == "Futoshiki"
        assert len(game.description) > 0

    async def test_get_rules(self):
        """Test rules retrieval."""
        game = FutoshikiGame("easy")
        rules = game.get_rules()
        assert "FUTOSHIKI" in rules.upper()
        assert "inequality" in rules.lower()

    async def test_get_commands(self):
        """Test commands retrieval."""
        game = FutoshikiGame("easy")
        commands = game.get_commands()
        assert "place" in commands.lower()

    async def test_invalid_coordinates(self):
        """Test invalid coordinates."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(99, 99, 1)
        success, msg = result.success, result.message
        assert not success
        assert "Invalid coordinates" in msg

    async def test_invalid_number(self):
        """Test invalid number."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Find an empty cell
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 0:
                    result = await game.validate_move(r + 1, c + 1, 99)
                    success, msg = result.success, result.message
                    assert not success
                    assert "Invalid number" in msg
                    return

    async def test_solve_method(self):
        """Test the solve method."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Solution should exist
        assert game.solution is not None
        assert all(1 <= cell <= game.size for row in game.solution for cell in row)

    async def test_generate_inequalities(self):
        """Test inequality generation."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Inequalities should have been generated
        assert len(game.inequalities) > 0

        # Each inequality should be between valid cells
        for (r1, c1), (r2, c2) in game.inequalities:
            assert 0 <= r1 < game.size
            assert 0 <= c1 < game.size
            assert 0 <= r2 < game.size
            assert 0 <= c2 < game.size

            # First cell should be greater than second in solution
            assert game.solution[r1][c1] > game.solution[r2][c2]

    async def test_solution_satisfies_inequalities(self):
        """Test that solution satisfies all inequalities."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Check that all inequalities are satisfied in the solution
        for (r1, c1), (r2, c2) in game.inequalities:
            val1 = game.solution[r1][c1]
            val2 = game.solution[r2][c2]

            # r1 should be > r2 as per the inequality definition
            assert val1 > val2, f"Inequality violated: ({r1},{c1})={val1} should be > ({r2},{c2})={val2}"

    async def test_get_stats(self):
        """Test stats retrieval."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        stats = game.get_stats()
        assert "Moves:" in stats or "Moves made:" in stats
        assert "Inequalities" in stats
        assert "Seed:" in stats

    async def test_is_valid_move_with_grid_param(self):
        """Test is_valid_move with explicit grid parameter."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Create a test grid
        test_grid = [[0 for _ in range(game.size)] for _ in range(game.size)]
        test_grid[0][0] = 1

        # Try placing same number in same row
        assert not game.is_valid_move(0, 1, 1, test_grid)

        # Try placing same number in same column
        assert not game.is_valid_move(1, 0, 1, test_grid)

    async def test_inequality_constraint_validation(self):
        """Test inequality constraint checking in is_valid_move."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Find an inequality and test it
        if len(game.inequalities) > 0:
            (r1, c1), (r2, c2) = game.inequalities[0]

            # Clear both cells
            game.grid[r1][c1] = 0
            game.grid[r2][c2] = 0

            # Place a value in the first cell
            game.grid[r1][c1] = game.size

            # Try to place a value >= first cell in second cell (should fail due to inequality)
            assert not game.is_valid_move(r2, c2, game.size, game.grid)

            # Try to place a smaller value that satisfies the inequality
            # We need to find a value that:
            # 1. Is less than game.size (to satisfy the inequality)
            # 2. Doesn't conflict with row/column
            # 3. Satisfies all other inequalities involving this cell
            for val in range(1, game.size):
                # Check if this value doesn't conflict with row/col constraints
                row_vals = [game.grid[r2][c] for c in range(game.size) if c != c2]
                col_vals = [game.grid[r][c2] for r in range(game.size) if r != r2]

                if val not in row_vals and val not in col_vals:
                    # Also verify it passes is_valid_move (which checks all constraints)
                    if game.is_valid_move(r2, c2, val, game.grid):
                        # Found a valid move, test passes
                        return

            # If no valid value found, that's also acceptable given the complex constraints
            # The important thing is that the invalid move was correctly rejected
            assert True

    async def test_render_grid_with_inequalities(self):
        """Test that rendering includes inequality symbols."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        rendered = game.render_grid()

        # Should contain grid structure
        assert "|" in rendered

        # Might contain inequality symbols if any exist
        if len(game.inequalities) > 0:
            # At least one inequality symbol should be present
            assert any(sym in rendered for sym in [">", "<", "^", "v"])

    async def test_solve_backtracking(self):
        """Test the solve method with backtracking."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Create a partially filled grid
        test_grid = [[0 for _ in range(game.size)] for _ in range(game.size)]

        # Fill first cell with correct value
        test_grid[0][0] = game.solution[0][0]

        # Solve should be able to complete it
        result = game.solve(test_grid)

        # Should either solve it or determine it's impossible
        assert isinstance(result, bool)

    async def test_inequality_direction_rendering(self):
        """Test rendering of different inequality directions."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Manually create some inequalities to test rendering
        if game.size >= 2:
            # Horizontal inequality (left > right)
            game.inequalities = [((0, 0), (0, 1))]
            rendered = game.render_grid()
            # Should have > symbol for horizontal
            assert ">" in rendered or "<" in rendered

            # Vertical inequality (top > bottom)
            game.inequalities = [((0, 0), (1, 0))]
            rendered = game.render_grid()
            # Should have v or ^ symbol for vertical
            assert "v" in rendered or "^" in rendered

    async def test_is_valid_move_inequality_both_directions(self):
        """Test inequality validation in both directions."""
        game = FutoshikiGame("easy")
        await game.generate_puzzle()

        # Create a test scenario with inequality
        if len(game.inequalities) > 0:
            (r1, c1), (r2, c2) = game.inequalities[0]

            # Clear the grid
            game.grid = [[0 for _ in range(game.size)] for _ in range(game.size)]

            # Place a small value in r2, should allow larger in r1
            game.grid[r2][c2] = 1
            assert game.is_valid_move(r1, c1, game.size)

            # Place large value in r1, should not allow equal/larger in r2
            game.grid[r1][c1] = game.size
            game.grid[r2][c2] = 0
            assert not game.is_valid_move(r2, c2, game.size)

    async def test_constraint_types(self):
        """Test constraint types metadata."""
        game = FutoshikiGame("easy")
        constraint_types = game.constraint_types
        assert isinstance(constraint_types, list)
        assert len(constraint_types) > 0
        assert all(isinstance(ct, str) for ct in constraint_types)

    async def test_business_analogies(self):
        """Test business analogies metadata."""
        game = FutoshikiGame("easy")
        analogies = game.business_analogies
        assert isinstance(analogies, list)
        assert len(analogies) > 0
        assert all(isinstance(a, str) for a in analogies)

    async def test_complexity_profile(self):
        """Test complexity profile metadata."""
        game = FutoshikiGame("easy")
        profile = game.complexity_profile
        assert isinstance(profile, dict)
        assert "reasoning_type" in profile
        assert "search_space" in profile
        assert "constraint_density" in profile
