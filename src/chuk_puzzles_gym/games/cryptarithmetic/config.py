"""Configuration for Cryptarithmetic puzzle game."""

from pydantic import BaseModel, Field

from ...models import DifficultyLevel


class CryptarithmeticConfig(BaseModel):
    """Configuration for a Cryptarithmetic puzzle."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY)
    max_word_length: int = Field(ge=2, le=6, description="Maximum word length")
    pre_assigned: int = Field(ge=0, description="Number of pre-assigned letter-digit pairs")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "CryptarithmeticConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"max_word_length": 3, "pre_assigned": 3},
            DifficultyLevel.MEDIUM: {"max_word_length": 4, "pre_assigned": 2},
            DifficultyLevel.HARD: {"max_word_length": 5, "pre_assigned": 0},
        }
        return cls(difficulty=difficulty, **config_map[difficulty])
