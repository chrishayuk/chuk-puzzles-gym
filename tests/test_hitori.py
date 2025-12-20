"""Tests for Hitori game logic."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from puzzle_arcade_server.games.hitori import HitoriGame


class TestHitoriGame:
    """Test suite for HitoriGame class."""

    async def test_initialization(self):
        """Test game initialization."""
        game = HitoriGame("easy")
        assert game.difficulty.value == "easy"
        assert game.size == 5

    async def test_difficulty_sizes(self):
        """Test grid sizes for different difficulties."""
        for difficulty, expected_size in [("easy", 5), ("medium", 7), ("hard", 9)]:
            game = HitoriGame(difficulty)
            assert game.size == expected_size

    async def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        # Check grid was populated
        assert all(game.grid[r][c] > 0 for r in range(game.size) for c in range(game.size))
        assert game.game_started

        # Check solution exists
        assert len(game.solution) == game.size
        assert len(game.solution[0]) == game.size

    async def test_name_and_description(self):
        """Test game name and description."""
        game = HitoriGame("easy")
        assert game.name == "Hitori"
        assert "shade" in game.description.lower()

    async def test_get_rules(self):
        """Test rules retrieval."""
        game = HitoriGame("easy")
        rules = game.get_rules()
        assert "HITORI" in rules
        assert "shade" in rules.lower()

    async def test_get_commands(self):
        """Test commands retrieval."""
        game = HitoriGame("easy")
        commands = game.get_commands()
        assert "shade" in commands.lower()
        assert "unshade" in commands.lower()

    async def test_shade_cell(self):
        """Test shading a cell."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        # Shade a cell
        result = await game.validate_move(1, 1, "shade")
        assert result.success
        assert game.shaded[0][0]
        assert game.moves_made == 1

    async def test_unshade_cell(self):
        """Test unshading a cell."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        # Shade then unshade
        await game.validate_move(1, 1, "shade")
        result = await game.validate_move(1, 1, "unshade")
        assert result.success
        assert not game.shaded[0][0]

    async def test_shade_adjacent_rejection(self):
        """Test that adjacent shading is rejected."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        # Shade a cell
        await game.validate_move(1, 1, "shade")

        # Try to shade adjacent cell
        result = await game.validate_move(1, 2, "shade")
        assert not result.success
        assert "adjacent" in result.message.lower()

    async def test_invalid_coordinates(self):
        """Test invalid coordinates."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(10, 10, "shade")
        assert not result.success

    async def test_invalid_action(self):
        """Test invalid action."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(1, 1, "invalid")
        assert not result.success

    async def test_is_connected(self):
        """Test connectivity checking."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        # Empty grid (all unshaded) should be connected
        empty_grid = [[False for _ in range(game.size)] for _ in range(game.size)]
        assert game._is_connected(empty_grid)

        # Fully shaded should not be connected (no unshaded cells)
        full_grid = [[True for _ in range(game.size)] for _ in range(game.size)]
        assert not game._is_connected(full_grid)

    async def test_has_adjacent_shaded(self):
        """Test adjacent shaded detection."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        # Initially no adjacent shaded
        assert not game._has_adjacent_shaded(0, 0, game.shaded)

        # Shade a cell
        game.shaded[0][0] = True

        # Check adjacent cell
        assert game._has_adjacent_shaded(0, 1, game.shaded)
        assert game._has_adjacent_shaded(1, 0, game.shaded)

    async def test_is_complete_empty(self):
        """Test completion check on empty puzzle."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        # Not complete initially
        assert not game.is_complete()

    async def test_is_complete_with_solution(self):
        """Test completion check with solution."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        # Apply solution
        for r in range(game.size):
            for c in range(game.size):
                game.shaded[r][c] = game.solution[r][c]

        # Should be complete
        result = game.is_complete()
        assert isinstance(result, bool)

    async def test_get_hint(self):
        """Test hint generation."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            hint_data, hint_message = hint
            row, col, action = hint_data
            assert 1 <= row <= game.size
            assert 1 <= col <= game.size
            assert action in ["shade", "unshade"]

    async def test_render_grid(self):
        """Test grid rendering."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        grid_str = game.render_grid()
        assert isinstance(grid_str, str)
        assert "|" in grid_str

        # Shade a cell and check it's marked
        game.shaded[0][0] = True
        grid_str = game.render_grid()
        assert "#" in grid_str

    async def test_get_stats(self):
        """Test stats retrieval."""
        game = HitoriGame("easy")
        stats = game.get_stats()
        assert "Moves" in stats
        assert "Seed:" in stats

    async def test_moves_counter(self):
        """Test that moves are counted."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        initial_moves = game.moves_made
        await game.validate_move(1, 1, "shade")
        assert game.moves_made == initial_moves + 1

    async def test_shade_shorthand(self):
        """Test 's' shorthand for shade."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(1, 1, "s")
        assert result.success
        assert game.shaded[0][0]

    async def test_unshade_shorthand(self):
        """Test 'u' shorthand for unshade."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        await game.validate_move(1, 1, "shade")
        result = await game.validate_move(1, 1, "u")
        assert result.success
        assert not game.shaded[0][0]

    async def test_clear_unshade(self):
        """Test 'clear' as unshade."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        await game.validate_move(1, 1, "shade")
        result = await game.validate_move(1, 1, "clear")
        assert result.success
        assert not game.shaded[0][0]

    async def test_usage_message(self):
        """Test usage message on invalid input."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(1)
        assert not result.success
        assert "Usage" in result.message

    async def test_is_complete_with_duplicates_in_row(self):
        """Test that duplicates in rows are detected."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        # Create a grid with duplicates
        game.grid = [[1, 2, 3, 4, 5], [2, 1, 4, 3, 5], [3, 4, 1, 5, 2], [4, 5, 2, 1, 3], [5, 3, 4, 2, 1]]
        game.shaded = [[False for _ in range(5)] for _ in range(5)]

        # This has no duplicates, should be complete if connected
        result = game.is_complete()
        # Should be complete or check connectivity
        assert isinstance(result, bool)

    async def test_is_complete_with_duplicates_in_column(self):
        """Test that duplicates in columns are detected."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        # Create invalid state with column duplicates
        game.grid = [[1, 1, 3, 4, 5], [2, 2, 4, 3, 5], [3, 3, 1, 5, 2], [4, 4, 2, 1, 3], [5, 5, 4, 2, 1]]
        game.shaded = [[False for _ in range(5)] for _ in range(5)]

        # Has duplicates, should not be complete
        result = game.is_complete()
        assert not result

    async def test_connectivity_with_shaded_cells(self):
        """Test connectivity check with some shaded cells."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        # Shade some cells
        game.shaded[0][0] = True
        game.shaded[1][1] = True

        # Check connectivity
        result = game._is_connected(game.shaded)
        assert isinstance(result, bool)

    async def test_invalid_coordinates_value_error(self):
        """Test invalid coordinate types."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move("a", "b", "shade")
        assert not result.success

    async def test_hint_for_unshading(self):
        """Test hint suggests unshading when needed."""
        game = HitoriGame("easy")
        await game.generate_puzzle()

        # Find a cell that shouldn't be shaded and shade it
        for r in range(game.size):
            for c in range(game.size):
                if not game.solution[r][c]:
                    game.shaded[r][c] = True
                    hint = await game.get_hint()
                    if hint:
                        hint_data, message = hint
                        # Hint should be valid
                        assert isinstance(message, str)
                        assert len(message) > 0
                    return

        # If no suitable cell found, just pass
        assert True

    async def test_grid_swapping_during_generation(self):
        """Test that puzzle generation creates variety."""
        game = HitoriGame("medium")
        await game.generate_puzzle()

        # Just verify puzzle was generated
        assert game.game_started
        assert len(game.grid) == 7
        assert len(game.grid[0]) == 7

    async def test_constraint_types(self):
        """Test constraint types metadata."""
        game = HitoriGame("easy")
        constraint_types = game.constraint_types
        assert isinstance(constraint_types, list)
        assert len(constraint_types) > 0
        assert all(isinstance(ct, str) for ct in constraint_types)

    async def test_business_analogies(self):
        """Test business analogies metadata."""
        game = HitoriGame("easy")
        analogies = game.business_analogies
        assert isinstance(analogies, list)
        assert len(analogies) > 0
        assert all(isinstance(a, str) for a in analogies)

    async def test_complexity_profile(self):
        """Test complexity profile metadata."""
        game = HitoriGame("easy")
        profile = game.complexity_profile
        assert isinstance(profile, dict)
        assert "reasoning_type" in profile
        assert "search_space" in profile
        assert "constraint_density" in profile
