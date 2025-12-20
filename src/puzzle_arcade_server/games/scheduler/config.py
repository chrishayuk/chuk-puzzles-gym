"""Configuration for Scheduler game."""

from pydantic import BaseModel, Field

from ...models.enums import DifficultyLevel


class SchedulerConfig(BaseModel):
    """Configuration for Scheduler game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
    num_tasks: int = Field(ge=1, le=20, description="Number of tasks")
    num_workers: int = Field(ge=1, le=10, description="Number of workers")
    dependency_prob: float = Field(ge=0.0, le=1.0, description="Probability of task dependencies")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "SchedulerConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"num_tasks": 4, "num_workers": 2, "dependency_prob": 0.3},
            DifficultyLevel.MEDIUM: {"num_tasks": 6, "num_workers": 2, "dependency_prob": 0.4},
            DifficultyLevel.HARD: {"num_tasks": 8, "num_workers": 3, "dependency_prob": 0.5},
        }
        params = config_map[difficulty]
        return cls(difficulty=difficulty, **params)
