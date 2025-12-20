"""Configuration for Logic Grid game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class LogicGridConfig(BaseModel):
    """Configuration for Logic Grid game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    num_people: int = Field(ge=3, le=5, description="Number of people")
    num_attributes: int = Field(ge=3, le=5, description="Number of attributes per category")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "LogicGridConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"num_people": 3, "num_attributes": 3},
            DifficultyLevel.MEDIUM: {"num_people": 4, "num_attributes": 4},
            DifficultyLevel.HARD: {"num_people": 5, "num_attributes": 5},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
