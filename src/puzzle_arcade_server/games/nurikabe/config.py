"""Configuration for Nurikabe game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class NurikabeConfig(BaseModel):
    """Configuration for Nurikabe game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=4, le=12, description="Grid size (NxN)")
    num_islands: int = Field(ge=1, description="Number of islands")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "NurikabeConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 6, "num_islands": 3},
            DifficultyLevel.MEDIUM: {"size": 8, "num_islands": 4},
            DifficultyLevel.HARD: {"size": 10, "num_islands": 5},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
