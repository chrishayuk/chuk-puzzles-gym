"""Tests for N-Queens puzzle game."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.nqueens import NQueensGame


class TestNQueensGame:
    """Test suite for NQueensGame."""

    async def test_initialization(self):
        game = NQueensGame("easy")
        assert game.size == 6
        assert game.name == "N-Queens"

    @pytest.mark.parametrize(
        "difficulty,expected_size,expected_pre",
        [("easy", 6, 3), ("medium", 8, 2), ("hard", 12, 1)],
    )
    async def test_difficulty_levels(self, difficulty, expected_size, expected_pre):
        game = NQueensGame(difficulty, seed=42)
        await game.generate_puzzle()
        assert game.size == expected_size
        initial_queens = sum(1 for row in game.initial_grid for cell in row if cell == 1)
        assert initial_queens == expected_pre

    async def test_generate_puzzle(self):
        game = NQueensGame("easy", seed=42)
        await game.generate_puzzle()
        assert game.game_started
        # Solution should have exactly N queens
        queen_count = sum(1 for row in game.solution for cell in row if cell == 1)
        assert queen_count == game.size

    async def test_solution_no_conflicts(self):
        game = NQueensGame("easy", seed=42)
        await game.generate_puzzle()
        n = game.size
        queens = []
        for r in range(n):
            for c in range(n):
                if game.solution[r][c] == 1:
                    queens.append((r, c))
        # Check no two queens conflict
        for i in range(len(queens)):
            for j in range(i + 1, len(queens)):
                r1, c1 = queens[i]
                r2, c2 = queens[j]
                assert r1 != r2, "Two queens in same row"
                assert c1 != c2, "Two queens in same column"
                assert abs(r1 - r2) != abs(c1 - c2), "Two queens on same diagonal"

    async def test_place_queen_valid(self):
        game = NQueensGame("easy", seed=42)
        await game.generate_puzzle()
        # Find an empty row and place from solution
        for r in range(game.size):
            c = game._queen_cols[r]
            if game.grid[r][c] == 0:
                result = await game.validate_move(r + 1, c + 1, 1)
                assert result.success
                assert game.grid[r][c] == 1
                return

    async def test_place_queen_conflict_row(self):
        game = NQueensGame("easy", seed=42)
        await game.generate_puzzle()
        # Find a row with a pre-placed queen, try to place another in same row
        for r in range(game.size):
            queen_col = None
            empty_col = None
            for c in range(game.size):
                if game.grid[r][c] == 1:
                    queen_col = c
                elif empty_col is None:
                    empty_col = c
            if queen_col is not None and empty_col is not None:
                result = await game.validate_move(r + 1, empty_col + 1, 1)
                assert not result.success
                assert "row" in result.message.lower()
                return

    async def test_place_queen_conflict_diagonal(self):
        game = NQueensGame("medium", seed=42)
        await game.generate_puzzle()
        # Place a queen, then try to place on diagonal
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 1:
                    # Try diagonal position
                    dr, dc = r + 1, c + 1
                    if 0 <= dr < game.size and 0 <= dc < game.size and game.grid[dr][dc] == 0:
                        result = await game.validate_move(dr + 1, dc + 1, 1)
                        assert not result.success
                        assert "diagonal" in result.message.lower()
                        return

    async def test_cannot_remove_pre_placed(self):
        game = NQueensGame("easy", seed=42)
        await game.generate_puzzle()
        for r in range(game.size):
            for c in range(game.size):
                if game.initial_grid[r][c] == 1:
                    result = await game.validate_move(r + 1, c + 1, 0)
                    assert not result.success
                    return

    async def test_clear_placed_queen(self):
        game = NQueensGame("easy", seed=42)
        await game.generate_puzzle()
        # Place a queen then remove it
        for r in range(game.size):
            c = game._queen_cols[r]
            if game.grid[r][c] == 0:
                await game.validate_move(r + 1, c + 1, 1)
                result = await game.validate_move(r + 1, c + 1, 0)
                assert result.success
                assert game.grid[r][c] == 0
                return

    async def test_is_complete(self):
        game = NQueensGame("easy", seed=42)
        await game.generate_puzzle()
        assert not game.is_complete()
        # Fill solution
        game.grid = [row[:] for row in game.solution]
        assert game.is_complete()

    async def test_is_complete_validates_rules(self):
        """is_complete checks for conflicts, not just solution match."""
        game = NQueensGame("easy", seed=42)
        await game.generate_puzzle()
        n = game.size
        game.grid = [[0] * n for _ in range(n)]
        # Place queens with no conflicts (use solution)
        for r in range(n):
            game.grid[r][game._queen_cols[r]] = 1
        assert game.is_complete()

    async def test_get_hint(self):
        game = NQueensGame("easy", seed=42)
        await game.generate_puzzle()
        hint = await game.get_hint()
        assert hint is not None
        hint_data, hint_message = hint
        row, col, val = hint_data
        assert val == 1
        assert game.solution[row - 1][col - 1] == 1

    async def test_render_grid(self):
        game = NQueensGame("easy", seed=42)
        await game.generate_puzzle()
        rendered = game.render_grid()
        assert isinstance(rendered, str)
        assert "Q" in rendered or "Queens" in rendered

    async def test_get_rules(self):
        game = NQueensGame("easy")
        assert "queen" in game.get_rules().lower()

    async def test_get_commands(self):
        game = NQueensGame("easy")
        assert "place" in game.get_commands().lower()

    async def test_constraint_types(self):
        game = NQueensGame("easy")
        assert len(game.constraint_types) > 0

    async def test_business_analogies(self):
        game = NQueensGame("easy")
        assert len(game.business_analogies) > 0

    async def test_complexity_profile(self):
        game = NQueensGame("easy")
        profile = game.complexity_profile
        assert "reasoning_type" in profile

    async def test_deterministic_seeding(self):
        game1 = NQueensGame("easy", seed=12345)
        await game1.generate_puzzle()
        game2 = NQueensGame("easy", seed=12345)
        await game2.generate_puzzle()
        assert game1.grid == game2.grid
        assert game1.solution == game2.solution

    async def test_out_of_bounds(self):
        game = NQueensGame("easy", seed=42)
        await game.generate_puzzle()
        result = await game.validate_move(0, 1, 1)
        assert not result.success

    async def test_moves_counter(self):
        game = NQueensGame("easy", seed=42)
        await game.generate_puzzle()
        assert game.moves_made == 0
        for r in range(game.size):
            c = game._queen_cols[r]
            if game.grid[r][c] == 0:
                await game.validate_move(r + 1, c + 1, 1)
                assert game.moves_made == 1
                return
