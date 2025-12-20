"""Configuration for Killer Sudoku game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class KillerSudokuConfig(BaseModel):
    """Configuration for Killer Sudoku game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    num_cages: int = Field(ge=15, le=35, description="Number of cages")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "KillerSudokuConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"num_cages": 20},
            DifficultyLevel.MEDIUM: {"num_cages": 25},
            DifficultyLevel.HARD: {"num_cages": 30},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
