"""Knapsack game models."""

from pydantic import BaseModel, ConfigDict, Field


class Item(BaseModel):
    """An item in the Knapsack game."""

    model_config = ConfigDict(frozen=True)  # Items don't change once created

    name: str = Field(min_length=1, description="Item name")
    weight: int = Field(gt=0, description="Item weight")
    value: int = Field(gt=0, description="Item value")
