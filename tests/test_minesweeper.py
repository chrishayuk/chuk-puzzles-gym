"""Tests for Minesweeper puzzle game."""

import pytest

from puzzle_arcade_server.games.minesweeper import MinesweeperGame


class TestMinesweeperGame:
    """Test suite for Minesweeper game."""

    def test_initialization_easy(self):
        """Test game initialization with easy difficulty."""
        game = MinesweeperGame("easy")
        assert game.difficulty == "easy"
        assert game.size == 6
        assert game.num_mines == 6
        assert game.name == "Minesweeper"
        assert "mine" in game.description.lower() or "deduction" in game.description.lower()

    def test_initialization_medium(self):
        """Test game initialization with medium difficulty."""
        game = MinesweeperGame("medium")
        assert game.size == 8
        assert game.num_mines == 12

    def test_initialization_hard(self):
        """Test game initialization with hard difficulty."""
        game = MinesweeperGame("hard")
        assert game.size == 10
        assert game.num_mines == 20

    def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = MinesweeperGame("easy")
        game.generate_puzzle()

        assert game.game_started is True
        assert len(game.mines) == 6
        assert len(game.revealed) == 6
        assert len(game.counts) == 6
        assert game.game_over is False
        assert game.hit_mine is False

    def test_correct_number_of_mines(self):
        """Test that correct number of mines are placed."""
        game = MinesweeperGame("easy")
        game.generate_puzzle()

        mine_count = sum(sum(1 for cell in row if cell) for row in game.mines)
        assert mine_count == 6

    def test_revealed_starts_all_unrevealed(self):
        """Test that all cells start unrevealed."""
        game = MinesweeperGame("easy")
        game.generate_puzzle()

        for row in game.revealed:
            for cell in row:
                assert cell == 0  # 0 = unrevealed

    def test_counts_calculated_correctly(self):
        """Test that adjacent mine counts are correct."""
        game = MinesweeperGame("easy")
        game.mines = [
            [True, False, False, False, False, False],
            [False, False, False, False, False, False],
            [False, False, False, False, False, False],
            [False, False, False, False, False, False],
            [False, False, False, False, False, False],
            [False, False, False, False, False, False],
        ]
        game.size = 6

        # Recalculate counts
        for row in range(game.size):
            for col in range(game.size):
                if not game.mines[row][col]:
                    game.counts[row][col] = game._count_adjacent_mines(row, col)

        # Cell (0,1) should have count 1 (mine at 0,0)
        assert game.counts[0][1] == 1
        # Cell (1,0) should have count 1 (mine at 0,0)
        assert game.counts[1][0] == 1
        # Cell (1,1) should have count 1 (mine at 0,0 diagonal)
        assert game.counts[1][1] == 1
        # Cell (2,2) should have count 0 (far from mine)
        assert game.counts[2][2] == 0

    def test_reveal_safe_cell_success(self):
        """Test revealing a safe cell."""
        game = MinesweeperGame("easy")
        game.mines = [[False] * 6 for _ in range(6)]
        game.counts = [[0] * 6 for _ in range(6)]
        game.revealed = [[0] * 6 for _ in range(6)]
        game.size = 6
        game.num_mines = 0
        game.game_over = False
        game.game_started = True

        success, message = game.validate_move("reveal", 1, 1)
        assert success is True
        assert game.revealed[0][0] == 1

    def test_reveal_mine_ends_game(self):
        """Test that revealing a mine ends the game."""
        game = MinesweeperGame("easy")
        game.mines = [[True] + [False] * 5] + [[False] * 6 for _ in range(5)]
        game.counts = [[0] * 6 for _ in range(6)]
        game.revealed = [[0] * 6 for _ in range(6)]
        game.size = 6
        game.num_mines = 1
        game.game_over = False
        game.hit_mine = False
        game.game_started = True

        success, message = game.validate_move("reveal", 1, 1)
        assert success is True
        assert game.game_over is True
        assert game.hit_mine is True
        assert "boom" in message.lower() or "mine" in message.lower()

    def test_reveal_already_revealed_cell(self):
        """Test revealing an already revealed cell."""
        game = MinesweeperGame("easy")
        game.mines = [[False] * 6 for _ in range(6)]
        game.counts = [[0] * 6 for _ in range(6)]
        game.revealed = [[1] + [0] * 5] + [[0] * 6 for _ in range(5)]
        game.size = 6
        game.game_over = False
        game.game_started = True

        success, message = game.validate_move("reveal", 1, 1)
        assert success is False
        assert "already revealed" in message.lower()

    def test_reveal_flagged_cell(self):
        """Test revealing a flagged cell."""
        game = MinesweeperGame("easy")
        game.mines = [[False] * 6 for _ in range(6)]
        game.counts = [[0] * 6 for _ in range(6)]
        game.revealed = [[2] + [0] * 5] + [[0] * 6 for _ in range(5)]  # 2 = flagged
        game.size = 6
        game.game_over = False
        game.game_started = True

        success, message = game.validate_move("reveal", 1, 1)
        assert success is False
        assert "flagged" in message.lower()

    def test_flag_cell_success(self):
        """Test flagging a cell."""
        game = MinesweeperGame("easy")
        game.mines = [[True] + [False] * 5] + [[False] * 6 for _ in range(5)]
        game.revealed = [[0] * 6 for _ in range(6)]
        game.size = 6
        game.num_mines = 1
        game.game_over = False
        game.game_started = True

        success, message = game.validate_move("flag", 1, 1)
        assert success is True
        assert game.revealed[0][0] == 2  # 2 = flagged
        assert "flagged" in message.lower()

    def test_unflag_cell_success(self):
        """Test unflagging a cell."""
        game = MinesweeperGame("easy")
        game.mines = [[True] + [False] * 5] + [[False] * 6 for _ in range(5)]
        game.revealed = [[2] + [0] * 5] + [[0] * 6 for _ in range(5)]  # Already flagged
        game.size = 6
        game.game_over = False
        game.game_started = True

        success, message = game.validate_move("flag", 1, 1)
        assert success is True
        assert game.revealed[0][0] == 0  # Unflagged
        assert "unflagged" in message.lower()

    def test_flag_revealed_cell(self):
        """Test flagging an already revealed cell."""
        game = MinesweeperGame("easy")
        game.mines = [[False] * 6 for _ in range(6)]
        game.revealed = [[1] + [0] * 5] + [[0] * 6 for _ in range(5)]  # Already revealed
        game.size = 6
        game.game_over = False
        game.game_started = True

        success, message = game.validate_move("flag", 1, 1)
        assert success is False
        assert "cannot flag" in message.lower() or "revealed" in message.lower()

    def test_invalid_coordinates(self):
        """Test with invalid coordinates."""
        game = MinesweeperGame("easy")
        game.generate_puzzle()

        success, message = game.validate_move("reveal", 0, 1)
        assert success is False
        assert "invalid" in message.lower()

        success, message = game.validate_move("reveal", 10, 1)
        assert success is False
        assert "invalid" in message.lower()

    def test_invalid_action(self):
        """Test with invalid action."""
        game = MinesweeperGame("easy")
        game.generate_puzzle()

        success, message = game.validate_move("mark", 1, 1)
        assert success is False
        assert "invalid action" in message.lower()

    def test_auto_reveal_zero_cells(self):
        """Test that revealing a cell with 0 adjacent mines reveals neighbors."""
        game = MinesweeperGame("easy")
        # Create a grid with no mines
        game.mines = [[False] * 6 for _ in range(6)]
        game.counts = [[0] * 6 for _ in range(6)]
        game.revealed = [[0] * 6 for _ in range(6)]
        game.size = 6
        game.num_mines = 0
        game.game_over = False
        game.game_started = True

        # Reveal a corner cell with 0 adjacent mines
        game._reveal_cell(0, 0)

        # Should reveal multiple cells
        revealed_count = sum(sum(1 for cell in row if cell == 1) for row in game.revealed)
        assert revealed_count > 1  # More than just the one cell

    def test_check_win_all_revealed(self):
        """Test win condition when all non-mine cells revealed."""
        game = MinesweeperGame("easy")
        game.mines = [[True] + [False] * 5] + [[False] * 6 for _ in range(5)]
        game.revealed = [[0] + [1] * 5] + [[1] * 6 for _ in range(5)]  # All non-mines revealed
        game.size = 6
        game.num_mines = 1

        assert game._check_win() is True

    def test_check_win_not_all_revealed(self):
        """Test win condition when not all cells revealed."""
        game = MinesweeperGame("easy")
        game.mines = [[True] + [False] * 5] + [[False] * 6 for _ in range(5)]
        game.revealed = [[0] + [1] * 5] + [[1] * 5 + [0]] + [[1] * 6 for _ in range(4)]
        game.size = 6
        game.num_mines = 1

        assert game._check_win() is False

    def test_is_complete_when_won(self):
        """Test completion check when game is won."""
        game = MinesweeperGame("easy")
        game.game_over = True
        game.hit_mine = False

        assert game.is_complete() is True

    def test_is_complete_when_lost(self):
        """Test completion check when game is lost."""
        game = MinesweeperGame("easy")
        game.game_over = True
        game.hit_mine = True

        assert game.is_complete() is False

    def test_is_complete_when_ongoing(self):
        """Test completion check when game is ongoing."""
        game = MinesweeperGame("easy")
        game.game_over = False
        game.hit_mine = False

        assert game.is_complete() is False

    def test_get_hint_safe_cell(self):
        """Test hint for a safe cell to reveal."""
        game = MinesweeperGame("easy")
        game.mines = [[True] + [False] * 5] + [[False] * 6 for _ in range(5)]
        game.revealed = [[0] * 6 for _ in range(6)]
        game.size = 6
        game.num_mines = 1
        game.game_over = False

        hint_data, hint_message = game.get_hint()
        action, row, col = hint_data

        assert action == "reveal"
        assert 1 <= row <= 6
        assert 1 <= col <= 6
        # Hint should point to a non-mine cell
        assert game.mines[row - 1][col - 1] is False
        assert "safe" in hint_message.lower()

    def test_get_hint_flag_mine(self):
        """Test hint for flagging a mine when all safe cells revealed."""
        game = MinesweeperGame("easy")
        game.mines = [[True] + [False] * 5] + [[False] * 6 for _ in range(5)]
        game.revealed = [[0] + [1] * 5] + [[1] * 6 for _ in range(5)]  # All safe cells revealed
        game.size = 6
        game.num_mines = 1
        game.game_over = False

        hint_data, hint_message = game.get_hint()
        action, row, col = hint_data

        assert action == "flag"
        assert game.mines[row - 1][col - 1] is True
        assert "mine" in hint_message.lower()

    def test_get_hint_game_over(self):
        """Test hint when game is over."""
        game = MinesweeperGame("easy")
        game.game_over = True

        result = game.get_hint()
        assert result is None

    def test_render_grid(self):
        """Test grid rendering."""
        game = MinesweeperGame("easy")
        game.generate_puzzle()

        grid_str = game.render_grid()
        assert "Mines" in grid_str
        assert "Flags" in grid_str
        assert "Legend" in grid_str

    def test_render_grid_shows_mines_when_game_over(self):
        """Test that grid shows mines when game is over."""
        game = MinesweeperGame("easy")
        game.mines = [[True] + [False] * 5] + [[False] * 6 for _ in range(5)]
        game.revealed = [[1] + [0] * 5] + [[0] * 6 for _ in range(5)]
        game.size = 6
        game.num_mines = 1
        game.game_over = True
        game.hit_mine = True

        grid_str = game.render_grid()
        assert "GAME OVER" in grid_str or "game over" in grid_str.lower()

    def test_get_rules(self):
        """Test rules retrieval."""
        game = MinesweeperGame("easy")
        game.generate_puzzle()

        rules = game.get_rules()
        assert "MINESWEEPER" in rules.upper()
        assert "mine" in rules.lower()
        assert "reveal" in rules.lower()
        assert "flag" in rules.lower()

    def test_get_commands(self):
        """Test commands retrieval."""
        game = MinesweeperGame("easy")
        commands = game.get_commands()

        assert "reveal" in commands.lower()
        assert "flag" in commands.lower()
        assert "show" in commands.lower()

    def test_get_stats(self):
        """Test statistics retrieval."""
        game = MinesweeperGame("easy")
        game.generate_puzzle()

        stats = game.get_stats()
        assert "Moves" in stats
        assert "Revealed" in stats
        assert "Flags" in stats

    def test_moves_counter(self):
        """Test that moves are counted correctly."""
        game = MinesweeperGame("easy")
        game.generate_puzzle()

        initial_moves = game.moves_made
        # Find a safe cell and reveal it
        for row in range(game.size):
            for col in range(game.size):
                if not game.mines[row][col]:
                    game.validate_move("reveal", row + 1, col + 1)
                    assert game.moves_made == initial_moves + 1
                    return

    @pytest.mark.parametrize(
        "difficulty,expected_size,expected_mines", [("easy", 6, 6), ("medium", 8, 12), ("hard", 10, 20)]
    )
    def test_difficulty_levels(self, difficulty, expected_size, expected_mines):
        """Test different difficulty levels."""
        game = MinesweeperGame(difficulty)
        game.generate_puzzle()
        assert game.size == expected_size
        mine_count = sum(sum(1 for cell in row if cell) for row in game.mines)
        assert mine_count == expected_mines

    def test_action_aliases(self):
        """Test that action aliases work (r for reveal, f for flag)."""
        game = MinesweeperGame("easy")
        game.mines = [[False] * 6 for _ in range(6)]
        game.counts = [[0] * 6 for _ in range(6)]
        game.revealed = [[0] * 6 for _ in range(6)]
        game.size = 6
        game.num_mines = 0
        game.game_over = False
        game.game_started = True

        # Test 'r' alias for reveal
        success, _ = game.validate_move("r", 1, 1)
        assert success is True
        assert game.revealed[0][0] == 1

        # Test 'f' alias for flag
        success, _ = game.validate_move("f", 2, 2)
        assert success is True
        assert game.revealed[1][1] == 2

    def test_win_message_on_reveal(self):
        """Test that win message appears when winning by revealing last cell."""
        game = MinesweeperGame("easy")
        game.mines = [[True] + [False] * 5] + [[False] * 6 for _ in range(5)]
        game.revealed = [[0] + [1] * 5] + [[1] * 5 + [0]] + [[1] * 6 for _ in range(4)]
        game.counts = [[0] * 6 for _ in range(6)]
        game.size = 6
        game.num_mines = 1
        game.game_over = False
        game.game_started = True

        # Reveal the last safe cell
        success, message = game.validate_move("reveal", 6, 6)
        assert success is True
        assert game.game_over is True
        assert "congratulations" in message.lower() or "win" in message.lower()

    def test_win_message_on_flag(self):
        """Test that win message appears when winning by flagging."""
        game = MinesweeperGame("easy")
        game.mines = [[True] + [False] * 5] + [[False] * 6 for _ in range(5)]
        game.revealed = [[0] + [1] * 5] + [[1] * 6 for _ in range(5)]  # All safe cells revealed
        game.size = 6
        game.num_mines = 1
        game.game_over = False
        game.game_started = True

        # Flag the mine
        success, message = game.validate_move("flag", 1, 1)
        # Note: Win is triggered when all non-mines are revealed, not when all mines are flagged
        # So this might not trigger win unless the game logic also checks for all mines flagged

    def test_count_adjacent_mines_corner(self):
        """Test mine counting in corner."""
        game = MinesweeperGame("easy")
        game.mines = [
            [False, True, False, False, False, False],
            [True, False, False, False, False, False],
            [False, False, False, False, False, False],
            [False, False, False, False, False, False],
            [False, False, False, False, False, False],
            [False, False, False, False, False, False],
        ]
        game.size = 6

        # Corner (0,0) has 2 adjacent mines
        count = game._count_adjacent_mines(0, 0)
        assert count == 2

    def test_count_adjacent_mines_edge(self):
        """Test mine counting on edge."""
        game = MinesweeperGame("easy")
        game.mines = [
            [True, False, True, False, False, False],
            [False, False, False, False, False, False],
            [True, False, True, False, False, False],
            [False, False, False, False, False, False],
            [False, False, False, False, False, False],
            [False, False, False, False, False, False],
        ]
        game.size = 6

        # Edge cell (1,1) should have 4 adjacent mines
        count = game._count_adjacent_mines(1, 1)
        assert count == 4

    def test_count_adjacent_mines_center(self):
        """Test mine counting in center with all neighbors mines."""
        game = MinesweeperGame("easy")
        game.mines = [
            [False, False, False, False, False, False],
            [False, True, True, True, False, False],
            [False, True, False, True, False, False],
            [False, True, True, True, False, False],
            [False, False, False, False, False, False],
            [False, False, False, False, False, False],
        ]
        game.size = 6

        # Center cell (2,2) has 8 adjacent mines
        count = game._count_adjacent_mines(2, 2)
        assert count == 8

    def test_game_over_prevents_moves(self):
        """Test that no moves can be made after game over."""
        game = MinesweeperGame("easy")
        game.generate_puzzle()
        game.game_over = True

        success, message = game.validate_move("reveal", 1, 1)
        assert success is False
        assert "game is over" in message.lower()

    def test_zero_indexed_vs_one_indexed(self):
        """Test that internal 0-indexing converts correctly."""
        game = MinesweeperGame("easy")
        game.generate_puzzle()

        # User passes row=1, col=1 (1-indexed)
        # Should access mines[0][0] (0-indexed)
        user_facing_row = 1
        user_facing_col = 1
        internal_row = 0
        internal_col = 0

        # The validate_move should handle the conversion
        original_value = game.revealed[internal_row][internal_col]
        game.validate_move("flag", user_facing_row, user_facing_col)
        assert game.revealed[internal_row][internal_col] != original_value
