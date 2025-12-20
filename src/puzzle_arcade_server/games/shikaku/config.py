"""Configuration for Shikaku game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class ShikakuConfig(BaseModel):
    """Configuration for Shikaku game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=5, le=10, description="Grid size (NxN)")
    num_clues: int = Field(ge=3, description="Number of clue numbers")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "ShikakuConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 5, "num_clues": 5},
            DifficultyLevel.MEDIUM: {"size": 7, "num_clues": 7},
            DifficultyLevel.HARD: {"size": 9, "num_clues": 10},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
