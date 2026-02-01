"""Command handler for Graph Coloring game."""

from typing import TYPE_CHECKING

from ...models import GameCommand, MoveResult
from .._base import CommandResult, GameCommandHandler
from .game import COLOR_NAMES

if TYPE_CHECKING:
    from .game import GraphColoringGame

# Build a lookup from lowercase color name to color number
_COLOR_NAME_TO_NUM = {name.lower(): i + 1 for i, name in enumerate(COLOR_NAMES)}


class GraphColoringCommandHandler(GameCommandHandler):
    """Handles commands for Graph Coloring game."""

    game: "GraphColoringGame"

    @property
    def supported_commands(self) -> set[GameCommand]:
        """Return the set of GameCommand enums this handler supports."""
        return {GameCommand.PLACE, GameCommand.CLEAR}

    async def handle_command(self, cmd: GameCommand, args: list[str]) -> CommandResult:
        """Handle a Graph Coloring command.

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

    def _parse_color(self, value: str) -> int | None:
        """Parse a color argument as either an integer or a color name."""
        # Try integer first
        try:
            return int(value)
        except ValueError:
            pass
        # Try color name lookup
        return _COLOR_NAME_TO_NUM.get(value.lower())

    async def _handle_place(self, args: list[str]) -> CommandResult:
        """Handle the PLACE command: place <node> <color>."""
        if len(args) != 2:
            return CommandResult(
                result=MoveResult(success=False, message="Usage: place <node> <color>"),
                should_display=False,
            )

        node = self.parse_int(args[0], "node")
        color = self._parse_color(args[1])

        if node is None:
            return self.error_result("Node must be an integer.")
        if color is None:
            valid = ", ".join(f"{i + 1}={COLOR_NAMES[i]}" for i in range(self.game.num_colors))
            return self.error_result(f"Invalid color. Use a number or name: {valid}")

        result = await self.game.validate_move(node, color)

        return CommandResult(
            result=result,
            should_display=result.success,
            is_game_over=result.success and self.game.is_complete(),
        )

    async def _handle_clear(self, args: list[str]) -> CommandResult:
        """Handle the CLEAR command: clear <node>."""
        if len(args) != 1:
            return CommandResult(
                result=MoveResult(success=False, message="Usage: clear <node>"),
                should_display=False,
            )

        node = self.parse_int(args[0], "node")

        if node is None:
            return self.error_result("Node must be an integer.")

        result = await self.game.validate_move(node, 0)

        return CommandResult(
            result=result,
            should_display=result.success,
        )
