"""Tests for Mastermind puzzle game."""

import pytest

from puzzle_arcade_server.games.mastermind import MastermindGame


class TestMastermindGame:
    """Test suite for Mastermind game."""

    async def test_initialization_easy(self):
        """Test game initialization with easy difficulty."""
        game = MastermindGame("easy")
        assert game.difficulty == "easy"
        assert game.code_length == 4
        assert game.num_colors == 6
        assert game.max_guesses == 12
        assert game.name == "Mastermind"

    async def test_initialization_medium(self):
        """Test game initialization with medium difficulty."""
        game = MastermindGame("medium")
        assert game.code_length == 5
        assert game.num_colors == 7
        assert game.max_guesses == 12

    async def test_initialization_hard(self):
        """Test game initialization with hard difficulty."""
        game = MastermindGame("hard")
        assert game.code_length == 6
        assert game.num_colors == 8
        assert game.max_guesses == 15

    async def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = MastermindGame("easy")
        await game.generate_puzzle()

        assert game.game_started is True
        assert game.moves_made == 0
        assert len(game.secret_code) == 4
        assert all(1 <= c <= 6 for c in game.secret_code)
        assert len(game.guesses) == 0
        assert len(game.feedback) == 0

    async def test_calculate_feedback_all_correct(self):
        """Test feedback calculation with all correct."""
        game = MastermindGame("easy")
        game.secret_code = [1, 2, 3, 4]

        black, white = game._calculate_feedback([1, 2, 3, 4])
        assert black == 4
        assert white == 0

    async def test_calculate_feedback_all_wrong(self):
        """Test feedback calculation with all wrong."""
        game = MastermindGame("easy")
        game.secret_code = [1, 2, 3, 4]

        black, white = game._calculate_feedback([5, 6, 5, 6])
        assert black == 0
        assert white == 0

    async def test_calculate_feedback_mixed(self):
        """Test feedback calculation with mixed results."""
        game = MastermindGame("easy")
        game.secret_code = [1, 2, 3, 4]

        # 1 correct position, 2 correct colors wrong position
        black, white = game._calculate_feedback([1, 3, 4, 5])
        assert black == 1  # 1 in position 0
        assert white == 2  # 3 and 4 are in code but wrong positions

    async def test_calculate_feedback_duplicates(self):
        """Test feedback calculation with duplicate colors."""
        game = MastermindGame("easy")
        game.secret_code = [1, 1, 2, 3]

        # Guess has duplicates
        black, white = game._calculate_feedback([1, 2, 3, 4])
        assert black == 1  # 1 in position 0
        assert white == 2  # 2 and 3 in wrong positions

    async def test_calculate_feedback_no_double_count(self):
        """Test that feedback doesn't double-count colors."""
        game = MastermindGame("easy")
        game.secret_code = [1, 2, 3, 4]

        # Guess has duplicate 1s, but code only has one 1
        black, white = game._calculate_feedback([1, 1, 1, 1])
        assert black == 1  # Only position 0 is correct
        assert white == 0  # No other 1s to match

    async def test_validate_move_success(self):
        """Test successful move validation."""
        game = MastermindGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(1, 2, 3, 4)
        success, _message = result.success, result.message
        assert success is True
        assert len(game.guesses) == 1
        assert game.moves_made == 1

    async def test_validate_move_wrong_length(self):
        """Test move with wrong number of colors."""
        game = MastermindGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(1, 2, 3)
        success, message = result.success, result.message
        assert success is False
        assert "exactly" in message.lower()

    async def test_validate_move_invalid_color(self):
        """Test move with invalid color."""
        game = MastermindGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(1, 2, 3, 99)
        success, message = result.success, result.message
        assert success is False
        assert "Invalid color" in message

    async def test_validate_move_win(self):
        """Test winning the game."""
        game = MastermindGame("easy")
        game.secret_code = [1, 2, 3, 4]
        game.guesses = []
        game.feedback = []
        game.game_started = True
        game.max_guesses = 10

        result = await game.validate_move(1, 2, 3, 4)
        success, message = result.success, result.message
        assert success is True
        assert "Congratulations" in message

    async def test_validate_move_game_over(self):
        """Test running out of guesses."""
        game = MastermindGame("easy")
        await game.generate_puzzle()
        game.secret_code = [1, 2, 3, 4]

        # Fill up all guesses except one
        for _ in range(game.max_guesses - 1):
            await game.validate_move(5, 5, 5, 5)

        # Last guess should still succeed but mark game as over
        result = await game.validate_move(5, 5, 5, 5)
        assert result.success is True
        assert result.game_over is True
        assert "Game over" in result.message
        assert "1 2 3 4" in result.message

    async def test_is_complete_won(self):
        """Test completion check when won."""
        game = MastermindGame("easy")
        game.secret_code = [1, 2, 3, 4]
        game.guesses = [[1, 2, 3, 4]]
        game.feedback = [(4, 0)]

        assert game.is_complete() is True

    async def test_is_complete_not_won(self):
        """Test completion check when not won."""
        game = MastermindGame("easy")
        game.secret_code = [1, 2, 3, 4]
        game.guesses = [[1, 2, 3, 5]]
        game.feedback = [(3, 0)]

        assert game.is_complete() is False

    async def test_is_complete_no_guesses(self):
        """Test completion check with no guesses."""
        game = MastermindGame("easy")
        await game.generate_puzzle()

        assert game.is_complete() is False

    async def test_get_hint_first_position(self):
        """Test hint for first guess - returns full secret code."""
        game = MastermindGame("easy")
        game.secret_code = [1, 2, 3, 4]
        game.guesses = []
        game.feedback = []

        hint_data, hint_message = await game.get_hint()
        # Hint now returns full secret code for evaluation purposes
        assert hint_data == (1, 2, 3, 4)
        assert "1 2 3 4" in hint_message

    async def test_get_hint_after_guess(self):
        """Test hint after making a guess - returns full secret code."""
        game = MastermindGame("easy")
        game.secret_code = [1, 2, 3, 4]
        game.guesses = [[5, 5, 5, 5]]
        game.feedback = [(0, 0)]

        hint_data, hint_message = await game.get_hint()
        assert hint_data is not None
        # Hint returns full secret code
        assert len(hint_data) == 4
        assert "secret code" in hint_message.lower()

    async def test_get_hint_solved(self):
        """Test hint when game is solved."""
        game = MastermindGame("easy")
        game.secret_code = [1, 2, 3, 4]
        game.guesses = [[1, 2, 3, 4]]
        game.feedback = [(4, 0)]

        result = await game.get_hint()
        assert result is None

    async def test_render_grid(self):
        """Test grid rendering."""
        game = MastermindGame("easy")
        await game.generate_puzzle()

        grid_str = game.render_grid()
        assert "Mastermind" in grid_str
        assert "Colors available:" in grid_str
        assert "Guesses remaining:" in grid_str

    async def test_render_grid_with_guesses(self):
        """Test grid rendering with guess history."""
        game = MastermindGame("easy")
        game.secret_code = [1, 2, 3, 4]
        game.guesses = [[1, 2, 5, 5]]
        game.feedback = [(2, 0)]
        game.game_started = True

        grid_str = game.render_grid()
        assert "Guess History:" in grid_str
        assert "Black" in grid_str
        assert "White" in grid_str

    async def test_get_rules(self):
        """Test rules retrieval."""
        game = MastermindGame("easy")
        rules = game.get_rules()

        assert "MASTERMIND" in rules
        assert "Black peg" in rules
        assert "White peg" in rules

    async def test_get_commands(self):
        """Test commands retrieval."""
        game = MastermindGame("easy")
        commands = game.get_commands()

        assert "guess" in commands.lower()
        assert "show" in commands.lower()
        assert "hint" in commands.lower()

    async def test_get_stats(self):
        """Test statistics retrieval."""
        game = MastermindGame("easy")
        await game.generate_puzzle()

        stats = game.get_stats()
        assert "Guesses:" in stats or "Guesses made:" in stats
        assert "Code:" in stats or "Code length:" in stats
        assert "Colors:" in stats
        assert "Seed:" in stats

    async def test_moves_counter(self):
        """Test that moves are counted correctly."""
        game = MastermindGame("easy")
        await game.generate_puzzle()

        initial_moves = game.moves_made
        await game.validate_move(1, 2, 3, 4)
        assert game.moves_made == initial_moves + 1

    async def test_color_names(self):
        """Test color name mapping."""
        game = MastermindGame("easy")

        assert game.color_names[1] == "Red"
        assert game.color_names[2] == "Blue"
        assert game.color_names[6] == "Purple"

    @pytest.mark.parametrize(
        "secret,guess,expected_black,expected_white",
        [
            ([1, 2, 3, 4], [1, 2, 3, 4], 4, 0),  # All correct
            ([1, 2, 3, 4], [4, 3, 2, 1], 0, 4),  # All wrong position
            ([1, 2, 3, 4], [1, 3, 2, 4], 2, 2),  # Mixed
            ([1, 1, 2, 2], [2, 2, 1, 1], 0, 4),  # Duplicates swapped
            ([1, 2, 3, 4], [5, 6, 5, 6], 0, 0),  # All wrong
        ],
    )
    async def test_feedback_scenarios(self, secret, guess, expected_black, expected_white):
        """Test various feedback scenarios."""
        game = MastermindGame("easy")
        game.secret_code = secret

        black, white = game._calculate_feedback(guess)
        assert black == expected_black
        assert white == expected_white

    async def test_feedback_stored_correctly(self):
        """Test that feedback is stored with guesses."""
        game = MastermindGame("easy")
        game.secret_code = [1, 2, 3, 4]
        game.guesses = []
        game.feedback = []
        game.game_started = True
        game.max_guesses = 10

        await game.validate_move(1, 2, 5, 6)

        assert len(game.guesses) == 1
        assert len(game.feedback) == 1
        assert game.guesses[0] == [1, 2, 5, 6]
        black, white = game.feedback[0]
        assert black == 2
        assert white == 0

    async def test_constraint_types(self):
        """Test constraint types metadata."""
        game = MastermindGame("easy")
        constraint_types = game.constraint_types
        assert isinstance(constraint_types, list)
        assert len(constraint_types) > 0
        assert all(isinstance(ct, str) for ct in constraint_types)

    async def test_business_analogies(self):
        """Test business analogies metadata."""
        game = MastermindGame("easy")
        analogies = game.business_analogies
        assert isinstance(analogies, list)
        assert len(analogies) > 0
        assert all(isinstance(a, str) for a in analogies)

    async def test_complexity_profile(self):
        """Test complexity profile metadata."""
        game = MastermindGame("easy")
        profile = game.complexity_profile
        assert isinstance(profile, dict)
        assert "reasoning_type" in profile
        assert "search_space" in profile
        assert "constraint_density" in profile
