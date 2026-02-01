"""Configuration for Numberlink puzzle game."""

from pydantic import BaseModel, Field

from ...models import DifficultyLevel


class NumberlinkConfig(BaseModel):
    """Configuration for a Numberlink puzzle."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY)
    size: int = Field(ge=4, le=12, description="Grid size (NxN)")
    num_pairs: int = Field(ge=2, le=15, description="Number of endpoint pairs")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "NumberlinkConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 5, "num_pairs": 4},
            DifficultyLevel.MEDIUM: {"size": 7, "num_pairs": 6},
            DifficultyLevel.HARD: {"size": 9, "num_pairs": 9},
        }
        return cls(difficulty=difficulty, **config_map[difficulty])
