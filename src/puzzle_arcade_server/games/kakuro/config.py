"""Configuration for Kakuro game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class KakuroConfig(BaseModel):
    """Configuration for Kakuro game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=4, le=10, description="Grid size")
    num_runs: int = Field(ge=1, description="Number of runs (horizontal + vertical)")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "KakuroConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 4, "num_runs": 6},
            DifficultyLevel.MEDIUM: {"size": 6, "num_runs": 10},
            DifficultyLevel.HARD: {"size": 8, "num_runs": 16},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
