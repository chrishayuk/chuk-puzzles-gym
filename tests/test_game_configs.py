"""Tests for game configuration classes."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Import all config classes
from chuk_puzzles_gym.games.binary.config import BinaryConfig
from chuk_puzzles_gym.games.bridges.config import BridgesConfig
from chuk_puzzles_gym.games.cryptarithmetic.config import CryptarithmeticConfig
from chuk_puzzles_gym.games.einstein.config import EinsteinConfig
from chuk_puzzles_gym.games.fillomino.config import FillominoConfig
from chuk_puzzles_gym.games.graph_coloring.config import GraphColoringConfig
from chuk_puzzles_gym.games.hidato.config import HidatoConfig
from chuk_puzzles_gym.games.hitori.config import HitoriConfig
from chuk_puzzles_gym.games.nqueens.config import NQueensConfig
from chuk_puzzles_gym.games.numberlink.config import NumberlinkConfig
from chuk_puzzles_gym.games.rush_hour.config import RushHourConfig
from chuk_puzzles_gym.games.shikaku.config import ShikakuConfig
from chuk_puzzles_gym.games.skyscrapers.config import SkyscrapersConfig
from chuk_puzzles_gym.games.star_battle.config import StarBattleConfig
from chuk_puzzles_gym.models import DifficultyLevel


class TestBinaryConfig:
    """Tests for BinaryConfig."""

    def test_from_difficulty_easy(self):
        """Test creating config from easy difficulty."""
        config = BinaryConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.size == 6

    def test_from_difficulty_medium(self):
        """Test creating config from medium difficulty."""
        config = BinaryConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.size == 8

    def test_from_difficulty_hard(self):
        """Test creating config from hard difficulty."""
        config = BinaryConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.size == 10


class TestBridgesConfig:
    """Tests for BridgesConfig."""

    def test_from_difficulty_easy(self):
        """Test creating config from easy difficulty."""
        config = BridgesConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.size == 5
        assert config.num_islands == 5

    def test_from_difficulty_medium(self):
        """Test creating config from medium difficulty."""
        config = BridgesConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.size == 7
        assert config.num_islands == 8

    def test_from_difficulty_hard(self):
        """Test creating config from hard difficulty."""
        config = BridgesConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.size == 9
        assert config.num_islands == 12


class TestEinsteinConfig:
    """Tests for EinsteinConfig."""

    def test_from_difficulty_easy(self):
        """Test creating config from easy difficulty."""
        config = EinsteinConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.num_clues == 12

    def test_from_difficulty_medium(self):
        """Test creating config from medium difficulty."""
        config = EinsteinConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.num_clues == 10

    def test_from_difficulty_hard(self):
        """Test creating config from hard difficulty."""
        config = EinsteinConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.num_clues == 8


class TestFillominoConfig:
    """Tests for FillominoConfig."""

    def test_from_difficulty_easy(self):
        """Test creating config from easy difficulty."""
        config = FillominoConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.size == 6

    def test_from_difficulty_medium(self):
        """Test creating config from medium difficulty."""
        config = FillominoConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.size == 8

    def test_from_difficulty_hard(self):
        """Test creating config from hard difficulty."""
        config = FillominoConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.size == 10


class TestHidatoConfig:
    """Tests for HidatoConfig."""

    def test_from_difficulty_easy(self):
        """Test creating config from easy difficulty."""
        config = HidatoConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.size == 5

    def test_from_difficulty_medium(self):
        """Test creating config from medium difficulty."""
        config = HidatoConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.size == 7

    def test_from_difficulty_hard(self):
        """Test creating config from hard difficulty."""
        config = HidatoConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.size == 9


class TestHitoriConfig:
    """Tests for HitoriConfig."""

    def test_from_difficulty_easy(self):
        """Test creating config from easy difficulty."""
        config = HitoriConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.size == 4

    def test_from_difficulty_medium(self):
        """Test creating config from medium difficulty."""
        config = HitoriConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.size == 5

    def test_from_difficulty_hard(self):
        """Test creating config from hard difficulty."""
        config = HitoriConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.size == 6


class TestShikakuConfig:
    """Tests for ShikakuConfig."""

    def test_from_difficulty_easy(self):
        """Test creating config from easy difficulty."""
        config = ShikakuConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.size == 5
        assert config.num_clues == 5

    def test_from_difficulty_medium(self):
        """Test creating config from medium difficulty."""
        config = ShikakuConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.size == 7
        assert config.num_clues == 7

    def test_from_difficulty_hard(self):
        """Test creating config from hard difficulty."""
        config = ShikakuConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.size == 9
        assert config.num_clues == 10


class TestStarBattleConfig:
    """Tests for StarBattleConfig."""

    def test_from_difficulty_easy(self):
        """Test creating config from easy difficulty."""
        config = StarBattleConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.size == 6

    def test_from_difficulty_medium(self):
        """Test creating config from medium difficulty."""
        config = StarBattleConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.size == 8

    def test_from_difficulty_hard(self):
        """Test creating config from hard difficulty."""
        config = StarBattleConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.size == 10


class TestSkyscrapersConfig:
    """Tests for SkyscrapersConfig."""

    def test_from_difficulty_easy(self):
        config = SkyscrapersConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.size == 4

    def test_from_difficulty_medium(self):
        config = SkyscrapersConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.size == 5

    def test_from_difficulty_hard(self):
        config = SkyscrapersConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.size == 6


class TestNQueensConfig:
    """Tests for NQueensConfig."""

    def test_from_difficulty_easy(self):
        config = NQueensConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.size == 6
        assert config.pre_placed == 3

    def test_from_difficulty_medium(self):
        config = NQueensConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.size == 8
        assert config.pre_placed == 2

    def test_from_difficulty_hard(self):
        config = NQueensConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.size == 12
        assert config.pre_placed == 1


class TestNumberlinkConfig:
    """Tests for NumberlinkConfig."""

    def test_from_difficulty_easy(self):
        config = NumberlinkConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.size == 5
        assert config.num_pairs == 4

    def test_from_difficulty_medium(self):
        config = NumberlinkConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.size == 7
        assert config.num_pairs == 6

    def test_from_difficulty_hard(self):
        config = NumberlinkConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.size == 9
        assert config.num_pairs == 9


class TestGraphColoringConfig:
    """Tests for GraphColoringConfig."""

    def test_from_difficulty_easy(self):
        config = GraphColoringConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.num_nodes == 6
        assert config.num_colors == 3

    def test_from_difficulty_medium(self):
        config = GraphColoringConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.num_nodes == 10
        assert config.num_colors == 4

    def test_from_difficulty_hard(self):
        config = GraphColoringConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.num_nodes == 15
        assert config.num_colors == 4


class TestCryptarithmeticConfig:
    """Tests for CryptarithmeticConfig."""

    def test_from_difficulty_easy(self):
        config = CryptarithmeticConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.max_word_length == 3
        assert config.pre_assigned == 3

    def test_from_difficulty_medium(self):
        config = CryptarithmeticConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.max_word_length == 4
        assert config.pre_assigned == 2

    def test_from_difficulty_hard(self):
        config = CryptarithmeticConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.max_word_length == 5
        assert config.pre_assigned == 0


class TestRushHourConfig:
    """Tests for RushHourConfig."""

    def test_from_difficulty_easy(self):
        config = RushHourConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.size == 6
        assert config.num_vehicles == 4

    def test_from_difficulty_medium(self):
        config = RushHourConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.size == 6
        assert config.num_vehicles == 8

    def test_from_difficulty_hard(self):
        config = RushHourConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.size == 6
        assert config.num_vehicles == 12
