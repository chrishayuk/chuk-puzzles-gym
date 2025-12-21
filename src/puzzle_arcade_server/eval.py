"""
Evaluation harness for puzzle-arcade-server.

Run benchmarks against puzzle games and collect metrics.

Usage:
    puzzle-arcade-eval sudoku --difficulty medium --episodes 10
    puzzle-arcade-eval --all --difficulty easy --episodes 5
    puzzle-arcade-eval kenken --seeds 1,2,3,4,5

    # Solver-free mode (pure model reasoning)
    puzzle-arcade-eval sudoku --solver-free

    # Solver-assisted with budget
    puzzle-arcade-eval sudoku --hint-budget 10 --hint-penalty 0.1
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from .games import AVAILABLE_GAMES
from .games._base import PuzzleGame
from .models import (
    DifficultyLevel,
    EpisodeResult,
    EpisodeStatus,
    MoveResult,
    SolverConfig,
)


@dataclass
class EvaluationReport:
    """Summary report of evaluation run.

    This wraps the Pydantic EvaluationSummary for backwards compatibility
    while providing additional output formatting methods.
    """

    game: str
    difficulty: str
    solver_config: SolverConfig = field(default_factory=SolverConfig)
    episodes: list[EpisodeResult] = field(default_factory=list)

    @property
    def total_episodes(self) -> int:
        return len(self.episodes)

    @property
    def solved_count(self) -> int:
        return sum(1 for e in self.episodes if e.success)

    @property
    def solve_rate(self) -> float:
        if not self.episodes:
            return 0.0
        return self.solved_count / self.total_episodes

    @property
    def avg_moves(self) -> float:
        if not self.episodes:
            return 0.0
        return sum(e.steps_taken for e in self.episodes) / self.total_episodes

    @property
    def avg_invalid_moves(self) -> float:
        if not self.episodes:
            return 0.0
        return sum(e.invalid_actions for e in self.episodes) / self.total_episodes

    @property
    def avg_time_ms(self) -> float:
        if not self.episodes:
            return 0.0
        return sum(e.wall_time_ms for e in self.episodes) / self.total_episodes

    @property
    def avg_efficiency(self) -> float:
        """Average efficiency score across solved episodes."""
        solved = [e for e in self.episodes if e.success]
        if not solved:
            return 0.0
        return sum(e.efficiency_score for e in solved) / len(solved)

    @property
    def avg_hints(self) -> float:
        if not self.episodes:
            return 0.0
        return sum(e.hints_used for e in self.episodes) / self.total_episodes

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# {self.game.title()} {self.difficulty.title()} Evaluation",
            "",
            f"**Episodes:** {self.total_episodes}",
            f"**Solved:** {self.solved_count}/{self.total_episodes} ({self.solve_rate:.1%})",
            f"**Avg Steps:** {self.avg_moves:.1f}",
            f"**Avg Invalid:** {self.avg_invalid_moves:.1f}",
            f"**Avg Hints:** {self.avg_hints:.1f}",
            f"**Avg Efficiency:** {self.avg_efficiency:.1%}",
            f"**Avg Time:** {self.avg_time_ms:.0f}ms",
            "",
            f"**Solver Config:** {'solver-free' if not self.solver_config.solver_allowed else f'budget={self.solver_config.hint_budget}, penalty={self.solver_config.hint_penalty}'}",
            "",
            "## Episode Details",
            "",
            "| Seed | Status | Steps | Invalid | Hints | Efficiency | Time (ms) |",
            "|------|--------|-------|---------|-------|------------|-----------|",
        ]
        for e in self.episodes:
            status = "solved" if e.success else e.status.value
            eff = f"{e.efficiency_score:.0%}" if e.success else "-"
            lines.append(
                f"| {e.seed} | {status} | {e.steps_taken} | {e.invalid_actions} | {e.hints_used} | {eff} | {e.wall_time_ms} |"
            )
        return "\n".join(lines)

    def to_json(self) -> str:
        """Generate JSON report."""
        return json.dumps(
            {
                "game": self.game,
                "difficulty": self.difficulty,
                "solver_config": {
                    "solver_allowed": self.solver_config.solver_allowed,
                    "hint_budget": self.solver_config.hint_budget,
                    "hint_penalty": self.solver_config.hint_penalty,
                },
                "summary": {
                    "total_episodes": self.total_episodes,
                    "solved_count": self.solved_count,
                    "solve_rate": self.solve_rate,
                    "avg_steps": self.avg_moves,
                    "avg_invalid": self.avg_invalid_moves,
                    "avg_hints": self.avg_hints,
                    "avg_efficiency": self.avg_efficiency,
                    "avg_time_ms": self.avg_time_ms,
                },
                "episodes": [e.to_summary_dict() for e in self.episodes],
            },
            indent=2,
        )

    def to_csv(self) -> str:
        """Generate CSV report."""
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "game",
                "difficulty",
                "seed",
                "status",
                "steps_taken",
                "invalid_actions",
                "hints_used",
                "efficiency",
                "wall_time_ms",
            ]
        )
        for e in self.episodes:
            writer.writerow(
                [
                    e.game,
                    e.difficulty.value,
                    e.seed,
                    e.status.value,
                    e.steps_taken,
                    e.invalid_actions,
                    e.hints_used,
                    f"{e.efficiency_score:.3f}",
                    e.wall_time_ms,
                ]
            )
        return output.getvalue()

    def print_summary(self) -> None:
        """Print human-readable summary to stdout."""
        print(f"\n{self.game.title()} {self.difficulty.title()} Evaluation ({self.total_episodes} episodes)")
        print("=" * 60)
        solver_mode = (
            "solver-free"
            if not self.solver_config.solver_allowed
            else f"solver-assisted (budget={self.solver_config.hint_budget})"
        )
        print(f"Mode:       {solver_mode}")
        print(f"Solved:     {self.solved_count}/{self.total_episodes} ({self.solve_rate:.1%})")
        print(f"Avg Steps:  {self.avg_moves:.1f}")
        print(f"Avg Invalid: {self.avg_invalid_moves:.1f}")
        print(f"Avg Hints:  {self.avg_hints:.1f}")
        print(f"Avg Efficiency: {self.avg_efficiency:.1%}")
        print(f"Avg Time:   {self.avg_time_ms:.0f}ms")


async def _apply_hint(game: PuzzleGame, hint_data: tuple) -> MoveResult:
    """Apply a hint to the game based on game type.

    Different games return hints in different formats:
    - Grid games (Sudoku, KenKen, etc.): (row, col, value)
    - Einstein: (house, attr, value)
    - Mastermind: (guess_sequence,)
    - Minesweeper: (row, col)
    - Lights Out: (row, col)
    - Knapsack: (item_id,)
    - Sokoban: (direction,)
    - Bridges: (r1, c1, r2, c2, count)
    - Shikaku: (r1, c1, r2, c2)
    - etc.
    """
    game_name = game.name.lower()

    # Grid-based number placement games
    if game_name in [
        "sudoku",
        "kenken",
        "kakuro",
        "killer sudoku",
        "futoshiki",
        "binary puzzle",
        "nonogram",
        "hidato",
        "fillomino",
    ]:
        if len(hint_data) >= 3:
            row, col, value = hint_data[0], hint_data[1], hint_data[2]
            return await game.validate_move(row, col, value)

    # Hitori - hint is (row, col, action) where action is "shade" or "unshade"
    if game_name in ["hitori"]:
        if len(hint_data) >= 3:
            row, col, action = hint_data[0], hint_data[1], hint_data[2]
            return await game.validate_move(row, col, action)

    # Star placement games
    if game_name in ["star battle"]:
        if len(hint_data) >= 2:
            row, col = hint_data[0], hint_data[1]
            return await game.validate_move(row, col, "place")

    # Tents game - hint is (row, col, action) where action is "place" or "remove"
    if game_name in ["tents and trees"]:
        if len(hint_data) >= 3:
            row, col, action = hint_data[0], hint_data[1], hint_data[2]
            return await game.validate_move(row, col, action)

    # Einstein puzzle - hint is (person, category, value)
    # validate_move expects (house, attr, value) where house is person name
    if game_name in ["einstein's puzzle", "einstein"]:
        if len(hint_data) >= 3:
            person, category, value = hint_data[0], hint_data[1], hint_data[2]
            return await game.validate_move(person, category, value)

    # Logic Grid puzzle - hint is (person, category, value)
    # validate_move expects (cat1, val1, cat2, val2, state)
    # Need to convert: connect person to category=value
    if game_name in ["logic grid"]:
        if len(hint_data) >= 3:
            person, category, value = hint_data[0], hint_data[1], hint_data[2]
            # Connect person to category=value means: cat1=person, val1=person, cat2=category, val2=value
            return await game.validate_move("person", person, category, value, True)

    # Mastermind - hint is now the complete secret code tuple
    # validate_move expects (*guess) - the full code
    if game_name in ["mastermind"]:
        # The hint provides the complete secret code
        return await game.validate_move(*hint_data)

    # Minesweeper
    if game_name in ["minesweeper"]:
        if len(hint_data) >= 2:
            row, col = hint_data[0], hint_data[1]
            action = hint_data[2] if len(hint_data) > 2 else "reveal"
            return await game.validate_move(row, col, action)

    # Lights Out - hint is (row, col), validate_move(row, col)
    # The issue is that pressing a cell toggles itself and neighbors
    # The hint gives one cell from the solution pattern, but we need to track presses
    if game_name in ["lights out"]:
        if len(hint_data) >= 2:
            row, col = hint_data[0], hint_data[1]
            return await game.validate_move(row, col)

    # Bridges
    if game_name in ["bridges"]:
        if len(hint_data) >= 5:
            r1, c1, r2, c2, count = hint_data[0], hint_data[1], hint_data[2], hint_data[3], hint_data[4]
            return await game.validate_move(r1, c1, r2, c2, count)

    # Shikaku
    if game_name in ["shikaku"]:
        if len(hint_data) >= 4:
            r1, c1, r2, c2 = hint_data[0], hint_data[1], hint_data[2], hint_data[3]
            return await game.validate_move(r1, c1, r2, c2)

    # Slitherlink
    if game_name in ["slitherlink"]:
        if len(hint_data) >= 4:
            r1, c1, r2, c2 = hint_data[0], hint_data[1], hint_data[2], hint_data[3]
            return await game.validate_move(r1, c1, r2, c2)

    # Nurikabe
    if game_name in ["nurikabe"]:
        if len(hint_data) >= 2:
            row, col = hint_data[0], hint_data[1]
            state = hint_data[2] if len(hint_data) > 2 else "sea"
            return await game.validate_move(row, col, state)

    # Knapsack - hint is (action, item_index) like ("select", 1)
    # validate_move expects (action, item_index)
    if game_name in ["knapsack"]:
        if len(hint_data) >= 2:
            action, item_index = hint_data[0], hint_data[1]
            return await game.validate_move(action, item_index)

    # Task Scheduler - hint is (task_id, worker, start_time)
    # validate_move expects (task_id, worker_id, start_time)
    if game_name in ["task scheduler"]:
        if len(hint_data) >= 3:
            task_id, worker, start_time = hint_data[0], hint_data[1], hint_data[2]
            return await game.validate_move(task_id, worker, start_time)

    # Sokoban - hint is a direction string like "up", "down", etc.
    # Note: Sokoban requires planning/search algorithms for reliable solving.
    # The greedy hint approach often gets stuck in loops.
    if game_name in ["sokoban"]:
        if hint_data:
            direction = hint_data if isinstance(hint_data, str) else hint_data
            return await game.validate_move(direction)

    # Generic fallback - try validate_move with hint args as tuple
    if isinstance(hint_data, tuple) and len(hint_data) >= 2:
        return await game.validate_move(*hint_data)

    # Single value fallback
    return await game.validate_move(hint_data)


async def run_episode(
    game_class: type[PuzzleGame],
    difficulty: str,
    seed: int,
    solver_config: SolverConfig | None = None,
    use_hints: bool = True,
    max_moves: int = 1000,
    timeout_sec: float = 30.0,
) -> EpisodeResult:
    """Run a single puzzle episode using hints to solve.

    Args:
        game_class: The puzzle game class to instantiate
        difficulty: Difficulty level (easy, medium, hard)
        seed: Random seed for reproducible puzzle generation
        solver_config: Configuration for solver/hint usage
        use_hints: Whether to use hints for auto-solving
        max_moves: Maximum moves before giving up
        timeout_sec: Maximum time in seconds before timeout

    Returns:
        EpisodeResult with all metrics and status
    """
    solver_config = solver_config or SolverConfig()
    game = game_class(difficulty=difficulty, seed=seed, solver_config=solver_config)
    await game.generate_puzzle()

    # Get optimal steps for efficiency calculation
    optimal_steps = game.optimal_steps

    started_at = datetime.now()
    start_time = time.perf_counter()

    steps_taken = 0
    invalid_actions = 0
    hints_used = 0
    retries = 0
    status = EpisodeStatus.FAILED

    while steps_taken < max_moves and not game.is_complete():
        # Check for timeout
        elapsed = time.perf_counter() - start_time
        if elapsed > timeout_sec:
            status = EpisodeStatus.TIMEOUT
            break

        if use_hints and game.can_use_hint():
            hint_result = await game.get_hint()
            if hint_result is None:
                # No hint available, puzzle might be complete or stuck
                break

            # Hints return (hint_data, hint_message) tuple
            hint_data, _hint_message = hint_result

            # Record hint usage (increments game.hints_used for budget tracking)
            game.record_hint()
            hints_used += 1

            # Apply the hint based on game type
            try:
                result = await _apply_hint(game, hint_data)
                if result.success:
                    steps_taken += 1
                else:
                    invalid_actions += 1
                    # If we get too many consecutive invalid moves, break
                    if invalid_actions > 50:
                        break
            except (TypeError, ValueError, AttributeError, IndexError):
                invalid_actions += 1
                if invalid_actions > 50:
                    break
        elif not use_hints:
            # Without hints, we can't solve automatically
            break
        else:
            # Hints exhausted (budget exceeded)
            break

    end_time = time.perf_counter()
    ended_at = datetime.now()
    wall_time_ms = int((end_time - start_time) * 1000)

    if game.is_complete():
        status = EpisodeStatus.SOLVED

    # Get retries from game if tracked
    retries = getattr(game, "retries", 0)

    return EpisodeResult(
        game=game.name,
        difficulty=DifficultyLevel(difficulty),
        seed=seed,
        started_at=started_at,
        ended_at=ended_at,
        wall_time_ms=wall_time_ms,
        status=status,
        steps_taken=steps_taken,
        invalid_actions=invalid_actions,
        hints_used=hints_used,
        retries=retries,
        optimal_steps=optimal_steps,
        solver_config=solver_config,
    )


async def evaluate_game(
    game_name: str,
    difficulty: str = "easy",
    episodes: int = 10,
    seeds: list[int] | None = None,
    solver_config: SolverConfig | None = None,
    use_hints: bool = True,
    max_moves: int = 1000,
    verbose: bool = False,
) -> EvaluationReport:
    """Run evaluation for a specific game.

    Args:
        game_name: Name of the game to evaluate
        difficulty: Difficulty level (easy, medium, hard)
        episodes: Number of episodes to run
        seeds: Specific seeds to use (generates random if None)
        solver_config: Configuration for solver/hint usage
        use_hints: Whether to use hints for auto-solving
        max_moves: Maximum moves per episode
        verbose: Print progress during evaluation

    Returns:
        EvaluationReport with all episode results
    """
    if game_name not in AVAILABLE_GAMES:
        raise ValueError(f"Unknown game: {game_name}. Available: {list(AVAILABLE_GAMES.keys())}")

    solver_config = solver_config or SolverConfig()
    game_class = AVAILABLE_GAMES[game_name]
    report = EvaluationReport(game=game_name, difficulty=difficulty, solver_config=solver_config)

    # Generate seeds if not provided
    if seeds is None:
        import random

        seeds = [random.randint(1, 2**31 - 1) for _ in range(episodes)]

    for i, seed in enumerate(seeds):
        if verbose:
            print(f"  Running episode {i + 1}/{len(seeds)} (seed={seed})...", end=" ", flush=True)

        result = await run_episode(
            game_class=game_class,  # type: ignore[type-abstract]
            difficulty=difficulty,
            seed=seed,
            solver_config=solver_config,
            use_hints=use_hints,
            max_moves=max_moves,
        )
        report.episodes.append(result)

        if verbose:
            status = "solved" if result.success else result.status.value
            eff = f", eff={result.efficiency_score:.0%}" if result.success else ""
            print(f"{status} ({result.steps_taken} steps{eff}, {result.wall_time_ms}ms)")

    return report


async def evaluate_all_games(
    difficulty: str = "easy",
    episodes: int = 5,
    solver_config: SolverConfig | None = None,
    use_hints: bool = True,
    verbose: bool = False,
) -> dict[str, EvaluationReport]:
    """Run evaluation for all available games.

    Args:
        difficulty: Difficulty level for all games
        episodes: Number of episodes per game
        solver_config: Configuration for solver/hint usage
        use_hints: Whether to use hints for auto-solving
        verbose: Print progress during evaluation

    Returns:
        Dict mapping game names to EvaluationReports
    """
    reports = {}

    for game_name in sorted(AVAILABLE_GAMES.keys()):
        if verbose:
            print(f"\nEvaluating {game_name}...")

        try:
            report = await evaluate_game(
                game_name=game_name,
                difficulty=difficulty,
                episodes=episodes,
                solver_config=solver_config,
                use_hints=use_hints,
                verbose=verbose,
            )
            reports[game_name] = report
        except Exception as e:
            if verbose:
                print(f"  Error: {e}")

    return reports


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Puzzle Arcade Evaluation Harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  puzzle-arcade-eval sudoku --difficulty medium --episodes 10
  puzzle-arcade-eval --all --difficulty easy --episodes 5
  puzzle-arcade-eval kenken --seeds 1,2,3,4,5 --output json
  puzzle-arcade-eval sudoku --output csv > results.csv

  # Solver configuration
  puzzle-arcade-eval sudoku --solver-free              # Pure model reasoning
  puzzle-arcade-eval sudoku --hint-budget 10           # Limited hints
  puzzle-arcade-eval sudoku --hint-penalty 0.1         # Penalize hint usage
        """,
    )

    parser.add_argument(
        "game",
        nargs="?",
        help="Game to evaluate (e.g., sudoku, kenken). Use --all for all games.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all available games",
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
        default=10,
        help="Number of episodes to run (default: 10)",
    )
    parser.add_argument(
        "--seeds",
        type=str,
        help="Comma-separated list of seeds to use (e.g., 1,2,3,4,5)",
    )
    parser.add_argument(
        "-o",
        "--output",
        choices=["text", "json", "csv", "markdown", "jsonl"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--max-moves",
        type=int,
        default=1000,
        help="Maximum moves per episode (default: 1000)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--list-games",
        action="store_true",
        help="List all available games and exit",
    )

    # Solver configuration arguments
    solver_group = parser.add_argument_group("solver configuration")
    solver_group.add_argument(
        "--solver-free",
        action="store_true",
        help="Disable solver hints (pure model reasoning mode)",
    )
    solver_group.add_argument(
        "--hint-budget",
        type=int,
        default=100,
        help="Maximum number of hints allowed (default: 100)",
    )
    solver_group.add_argument(
        "--hint-penalty",
        type=float,
        default=0.0,
        help="Score penalty per hint used, 0.0-1.0 (default: 0.0)",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the evaluation CLI."""
    args = parse_args()

    if args.list_games:
        print("Available games:")
        for name in sorted(AVAILABLE_GAMES.keys()):
            game = AVAILABLE_GAMES[name]("easy")  # type: ignore[abstract]
            print(f"  {name:20} - {game.description}")
        return

    if not args.game and not args.all:
        print("Error: Please specify a game or use --all")
        print("Use --list-games to see available games")
        sys.exit(1)

    # Parse seeds if provided
    seeds = None
    if args.seeds:
        seeds = [int(s.strip()) for s in args.seeds.split(",")]

    # Build solver configuration
    if args.solver_free:
        solver_config = SolverConfig.solver_free()
    else:
        solver_config = SolverConfig(
            solver_allowed=True,
            hint_budget=args.hint_budget,
            hint_penalty=args.hint_penalty,
        )

    # Run evaluation
    if args.all:
        reports = asyncio.run(
            evaluate_all_games(
                difficulty=args.difficulty,
                episodes=args.episodes,
                solver_config=solver_config,
                verbose=args.verbose,
            )
        )

        # Output results
        if args.output == "json":
            print(
                json.dumps(
                    {name: json.loads(r.to_json()) for name, r in reports.items()},
                    indent=2,
                )
            )
        elif args.output == "jsonl":
            # Stream one-line JSON per episode
            for report in reports.values():
                for episode in report.episodes:
                    print(episode.to_jsonl())
        elif args.output == "csv":
            # Combine all CSVs
            first = True
            for report in reports.values():
                csv_out = report.to_csv()
                if first:
                    print(csv_out, end="")
                    first = False
                else:
                    # Skip header for subsequent reports
                    lines = csv_out.split("\n")
                    print("\n".join(lines[1:]), end="")
        elif args.output == "markdown":
            for report in reports.values():
                print(report.to_markdown())
                print("\n---\n")
        else:
            print("\n" + "=" * 60)
            print("PUZZLE ARCADE EVALUATION SUMMARY")
            print("=" * 60)
            for report in reports.values():
                report.print_summary()
    else:
        report = asyncio.run(
            evaluate_game(
                game_name=args.game,
                difficulty=args.difficulty,
                episodes=args.episodes,
                seeds=seeds,
                solver_config=solver_config,
                max_moves=args.max_moves,
                verbose=args.verbose,
            )
        )

        # Output results
        if args.output == "json":
            print(report.to_json())
        elif args.output == "jsonl":
            for episode in report.episodes:
                print(episode.to_jsonl())
        elif args.output == "csv":
            print(report.to_csv())
        elif args.output == "markdown":
            print(report.to_markdown())
        else:
            report.print_summary()


if __name__ == "__main__":
    main()
