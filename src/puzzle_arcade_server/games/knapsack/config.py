"""Configuration for Knapsack game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class KnapsackConfig(BaseModel):
    """Configuration for Knapsack game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    num_items: int = Field(ge=1, le=20, description="Number of items")
    max_weight: int = Field(ge=1, description="Maximum knapsack capacity")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "KnapsackConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"num_items": 5, "max_weight": 20},
            DifficultyLevel.MEDIUM: {"num_items": 8, "max_weight": 35},
            DifficultyLevel.HARD: {"num_items": 12, "max_weight": 50},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
