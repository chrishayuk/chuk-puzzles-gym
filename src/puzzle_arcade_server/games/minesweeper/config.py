"""Configuration for Minesweeper game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class MinesweeperConfig(BaseModel):
    """Configuration for Minesweeper game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    size: int = Field(ge=4, le=20, description="Grid size (NxN)")
    mines: int = Field(ge=1, description="Number of mines")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "MinesweeperConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 6, "mines": 6},
            DifficultyLevel.MEDIUM: {"size": 8, "mines": 12},
            DifficultyLevel.HARD: {"size": 10, "mines": 20},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
