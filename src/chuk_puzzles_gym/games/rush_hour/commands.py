"""Command handler for Rush Hour game."""

from typing import TYPE_CHECKING

from ...models import GameCommand, MoveResult
from .._base import CommandResult, GameCommandHandler

if TYPE_CHECKING:
    from .game import RushHourGame


class RushHourCommandHandler(GameCommandHandler):
    """Handles commands for Rush Hour game."""

    game: "RushHourGame"

    @property
    def supported_commands(self) -> set[GameCommand]:
        """Return the set of GameCommand enums this handler supports."""
        return {GameCommand.MOVE}

    async def handle_command(self, cmd: GameCommand, args: list[str]) -> CommandResult:
        """Handle a Rush Hour command.

        Args:
            cmd: The GameCommand enum value
            args: List of string arguments (already split from input)

        Returns:
            CommandResult with the move result and display flags
        """
        if cmd == GameCommand.MOVE:
            return await self._handle_move(args)
        else:
            return self.error_result(f"Unknown command: {cmd}")

    async def _handle_move(self, args: list[str]) -> CommandResult:
        """Handle the MOVE command: move <vehicle> <direction>."""
        if len(args) != 2:
            return CommandResult(
                result=MoveResult(
                    success=False,
                    message="Usage: move <vehicle> <direction>\nDirections: left, right, up, down",
                ),
                should_display=False,
            )

        vehicle_id = args[0].upper()
        direction = args[1].lower()

        result = await self.game.validate_move(vehicle_id, direction)

        return CommandResult(
            result=result,
            should_display=result.success,
            is_game_over=result.game_over,
        )
