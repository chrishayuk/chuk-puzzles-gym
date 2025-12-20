"""KenKen game models."""

from pydantic import BaseModel, ConfigDict, Field

from .enums import ArithmeticOperation


class Cage(BaseModel):
    """A cage in KenKen game."""

    model_config = ConfigDict(frozen=True)  # Cages don't change once created

    cells: list[tuple[int, int]] = Field(min_length=1, description="List of cell coordinates (0-indexed)")
    operation: ArithmeticOperation | None = Field(description="Arithmetic operation for the cage")
    target: int = Field(description="Target value for the cage")
