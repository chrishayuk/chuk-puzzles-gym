"""Abstract base class for game command handlers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...models import GameCommand, MoveResult

if TYPE_CHECKING:
    from .game import PuzzleGame


@dataclass
class CommandResult:
    """Result of executing a game command."""

    result: MoveResult
    should_display: bool = True
    is_game_over: bool = False


class GameCommandHandler(ABC):
    """Abstract base class for handling game-specific commands.

    Each game implements its own command handler that knows how to:
    - Parse command arguments
    - Validate and execute moves
    - Return appropriate results

    This decouples game logic from server routing.
    """

    def __init__(self, game: "PuzzleGame"):
        """Initialize with the game instance.

        Args:
            game: The puzzle game instance to handle commands for
        """
        self.game = game

    @property
    @abstractmethod
    def supported_commands(self) -> set[GameCommand]:
        """Return the set of GameCommand enums this handler supports.

        Returns:
            Set of GameCommand values this game responds to
        """
        pass

    @abstractmethod
    async def handle_command(self, cmd: GameCommand, args: list[str]) -> CommandResult:
        """Handle a game-specific command.

        Args:
            cmd: The GameCommand enum value
            args: List of string arguments (already split from input)

        Returns:
            CommandResult with the move result and display flags
        """
        pass

    def parse_int(self, value: str, name: str) -> int | None:
        """Helper to parse an integer argument.

        Args:
            value: String value to parse
            name: Name of the argument (for error messages)

        Returns:
            Parsed integer or None if invalid
        """
        try:
            return int(value)
        except ValueError:
            return None

    def error_result(self, message: str) -> CommandResult:
        """Create an error CommandResult.

        Args:
            message: Error message to display

        Returns:
            CommandResult with failed MoveResult
        """
        return CommandResult(
            result=MoveResult(success=False, message=message),
            should_display=False,
        )
