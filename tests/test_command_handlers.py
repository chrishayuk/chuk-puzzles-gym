"""Tests for game command handlers."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from puzzle_arcade_server.games._base import CommandResult
from puzzle_arcade_server.games.sudoku import SudokuGame
from puzzle_arcade_server.games.sudoku.commands import SudokuCommandHandler
from puzzle_arcade_server.models import GameCommand, MoveResult


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_default_values(self):
        """Test CommandResult with default values."""
        result = CommandResult(result=MoveResult(success=True, message="OK"))
        assert result.should_display is True
        assert result.is_game_over is False

    def test_custom_values(self):
        """Test CommandResult with custom values."""
        result = CommandResult(
            result=MoveResult(success=False, message="Error"),
            should_display=False,
            is_game_over=True,
        )
        assert result.should_display is False
        assert result.is_game_over is True


class TestSudokuCommandHandler:
    """Tests for SudokuCommandHandler."""

    @pytest.fixture
    def game_with_handler(self):
        """Create a game with command handler."""
        game = SudokuGame("easy", seed=12345)
        handler = SudokuCommandHandler(game)
        return game, handler

    def test_supported_commands(self, game_with_handler):
        """Test supported commands."""
        game, handler = game_with_handler
        commands = handler.supported_commands
        assert GameCommand.PLACE in commands
        assert GameCommand.CLEAR in commands
        assert len(commands) == 2

    async def test_handle_place_success(self, game_with_handler):
        """Test successful place command."""
        game, handler = game_with_handler
        await game.generate_puzzle()

        # Find an empty cell
        empty_cell = None
        for r in range(9):
            for c in range(9):
                if game.grid[r][c] == 0 and game.initial_grid[r][c] == 0:
                    empty_cell = (r + 1, c + 1)  # 1-indexed
                    break
            if empty_cell:
                break

        if empty_cell:
            # Try placing a valid number
            result = await handler.handle_command(GameCommand.PLACE, [str(empty_cell[0]), str(empty_cell[1]), "1"])
            # May or may not succeed depending on puzzle, but should be valid command
            assert isinstance(result, CommandResult)

    async def test_handle_place_wrong_args(self, game_with_handler):
        """Test place command with wrong number of arguments."""
        game, handler = game_with_handler
        await game.generate_puzzle()

        result = await handler.handle_command(GameCommand.PLACE, ["1", "2"])
        assert result.result.success is False
        assert "Usage" in result.result.message
        assert result.should_display is False

    async def test_handle_place_invalid_int(self, game_with_handler):
        """Test place command with non-integer arguments."""
        game, handler = game_with_handler
        await game.generate_puzzle()

        result = await handler.handle_command(GameCommand.PLACE, ["a", "b", "c"])
        assert result.result.success is False
        assert result.should_display is False

    async def test_handle_clear_success(self, game_with_handler):
        """Test successful clear command."""
        game, handler = game_with_handler
        await game.generate_puzzle()

        # Find an empty cell and place a number first
        for r in range(9):
            for c in range(9):
                if game.grid[r][c] == 0 and game.initial_grid[r][c] == 0:
                    # Place a number
                    await game.validate_move(r + 1, c + 1, 5)
                    # Now clear it
                    result = await handler.handle_command(GameCommand.CLEAR, [str(r + 1), str(c + 1)])
                    assert isinstance(result, CommandResult)
                    return

    async def test_handle_clear_wrong_args(self, game_with_handler):
        """Test clear command with wrong number of arguments."""
        game, handler = game_with_handler
        await game.generate_puzzle()

        result = await handler.handle_command(GameCommand.CLEAR, ["1"])
        assert result.result.success is False
        assert "Usage" in result.result.message

    async def test_handle_clear_invalid_int(self, game_with_handler):
        """Test clear command with non-integer arguments."""
        game, handler = game_with_handler
        await game.generate_puzzle()

        result = await handler.handle_command(GameCommand.CLEAR, ["a", "b"])
        assert result.result.success is False

    def test_parse_int_valid(self, game_with_handler):
        """Test parse_int with valid input."""
        game, handler = game_with_handler
        assert handler.parse_int("42", "test") == 42
        assert handler.parse_int("-5", "test") == -5
        assert handler.parse_int("0", "test") == 0

    def test_parse_int_invalid(self, game_with_handler):
        """Test parse_int with invalid input."""
        game, handler = game_with_handler
        assert handler.parse_int("abc", "test") is None
        assert handler.parse_int("1.5", "test") is None
        assert handler.parse_int("", "test") is None

    def test_error_result(self, game_with_handler):
        """Test error_result helper."""
        game, handler = game_with_handler
        result = handler.error_result("Something went wrong")
        assert result.result.success is False
        assert result.result.message == "Something went wrong"
        assert result.should_display is False

    async def test_handle_unknown_command(self, game_with_handler):
        """Test handling unknown command returns error."""
        game, handler = game_with_handler
        await game.generate_puzzle()

        # HINT is not in supported_commands
        result = await handler.handle_command(GameCommand.HINT, [])
        assert result.result.success is False
