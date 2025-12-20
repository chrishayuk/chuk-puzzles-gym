"""Scheduler game models."""

from pydantic import BaseModel, ConfigDict, Field


class Task(BaseModel):
    """A task in the Scheduler game."""

    model_config = ConfigDict(frozen=False)  # Allow mutation for game state

    id: int = Field(ge=0, description="Task ID")
    name: str = Field(min_length=1, description="Task name")
    duration: int = Field(gt=0, description="Task duration in time units")
    dependencies: list[int] = Field(default_factory=list, description="List of task IDs this task depends on")
