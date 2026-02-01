"""Tests for Numberlink puzzle game."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.numberlink import NumberlinkGame


class TestNumberlinkGame:
    """Test suite for NumberlinkGame."""

    async def test_initialization(self):
        game = NumberlinkGame("easy")
        assert game.size == 5
        assert game.num_pairs == 4
        assert game.name == "Numberlink"

    @pytest.mark.parametrize(
        "difficulty,expected_size,expected_pairs",
        [("easy", 5, 4), ("medium", 7, 6), ("hard", 9, 9)],
    )
    async def test_difficulty_levels(self, difficulty, expected_size, expected_pairs):
        game = NumberlinkGame(difficulty, seed=42)
        await game.generate_puzzle()
        assert game.size == expected_size

    async def test_generate_puzzle(self):
        game = NumberlinkGame("easy", seed=42)
        await game.generate_puzzle()
        assert game.game_started
        # Solution should fill entire grid
        n = game.size
        for r in range(n):
            for c in range(n):
                assert game.solution[r][c] > 0, f"Cell ({r},{c}) is empty in solution"
        # Each pair should have exactly 2 endpoints
        for _pair_id, pts in game.endpoints.items():
            assert len(pts) == 2

    async def test_endpoints_in_initial_grid(self):
        game = NumberlinkGame("easy", seed=42)
        await game.generate_puzzle()
        for pair_id, pts in game.endpoints.items():
            for r, c in pts:
                assert game.initial_grid[r][c] == pair_id

    async def test_place_valid(self):
        game = NumberlinkGame("easy", seed=42)
        await game.generate_puzzle()
        # Find a non-endpoint empty cell and place from solution
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 0:
                    val = game.solution[r][c]
                    result = await game.validate_move(r + 1, c + 1, val)
                    assert result.success
                    assert game.grid[r][c] == val
                    return

    async def test_cannot_modify_endpoints(self):
        game = NumberlinkGame("easy", seed=42)
        await game.generate_puzzle()
        for _pair_id, pts in game.endpoints.items():
            r, c = pts[0]
            result = await game.validate_move(r + 1, c + 1, 1)
            assert not result.success
            return

    async def test_clear_cell(self):
        game = NumberlinkGame("easy", seed=42)
        await game.generate_puzzle()
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 0:
                    val = game.solution[r][c]
                    await game.validate_move(r + 1, c + 1, val)
                    result = await game.validate_move(r + 1, c + 1, 0)
                    assert result.success
                    assert game.grid[r][c] == 0
                    return

    async def test_invalid_pair_number(self):
        game = NumberlinkGame("easy", seed=42)
        await game.generate_puzzle()
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 0:
                    result = await game.validate_move(r + 1, c + 1, game.num_pairs + 1)
                    assert not result.success
                    return

    async def test_is_complete(self):
        game = NumberlinkGame("easy", seed=42)
        await game.generate_puzzle()
        assert not game.is_complete()
        game.grid = [row[:] for row in game.solution]
        assert game.is_complete()

    async def test_get_hint(self):
        game = NumberlinkGame("easy", seed=42)
        await game.generate_puzzle()
        hint = await game.get_hint()
        assert hint is not None
        hint_data, hint_message = hint
        row, col, val = hint_data
        assert game.solution[row - 1][col - 1] == val

    async def test_render_grid(self):
        game = NumberlinkGame("easy", seed=42)
        await game.generate_puzzle()
        rendered = game.render_grid()
        assert isinstance(rendered, str)
        assert len(rendered) > 0

    async def test_get_rules(self):
        game = NumberlinkGame("easy")
        assert "path" in game.get_rules().lower() or "connect" in game.get_rules().lower()

    async def test_get_commands(self):
        game = NumberlinkGame("easy")
        assert "place" in game.get_commands().lower()

    async def test_get_stats(self):
        game = NumberlinkGame("easy", seed=42)
        await game.generate_puzzle()
        assert "Seed" in game.get_stats()

    async def test_constraint_types(self):
        game = NumberlinkGame("easy")
        assert len(game.constraint_types) > 0

    async def test_business_analogies(self):
        game = NumberlinkGame("easy")
        assert len(game.business_analogies) > 0

    async def test_complexity_profile(self):
        game = NumberlinkGame("easy")
        profile = game.complexity_profile
        assert "reasoning_type" in profile

    async def test_deterministic_seeding(self):
        game1 = NumberlinkGame("easy", seed=12345)
        await game1.generate_puzzle()
        game2 = NumberlinkGame("easy", seed=12345)
        await game2.generate_puzzle()
        assert game1.grid == game2.grid
        assert game1.solution == game2.solution

    async def test_out_of_bounds(self):
        game = NumberlinkGame("easy", seed=42)
        await game.generate_puzzle()
        result = await game.validate_move(0, 0, 1)
        assert not result.success
