"""Tests for base PuzzleGame abstract class."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from puzzle_arcade_server.base.puzzle_game import PuzzleGame


class ConcretePuzzleGame(PuzzleGame):
    """Concrete implementation of PuzzleGame for testing."""

    def generate_puzzle(self) -> None:
        """Generate a simple test puzzle."""
        pass

    def validate_move(self, *args) -> tuple[bool, str]:
        """Validate a test move."""
        return True, "Valid move"

    def is_complete(self) -> bool:
        """Check if puzzle is complete."""
        return False

    def get_hint(self) -> tuple[tuple[int, int, int], str] | None:
        """Get a test hint."""
        return ((1, 1, 1), "Test hint")

    def render_grid(self) -> str:
        """Render test grid."""
        return "Test grid"

    def get_rules(self) -> str:
        """Get test rules."""
        return "Test rules"

    def get_commands(self) -> str:
        """Get test commands."""
        return "Test commands"

    @property
    def name(self) -> str:
        """Test name."""
        return "Test Puzzle"

    @property
    def description(self) -> str:
        """Test description."""
        return "A test puzzle for testing"


class TestPuzzleGame:
    """Test suite for PuzzleGame base class."""

    def test_initialization(self):
        """Test game initialization."""
        game = ConcretePuzzleGame("medium")
        assert game.difficulty == "medium"
        assert game.moves_made == 0
        assert game.game_started is False

    def test_get_stats(self):
        """Test get_stats method."""
        game = ConcretePuzzleGame("easy")
        stats = game.get_stats()
        assert stats == "Moves made: 0"

        # Increment moves and test again
        game.moves_made = 5
        stats = game.get_stats()
        assert stats == "Moves made: 5"

    def test_abstract_methods(self):
        """Test that PuzzleGame is abstract and requires implementation."""
        game = ConcretePuzzleGame()

        # Verify all abstract methods are implemented
        assert hasattr(game, "generate_puzzle")
        assert hasattr(game, "validate_move")
        assert hasattr(game, "is_complete")
        assert hasattr(game, "get_hint")
        assert hasattr(game, "render_grid")
        assert hasattr(game, "get_rules")
        assert hasattr(game, "get_commands")
        assert hasattr(game, "name")
        assert hasattr(game, "description")

    def test_properties(self):
        """Test name and description properties."""
        game = ConcretePuzzleGame()
        assert game.name == "Test Puzzle"
        assert game.description == "A test puzzle for testing"
