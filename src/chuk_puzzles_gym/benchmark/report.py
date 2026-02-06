"""Output formatting for CHUK-R benchmark results.

Supports text (human-readable), JSON, and markdown output.
"""

from __future__ import annotations

import json
from typing import Any

from .models import ChukRBenchmarkResult


def format_text(result: ChukRBenchmarkResult) -> str:
    """Generate human-readable text report."""
    lines: list[str] = []
    evaluated_count = sum(1 for g in result.games if g.episodes_evaluated > 0)

    lines.append("")
    lines.append("=" * 64)
    lines.append("  CHUK REASONING SCORE (CHUK-R)")
    lines.append("=" * 64)
    lines.append(f"  Difficulty:     {result.difficulty.title()}")
    lines.append(f"  Episodes/game:  {result.episodes_per_game}")
    lines.append(f"  Solver:         {result.solver_config_desc}")
    lines.append(f"  Coverage:       {result.coverage:.0%} ({evaluated_count}/30 games)")
    lines.append("")

    # Family scores
    lines.append("-" * 64)
    lines.append(f"  {'Family':<14} {'Score':>8} {'Games':>8} {'Solve%':>8}")
    lines.append("-" * 64)
    for fam in result.families:
        if fam.evaluated_count > 0:
            solved_eps = sum(g.episodes_solved for g in fam.games)
            total_eps = sum(g.episodes_evaluated for g in fam.games)
            solve_pct = solved_eps / total_eps if total_eps > 0 else 0.0
            lines.append(
                f"  {fam.family:<14} {fam.score:>7.1f} {fam.evaluated_count:>5}/{fam.total_games:<3} {solve_pct:>7.0%}"
            )
        else:
            lines.append(f"  {fam.family:<14} {'--':>8} {0:>5}/{fam.total_games:<3} {'--':>8}")

    lines.append("-" * 64)
    lines.append(f"  {'CHUK-R':<14} {result.chuk_r:>7.1f}")
    lines.append("=" * 64)

    # Per-game detail
    lines.append("")
    lines.append("Per-Game Breakdown:")
    lines.append(f"  {'Game':<20} {'Family':<12} {'Score':>7} {'Solved':>8} {'Solve%':>7}")
    lines.append("  " + "-" * 56)
    for g in sorted(result.games, key=lambda x: (-x.score, x.game)):
        if g.episodes_evaluated > 0:
            lines.append(
                f"  {g.game:<20} {g.family:<12} {g.score:>6.1f}"
                f" {g.episodes_solved:>4}/{g.episodes_evaluated:<3}"
                f" {g.solve_rate:>6.0%}"
            )

    lines.append("")
    return "\n".join(lines)


def format_json(result: ChukRBenchmarkResult) -> str:
    """Generate JSON report."""
    data: dict[str, Any] = {
        "chuk_r": round(result.chuk_r, 2),
        "timestamp": result.timestamp.isoformat(),
        "difficulty": result.difficulty,
        "episodes_per_game": result.episodes_per_game,
        "solver_config": result.solver_config_desc,
        "coverage": round(result.coverage, 3),
        "overall_solve_rate": round(result.overall_solve_rate, 3),
        "families": {},
        "games": {},
    }
    for fam in result.families:
        data["families"][fam.family] = {
            "score": round(fam.score, 2),
            "evaluated": fam.evaluated_count,
            "total": fam.total_games,
            "coverage": round(fam.coverage, 3),
        }
    for g in result.games:
        if g.episodes_evaluated > 0:
            data["games"][g.game] = {
                "score": round(g.score, 2),
                "score_std": round(g.score_std, 2),
                "family": g.family,
                "episodes": g.episodes_evaluated,
                "solved": g.episodes_solved,
                "solve_rate": round(g.solve_rate, 3),
            }
    return json.dumps(data, indent=2)


def format_markdown(result: ChukRBenchmarkResult) -> str:
    """Generate markdown report."""
    evaluated_count = sum(1 for g in result.games if g.episodes_evaluated > 0)
    lines: list[str] = []
    lines.append(f"# CHUK Reasoning Score (CHUK-R): **{result.chuk_r:.1f}**")
    lines.append("")
    lines.append(f"- **Difficulty:** {result.difficulty.title()}")
    lines.append(f"- **Episodes/game:** {result.episodes_per_game}")
    lines.append(f"- **Solver:** {result.solver_config_desc}")
    lines.append(f"- **Coverage:** {result.coverage:.0%} ({evaluated_count}/30 games)")
    lines.append(f"- **Overall Solve Rate:** {result.overall_solve_rate:.1%}")
    lines.append("")
    lines.append("## Family Scores")
    lines.append("")
    lines.append("| Family | Score | Games Evaluated | Coverage |")
    lines.append("|--------|------:|:---------------:|:--------:|")
    for fam in result.families:
        lines.append(
            f"| {fam.family} | {fam.score:.1f} | {fam.evaluated_count}/{fam.total_games} | {fam.coverage:.0%} |"
        )
    lines.append("")
    lines.append("## Per-Game Scores")
    lines.append("")
    lines.append("| Game | Family | Score | Solved | Solve Rate |")
    lines.append("|------|--------|------:|:------:|:----------:|")
    for g in sorted(result.games, key=lambda x: (-x.score, x.game)):
        if g.episodes_evaluated > 0:
            lines.append(
                f"| {g.game} | {g.family} | {g.score:.1f}"
                f" | {g.episodes_solved}/{g.episodes_evaluated}"
                f" | {g.solve_rate:.0%} |"
            )
    lines.append("")
    return "\n".join(lines)
