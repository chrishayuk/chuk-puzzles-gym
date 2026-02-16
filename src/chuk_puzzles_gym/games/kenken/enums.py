"""KenKen game enums."""

from enum import StrEnum


class ArithmeticOperation(StrEnum):
    """Arithmetic operations for KenKen cages."""

    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    NONE = ""  # For single-cell cages
