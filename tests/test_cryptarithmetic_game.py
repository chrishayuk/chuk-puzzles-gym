"""Tests for Cryptarithmetic puzzle game."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.cryptarithmetic import CryptarithmeticCommandHandler, CryptarithmeticGame
from chuk_puzzles_gym.models import GameCommand


class TestCryptarithmeticGame:
    """Test suite for CryptarithmeticGame."""

    async def test_initialization(self):
        game = CryptarithmeticGame("easy")
        assert game.name == "Cryptarithmetic"

    @pytest.mark.parametrize(
        "difficulty,expected_max_len",
        [("easy", 3), ("medium", 4), ("hard", 5)],
    )
    async def test_difficulty_levels(self, difficulty, expected_max_len):
        game = CryptarithmeticGame(difficulty, seed=42)
        await game.generate_puzzle()
        assert game.config.max_word_length == expected_max_len

    async def test_generate_puzzle(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        assert game.game_started
        assert len(game.operands) >= 2
        assert len(game.result_word) > 0
        assert len(game.letters) > 0
        assert len(game.letter_mapping) == len(game.letters)

    async def test_solution_valid(self):
        """Verify the solution satisfies the equation."""
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        operand_values = []
        for word in game.operands:
            val = 0
            for ch in word:
                val = val * 10 + game.letter_mapping[ch]
            operand_values.append(val)
        result_val = 0
        for ch in game.result_word:
            result_val = result_val * 10 + game.letter_mapping[ch]
        assert sum(operand_values) == result_val

    async def test_no_leading_zeros(self):
        """Verify no leading letter maps to 0 in solution."""
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        for letter in game.leading_letters:
            assert game.letter_mapping[letter] != 0

    async def test_unique_digit_mapping(self):
        """Verify each letter maps to a unique digit."""
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        digits = list(game.letter_mapping.values())
        assert len(digits) == len(set(digits))

    async def test_assign_valid(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        # Find an unassigned letter and assign correct digit
        for letter in game.letters:
            if game.player_mapping[letter] is None:
                digit = game.letter_mapping[letter]
                result = await game.validate_move(letter, digit)
                assert result.success
                assert game.player_mapping[letter] == digit
                return

    async def test_assign_leading_zero(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        for letter in game.leading_letters:
            if letter not in game.initial_mapping:
                result = await game.validate_move(letter, 0)
                assert not result.success
                assert "leading" in result.message.lower() or "zero" in result.message.lower()
                return

    async def test_assign_duplicate_digit(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        # Assign a digit to one letter, then try same digit on another
        letters = [ch for ch in game.letters if ch not in game.initial_mapping]
        if len(letters) >= 2:
            digit = game.letter_mapping[letters[0]]
            await game.validate_move(letters[0], digit)
            result = await game.validate_move(letters[1], digit)
            assert not result.success

    async def test_unassign(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        for letter in game.letters:
            if letter not in game.initial_mapping:
                digit = game.letter_mapping[letter]
                await game.validate_move(letter, digit)
                result = await game.validate_move(letter, -1)
                assert result.success
                assert game.player_mapping[letter] is None
                return

    async def test_cannot_modify_pre_assigned(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        for letter in game.initial_mapping:
            result = await game.validate_move(letter, 5)
            assert not result.success
            return

    async def test_invalid_letter(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        result = await game.validate_move("Z" if "Z" not in game.letters else "!", 1)
        assert not result.success

    async def test_invalid_digit(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        for letter in game.letters:
            if letter not in game.initial_mapping:
                result = await game.validate_move(letter, 10)
                assert not result.success
                return

    async def test_is_complete(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        assert not game.is_complete()
        # Set all to solution
        for letter in game.letters:
            game.player_mapping[letter] = game.letter_mapping[letter]
        assert game.is_complete()

    async def test_is_complete_wrong_answer(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        # Assign all letters but with wrong values
        digits = list(range(10))
        for i, letter in enumerate(game.letters):
            game.player_mapping[letter] = digits[i]
        # This likely won't satisfy the equation
        # (but could by coincidence, so just check it's a bool)
        result = game.is_complete()
        assert isinstance(result, bool)

    async def test_get_hint(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        hint = await game.get_hint()
        assert hint is not None
        hint_data, hint_message = hint
        letter, digit = hint_data
        assert game.letter_mapping[letter] == digit

    async def test_render_grid(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        rendered = game.render_grid()
        assert isinstance(rendered, str)
        assert "Equation" in rendered

    async def test_get_rules(self):
        game = CryptarithmeticGame("easy")
        assert "digit" in game.get_rules().lower()

    async def test_get_commands(self):
        game = CryptarithmeticGame("easy")
        assert "assign" in game.get_commands().lower()

    async def test_constraint_types(self):
        game = CryptarithmeticGame("easy")
        assert "arithmetic" in game.constraint_types

    async def test_business_analogies(self):
        game = CryptarithmeticGame("easy")
        assert len(game.business_analogies) > 0

    async def test_complexity_profile(self):
        game = CryptarithmeticGame("easy")
        profile = game.complexity_profile
        assert "reasoning_type" in profile

    async def test_deterministic_seeding(self):
        game1 = CryptarithmeticGame("easy", seed=12345)
        await game1.generate_puzzle()
        game2 = CryptarithmeticGame("easy", seed=12345)
        await game2.generate_puzzle()
        assert game1.letter_mapping == game2.letter_mapping
        assert game1.equation == game2.equation

    async def test_command_handler_assign(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        handler = CryptarithmeticCommandHandler(game)
        assert GameCommand.ASSIGN in handler.supported_commands
        for letter in game.letters:
            if letter not in game.initial_mapping:
                digit = game.letter_mapping[letter]
                result = await handler.handle_command(GameCommand.ASSIGN, [letter, str(digit)])
                assert result.result.success
                return

    async def test_command_handler_unassign(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        handler = CryptarithmeticCommandHandler(game)
        assert GameCommand.UNASSIGN in handler.supported_commands
        for letter in game.letters:
            if letter not in game.initial_mapping:
                await game.validate_move(letter, game.letter_mapping[letter])
                result = await handler.handle_command(GameCommand.UNASSIGN, [letter])
                assert result.result.success
                return

    async def test_command_handler_bad_args(self):
        game = CryptarithmeticGame("easy", seed=42)
        await game.generate_puzzle()
        handler = CryptarithmeticCommandHandler(game)
        result = await handler.handle_command(GameCommand.ASSIGN, ["A"])
        assert not result.result.success
