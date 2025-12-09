"""Tests for Sudoku game logic."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from puzzle_arcade_server.games.sudoku import SudokuGame


class TestSudokuGame:
    """Test suite for SudokuGame class."""

    def test_initialization(self):
        """Test game initialization."""
        game = SudokuGame("easy")
        assert game.difficulty == "easy"
        assert len(game.grid) == 9
        assert len(game.grid[0]) == 9

    def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = SudokuGame("easy")
        game.generate_puzzle()

        # Check that solution is valid
        assert all(len(row) == 9 for row in game.solution)
        assert all(1 <= cell <= 9 for row in game.solution for cell in row)

        # Check that some cells are empty (0)
        empty_count = sum(1 for row in game.grid for cell in row if cell == 0)
        assert empty_count == 35  # Easy difficulty removes 35 cells

    def test_is_valid_move(self):
        """Test move validation."""
        game = SudokuGame("easy")
        game.generate_puzzle()

        # Test valid move (empty cell)
        row, col = 0, 0
        # Find an empty cell
        for r in range(9):
            for c in range(9):
                if game.grid[r][c] == 0:
                    row, col = r, c
                    break

        # Get the correct value from solution
        correct_num = game.solution[row][col]
        assert game.is_valid_move(row, col, correct_num)

    def test_place_number(self):
        """Test placing a number."""
        game = SudokuGame("easy")
        game.generate_puzzle()

        # Find an empty cell
        for r in range(9):
            for c in range(9):
                if game.grid[r][c] == 0:
                    # Try to place the correct number (1-indexed for user)
                    success, msg = game.validate_move(r + 1, c + 1, game.solution[r][c])
                    assert success
                    assert game.grid[r][c] == game.solution[r][c]
                    break

    def test_cannot_modify_initial_cells(self):
        """Test that initial cells cannot be modified."""
        game = SudokuGame("easy")
        game.generate_puzzle()

        # Find an initial cell (non-zero in initial_grid)
        for r in range(9):
            for c in range(9):
                if game.initial_grid[r][c] != 0:
                    success, msg = game.validate_move(r + 1, c + 1, 5)
                    assert not success
                    assert "Cannot modify" in msg
                    break

    def test_is_complete(self):
        """Test puzzle completion check."""
        game = SudokuGame("easy")
        game.generate_puzzle()

        # Initially not complete
        assert not game.is_complete()

        # Fill with solution
        game.grid = [row[:] for row in game.solution]
        assert game.is_complete()

    def test_get_hint(self):
        """Test hint generation."""
        game = SudokuGame("easy")
        game.generate_puzzle()

        hint = game.get_hint()
        assert hint is not None
        hint_data, hint_message = hint
        row, col, num = hint_data

        # Check hint is valid (1-indexed)
        assert 1 <= row <= 9
        assert 1 <= col <= 9
        assert 1 <= num <= 9
        assert num == game.solution[row - 1][col - 1]

    def test_difficulty_levels(self):
        """Test different difficulty levels."""
        for difficulty, expected_removed in [("easy", 35), ("medium", 45), ("hard", 55)]:
            game = SudokuGame(difficulty)
            game.generate_puzzle()

            empty_count = sum(1 for row in game.grid for cell in row if cell == 0)
            assert empty_count == expected_removed

    def test_render_grid(self):
        """Test grid rendering."""
        game = SudokuGame("easy")
        game.generate_puzzle()

        grid_str = game.render_grid()
        assert isinstance(grid_str, str)
        assert "1 2 3" in grid_str  # Column headers
        assert "|" in grid_str  # Grid lines

    def test_clear_cell(self):
        """Test clearing a cell."""
        game = SudokuGame("easy")
        game.generate_puzzle()

        # Find an empty cell and place the correct number
        for r in range(9):
            for c in range(9):
                if game.grid[r][c] == 0:
                    correct_num = game.solution[r][c]
                    success, msg = game.validate_move(r + 1, c + 1, correct_num)
                    assert success
                    assert game.grid[r][c] == correct_num

                    # Clear it
                    success, msg = game.validate_move(r + 1, c + 1, 0)
                    assert success
                    assert game.grid[r][c] == 0
                    return  # Exit after testing one cell

    def test_invalid_move(self):
        """Test invalid move detection."""
        game = SudokuGame("easy")
        game.generate_puzzle()

        # Create a conflict by placing duplicate in row
        for r in range(9):
            # Find first non-empty cell in row
            existing_num = None
            existing_col = None
            for c in range(9):
                if game.grid[r][c] != 0:
                    existing_num = game.grid[r][c]
                    existing_col = c
                    break

            if existing_num:
                # Try to place same number in different column
                for c in range(9):
                    if c != existing_col and game.grid[r][c] == 0:
                        success, msg = game.validate_move(r + 1, c + 1, existing_num)
                        assert not success
                        assert "conflicts" in msg.lower() or "invalid" in msg.lower()
                        break
                break
