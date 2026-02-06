"""Pydantic models for CHUK-R benchmark results.

Follows the frozen-model pattern from models/evaluation.py.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from .families import ALL_BENCHMARK_GAMES


class GameBenchmarkResult(BaseModel):
    """Benchmark result for a single game."""

    model_config = ConfigDict(frozen=True)

    game: str = Field(description="Game identifier (e.g., 'sudoku')")
    family: str = Field(description="Reasoning family (Logic, Constraint, Search, Planning)")
    difficulty: str = Field(description="Difficulty level used")
    episodes_evaluated: int = Field(ge=0, description="Number of episodes run")
    episodes_solved: int = Field(ge=0, description="Number of episodes solved")
    episode_scores: list[float] = Field(default_factory=list, description="Per-episode scores (0-100)")

    @computed_field
    @property
    def score(self) -> float:
        """Mean episode score for this game (0-100)."""
        if not self.episode_scores:
            return 0.0
        return sum(self.episode_scores) / len(self.episode_scores)

    @computed_field
    @property
    def solve_rate(self) -> float:
        """Fraction of episodes solved."""
        if self.episodes_evaluated == 0:
            return 0.0
        return self.episodes_solved / self.episodes_evaluated

    @computed_field
    @property
    def score_std(self) -> float:
        """Standard deviation of episode scores."""
        if len(self.episode_scores) < 2:
            return 0.0
        mean = self.score
        variance = sum((s - mean) ** 2 for s in self.episode_scores) / len(self.episode_scores)
        return variance**0.5


class FamilyBenchmarkResult(BaseModel):
    """Benchmark result for a reasoning family."""

    model_config = ConfigDict(frozen=True)

    family: str = Field(description="Family name (Logic, Constraint, Search, Planning)")
    games: list[GameBenchmarkResult] = Field(default_factory=list, description="Results for each game in this family")
    total_games: int = Field(description="Total games in this family (for coverage)")

    @computed_field
    @property
    def score(self) -> float:
        """Mean game score across evaluated games (0-100)."""
        scored = [g.score for g in self.games if g.episodes_evaluated > 0]
        if not scored:
            return 0.0
        return sum(scored) / len(scored)

    @computed_field
    @property
    def evaluated_count(self) -> int:
        """Number of games actually evaluated."""
        return sum(1 for g in self.games if g.episodes_evaluated > 0)

    @computed_field
    @property
    def coverage(self) -> float:
        """Fraction of family games that were evaluated."""
        if self.total_games == 0:
            return 0.0
        return self.evaluated_count / self.total_games


class ChukRBenchmarkResult(BaseModel):
    """Complete CHUK-R benchmark result."""

    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(description="When the benchmark was run")
    difficulty: str = Field(description="Difficulty level used")
    episodes_per_game: int = Field(description="Target episodes per game")
    solver_config_desc: str = Field(description="Solver config description")

    families: list[FamilyBenchmarkResult] = Field(default_factory=list, description="Per-family results")
    games: list[GameBenchmarkResult] = Field(default_factory=list, description="All per-game results")

    @computed_field
    @property
    def chuk_r(self) -> float:
        """The CHUK-R aggregate score (0-100)."""
        family_scores = [f.score for f in self.families if f.evaluated_count > 0]
        if not family_scores:
            return 0.0
        return sum(family_scores) / len(family_scores)

    @computed_field
    @property
    def total_episodes(self) -> int:
        """Total episodes across all games."""
        return sum(g.episodes_evaluated for g in self.games)

    @computed_field
    @property
    def total_solved(self) -> int:
        """Total episodes solved across all games."""
        return sum(g.episodes_solved for g in self.games)

    @computed_field
    @property
    def overall_solve_rate(self) -> float:
        """Aggregate solve rate across all episodes."""
        if self.total_episodes == 0:
            return 0.0
        return self.total_solved / self.total_episodes

    @computed_field
    @property
    def coverage(self) -> float:
        """Fraction of all 30 games that were evaluated."""
        evaluated = sum(1 for g in self.games if g.episodes_evaluated > 0)
        total = len(ALL_BENCHMARK_GAMES)
        if total == 0:
            return 0.0
        return evaluated / total

    @computed_field
    @property
    def families_evaluated(self) -> int:
        """Number of families with at least one evaluated game."""
        return sum(1 for f in self.families if f.evaluated_count > 0)
