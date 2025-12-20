"""Configuration for Binary Puzzle game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class BinaryConfig(BaseModel):
    """Configuration for Binary Puzzle game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=4, le=14, description="Grid size (NxN, must be even)")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "BinaryConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 6},
            DifficultyLevel.MEDIUM: {"size": 8},
            DifficultyLevel.HARD: {"size": 10},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
