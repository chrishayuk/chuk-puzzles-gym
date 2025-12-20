"""Configuration for Sudoku game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class SudokuConfig(BaseModel):
    """Configuration for Sudoku game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    cells_to_remove: int = Field(ge=0, le=64, description="Number of cells to remove from solution")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "SudokuConfig":
        """Create config from difficulty level."""
        cells_map = {
            DifficultyLevel.EASY: 35,
            DifficultyLevel.MEDIUM: 45,
            DifficultyLevel.HARD: 55,
        }
        return cls(difficulty=difficulty, cells_to_remove=cells_map[difficulty])
