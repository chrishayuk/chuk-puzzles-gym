#!/usr/bin/env python3
"""
Example: CHUK-R Reasoning Benchmark

Demonstrates the CHUK Reasoning Score (CHUK-R) benchmark system that produces
a single aggregate score (0-100) measuring reasoning capabilities across
30 puzzle games organized into 4 reasoning families:

  - Logic (10 games):      Pure deductive reasoning, grid uniqueness, patterns
  - Constraint (12 games): Multi-constraint interaction, sums, connectivity
  - Search (4 games):      Feedback-driven, iterative, path-finding
  - Planning (4 games):    Sequential actions, irreversible decisions

The scoring formula combines multiple metrics per episode:
  - Efficiency (40%):   optimal_steps / steps_taken
  - Error rate (15%):   1 - (invalid / total)
  - Backtrack (15%):    1 - backtrack_rate
  - Steadiness (15%):   progress_steadiness
  - Hint indep (15%):   1 - hint_dependency

Unsolved episodes score 0. Scores aggregate: episode → game → family → CHUK-R.

Three scenarios are shown:
  1. Single-game benchmark — score one game
  2. Single-family benchmark — score all games in one reasoning family
  3. Full CHUK-R benchmark — score all 30 games across all families
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.benchmark import (
    REASONING_FAMILIES,
    build_benchmark_result,
    format_text,
    get_family,
    score_episode,
    score_game,
)
from chuk_puzzles_gym.eval import evaluate_game

# ── Scenario 1: Single-game benchmark ─────────────────────────────────────────


async def demo_single_game():
    """Run a benchmark on a single game and inspect the scoring."""
    print("=" * 70)
    print("Scenario 1: Single-Game Benchmark")
    print("=" * 70)

    # Evaluate sudoku with 5 episodes
    report = await evaluate_game(
        "sudoku",
        difficulty="easy",
        episodes=5,
        seeds=[42, 43, 44, 45, 46],
        verbose=False,
    )

    print(f"\n  Game:     {report.game}")
    print(f"  Family:   {get_family(report.game)}")
    print(f"  Episodes: {report.total_episodes}")
    print(f"  Solved:   {report.solved_count}")

    # Score each episode individually
    print("\n  Per-Episode Scores:")
    print(f"    {'Seed':>6s}  {'Status':>8s}  {'Steps':>5s}  {'Inv':>4s}  {'Score':>6s}")
    print("    " + "-" * 38)

    for ep in report.episodes:
        score = score_episode(ep)
        status = "SOLVED" if ep.success else ep.status.value.upper()
        print(f"    {ep.seed:>6d}  {status:>8s}  {ep.steps_taken:>5d}  {ep.invalid_actions:>4d}  {score:>6.1f}")

    # Aggregate into a game result
    game_result = score_game(report)
    print(f"\n  Game Score:     {game_result.score:.1f}")
    print(f"  Score Std Dev:  {game_result.score_std:.1f}")
    print(f"  Solve Rate:     {game_result.solve_rate:.0%}")


# ── Scenario 2: Single-family benchmark ───────────────────────────────────────


async def demo_single_family():
    """Run a benchmark on all games in one reasoning family."""
    print("\n")
    print("=" * 70)
    print("Scenario 2: Single-Family Benchmark (Logic)")
    print("=" * 70)

    family = "Logic"
    games = REASONING_FAMILIES[family]

    print(f"\n  Family: {family}")
    print(f"  Games:  {', '.join(games)}")
    print("\n  Running 2 episodes per game...")

    # Evaluate each game in the family
    reports = {}
    for game_name in games:
        report = await evaluate_game(
            game_name,
            difficulty="easy",
            episodes=2,
            verbose=False,
        )
        reports[game_name] = report

    # Build benchmark result
    result = build_benchmark_result(
        reports=reports,
        difficulty="easy",
        episodes_per_game=2,
        solver_config_desc="hints (default)",
    )

    # Show per-game scores
    print(f"\n  {'Game':<20s}  {'Score':>6s}  {'Solved':>8s}")
    print("  " + "-" * 38)

    for g in sorted(result.games, key=lambda x: -x.score):
        print(f"  {g.game:<20s}  {g.score:>6.1f}  {g.episodes_solved}/{g.episodes_evaluated}")

    # Show family score
    logic_family = next(f for f in result.families if f.family == "Logic")
    print(f"\n  Logic Family Score: {logic_family.score:.1f}")
    print(f"  Games Evaluated:    {logic_family.evaluated_count}/{logic_family.total_games}")


# ── Scenario 3: Full CHUK-R benchmark ─────────────────────────────────────────


async def demo_full_benchmark():
    """Run a full CHUK-R benchmark across all 30 games."""
    print("\n")
    print("=" * 70)
    print("Scenario 3: Full CHUK-R Benchmark (subset for demo)")
    print("=" * 70)

    # For this demo, we'll use 1 game from each family to keep it quick
    demo_games = ["sudoku", "kenken", "mastermind", "sokoban"]

    print(f"\n  Demo subset: {', '.join(demo_games)}")
    print("  (In production, use chuk-puzzles-benchmark CLI for all 30 games)")
    print("\n  Running 3 episodes per game...")

    reports = {}
    for game_name in demo_games:
        print(f"    Evaluating {game_name}...")
        report = await evaluate_game(
            game_name,
            difficulty="easy",
            episodes=3,
            verbose=False,
        )
        reports[game_name] = report

    # Build full benchmark result
    result = build_benchmark_result(
        reports=reports,
        difficulty="easy",
        episodes_per_game=3,
        solver_config_desc="hints (budget=100)",
    )

    # Show text output (same as CLI)
    print(format_text(result))

    # Show that JSON and Markdown are also available
    print("\n  Other output formats available:")
    print("    - format_json(result)     → structured JSON")
    print("    - format_markdown(result) → markdown tables")


# ── Scenario 4: Understanding the scoring formula ─────────────────────────────


async def demo_scoring_formula():
    """Demonstrate how the scoring formula works."""
    print("\n")
    print("=" * 70)
    print("Scenario 4: Understanding the Scoring Formula")
    print("=" * 70)

    print("""
  Per-Episode Score Formula (0-100):

    score = 0                          (if episode not solved)

    score = 100 × (                    (if episode solved)
        0.40 × efficiency       +      optimal_steps / steps_taken
        0.15 × (1 - error_rate) +      invalid / (steps + invalid)
        0.15 × (1 - backtrack)  +      from reasoning_metrics
        0.15 × steadiness       +      from reasoning_metrics
        0.15 × (1 - hint_dep)          hints_used / steps_taken
    )

  Aggregation Chain:

    episode_score  →  game_score (mean)  →  family_score (mean)  →  CHUK-R (mean)

  Example calculations:
    """)

    # Perfect episode
    report = await evaluate_game("binary", difficulty="easy", episodes=1, seeds=[42])
    ep = report.episodes[0]
    score = score_episode(ep)

    print("  Binary Puzzle (seed 42):")
    print(f"    Solved:     {ep.success}")
    print(f"    Steps:      {ep.steps_taken}")
    print(f"    Optimal:    {ep.optimal_steps}")
    print(f"    Invalid:    {ep.invalid_actions}")
    print(f"    Hints:      {ep.hints_used}")
    print(f"    Efficiency: {ep.efficiency_score:.2f}")
    print(f"    Error rate: {ep.error_rate:.2f}")
    print(f"    Hint dep:   {ep.hint_dependency:.2f}")
    if ep.reasoning_metrics:
        rm = ep.reasoning_metrics
        print(f"    Backtrack:  {rm.backtrack_rate:.2f}")
        print(f"    Steadiness: {rm.progress_steadiness:.2f}")
    print(f"    → Score:    {score:.1f}")


# ── Main ─────────────────────────────────────────────────────────────────────


async def main():
    print()
    print("Puzzle Arcade - CHUK-R Reasoning Benchmark Demo")
    print("A single aggregate score measuring reasoning across 30 puzzles.")
    print()

    await demo_single_game()
    await demo_single_family()
    await demo_full_benchmark()
    await demo_scoring_formula()

    print("\n")
    print("=" * 70)
    print("CLI Usage")
    print("=" * 70)
    print("""
  The CHUK-R benchmark is also available via CLI:

    # Full benchmark (all 30 games)
    chuk-puzzles-benchmark -d easy -n 5 -v

    # Single family
    chuk-puzzles-benchmark --family Logic -n 10

    # Specific games
    chuk-puzzles-benchmark --games sudoku,kenken,mastermind -o json

    # List game-to-family mapping
    chuk-puzzles-benchmark --list-families

    # Solver-free mode (pure model reasoning, no hints)
    chuk-puzzles-benchmark --solver-free

  Output formats: text (default), json, markdown
""")


if __name__ == "__main__":
    asyncio.run(main())
