"""Configuration for Futoshiki game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class FutoshikiConfig(BaseModel):
    """Configuration for Futoshiki game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=4, le=9, description="Grid size (NxN)")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "FutoshikiConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 4},
            DifficultyLevel.MEDIUM: {"size": 5},
            DifficultyLevel.HARD: {"size": 6},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
