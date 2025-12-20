"""Configuration for Lights Out game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class LightsOutConfig(BaseModel):
    """Configuration for Lights Out game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=3, le=10, description="Grid size (NxN)")
    num_presses: int = Field(ge=1, description="Number of initial presses to create puzzle")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "LightsOutConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 5, "num_presses": 3},
            DifficultyLevel.MEDIUM: {"size": 6, "num_presses": 5},
            DifficultyLevel.HARD: {"size": 7, "num_presses": 7},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
