"""Base configuration models for games."""

from pydantic import BaseModel, Field

from .enums import DifficultyLevel


class GameConfig(BaseModel):
    """Base configuration for all games."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, description="Game difficulty level")
