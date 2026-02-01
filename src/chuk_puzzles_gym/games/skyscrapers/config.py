"""Configuration for Skyscrapers puzzle game."""

from pydantic import BaseModel, Field

from ...models import DifficultyLevel


class SkyscrapersConfig(BaseModel):
    """Configuration for a Skyscrapers puzzle."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY)
    size: int = Field(ge=4, le=9, description="Grid size (NxN)")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "SkyscrapersConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 4},
            DifficultyLevel.MEDIUM: {"size": 5},
            DifficultyLevel.HARD: {"size": 6},
        }
        return cls(difficulty=difficulty, **config_map[difficulty])
