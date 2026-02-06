"""CHUK-R Reasoning Benchmark scoring for puzzle games.

Computes a single aggregate CHUK Reasoning Score (CHUK-R) from 0-100
by evaluating 30 puzzle games across 4 reasoning families:
Logic, Constraint, Search, and Planning.
"""

from .families import (
    ALL_BENCHMARK_GAMES,
    REASONING_FAMILIES,
    get_family,
    get_family_games,
)
from .models import (
    ChukRBenchmarkResult,
    FamilyBenchmarkResult,
    GameBenchmarkResult,
)
from .report import format_json, format_markdown, format_text
from .scoring import build_benchmark_result, score_episode, score_game

__all__ = [
    "ALL_BENCHMARK_GAMES",
    "REASONING_FAMILIES",
    "get_family",
    "get_family_games",
    "ChukRBenchmarkResult",
    "FamilyBenchmarkResult",
    "GameBenchmarkResult",
    "format_json",
    "format_markdown",
    "format_text",
    "build_benchmark_result",
    "score_episode",
    "score_game",
]
