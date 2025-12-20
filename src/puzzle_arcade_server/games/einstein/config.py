"""Configuration for Einstein game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class EinsteinConfig(BaseModel):
    """Configuration for Einstein puzzle game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    num_clues: int = Field(ge=5, le=15, description="Number of clues provided")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "EinsteinConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"num_clues": 12},
            DifficultyLevel.MEDIUM: {"num_clues": 10},
            DifficultyLevel.HARD: {"num_clues": 8},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
