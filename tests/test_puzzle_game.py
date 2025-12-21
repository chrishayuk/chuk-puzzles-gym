"""Tests for base PuzzleGame abstract class."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from puzzle_arcade_server.games._base import PuzzleGame


class ConcretePuzzleGame(PuzzleGame):
    """Concrete implementation of PuzzleGame for testing."""

    async def generate_puzzle(self) -> None:
        """Generate a simple test puzzle."""
        pass

    async def validate_move(self, *args):
        """Validate a test move."""
        from puzzle_arcade_server.models import MoveResult

        return MoveResult(success=True, message="Valid move")

    def is_complete(self) -> bool:
        """Check if puzzle is complete."""
        return False

    async def get_hint(self) -> tuple[tuple[int, int, int], str] | None:
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

    async def test_initialization(self):
        """Test game initialization."""
        from puzzle_arcade_server.models import DifficultyLevel

        game = ConcretePuzzleGame("medium")
        assert game.difficulty == DifficultyLevel.MEDIUM
        assert game.moves_made == 0
        assert game.game_started is False
        assert game.seed is not None
        assert game._rng is not None

    async def test_deterministic_seed(self):
        """Test that the same seed produces the same RNG state."""
        game1 = ConcretePuzzleGame("easy", seed=12345)
        game2 = ConcretePuzzleGame("easy", seed=12345)

        # Same seed should produce same random values
        assert game1._rng.randint(0, 100) == game2._rng.randint(0, 100)
        assert game1._rng.random() == game2._rng.random()

    async def test_get_stats(self):
        """Test get_stats method."""
        game = ConcretePuzzleGame("easy", seed=42)
        stats = game.get_stats()
        assert "Moves: 0" in stats
        assert "Seed: 42" in stats

        # Increment moves and test again
        game.moves_made = 5
        stats = game.get_stats()
        assert "Moves: 5" in stats
        assert "Seed: 42" in stats

        # Test with invalid moves and hints
        game.invalid_moves = 2
        game.hints_used = 3
        stats = game.get_stats()
        assert "Moves: 5" in stats
        assert "Invalid: 2" in stats
        assert "Hints: 3" in stats
        assert "Seed: 42" in stats

    async def test_abstract_methods(self):
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

    async def test_properties(self):
        """Test name and description properties."""
        game = ConcretePuzzleGame()
        assert game.name == "Test Puzzle"
        assert game.description == "A test puzzle for testing"

    async def test_constraint_types(self):
        """Test default constraint_types property."""
        game = ConcretePuzzleGame()
        assert game.constraint_types == []

    async def test_business_analogies(self):
        """Test default business_analogies property."""
        game = ConcretePuzzleGame()
        assert game.business_analogies == []

    async def test_complexity_profile(self):
        """Test default complexity_profile property."""
        game = ConcretePuzzleGame()
        profile = game.complexity_profile
        assert profile["reasoning_type"] == "deductive"
        assert profile["search_space"] == "medium"
        assert profile["constraint_density"] == "moderate"

    async def test_complexity_metrics(self):
        """Test default complexity_metrics property."""
        game = ConcretePuzzleGame()
        metrics = game.complexity_metrics
        assert metrics["variable_count"] == 0
        assert metrics["constraint_count"] == 0
        assert metrics["domain_size"] == 0
        assert metrics["branching_factor"] == 0.0
        assert metrics["empty_cells"] == 0

    async def test_difficulty_enum(self):
        """Test initialization with DifficultyLevel enum."""
        from puzzle_arcade_server.models import DifficultyLevel

        game = ConcretePuzzleGame(DifficultyLevel.HARD)
        assert game.difficulty == DifficultyLevel.HARD
