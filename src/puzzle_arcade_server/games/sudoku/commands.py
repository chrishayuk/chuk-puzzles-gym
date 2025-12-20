"""Command handler for Sudoku game."""

from typing import TYPE_CHECKING

from ...models import GameCommand, MoveResult
from .._base import CommandResult, GameCommandHandler

if TYPE_CHECKING:
    from .game import SudokuGame


class SudokuCommandHandler(GameCommandHandler):
    """Handles commands for Sudoku game."""

    game: "SudokuGame"

    @property
    def supported_commands(self) -> set[GameCommand]:
        """Return the set of GameCommand enums this handler supports."""
        return {GameCommand.PLACE, GameCommand.CLEAR}

    async def handle_command(self, cmd: GameCommand, args: list[str]) -> CommandResult:
        """Handle a Sudoku-specific command.

        Args:
            cmd: The GameCommand enum value
            args: List of string arguments (already split from input)

        Returns:
            CommandResult with the move result and display flags
        """
        if cmd == GameCommand.PLACE:
            return await self._handle_place(args)
        elif cmd == GameCommand.CLEAR:
            return await self._handle_clear(args)
        else:
            return self.error_result(f"Unknown command: {cmd}")

    async def _handle_place(self, args: list[str]) -> CommandResult:
        """Handle the PLACE command.

        Args:
            args: [row, col, num] - all as strings

        Returns:
            CommandResult with move result
        """
        if len(args) != 3:
            return CommandResult(
                result=MoveResult(success=False, message="Usage: place <row> <col> <num>\nExample: place 1 5 7"),
                should_display=False,
            )

        row = self.parse_int(args[0], "row")
        col = self.parse_int(args[1], "col")
        num = self.parse_int(args[2], "num")

        if row is None or col is None or num is None:
            return self.error_result("Row, column, and number must be integers.")

        result = await self.game.validate_move(row, col, num)

        return CommandResult(
            result=result,
            should_display=result.success,
            is_game_over=result.success and self.game.is_complete(),
        )

    async def _handle_clear(self, args: list[str]) -> CommandResult:
        """Handle the CLEAR command.

        Args:
            args: [row, col] - as strings

        Returns:
            CommandResult with move result
        """
        if len(args) != 2:
            return CommandResult(
                result=MoveResult(success=False, message="Usage: clear <row> <col>"),
                should_display=False,
            )

        row = self.parse_int(args[0], "row")
        col = self.parse_int(args[1], "col")

        if row is None or col is None:
            return self.error_result("Row and column must be integers.")

        # Clear is just a validate_move with num=0
        result = await self.game.validate_move(row, col, 0)

        return CommandResult(
            result=result,
            should_display=result.success,
        )
