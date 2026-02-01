"""Configuration for Rush Hour puzzle game."""

from pydantic import BaseModel, Field

from ...models import DifficultyLevel


class RushHourConfig(BaseModel):
    """Configuration for a Rush Hour puzzle."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY)
    size: int = Field(default=6, ge=6, le=8, description="Board size")
    num_vehicles: int = Field(ge=2, le=15, description="Number of blocking vehicles")
    min_moves: int = Field(ge=1, description="Minimum solution moves for difficulty")
    max_moves: int = Field(ge=1, description="Maximum solution moves for difficulty")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "RushHourConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 6, "num_vehicles": 4, "min_moves": 3, "max_moves": 12},
            DifficultyLevel.MEDIUM: {"size": 6, "num_vehicles": 8, "min_moves": 8, "max_moves": 25},
            DifficultyLevel.HARD: {"size": 6, "num_vehicles": 12, "min_moves": 15, "max_moves": 50},
        }
        return cls(difficulty=difficulty, **config_map[difficulty])
