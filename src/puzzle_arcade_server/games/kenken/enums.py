"""KenKen game enums."""

from enum import Enum


class ArithmeticOperation(str, Enum):
    """Arithmetic operations for KenKen cages."""

    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    NONE = ""  # For single-cell cages
