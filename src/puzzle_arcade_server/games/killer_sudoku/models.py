"""Killer Sudoku game models."""

from pydantic import BaseModel, ConfigDict, Field


class Cage(BaseModel):
    """A cage in Killer Sudoku game.

    Unlike KenKen cages, Killer Sudoku cages only use addition.
    """

    model_config = ConfigDict(frozen=True)

    cells: list[tuple[int, int]] = Field(min_length=1, description="List of cell coordinates (0-indexed)")
    target: int = Field(description="Target sum for the cage")
