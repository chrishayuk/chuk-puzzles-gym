"""Configuration for Fillomino game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class FillominoConfig(BaseModel):
    """Configuration for Fillomino game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=6, le=10, description="Grid size (NxN)")
    num_clues: int = Field(ge=4, description="Number of clue numbers to reveal")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "FillominoConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 6, "num_clues": 8},
            DifficultyLevel.MEDIUM: {"size": 8, "num_clues": 10},
            DifficultyLevel.HARD: {"size": 10, "num_clues": 12},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
