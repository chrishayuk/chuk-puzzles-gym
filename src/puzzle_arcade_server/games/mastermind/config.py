"""Configuration for Mastermind game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class MastermindConfig(BaseModel):
    """Configuration for Mastermind game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    code_length: int = Field(ge=3, le=6, description="Length of the secret code")
    num_colors: int = Field(ge=4, le=8, description="Number of available colors")
    max_guesses: int = Field(ge=8, le=15, description="Maximum number of guesses allowed")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "MastermindConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"code_length": 4, "num_colors": 6, "max_guesses": 12},
            DifficultyLevel.MEDIUM: {"code_length": 5, "num_colors": 7, "max_guesses": 12},
            DifficultyLevel.HARD: {"code_length": 6, "num_colors": 8, "max_guesses": 15},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
