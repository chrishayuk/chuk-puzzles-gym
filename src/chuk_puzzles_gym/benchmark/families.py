"""Reasoning family definitions for CHUK-R benchmark.

Groups the 30 puzzle games into 4 reasoning families based on
the dominant cognitive skill each puzzle exercises.
"""

from __future__ import annotations

REASONING_FAMILIES: dict[str, list[str]] = {
    "Logic": [
        "sudoku",
        "binary",
        "futoshiki",
        "nonogram",
        "logic",
        "skyscrapers",
        "nqueens",
        "graph_coloring",
        "cryptarithmetic",
        "hitori",
    ],
    "Constraint": [
        "kenken",
        "kakuro",
        "killer",
        "slither",
        "bridges",
        "nurikabe",
        "fillomino",
        "shikaku",
        "hidato",
        "star_battle",
        "tents",
        "einstein",
    ],
    "Search": [
        "mastermind",
        "minesweeper",
        "numberlink",
        "lights",
    ],
    "Planning": [
        "sokoban",
        "rush_hour",
        "knapsack",
        "scheduler",
    ],
}

ALL_BENCHMARK_GAMES: list[str] = [game for games in REASONING_FAMILIES.values() for game in games]


def get_family(game_name: str) -> str | None:
    """Return the reasoning family for a game, or None if not mapped."""
    for family, games in REASONING_FAMILIES.items():
        if game_name in games:
            return family
    return None


def get_family_games(family: str) -> list[str]:
    """Return the list of games in a reasoning family."""
    return REASONING_FAMILIES.get(family, [])
