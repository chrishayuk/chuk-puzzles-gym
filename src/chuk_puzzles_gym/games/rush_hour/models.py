"""Models for Rush Hour puzzle game."""

from pydantic import BaseModel, ConfigDict, Field


class Vehicle(BaseModel):
    """A vehicle on the Rush Hour board."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1, max_length=1, description="Vehicle identifier (letter)")
    row: int = Field(ge=0, description="Top-left row position")
    col: int = Field(ge=0, description="Top-left column position")
    length: int = Field(ge=2, le=3, description="Vehicle length (2 or 3)")
    orientation: str = Field(description="'h' for horizontal, 'v' for vertical")
