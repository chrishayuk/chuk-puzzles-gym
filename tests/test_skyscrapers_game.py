"""Tests for Skyscrapers puzzle game."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.skyscrapers import SkyscrapersGame


class TestSkyscrapersGame:
    """Test suite for SkyscrapersGame."""

    async def test_initialization(self):
        game = SkyscrapersGame("easy")
        assert game.size == 4
        assert game.name == "Skyscrapers"

    @pytest.mark.parametrize(
        "difficulty,expected_size",
        [("easy", 4), ("medium", 5), ("hard", 6)],
    )
    async def test_difficulty_levels(self, difficulty, expected_size):
        game = SkyscrapersGame(difficulty)
        await game.generate_puzzle()
        assert game.size == expected_size

    async def test_generate_puzzle(self):
        game = SkyscrapersGame("easy", seed=42)
        await game.generate_puzzle()
        assert game.game_started
        assert len(game.solution) == game.size
        assert all(len(row) == game.size for row in game.solution)
        # Verify Latin square property
        n = game.size
        for r in range(n):
            assert sorted(game.solution[r]) == list(range(1, n + 1))
        for c in range(n):
            col = [game.solution[r][c] for r in range(n)]
            assert sorted(col) == list(range(1, n + 1))

    async def test_visibility_clues(self):
        game = SkyscrapersGame("easy", seed=42)
        await game.generate_puzzle()
        # Verify clues are computed correctly from solution
        n = game.size
        for c in range(n):
            col = [game.solution[r][c] for r in range(n)]
            count = 0
            max_h = 0
            for h in col:
                if h > max_h:
                    count += 1
                    max_h = h
            assert game.clues["top"][c] == count

    async def test_place_valid(self):
        game = SkyscrapersGame("easy", seed=42)
        await game.generate_puzzle()
        # Find an empty cell and place the correct value
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 0:
                    val = game.solution[r][c]
                    result = await game.validate_move(r + 1, c + 1, val)
                    assert result.success
                    assert game.grid[r][c] == val
                    return

    async def test_place_invalid_duplicate_row(self):
        game = SkyscrapersGame("easy", seed=42)
        await game.generate_puzzle()
        # Find a row with a known value and try to place duplicate
        for r in range(game.size):
            existing_val = None
            empty_col = None
            for c in range(game.size):
                if game.grid[r][c] != 0:
                    existing_val = game.grid[r][c]
                elif empty_col is None:
                    empty_col = c
            if existing_val is not None and empty_col is not None:
                result = await game.validate_move(r + 1, empty_col + 1, existing_val)
                assert not result.success
                return

    async def test_cannot_modify_initial_cells(self):
        game = SkyscrapersGame("easy", seed=42)
        await game.generate_puzzle()
        for r in range(game.size):
            for c in range(game.size):
                if game.initial_grid[r][c] != 0:
                    result = await game.validate_move(r + 1, c + 1, 1)
                    assert not result.success
                    assert "initial" in result.message.lower() or "cannot" in result.message.lower()
                    return

    async def test_clear_cell(self):
        game = SkyscrapersGame("easy", seed=42)
        await game.generate_puzzle()
        # Find empty cell, place, then clear
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 0:
                    val = game.solution[r][c]
                    await game.validate_move(r + 1, c + 1, val)
                    result = await game.validate_move(r + 1, c + 1, 0)
                    assert result.success
                    assert game.grid[r][c] == 0
                    return

    async def test_is_complete(self):
        game = SkyscrapersGame("easy", seed=42)
        await game.generate_puzzle()
        assert not game.is_complete()
        game.grid = [row[:] for row in game.solution]
        assert game.is_complete()

    async def test_get_hint(self):
        game = SkyscrapersGame("easy", seed=42)
        await game.generate_puzzle()
        hint = await game.get_hint()
        assert hint is not None
        hint_data, hint_message = hint
        row, col, val = hint_data
        assert 1 <= row <= game.size
        assert 1 <= col <= game.size
        assert val == game.solution[row - 1][col - 1]

    async def test_render_grid(self):
        game = SkyscrapersGame("easy", seed=42)
        await game.generate_puzzle()
        rendered = game.render_grid()
        assert isinstance(rendered, str)
        assert len(rendered) > 0

    async def test_get_rules(self):
        game = SkyscrapersGame("easy")
        rules = game.get_rules()
        assert isinstance(rules, str)
        assert "skyscrapers" in rules.lower() or "visible" in rules.lower()

    async def test_get_commands(self):
        game = SkyscrapersGame("easy")
        commands = game.get_commands()
        assert isinstance(commands, str)
        assert "place" in commands.lower()

    async def test_get_stats(self):
        game = SkyscrapersGame("easy", seed=42)
        await game.generate_puzzle()
        stats = game.get_stats()
        assert "Seed" in stats

    async def test_constraint_types(self):
        game = SkyscrapersGame("easy")
        assert isinstance(game.constraint_types, list)
        assert len(game.constraint_types) > 0

    async def test_business_analogies(self):
        game = SkyscrapersGame("easy")
        assert isinstance(game.business_analogies, list)
        assert len(game.business_analogies) > 0

    async def test_complexity_profile(self):
        game = SkyscrapersGame("easy")
        profile = game.complexity_profile
        assert isinstance(profile, dict)
        assert "reasoning_type" in profile

    async def test_deterministic_seeding(self):
        game1 = SkyscrapersGame("easy", seed=12345)
        await game1.generate_puzzle()
        game2 = SkyscrapersGame("easy", seed=12345)
        await game2.generate_puzzle()
        assert game1.grid == game2.grid
        assert game1.solution == game2.solution

    async def test_out_of_bounds(self):
        game = SkyscrapersGame("easy", seed=42)
        await game.generate_puzzle()
        result = await game.validate_move(0, 0, 1)
        assert not result.success
        result = await game.validate_move(game.size + 1, 1, 1)
        assert not result.success

    async def test_invalid_value(self):
        game = SkyscrapersGame("easy", seed=42)
        await game.generate_puzzle()
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 0:
                    result = await game.validate_move(r + 1, c + 1, game.size + 1)
                    assert not result.success
                    return
