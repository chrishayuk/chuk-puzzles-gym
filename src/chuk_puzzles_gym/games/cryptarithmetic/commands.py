"""Command handler for Cryptarithmetic game."""

from typing import TYPE_CHECKING

from ...models import GameCommand, MoveResult
from .._base import CommandResult, GameCommandHandler

if TYPE_CHECKING:
    from .game import CryptarithmeticGame


class CryptarithmeticCommandHandler(GameCommandHandler):
    """Handles commands for Cryptarithmetic game."""

    game: "CryptarithmeticGame"

    @property
    def supported_commands(self) -> set[GameCommand]:
        """Return the set of GameCommand enums this handler supports."""
        return {GameCommand.ASSIGN, GameCommand.UNASSIGN}

    async def handle_command(self, cmd: GameCommand, args: list[str]) -> CommandResult:
        """Handle a Cryptarithmetic command.

        Args:
            cmd: The GameCommand enum value
            args: List of string arguments (already split from input)

        Returns:
            CommandResult with the move result and display flags
        """
        if cmd == GameCommand.ASSIGN:
            return await self._handle_assign(args)
        elif cmd == GameCommand.UNASSIGN:
            return await self._handle_unassign(args)
        else:
            return self.error_result(f"Unknown command: {cmd}")

    async def _handle_assign(self, args: list[str]) -> CommandResult:
        """Handle the ASSIGN command: assign <letter> <digit>."""
        if len(args) != 2:
            return CommandResult(
                result=MoveResult(success=False, message="Usage: assign <letter> <digit>"),
                should_display=False,
            )

        letter = args[0].upper()
        digit = self.parse_int(args[1], "digit")

        if digit is None:
            return self.error_result("Digit must be an integer (0-9).")

        result = await self.game.validate_move(letter, digit)

        return CommandResult(
            result=result,
            should_display=result.success,
            is_game_over=result.success and self.game.is_complete(),
        )

    async def _handle_unassign(self, args: list[str]) -> CommandResult:
        """Handle the UNASSIGN command: unassign <letter>."""
        if len(args) != 1:
            return CommandResult(
                result=MoveResult(success=False, message="Usage: unassign <letter>"),
                should_display=False,
            )

        letter = args[0].upper()
        result = await self.game.validate_move(letter, -1)

        return CommandResult(
            result=result,
            should_display=result.success,
        )
