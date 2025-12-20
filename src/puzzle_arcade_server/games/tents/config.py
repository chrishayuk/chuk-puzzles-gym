"""Configuration for Tents game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class TentsConfig(BaseModel):
    """Configuration for Tents and Trees game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=6, le=10, description="Grid size (NxN)")
    num_trees: int = Field(ge=4, description="Number of tree-tent pairs")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "TentsConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 6, "num_trees": 6},
            DifficultyLevel.MEDIUM: {"size": 8, "num_trees": 10},
            DifficultyLevel.HARD: {"size": 10, "num_trees": 15},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
