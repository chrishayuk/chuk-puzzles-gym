"""Nurikabe game enums."""

from enum import StrEnum


class NurikabeColor(StrEnum):
    """Colors for Nurikabe cells."""

    WHITE = "white"
    W = "w"
    BLACK = "black"
    B = "b"
    CLEAR = "clear"
    C = "c"
