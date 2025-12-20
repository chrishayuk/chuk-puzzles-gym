"""Logic Grid puzzle game models."""

from pydantic import BaseModel, ConfigDict


class LogicGridCategories(BaseModel):
    """Categories for Logic Grid puzzle."""

    model_config = ConfigDict(frozen=True)

    person: list[str]
    color: list[str]
    pet: list[str]
    drink: list[str]


class PersonAttributes(BaseModel):
    """Attributes for a person in Logic Grid puzzle."""

    model_config = ConfigDict(frozen=False)

    color: str
    pet: str
    drink: str
