"""Configuration for Nonogram game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class NonogramConfig(BaseModel):
    """Configuration for Nonogram game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=5, le=10, description="Grid size (NxN)")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "NonogramConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 5},
            DifficultyLevel.MEDIUM: {"size": 7},
            DifficultyLevel.HARD: {"size": 10},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
