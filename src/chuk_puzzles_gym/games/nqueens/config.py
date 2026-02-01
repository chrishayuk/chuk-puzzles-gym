"""Configuration for N-Queens puzzle game."""

from pydantic import BaseModel, Field

from ...models import DifficultyLevel


class NQueensConfig(BaseModel):
    """Configuration for an N-Queens puzzle."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY)
    size: int = Field(ge=4, le=20, description="Board size (N)")
    pre_placed: int = Field(ge=0, description="Number of pre-placed queens as hints")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "NQueensConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 6, "pre_placed": 3},
            DifficultyLevel.MEDIUM: {"size": 8, "pre_placed": 2},
            DifficultyLevel.HARD: {"size": 12, "pre_placed": 1},
        }
        return cls(difficulty=difficulty, **config_map[difficulty])
