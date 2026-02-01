"""Tests for Rush Hour puzzle game."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.rush_hour import RushHourCommandHandler, RushHourGame
from chuk_puzzles_gym.games.rush_hour.models import Vehicle
from chuk_puzzles_gym.models import GameCommand


class TestRushHourGame:
    """Test suite for RushHourGame."""

    async def test_initialization(self):
        game = RushHourGame("easy")
        assert game.size == 6
        assert game.name == "Rush Hour"

    @pytest.mark.parametrize(
        "difficulty,expected_vehicles",
        [("easy", 4), ("medium", 8), ("hard", 12)],
    )
    async def test_difficulty_levels(self, difficulty, expected_vehicles):
        game = RushHourGame(difficulty, seed=42)
        await game.generate_puzzle()
        assert game.config.num_vehicles == expected_vehicles

    async def test_generate_puzzle(self):
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        assert game.game_started
        assert "X" in game.vehicles
        # Target car should be horizontal on exit row
        target = game.vehicles["X"]
        assert target.orientation == "h"
        assert target.row == game.exit_row

    async def test_puzzle_solvable(self):
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        assert game.min_solution_moves is not None
        assert game.min_solution_moves > 0

    async def test_move_horizontal_right(self):
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        # Find any horizontal vehicle that can move right
        for vid, v in game.vehicles.items():
            if v.orientation == "h" and v.col + v.length < game.size:
                # Check if path is clear
                clear = True
                for _i in range(v.length):
                    if game.grid[v.row][v.col + v.length] != ".":
                        clear = False
                        break
                if clear:
                    result = await game.validate_move(vid, "right")
                    assert result.success
                    assert game.vehicles[vid].col == v.col + 1
                    return

    async def test_move_wrong_direction(self):
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        # Horizontal vehicle can't move up/down
        target = game.vehicles["X"]
        assert target.orientation == "h"
        result = await game.validate_move("X", "up")
        assert not result.success

    async def test_move_invalid_vehicle(self):
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        result = await game.validate_move("Z", "left")
        assert not result.success

    async def test_move_blocked(self):
        """Vehicle cannot pass through another vehicle."""
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        # Try moving target car into a blocker
        target = game.vehicles["X"]
        # Check if blocked to the right
        if target.col + target.length < game.size:
            blocker = game.grid[target.row][target.col + target.length]
            if blocker != ".":
                result = await game.validate_move("X", "right")
                assert not result.success
                assert "blocked" in result.message.lower() or blocker in result.message

    async def test_move_wall(self):
        """Vehicle cannot move outside the board."""
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        # Find a vehicle at a wall
        for vid, v in game.vehicles.items():
            if v.orientation == "h" and v.col == 0:
                result = await game.validate_move(vid, "left")
                assert not result.success
                return

    async def test_is_complete(self):
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        assert not game.is_complete()
        # Move target car to exit
        target = game.vehicles["X"]
        game.vehicles["X"] = Vehicle(
            id="X", row=target.row, col=game.size - target.length, length=target.length, orientation="h"
        )
        game.grid = game._build_grid()
        assert game.is_complete()

    async def test_get_hint(self):
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        hint = await game.get_hint()
        # Hint might be None if BFS can't find solution from current state
        # But for a freshly generated solvable puzzle, it should work
        if hint is not None:
            hint_data, hint_message = hint
            vid, direction = hint_data
            assert vid in game.vehicles
            assert direction in ("left", "right", "up", "down")

    async def test_render_grid(self):
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        rendered = game.render_grid()
        assert isinstance(rendered, str)
        assert "X" in rendered
        assert ">" in rendered  # Exit marker

    async def test_get_rules(self):
        game = RushHourGame("easy")
        assert "vehicle" in game.get_rules().lower() or "slide" in game.get_rules().lower()

    async def test_get_commands(self):
        game = RushHourGame("easy")
        assert "move" in game.get_commands().lower()

    async def test_get_stats(self):
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        assert "Seed" in game.get_stats()

    async def test_constraint_types(self):
        game = RushHourGame("easy")
        assert "sequential_planning" in game.constraint_types

    async def test_business_analogies(self):
        game = RushHourGame("easy")
        assert len(game.business_analogies) > 0

    async def test_complexity_profile(self):
        game = RushHourGame("easy")
        profile = game.complexity_profile
        assert "reasoning_type" in profile

    async def test_deterministic_seeding(self):
        game1 = RushHourGame("easy", seed=12345)
        await game1.generate_puzzle()
        game2 = RushHourGame("easy", seed=12345)
        await game2.generate_puzzle()
        assert game1.grid == game2.grid

    async def test_moves_counter(self):
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        assert game.moves_made == 0
        # Try to make a valid move
        for vid, v in game.vehicles.items():
            if v.orientation == "h":
                if v.col + v.length < game.size and game.grid[v.row][v.col + v.length] == ".":
                    await game.validate_move(vid, "right")
                    assert game.moves_made == 1
                    return
                if v.col > 0 and game.grid[v.row][v.col - 1] == ".":
                    await game.validate_move(vid, "left")
                    assert game.moves_made == 1
                    return
            else:
                if v.row + v.length < game.size and game.grid[v.row + v.length][v.col] == ".":
                    await game.validate_move(vid, "down")
                    assert game.moves_made == 1
                    return
                if v.row > 0 and game.grid[v.row - 1][v.col] == ".":
                    await game.validate_move(vid, "up")
                    assert game.moves_made == 1
                    return

    async def test_vehicle_model(self):
        v = Vehicle(id="X", row=2, col=0, length=2, orientation="h")
        assert v.id == "X"
        assert v.row == 2
        assert v.col == 0
        assert v.length == 2
        assert v.orientation == "h"

    async def test_command_handler_move(self):
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        handler = RushHourCommandHandler(game)
        assert GameCommand.MOVE in handler.supported_commands
        # Try a move via handler
        for vid, v in game.vehicles.items():
            if v.orientation == "h" and v.col + v.length < game.size:
                if game.grid[v.row][v.col + v.length] == ".":
                    result = await handler.handle_command(GameCommand.MOVE, [vid, "right"])
                    assert result.result.success
                    return

    async def test_command_handler_bad_args(self):
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        handler = RushHourCommandHandler(game)
        result = await handler.handle_command(GameCommand.MOVE, ["X"])
        assert not result.result.success

    async def test_win_sets_game_over(self):
        """Winning move should set game_over flag in MoveResult."""
        game = RushHourGame("easy", seed=42)
        await game.generate_puzzle()
        # Clear path and move X to exit
        # Manually set up winning condition: X one step from exit
        # Remove all vehicles except X
        game.vehicles = {"X": Vehicle(id="X", row=game.exit_row, col=game.size - 3, length=2, orientation="h")}
        game.grid = game._build_grid()
        result = await game.validate_move("X", "right")
        assert result.success
        assert result.game_over
        assert game.is_complete()
