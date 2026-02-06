"""CLI entry point for CHUK-R benchmark scoring.

Usage:
    chuk-puzzles-benchmark                              # All games, easy, 5 episodes
    chuk-puzzles-benchmark -d medium -n 10              # All games, medium, 10 eps
    chuk-puzzles-benchmark --games sudoku,kenken -o json # Specific games, JSON output
    chuk-puzzles-benchmark --family Logic -n 10         # Only Logic family
    chuk-puzzles-benchmark --solver-free                # Pure model reasoning
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from ..eval import evaluate_all_games, evaluate_game
from ..games import AVAILABLE_GAMES
from ..models import SolverConfig
from .families import REASONING_FAMILIES
from .report import format_json, format_markdown, format_text
from .scoring import build_benchmark_result


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=("CHUK-R Reasoning Benchmark — Aggregate reasoning score for puzzle games"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chuk-puzzles-benchmark                                 # All games, easy, 5 eps
  chuk-puzzles-benchmark -d medium -n 10                 # All games, medium, 10 eps
  chuk-puzzles-benchmark --games sudoku,kenken -o json   # Specific games, JSON
  chuk-puzzles-benchmark --family Logic -n 10            # Logic family only
  chuk-puzzles-benchmark --solver-free                   # No hints
        """,
    )
    parser.add_argument(
        "-d",
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="easy",
        help="Difficulty level (default: easy)",
    )
    parser.add_argument(
        "-n",
        "--episodes",
        type=int,
        default=5,
        help="Episodes per game (default: 5)",
    )
    parser.add_argument(
        "--games",
        type=str,
        help="Comma-separated list of games to evaluate (default: all)",
    )
    parser.add_argument(
        "--family",
        choices=list(REASONING_FAMILIES.keys()),
        help="Evaluate only games in a specific family",
    )
    parser.add_argument(
        "-o",
        "--output",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show per-game progress",
    )
    parser.add_argument(
        "--list-families",
        action="store_true",
        help="List reasoning families and games, then exit",
    )

    solver_group = parser.add_argument_group("solver configuration")
    solver_group.add_argument(
        "--solver-free",
        action="store_true",
        help="Disable solver hints (pure model reasoning)",
    )
    solver_group.add_argument(
        "--hint-budget",
        type=int,
        default=100,
        help="Max hints allowed (default: 100)",
    )
    solver_group.add_argument(
        "--hint-penalty",
        type=float,
        default=0.0,
        help="Score penalty per hint, 0.0-1.0 (default: 0.0)",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the CHUK-R benchmark CLI."""
    args = parse_args()

    if args.list_families:
        print("CHUK-R Reasoning Families:")
        print("=" * 50)
        for family, games in REASONING_FAMILIES.items():
            print(f"\n{family} ({len(games)} games):")
            for g in games:
                marker = "" if g in AVAILABLE_GAMES else " [missing]"
                print(f"    {g}{marker}")
        return

    # Determine which games to evaluate
    if args.games:
        game_list = [g.strip() for g in args.games.split(",")]
    elif args.family:
        game_list = list(REASONING_FAMILIES[args.family])
    else:
        game_list = None  # all games

    # Build solver config
    if args.solver_free:
        solver_config = SolverConfig.solver_free()
        solver_desc = "solver-free"
    else:
        solver_config = SolverConfig(
            solver_allowed=True,
            hint_budget=args.hint_budget,
            hint_penalty=args.hint_penalty,
        )
        solver_desc = f"hints (budget={args.hint_budget}, penalty={args.hint_penalty})"

    # Run evaluations
    if game_list:
        reports = {}
        for game_name in game_list:
            if game_name not in AVAILABLE_GAMES:
                print(
                    f"Warning: Unknown game '{game_name}', skipping.",
                    file=sys.stderr,
                )
                continue
            if args.verbose:
                print(f"Evaluating {game_name}...", file=sys.stderr)
            report = asyncio.run(
                evaluate_game(
                    game_name=game_name,
                    difficulty=args.difficulty,
                    episodes=args.episodes,
                    solver_config=solver_config,
                    verbose=args.verbose,
                )
            )
            reports[game_name] = report
    else:
        if args.verbose:
            print("Evaluating all 30 games...", file=sys.stderr)
        reports = asyncio.run(
            evaluate_all_games(
                difficulty=args.difficulty,
                episodes=args.episodes,
                solver_config=solver_config,
                verbose=args.verbose,
            )
        )

    # Build and format results
    result = build_benchmark_result(
        reports=reports,
        difficulty=args.difficulty,
        episodes_per_game=args.episodes,
        solver_config_desc=solver_desc,
    )

    if args.output == "json":
        print(format_json(result))
    elif args.output == "markdown":
        print(format_markdown(result))
    else:
        print(format_text(result))


if __name__ == "__main__":
    main()
