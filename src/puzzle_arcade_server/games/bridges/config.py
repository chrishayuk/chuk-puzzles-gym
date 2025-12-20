"""Configuration for Bridges game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class BridgesConfig(BaseModel):
    """Configuration for Bridges game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=5, le=10, description="Grid size (NxN)")
    num_islands: int = Field(ge=4, description="Number of islands")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "BridgesConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 5, "num_islands": 5},
            DifficultyLevel.MEDIUM: {"size": 7, "num_islands": 8},
            DifficultyLevel.HARD: {"size": 9, "num_islands": 12},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
