"""Nurikabe game enums."""

from enum import Enum


class NurikabeColor(str, Enum):
    """Colors for Nurikabe cells."""

    WHITE = "white"
    W = "w"
    BLACK = "black"
    B = "b"
    CLEAR = "clear"
    C = "c"
