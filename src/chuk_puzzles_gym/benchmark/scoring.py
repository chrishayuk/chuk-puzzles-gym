"""Scoring functions for CHUK-R benchmark.

Implements the scoring chain:
  per-episode (0-100) → per-game (mean) → per-family (mean) → CHUK-R (mean).
"""

from __future__ import annotations

from datetime import datetime

from ..eval import EvaluationReport
from ..models.evaluation import EpisodeResult
from .families import REASONING_FAMILIES, get_family
from .models import (
    ChukRBenchmarkResult,
    FamilyBenchmarkResult,
    GameBenchmarkResult,
)

# Component weights (sum to 1.0)
W_EFFICIENCY = 0.40
W_ERROR = 0.15
W_BACKTRACK = 0.15
W_STEADINESS = 0.15
W_HINT = 0.15


def score_episode(episode: EpisodeResult) -> float:
    """Compute a single 0-100 score for one episode.

    Unsolved episodes always score 0.  Solved episodes combine:
      - efficiency (40%): optimal_steps / steps_taken
      - error rate (15%): 1 - error_rate
      - backtrack rate (15%): 1 - backtrack_rate
      - progress steadiness (15%): progress_steadiness
      - hint independence (15%): 1 - hint_dependency
    """
    if not episode.success:
        return 0.0

    # Efficiency component
    if episode.efficiency_score > 0.0:
        eff = episode.efficiency_score
    else:
        # Fallback when optimal_steps is unknown
        eff = max(0.0, 1.0 - min(1.0, (episode.steps_taken - 1) / 100))

    # Error component
    err = 1.0 - episode.error_rate

    # Reasoning metrics components
    rm = episode.reasoning_metrics
    if rm is not None:
        bt = 1.0 - min(1.0, rm.backtrack_rate)
        stead = rm.progress_steadiness
    else:
        bt = 1.0
        stead = 1.0

    # Hint independence component
    hint = 1.0 - episode.hint_dependency

    raw = W_EFFICIENCY * eff + W_ERROR * err + W_BACKTRACK * bt + W_STEADINESS * stead + W_HINT * hint

    return round(max(0.0, min(100.0, raw * 100)), 2)


def score_game(report: EvaluationReport) -> GameBenchmarkResult:
    """Score all episodes for a single game into a GameBenchmarkResult."""
    family = get_family(report.game) or "Unknown"
    episode_scores = [score_episode(ep) for ep in report.episodes]
    solved = sum(1 for ep in report.episodes if ep.success)

    return GameBenchmarkResult(
        game=report.game,
        family=family,
        difficulty=report.difficulty,
        episodes_evaluated=len(report.episodes),
        episodes_solved=solved,
        episode_scores=episode_scores,
    )


def build_benchmark_result(
    reports: dict[str, EvaluationReport],
    difficulty: str,
    episodes_per_game: int,
    solver_config_desc: str = "default",
) -> ChukRBenchmarkResult:
    """Build a complete CHUK-R benchmark result from evaluation reports.

    Args:
        reports: Dict mapping game_name -> EvaluationReport.
        difficulty: Difficulty level used.
        episodes_per_game: Target episodes per game.
        solver_config_desc: Human-readable solver config description.

    Returns:
        Complete ChukRBenchmarkResult with per-game, per-family,
        and aggregate scores.
    """
    # Score each game
    game_results: list[GameBenchmarkResult] = []
    for _game_name, report in reports.items():
        game_results.append(score_game(report))

    # Build family results
    family_results: list[FamilyBenchmarkResult] = []
    for family_name, family_games in REASONING_FAMILIES.items():
        family_game_results = [g for g in game_results if g.game in family_games]
        # Add placeholder entries for games not evaluated
        evaluated_names = {g.game for g in family_game_results}
        for game_name in family_games:
            if game_name not in evaluated_names:
                family_game_results.append(
                    GameBenchmarkResult(
                        game=game_name,
                        family=family_name,
                        difficulty=difficulty,
                        episodes_evaluated=0,
                        episodes_solved=0,
                        episode_scores=[],
                    )
                )
        family_results.append(
            FamilyBenchmarkResult(
                family=family_name,
                games=family_game_results,
                total_games=len(family_games),
            )
        )

    return ChukRBenchmarkResult(
        timestamp=datetime.now(),
        difficulty=difficulty,
        episodes_per_game=episodes_per_game,
        solver_config_desc=solver_config_desc,
        families=family_results,
        games=[g for g in game_results if g.episodes_evaluated > 0],
    )
