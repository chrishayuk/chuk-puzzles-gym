"""
Evaluation harness for puzzle-arcade-server.

Run benchmarks against puzzle games and collect metrics.

Usage:
    puzzle-arcade-eval sudoku --difficulty medium --episodes 10
    puzzle-arcade-eval --all --difficulty easy --episodes 5
    puzzle-arcade-eval kenken --seeds 1,2,3,4,5
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
from .models import MoveResult


@dataclass
class EpisodeResult:
    """Result of a single puzzle episode."""

    game: str
    difficulty: str
    seed: int
    status: str  # "solved", "failed", "timeout"
    moves_made: int
    invalid_moves: int
    hints_used: int
    wall_time_ms: int
    started_at: datetime
    ended_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "game": self.game,
            "difficulty": self.difficulty,
            "seed": self.seed,
            "status": self.status,
            "moves_made": self.moves_made,
            "invalid_moves": self.invalid_moves,
            "hints_used": self.hints_used,
            "wall_time_ms": self.wall_time_ms,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
        }


@dataclass
class EvaluationReport:
    """Summary report of evaluation run."""

    game: str
    difficulty: str
    episodes: list[EpisodeResult] = field(default_factory=list)

    @property
    def total_episodes(self) -> int:
        return len(self.episodes)

    @property
    def solved_count(self) -> int:
        return sum(1 for e in self.episodes if e.status == "solved")

    @property
    def solve_rate(self) -> float:
        if not self.episodes:
            return 0.0
        return self.solved_count / self.total_episodes

    @property
    def avg_moves(self) -> float:
        if not self.episodes:
            return 0.0
        return sum(e.moves_made for e in self.episodes) / self.total_episodes

    @property
    def avg_invalid_moves(self) -> float:
        if not self.episodes:
            return 0.0
        return sum(e.invalid_moves for e in self.episodes) / self.total_episodes

    @property
    def avg_time_ms(self) -> float:
        if not self.episodes:
            return 0.0
        return sum(e.wall_time_ms for e in self.episodes) / self.total_episodes

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# {self.game.title()} {self.difficulty.title()} Evaluation",
            "",
            f"**Episodes:** {self.total_episodes}",
            f"**Solved:** {self.solved_count}/{self.total_episodes} ({self.solve_rate:.1%})",
            f"**Avg Moves:** {self.avg_moves:.1f}",
            f"**Avg Invalid:** {self.avg_invalid_moves:.1f}",
            f"**Avg Time:** {self.avg_time_ms:.0f}ms",
            "",
            "## Episode Details",
            "",
            "| Seed | Status | Moves | Invalid | Time (ms) |",
            "|------|--------|-------|---------|-----------|",
        ]
        for e in self.episodes:
            lines.append(f"| {e.seed} | {e.status} | {e.moves_made} | {e.invalid_moves} | {e.wall_time_ms} |")
        return "\n".join(lines)

    def to_json(self) -> str:
        """Generate JSON report."""
        return json.dumps(
            {
                "game": self.game,
                "difficulty": self.difficulty,
                "summary": {
                    "total_episodes": self.total_episodes,
                    "solved_count": self.solved_count,
                    "solve_rate": self.solve_rate,
                    "avg_moves": self.avg_moves,
                    "avg_invalid_moves": self.avg_invalid_moves,
                    "avg_time_ms": self.avg_time_ms,
                },
                "episodes": [e.to_dict() for e in self.episodes],
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
                "moves_made",
                "invalid_moves",
                "hints_used",
                "wall_time_ms",
            ]
        )
        for e in self.episodes:
            writer.writerow(
                [
                    e.game,
                    e.difficulty,
                    e.seed,
                    e.status,
                    e.moves_made,
                    e.invalid_moves,
                    e.hints_used,
                    e.wall_time_ms,
                ]
            )
        return output.getvalue()

    def print_summary(self) -> None:
        """Print human-readable summary to stdout."""
        print(f"\n{self.game.title()} {self.difficulty.title()} Evaluation ({self.total_episodes} episodes)")
        print("=" * 50)
        print(f"Solved:     {self.solved_count}/{self.total_episodes} ({self.solve_rate:.1%})")
        print(f"Avg Moves:  {self.avg_moves:.1f}")
        print(f"Avg Invalid: {self.avg_invalid_moves:.1f}")
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
    use_hints: bool = True,
    max_moves: int = 1000,
) -> EpisodeResult:
    """Run a single puzzle episode using hints to solve."""
    game = game_class(difficulty=difficulty, seed=seed)
    await game.generate_puzzle()

    started_at = datetime.now()
    start_time = time.perf_counter()

    moves_made = 0
    invalid_moves = 0
    hints_used = 0
    status = "failed"
    max_time_sec = 30  # Timeout after 30 seconds per episode

    while moves_made < max_moves and not game.is_complete():
        # Check for timeout
        elapsed = time.perf_counter() - start_time
        if elapsed > max_time_sec:
            status = "timeout"
            break

        if use_hints:
            hint_result = await game.get_hint()
            if hint_result is None:
                # No hint available, puzzle might be complete or stuck
                break

            # Hints return (hint_data, hint_message) tuple
            # hint_data contains the actual move information
            hint_data, _hint_message = hint_result
            hints_used += 1

            # Apply the hint based on game type
            try:
                result = await _apply_hint(game, hint_data)
                if result.success:
                    moves_made += 1
                else:
                    invalid_moves += 1
                    # If we get too many consecutive invalid moves, break
                    if invalid_moves > 50:
                        break
            except (TypeError, ValueError, AttributeError, IndexError):
                invalid_moves += 1
                # Continue trying - some games may have tricky hint formats
                if invalid_moves > 50:
                    break
        else:
            # Without hints, we can't solve automatically
            break

    end_time = time.perf_counter()
    ended_at = datetime.now()
    wall_time_ms = int((end_time - start_time) * 1000)

    if game.is_complete():
        status = "solved"

    return EpisodeResult(
        game=game.name,
        difficulty=difficulty,
        seed=seed,
        status=status,
        moves_made=moves_made,
        invalid_moves=invalid_moves,
        hints_used=hints_used,
        wall_time_ms=wall_time_ms,
        started_at=started_at,
        ended_at=ended_at,
    )


async def evaluate_game(
    game_name: str,
    difficulty: str = "easy",
    episodes: int = 10,
    seeds: list[int] | None = None,
    use_hints: bool = True,
    max_moves: int = 1000,
    verbose: bool = False,
) -> EvaluationReport:
    """Run evaluation for a specific game."""
    if game_name not in AVAILABLE_GAMES:
        raise ValueError(f"Unknown game: {game_name}. Available: {list(AVAILABLE_GAMES.keys())}")

    game_class = AVAILABLE_GAMES[game_name]
    report = EvaluationReport(game=game_name, difficulty=difficulty)

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
            use_hints=use_hints,
            max_moves=max_moves,
        )
        report.episodes.append(result)

        if verbose:
            print(f"{result.status} ({result.moves_made} moves, {result.wall_time_ms}ms)")

    return report


async def evaluate_all_games(
    difficulty: str = "easy",
    episodes: int = 5,
    use_hints: bool = True,
    verbose: bool = False,
) -> dict[str, EvaluationReport]:
    """Run evaluation for all available games."""
    reports = {}

    for game_name in sorted(AVAILABLE_GAMES.keys()):
        if verbose:
            print(f"\nEvaluating {game_name}...")

        try:
            report = await evaluate_game(
                game_name=game_name,
                difficulty=difficulty,
                episodes=episodes,
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
        choices=["text", "json", "csv", "markdown"],
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

    # Run evaluation
    if args.all:
        reports = asyncio.run(
            evaluate_all_games(
                difficulty=args.difficulty,
                episodes=args.episodes,
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
                max_moves=args.max_moves,
                verbose=args.verbose,
            )
        )

        # Output results
        if args.output == "json":
            print(report.to_json())
        elif args.output == "csv":
            print(report.to_csv())
        elif args.output == "markdown":
            print(report.to_markdown())
        else:
            report.print_summary()


if __name__ == "__main__":
    main()
