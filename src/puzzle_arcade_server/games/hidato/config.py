"""Configuration for Hidato game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class HidatoConfig(BaseModel):
    """Configuration for Hidato game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=5, le=9, description="Grid size (NxN)")
    num_clues: int = Field(ge=2, description="Number of clue numbers to reveal")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "HidatoConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 5, "num_clues": 8},
            DifficultyLevel.MEDIUM: {"size": 7, "num_clues": 12},
            DifficultyLevel.HARD: {"size": 9, "num_clues": 15},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
