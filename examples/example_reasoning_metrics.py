#!/usr/bin/env python3
"""
Example: Reasoning Depth Metrics

Demonstrates the reasoning depth metrics system that measures *how* an agent
reasons, not just whether it solves a puzzle. This goes beyond binary
success/failure to track:

  - Backtrack detection: did the agent revise previous placements?
  - Progress tracking: how steadily did the agent advance toward a solution?
  - Error patterns: were invalid moves isolated or clustered in streaks?
  - Reasoning overhead: how much wasted work relative to optimal?

Four scenarios are shown:

  1. Perfect solver (hint-based) — baseline metrics
  2. Gym environment with mixed valid/invalid moves — realistic agent behavior
  3. Multi-game evaluation comparison — cross-puzzle reasoning profile
  4. Evaluation harness with aggregate metrics — all output formats
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.eval import evaluate_game, run_episode
from chuk_puzzles_gym.games import AVAILABLE_GAMES
from chuk_puzzles_gym.gym_env import PuzzleEnv

# ── Scenario 1: Perfect solver via hints ─────────────────────────────────────


async def demo_perfect_solver():
    """Run a puzzle using the built-in hint solver and inspect metrics."""
    print("=" * 70)
    print("Scenario 1: Perfect Solver (hint-based)")
    print("=" * 70)

    game_class = AVAILABLE_GAMES["sudoku"]
    result = await run_episode(
        game_class=game_class,
        difficulty="easy",
        seed=42,
        use_hints=True,
        max_moves=200,
    )

    print(f"\n  Game:       {result.game}")
    print(f"  Status:     {result.status.value}")
    print(f"  Steps:      {result.steps_taken}")
    print(f"  Invalid:    {result.invalid_actions}")
    print(f"  Efficiency: {result.efficiency_score:.0%}")

    rm = result.reasoning_metrics
    if rm:
        print("\n  Reasoning Depth Metrics:")
        print(f"    Backtrack Count:      {rm.backtrack_count}")
        print(f"    Backtrack Rate:       {rm.backtrack_rate:.0%}")
        print(f"    Reasoning Overhead:   {rm.reasoning_overhead:.1f}x optimal")
        print(f"    Progress Velocity:    {rm.progress_velocity:.2f} cells/step")
        print(f"    Progress Steadiness:  {rm.progress_steadiness:.0%}")
        print(f"    Error Streak Max:     {rm.error_streak_max}")
        print(f"    Total Actions:        {rm.total_actions}")
        print(f"    Optimal Path Length:  {rm.optimal_path_length}")

        # Show solver distance curve
        trace = rm.solver_distance_trace
        if trace:
            print(f"\n  Solver Distance Curve ({len(trace)} points):")
            print(f"    Start: {trace[0]} remaining")
            if len(trace) > 2:
                mid = len(trace) // 2
                print(f"    Mid:   {trace[mid]} remaining")
            print(f"    End:   {trace[-1]} remaining")

    print("\n  A perfect solver has:")
    print("    - 0 backtracks (never revises)")
    print("    - 1.0x overhead (no wasted moves)")
    print("    - 100% steadiness (monotonic progress)")
    print("    - 1.0 velocity (one cell per step)")


# ── Scenario 2: Simulated imperfect agent via Gym env ────────────────────────


async def demo_gym_agent():
    """Simulate a realistic agent that makes some mistakes."""
    print("\n")
    print("=" * 70)
    print("Scenario 2: Simulated Agent via Gym Environment")
    print("=" * 70)

    env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
    obs, info = await env.reset()

    print(f"\n  Game:            {obs['game']}")
    print(f"  Optimal steps:   {info['optimal_steps']}")
    print(f"  Initial metrics: {info['reasoning_metrics']}")

    # Phase 1: Make a few invalid moves (simulating an agent exploring)
    print("\n  Phase 1: Agent makes 3 invalid attempts...")
    for _ in range(3):
        await env.step("place 1 1 99")

    # Phase 2: Solve correctly using hints
    print("  Phase 2: Agent uses hints to solve correctly...")
    steps = 0
    while True:
        hint = await env.game.get_hint()
        if hint is None:
            break
        row, col, val = hint[0]
        obs, reward, terminated, truncated, info = await env.step(f"place {row} {col} {val}")
        steps += 1
        if terminated:
            break

    print(f"\n  Solved: {obs['is_complete']}")
    print(f"  Valid steps: {steps}")

    # Get final reasoning metrics
    rm = env.game.get_reasoning_metrics()
    print("\n  Reasoning Depth Metrics:")
    print(f"    Backtrack Count:      {rm.backtrack_count}")
    print(f"    Backtrack Rate:       {rm.backtrack_rate:.0%}")
    print(f"    Progress Velocity:    {rm.progress_velocity:.2f} cells/step")
    print(f"    Progress Steadiness:  {rm.progress_steadiness:.0%}")
    print(f"    Error Streak Max:     {rm.error_streak_max}")
    print(f"    Avg Error Streak:     {rm.avg_error_streak:.1f}")
    print(f"    Total Actions:        {rm.total_actions}")

    # The metrics from the info dict on termination
    if "reasoning_metrics" in info:
        print("\n  (These metrics are also available in the step info dict")
        print("   on episode termination for RL training loops.)")

    print("\n  An imperfect agent shows:")
    print("    - Error streaks from invalid attempts")
    print("    - Higher total actions than optimal")
    print("    - Overhead > 1.0x reflecting wasted work")

    env.close()


# ── Scenario 3: Multi-game reasoning profile ─────────────────────────────────


async def demo_multi_game():
    """Compare reasoning metrics across different puzzle types."""
    print("\n")
    print("=" * 70)
    print("Scenario 3: Multi-Game Reasoning Profile")
    print("=" * 70)

    games = ["sudoku", "kenken", "binary", "bridges", "lights", "knapsack"]

    print(
        f"\n  {'Game':20s} {'Status':8s} {'Steps':>5s} {'Inv':>4s} "
        f"{'BT':>3s} {'Steady':>7s} {'Overhead':>9s} {'Vel':>5s} {'ErrMax':>6s}"
    )
    print("  " + "-" * 75)

    for game_name in games:
        game_class = AVAILABLE_GAMES[game_name]
        result = await run_episode(
            game_class=game_class,
            difficulty="easy",
            seed=42,
            use_hints=True,
            max_moves=200,
        )

        rm = result.reasoning_metrics
        status = "SOLVED" if result.success else result.status.value.upper()

        if rm:
            print(
                f"  {result.game:20s} {status:8s} {result.steps_taken:5d} "
                f"{result.invalid_actions:4d} {rm.backtrack_count:3d} "
                f"{rm.progress_steadiness:6.0%}  {rm.reasoning_overhead:8.1f}x "
                f"{rm.progress_velocity:5.2f} {rm.error_streak_max:6d}"
            )

    print("\n  Grid-based puzzles (Sudoku, KenKen, Binary, Lights Out) show")
    print("  100% steadiness because each hint fills exactly one cell.")
    print("  Other puzzles may show different patterns based on how their")
    print("  optimal_steps property tracks remaining work.")


# ── Scenario 4: Evaluation harness with reasoning metrics ────────────────────


async def demo_eval_harness():
    """Use the evaluation harness to get aggregate reasoning metrics."""
    print("\n")
    print("=" * 70)
    print("Scenario 4: Evaluation Harness with Aggregate Metrics")
    print("=" * 70)

    report = await evaluate_game(
        "sudoku",
        difficulty="easy",
        episodes=5,
        seeds=[42, 43, 44, 45, 46],
        verbose=True,
    )

    # Text summary (includes reasoning depth section)
    report.print_summary()

    # JSON output (includes reasoning metrics per episode)
    import json

    parsed = json.loads(report.to_json())
    print("\n  JSON summary.reasoning:")
    print(f"    {json.dumps(parsed['summary'].get('reasoning', {}), indent=4)}")

    # CSV output (includes reasoning columns)
    csv_lines = report.to_csv().strip().split("\n")
    print("\n  CSV header:")
    print(f"    {csv_lines[0]}")
    print("  CSV first row:")
    print(f"    {csv_lines[1]}")


# ── Main ─────────────────────────────────────────────────────────────────────


async def main():
    print()
    print("Puzzle Arcade - Reasoning Depth Metrics Demo")
    print("Measuring *how* agents reason, not just if they succeed.")
    print()

    await demo_perfect_solver()
    await demo_gym_agent()
    await demo_multi_game()
    await demo_eval_harness()

    print("\n")
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("""
  Reasoning depth metrics enable measuring the *quality* of reasoning:

  - backtrack_rate:       How often the agent revises previous decisions
  - progress_steadiness:  How monotonically the agent advances (1.0 = perfect)
  - progress_velocity:    Average cells solved per step
  - reasoning_overhead:   Total actions / optimal path (1.0 = no waste)
  - error_streak_max:     Longest run of consecutive invalid moves
  - solver_distance_trace: Remaining work after each valid move

  These metrics are available in:
    - EpisodeResult.reasoning_metrics  (eval harness)
    - PuzzleEnv step info dict         (gym environment)
    - Server state/completion output   (telnet/WebSocket, all output modes)
    - All output formats               (JSON, CSV, markdown, text)
""")


if __name__ == "__main__":
    asyncio.run(main())
