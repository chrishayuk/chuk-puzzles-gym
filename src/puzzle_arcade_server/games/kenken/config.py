"""Configuration for KenKen game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class KenKenConfig(BaseModel):
    """Configuration for KenKen game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=3, le=9, description="Grid size (NxN)")
    num_cages: int = Field(ge=1, description="Number of cages")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "KenKenConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 4, "num_cages": 8},
            DifficultyLevel.MEDIUM: {"size": 5, "num_cages": 12},
            DifficultyLevel.HARD: {"size": 6, "num_cages": 18},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
