"""
Dataset export for puzzle games.

Generates JSONL datasets for training and benchmarking.
Includes step-by-step solution traces for teacher-forcing training.

Uses chuk-gym-core's Problem schema and JSONLExporter for consistency
with chuk-math-gym's export format.
"""

import asyncio
from pathlib import Path
from typing import Any, TextIO

from chuk_gym_core import DifficultyLevel, DifficultyProfile, JSONLExporter, Problem

from chuk_puzzles_gym.games import AVAILABLE_GAMES
from chuk_puzzles_gym.games._base import PuzzleGame
from chuk_puzzles_gym.models import SolverConfig
from chuk_puzzles_gym.trace import TraceGenerator


class DatasetExporter:
    """
    Export puzzle problems to JSONL format for training.

    Uses chuk-gym-core's Problem schema and JSONLExporter for
    consistency with chuk-math-gym's export format.

    Usage:
        exporter = DatasetExporter("puzzles.jsonl")

        # Generate problems for all games
        await exporter.export_all_games(
            count_per_game=100,
            difficulties=[DifficultyLevel.EASY, DifficultyLevel.MEDIUM],
        )

        # Or specific game
        await exporter.export_game(
            game_name="sudoku",
            count=1000,
            difficulty=DifficultyLevel.HARD,
        )

        exporter.close()
    """

    def __init__(
        self,
        output: str | Path | TextIO,
        include_solution: bool = True,
        include_trace: bool = True,
    ):
        """
        Initialize the exporter.

        Args:
            output: Output file path or file handle
            include_solution: Whether to include canonical solutions
            include_trace: Whether to include step-by-step traces
        """
        self.include_solution = include_solution
        self._trace_generator = TraceGenerator()

        # Use core JSONLExporter for consistent output format
        self._exporter = JSONLExporter(
            output=output,
            include_trace=include_trace,
        )

    def __enter__(self) -> "DatasetExporter":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the output file."""
        self._exporter.close()

    async def export_game(
        self,
        game_name: str,
        count: int,
        difficulty: DifficultyLevel | str = DifficultyLevel.MEDIUM,
        start_seed: int = 0,
        solver_config: SolverConfig | None = None,
    ) -> int:
        """
        Export problems for a specific game.

        Args:
            game_name: Name of the puzzle game
            count: Number of problems to generate
            difficulty: Difficulty level
            start_seed: Starting seed for reproducibility
            solver_config: Solver configuration

        Returns:
            Number of problems exported
        """
        if game_name not in AVAILABLE_GAMES:
            raise ValueError(f"Unknown game: {game_name}")

        game_class = AVAILABLE_GAMES[game_name]
        if isinstance(difficulty, str):
            difficulty = DifficultyLevel(difficulty)

        exported = 0
        for i in range(count):
            seed = start_seed + i

            # Create game and generate puzzle (game_class is always a concrete subclass)
            game = game_class(  # type: ignore[abstract]
                difficulty=difficulty,
                seed=seed,
                solver_config=solver_config or SolverConfig(),
            )
            await game.generate_puzzle()

            # Generate solution trace
            trace = self._trace_generator.generate(game)

            # Convert game to Problem and export using core exporter
            problem = self._game_to_problem(game, seed, difficulty)
            self._exporter.write_problem(problem, trace)
            exported += 1

        return exported

    async def export_all_games(
        self,
        count_per_game: int,
        difficulties: list[DifficultyLevel] | None = None,
        start_seed: int = 0,
        games: list[str] | None = None,
    ) -> int:
        """
        Export problems for multiple games.

        Args:
            count_per_game: Number of problems per game/difficulty combo
            difficulties: Difficulty levels to include (default: all)
            start_seed: Starting seed
            games: Specific games to include (default: all)

        Returns:
            Total number of problems exported
        """
        if difficulties is None:
            difficulties = [
                DifficultyLevel.EASY,
                DifficultyLevel.MEDIUM,
                DifficultyLevel.HARD,
            ]

        game_names = games or list(AVAILABLE_GAMES.keys())
        total = 0

        for game_name in game_names:
            for difficulty in difficulties:
                count = await self.export_game(
                    game_name=game_name,
                    count=count_per_game,
                    difficulty=difficulty,
                    start_seed=start_seed + total,
                )
                total += count

        return total

    def _game_to_problem(
        self,
        game: PuzzleGame,
        seed: int,
        difficulty: DifficultyLevel,
    ) -> Problem:
        """Convert a game instance to a chuk-gym-core Problem.

        Uses the core Problem schema for consistency with chuk-math-gym.
        """
        domain = game.name.lower().replace(" ", "_")
        profile = game.difficulty_profile

        # Build gold_answer from canonical solution if available
        gold_answer = None
        if self.include_solution:
            canonical = game.canonical_solution
            if canonical:
                gold_answer = str(canonical)

        # Build reasoning tags from complexity profile
        complexity_profile = game.complexity_profile
        reasoning_type = complexity_profile.get("reasoning_type", "deductive")
        search_space = complexity_profile.get("search_space", "medium")
        tags = [domain, difficulty.value, f"reasoning:{reasoning_type}", f"search:{search_space}"]

        # Create Problem using core schema
        return Problem(
            # Identity
            id=Problem.generate_id(domain, difficulty, seed),
            seed=seed,
            # Classification
            domain=domain,
            difficulty=difficulty,
            # Content
            prompt=f"{game.name}: {game.description}\n\n{game.get_rules()}\n\n{game.render_grid()}",
            initial_state=game.grid if hasattr(game, "grid") else None,
            gold_answer=gold_answer,
            # Constraint metadata
            constraint_types=game.constraint_types,
            business_analogies=game.business_analogies,
            # Difficulty profile
            difficulty_profile=DifficultyProfile(
                logic_depth=profile.logic_depth,
                branching_factor=profile.branching_factor,
                state_observability=profile.state_observability,
                constraint_density=profile.constraint_density,
            ),
            # Metadata
            operation_count=game.optimal_steps,
            tags=tags,
        )

    @property
    def count(self) -> int:
        """Number of records written."""
        return self._exporter.count

    def flush(self) -> None:
        """Flush the output buffer."""
        self._exporter.flush()


async def generate_dataset(
    output_path: str | Path,
    games: list[str] | None = None,
    count_per_game: int = 100,
    difficulties: list[str] | None = None,
    start_seed: int = 0,
    include_trace: bool = True,
) -> int:
    """
    Generate a complete puzzle dataset.

    Args:
        output_path: Path to output JSONL file
        games: Games to include (default: all)
        count_per_game: Problems per game/difficulty
        difficulties: Difficulties to include (default: easy, medium, hard)
        start_seed: Starting seed
        include_trace: Whether to include step-by-step traces

    Returns:
        Total number of problems generated
    """
    diff_levels = None
    if difficulties:
        diff_levels = [DifficultyLevel(d) for d in difficulties]

    with DatasetExporter(
        output_path,
        include_trace=include_trace,
    ) as exporter:
        total = await exporter.export_all_games(
            count_per_game=count_per_game,
            difficulties=diff_levels,
            start_seed=start_seed,
            games=games,
        )

    return total


async def export_problems(
    game_name: str,
    count: int,
    output_path: str | Path,
    difficulty: str = "medium",
    start_seed: int = 0,
) -> int:
    """
    Export problems for a single game.

    Args:
        game_name: Name of the puzzle game
        count: Number of problems
        output_path: Path to output JSONL file
        difficulty: Difficulty level
        start_seed: Starting seed

    Returns:
        Number of problems exported
    """
    with DatasetExporter(output_path) as exporter:
        exported = await exporter.export_game(
            game_name=game_name,
            count=count,
            difficulty=DifficultyLevel(difficulty),
            start_seed=start_seed,
        )

    return exported


def main() -> None:
    """CLI entry point for dataset generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate puzzle datasets for training and benchmarking")
    parser.add_argument(
        "-o",
        "--output",
        default="puzzles.jsonl",
        help="Output file path (default: puzzles.jsonl)",
    )
    parser.add_argument(
        "-g",
        "--games",
        nargs="+",
        help="Games to include (default: all)",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=100,
        help="Problems per game/difficulty (default: 100)",
    )
    parser.add_argument(
        "-d",
        "--difficulties",
        nargs="+",
        default=["easy", "medium", "hard"],
        help="Difficulties to include",
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=0,
        help="Starting seed (default: 0)",
    )
    parser.add_argument(
        "--no-trace",
        action="store_true",
        help="Exclude step-by-step solution traces",
    )
    parser.add_argument(
        "--list-games",
        action="store_true",
        help="List available games and exit",
    )

    args = parser.parse_args()

    if args.list_games:
        print("Available games:")
        for name in sorted(AVAILABLE_GAMES.keys()):
            game_class = AVAILABLE_GAMES[name]
            # Create instance to get description (game_class is always a concrete subclass)
            game = game_class()  # type: ignore[abstract]
            print(f"  {name}: {game.description}")
        return

    total = asyncio.run(
        generate_dataset(
            output_path=args.output,
            games=args.games,
            count_per_game=args.count,
            difficulties=args.difficulties,
            start_seed=args.seed,
            include_trace=not args.no_trace,
        )
    )

    print(f"Generated {total} problems -> {args.output}")


if __name__ == "__main__":
    main()
