"""Tests for Nonogram game logic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from puzzle_arcade_server.games.nonogram import NonogramGame


class TestNonogramGame:
    """Test suite for NonogramGame class."""

    def test_initialization(self):
        """Test game initialization."""
        game = NonogramGame("easy")
        assert game.difficulty == "easy"
        assert game.size == 5

    def test_difficulty_sizes(self):
        """Test different difficulty sizes."""
        for difficulty, expected_size in [("easy", 5), ("medium", 8), ("hard", 10)]:
            game = NonogramGame(difficulty)
            assert game.size == expected_size

    def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = NonogramGame("easy")
        game.generate_puzzle()

        # Check clues were generated
        assert len(game.row_clues) == game.size
        assert len(game.col_clues) == game.size

        # Grid should start with all unknown (-1)
        assert all(cell == -1 for row in game.grid for cell in row)

    def test_mark_cell(self):
        """Test marking cells."""
        game = NonogramGame("easy")
        game.generate_puzzle()

        # Mark as filled (1)
        success, msg = game.validate_move(1, 1, 1)
        assert success
        assert game.grid[0][0] == 1

        # Mark as empty (0)
        success, msg = game.validate_move(1, 2, 0)
        assert success
        assert game.grid[0][1] == 0

        # Clear (-1)
        success, msg = game.validate_move(1, 1, -1)
        assert success
        assert game.grid[0][0] == -1

    def test_is_complete(self):
        """Test completion check."""
        game = NonogramGame("easy")
        game.generate_puzzle()

        assert not game.is_complete()

        # Fill with solution
        game.grid = [row[:] for row in game.solution]
        assert game.is_complete()

    def test_get_hint(self):
        """Test hint generation."""
        game = NonogramGame("easy")
        game.generate_puzzle()

        hint = game.get_hint()
        if hint:
            hint_data, hint_message = hint
            row, col, val = hint_data
            assert 1 <= row <= game.size
            assert 1 <= col <= game.size
            assert val in [0, 1]

    def test_render_grid(self):
        """Test grid rendering."""
        game = NonogramGame("easy")
        game.generate_puzzle()

        grid_str = game.render_grid()
        assert isinstance(grid_str, str)
        assert "?" in grid_str or "X" in grid_str or "■" in grid_str

    def test_name_and_description(self):
        """Test name and description."""
        game = NonogramGame("easy")
        assert game.name == "Nonogram"
        assert len(game.description) > 0

    def test_get_rules(self):
        """Test rules retrieval."""
        game = NonogramGame("easy")
        rules = game.get_rules()
        assert "NONOGRAM" in rules.upper()

    def test_get_commands(self):
        """Test commands retrieval."""
        game = NonogramGame("easy")
        commands = game.get_commands()
        assert "place" in commands.lower()

    def test_invalid_coordinates(self):
        """Test invalid coordinates."""
        game = NonogramGame("easy")
        game.generate_puzzle()

        success, msg = game.validate_move(99, 99, 1)
        assert not success
        assert "Invalid coordinates" in msg

    def test_invalid_value(self):
        """Test invalid value."""
        game = NonogramGame("easy")
        game.generate_puzzle()

        success, msg = game.validate_move(1, 1, 99)
        assert not success
        assert "Invalid value" in msg
