"""Tests for Lights Out puzzle game."""

import pytest

from puzzle_arcade_server.games.lights_out import LightsOutGame


class TestLightsOutGame:
    """Test suite for Lights Out game."""

    async def test_initialization_easy(self):
        """Test game initialization with easy difficulty."""
        game = LightsOutGame("easy")
        assert game.difficulty == "easy"
        assert game.size == 5
        assert game.name == "Lights Out"
        assert "XOR" in game.description

    async def test_initialization_medium(self):
        """Test game initialization with medium difficulty."""
        game = LightsOutGame("medium")
        assert game.difficulty == "medium"
        assert game.size == 6

    async def test_initialization_hard(self):
        """Test game initialization with hard difficulty."""
        game = LightsOutGame("hard")
        assert game.difficulty == "hard"
        assert game.size == 7

    async def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = LightsOutGame("easy")
        await game.generate_puzzle()

        assert game.game_started is True
        assert game.moves_made == 0
        assert len(game.grid) == 5
        assert len(game.grid[0]) == 5

        # Check that at least some lights are on
        total_lights = sum(sum(row) for row in game.grid)
        assert total_lights > 0

    async def test_toggle_cell(self):
        """Test cell toggling mechanism."""
        game = LightsOutGame("easy")
        game.grid = [[0 for _ in range(5)] for _ in range(5)]

        # Toggle center cell
        game._toggle_cell(2, 2, game.grid)

        # Center and 4 neighbors should be toggled
        assert game.grid[2][2] == 1  # Center
        assert game.grid[1][2] == 1  # Top
        assert game.grid[3][2] == 1  # Bottom
        assert game.grid[2][1] == 1  # Left
        assert game.grid[2][3] == 1  # Right

        # Corners should not be affected
        assert game.grid[0][0] == 0
        assert game.grid[4][4] == 0

    async def test_toggle_corner(self):
        """Test toggling a corner cell."""
        game = LightsOutGame("easy")
        game.grid = [[0 for _ in range(5)] for _ in range(5)]

        # Toggle top-left corner
        game._toggle_cell(0, 0, game.grid)

        # Corner and 2 neighbors should be toggled
        assert game.grid[0][0] == 1  # Corner
        assert game.grid[0][1] == 1  # Right
        assert game.grid[1][0] == 1  # Bottom

        # Other cells should not be affected
        assert game.grid[0][2] == 0
        assert game.grid[1][1] == 0

    async def test_validate_move_success(self):
        """Test successful move validation."""
        game = LightsOutGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(3, 3)
        success, message = result.success, result.message
        assert success is True
        assert "Toggled light" in message

    async def test_validate_move_invalid_coordinates(self):
        """Test move validation with invalid coordinates."""
        game = LightsOutGame("easy")
        await game.generate_puzzle()

        # Out of bounds
        result = await game.validate_move(0, 0)
        success, message = result.success, result.message
        assert success is False
        assert "Invalid coordinates" in message

        result = await game.validate_move(6, 6)
        success, message = result.success, result.message
        assert success is False
        assert "Invalid coordinates" in message

    async def test_is_complete_all_off(self):
        """Test completion check when all lights are off."""
        game = LightsOutGame("easy")
        game.grid = [[0 for _ in range(5)] for _ in range(5)]

        assert game.is_complete() is True

    async def test_is_complete_lights_on(self):
        """Test completion check when lights are still on."""
        game = LightsOutGame("easy")
        game.grid = [[0 for _ in range(5)] for _ in range(5)]
        game.grid[2][2] = 1  # One light on

        assert game.is_complete() is False

    async def test_get_hint(self):
        """Test hint generation."""
        game = LightsOutGame("easy")
        await game.generate_puzzle()

        # Should return a hint
        hint_data, hint_message = await game.get_hint()
        assert hint_data is not None
        assert hint_message is not None
        assert "pressing" in hint_message.lower()

    async def test_get_hint_solved(self):
        """Test hint when puzzle is already solved."""
        game = LightsOutGame("easy")
        game.grid = [[0 for _ in range(5)] for _ in range(5)]
        game.presses = [[0 for _ in range(5)] for _ in range(5)]

        result = await game.get_hint()
        assert result is None

    async def test_render_grid(self):
        """Test grid rendering."""
        game = LightsOutGame("easy")
        await game.generate_puzzle()

        grid_str = game.render_grid()
        assert "●" in grid_str or "○" in grid_str
        assert "|" in grid_str
        assert "+" in grid_str

    async def test_get_rules(self):
        """Test rules retrieval."""
        game = LightsOutGame("easy")
        rules = game.get_rules()

        assert "LIGHTS OUT" in rules
        assert "toggle" in rules.lower()
        assert "neighbors" in rules.lower()

    async def test_get_commands(self):
        """Test commands retrieval."""
        game = LightsOutGame("easy")
        commands = game.get_commands()

        assert "press" in commands.lower()
        assert "show" in commands.lower()
        assert "hint" in commands.lower()

    async def test_get_stats(self):
        """Test statistics retrieval."""
        game = LightsOutGame("easy")
        await game.generate_puzzle()

        stats = game.get_stats()
        assert "Moves" in stats
        assert "Lights ON:" in stats
        assert "Grid" in stats
        assert "Seed:" in stats

    async def test_moves_counter(self):
        """Test that moves are counted correctly."""
        game = LightsOutGame("easy")
        await game.generate_puzzle()

        initial_moves = game.moves_made
        await game.validate_move(3, 3)
        assert game.moves_made == initial_moves + 1

        await game.validate_move(2, 2)
        assert game.moves_made == initial_moves + 2

    async def test_toggle_twice_returns_original(self):
        """Test that toggling twice returns to original state."""
        game = LightsOutGame("easy")
        game.grid = [[0 for _ in range(5)] for _ in range(5)]

        original = [row[:] for row in game.grid]

        # Toggle twice
        game._toggle_cell(2, 2, game.grid)
        game._toggle_cell(2, 2, game.grid)

        assert game.grid == original

    async def test_puzzle_generation_creates_initial_state(self):
        """Test that puzzle generation stores initial state."""
        game = LightsOutGame("easy")
        await game.generate_puzzle()

        # Initial grid should be stored
        assert len(game.initial_grid) == game.size
        assert game.initial_grid == game.grid

    @pytest.mark.parametrize("difficulty,expected_size", [("easy", 5), ("medium", 6), ("hard", 7)])
    async def test_difficulty_levels(self, difficulty, expected_size):
        """Test different difficulty levels."""
        game = LightsOutGame(difficulty)
        assert game.size == expected_size

    async def test_edge_cells_have_fewer_neighbors(self):
        """Test that edge cells affect fewer neighbors."""
        game = LightsOutGame("easy")
        game.grid = [[0 for _ in range(5)] for _ in range(5)]

        # Toggle edge cell (not corner)
        game._toggle_cell(0, 2, game.grid)

        # Should toggle cell itself + 3 neighbors (not 4)
        total_on = sum(sum(row) for row in game.grid)
        assert total_on == 4  # Cell + top neighbor + left neighbor + right neighbor

    async def test_constraint_types(self):
        """Test constraint types metadata."""
        game = LightsOutGame("easy")
        constraint_types = game.constraint_types
        assert isinstance(constraint_types, list)
        assert len(constraint_types) > 0
        assert all(isinstance(ct, str) for ct in constraint_types)

    async def test_business_analogies(self):
        """Test business analogies metadata."""
        game = LightsOutGame("easy")
        analogies = game.business_analogies
        assert isinstance(analogies, list)
        assert len(analogies) > 0
        assert all(isinstance(a, str) for a in analogies)

    async def test_complexity_profile(self):
        """Test complexity profile metadata."""
        game = LightsOutGame("easy")
        profile = game.complexity_profile
        assert isinstance(profile, dict)
        assert "reasoning_type" in profile
        assert "search_space" in profile
        assert "constraint_density" in profile
