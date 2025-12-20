"""Einstein's Puzzle game models."""

from pydantic import BaseModel, ConfigDict


class HouseAssignment(BaseModel):
    """Attribute assignments for a house in Einstein's Puzzle."""

    model_config = ConfigDict(frozen=False)  # Allow mutation during gameplay

    color: str | None = None
    nationality: str | None = None
    drink: str | None = None
    smoke: str | None = None
    pet: str | None = None

    def is_complete(self) -> bool:
        """Check if all attributes are assigned."""
        return all(
            [
                self.color is not None,
                self.nationality is not None,
                self.drink is not None,
                self.smoke is not None,
                self.pet is not None,
            ]
        )

    def get_attribute(self, attr_type: str) -> str | None:
        """Get attribute value by type."""
        return getattr(self, attr_type.lower(), None)

    def set_attribute(self, attr_type: str, value: str) -> None:
        """Set attribute value by type."""
        setattr(self, attr_type.lower(), value)
