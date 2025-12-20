"""Configuration for Sokoban game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class SokobanConfig(BaseModel):
    """Configuration for Sokoban game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=6, le=10, description="Grid size (NxN)")
    num_boxes: int = Field(ge=2, le=6, description="Number of boxes to push")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "SokobanConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 6, "num_boxes": 2},
            DifficultyLevel.MEDIUM: {"size": 8, "num_boxes": 3},
            DifficultyLevel.HARD: {"size": 10, "num_boxes": 4},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
