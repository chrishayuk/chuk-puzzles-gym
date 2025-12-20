"""Configuration for Star Battle game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class StarBattleConfig(BaseModel):
    """Configuration for Star Battle game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=6, le=10, description="Grid size (NxN)")
    stars_per_row: int = Field(ge=1, le=2, description="Number of stars per row/column/region")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "StarBattleConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 6, "stars_per_row": 1},
            DifficultyLevel.MEDIUM: {"size": 8, "stars_per_row": 2},
            DifficultyLevel.HARD: {"size": 10, "stars_per_row": 2},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
