#!/usr/bin/env python3
"""
LLM Benchmark Agent for CHUK-R

Evaluates an LLM (e.g., gpt-4o-mini) on puzzle games using the CHUK-R benchmark.
The agent receives puzzle state and rules, then decides moves autonomously.

Requirements:
    pip install openai

Usage:
    # Set your API key
    export OPENAI_API_KEY="sk-..."

    # Run benchmark on a single game
    python examples/llm_benchmark_agent.py --game sudoku --episodes 3

    # Run on multiple games
    python examples/llm_benchmark_agent.py --games sudoku,binary,kenken --episodes 2

    # Run on a full family
    python examples/llm_benchmark_agent.py --family Logic --episodes 2

    # Use a different model
    python examples/llm_benchmark_agent.py --model gpt-4o --game sudoku
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.benchmark import (
    REASONING_FAMILIES,
    build_benchmark_result,
    format_json,
    format_text,
)
from chuk_puzzles_gym.eval import EvaluationReport
from chuk_puzzles_gym.games import AVAILABLE_GAMES
from chuk_puzzles_gym.gym_env import PuzzleEnv
from chuk_puzzles_gym.models import DifficultyLevel, EpisodeResult, EpisodeStatus

# Try to import openai
try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    sys.exit(1)


@dataclass
class LLMAgentConfig:
    """Configuration for the LLM agent."""

    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 256
    max_moves: int = 200
    max_invalid_streak: int = 10


@dataclass
class EpisodeStats:
    """Stats collected during an episode."""

    moves: list[dict[str, Any]] = field(default_factory=list)
    total_tokens: int = 0
    api_calls: int = 0


def build_system_prompt(game_name: str, rules: str, commands: str) -> str:
    """Build the system prompt for the LLM."""
    return f"""You are a puzzle-solving agent playing {game_name}.

RULES:
{rules}

COMMANDS:
{commands}

INSTRUCTIONS:
1. Analyze the current puzzle state carefully
2. Decide on ONE move to make
3. Respond with ONLY the command to execute (e.g., "place 1 2 5")
4. Do not explain your reasoning - just output the command
5. If you're stuck, try a different approach

IMPORTANT: Output ONLY the command, nothing else."""


def build_user_prompt(grid: str, stats: str, last_result: str | None = None) -> str:
    """Build the user prompt with current state."""
    prompt = f"""Current puzzle state:

{grid}

{stats}"""

    if last_result:
        prompt += f"\n\nResult of last move: {last_result}"

    prompt += "\n\nYour move:"
    return prompt


def extract_command(response: str) -> str:
    """Extract the command from LLM response."""
    # Clean up the response
    response = response.strip()

    # Remove markdown code blocks if present
    if response.startswith("```"):
        lines = response.split("\n")
        response = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        response = response.strip()

    # Take first line if multiple lines
    lines = response.strip().split("\n")
    command = lines[0].strip()

    # Remove quotes if wrapped
    if command.startswith('"') and command.endswith('"'):
        command = command[1:-1]
    if command.startswith("'") and command.endswith("'"):
        command = command[1:-1]

    return command


async def run_llm_episode(
    client: OpenAI,
    game_name: str,
    difficulty: str,
    seed: int,
    config: LLMAgentConfig,
    verbose: bool = False,
) -> tuple[EpisodeResult, EpisodeStats]:
    """Run a single episode with the LLM agent."""
    env = PuzzleEnv(game_name, difficulty=difficulty, seed=seed)
    obs, info = await env.reset()

    stats = EpisodeStats()
    started_at = datetime.now()

    # Get game info for prompts
    game = env.game
    rules = game.get_rules()
    commands = game.get_commands()
    system_prompt = build_system_prompt(game_name, rules, commands)

    if verbose:
        print(f"\n  Episode seed={seed}")
        print(f"  Optimal steps: {info.get('optimal_steps', 'unknown')}")

    valid_moves = 0
    invalid_moves = 0
    invalid_streak = 0
    last_result = None

    for step in range(config.max_moves):
        # Build prompt with current state
        grid = game.render_grid()
        game_stats = game.get_stats()
        user_prompt = build_user_prompt(grid, game_stats, last_result)

        # Call LLM
        try:
            response = client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            stats.api_calls += 1
            stats.total_tokens += response.usage.total_tokens if response.usage else 0

            command = extract_command(response.choices[0].message.content or "")
        except Exception as e:
            if verbose:
                print(f"    API error: {e}")
            last_result = f"API error: {e}"
            invalid_moves += 1
            invalid_streak += 1
            if invalid_streak >= config.max_invalid_streak:
                break
            continue

        if verbose:
            print(f"    Step {step + 1}: {command}")

        # Execute command
        obs, reward, terminated, truncated, info = await env.step(command)

        move_record = {
            "step": step,
            "command": command,
            "success": info.get("move_valid", False),
            "reward": reward,
        }
        stats.moves.append(move_record)

        if info.get("move_valid", False):
            valid_moves += 1
            invalid_streak = 0
            last_result = f"Move accepted: {command}"
        else:
            invalid_moves += 1
            invalid_streak += 1
            last_result = f"Invalid move: {info.get('message', 'rejected')}"
            if verbose:
                print(f"      Invalid: {info.get('message', '')}")

        if terminated:
            if verbose:
                print(f"    Solved in {valid_moves} moves!")
            break

        if invalid_streak >= config.max_invalid_streak:
            if verbose:
                print(f"    Giving up after {invalid_streak} consecutive invalid moves")
            break

    ended_at = datetime.now()
    env.close()

    # Determine status
    if obs.get("is_complete", False):
        status = EpisodeStatus.SOLVED
    elif step >= config.max_moves - 1:
        status = EpisodeStatus.TIMEOUT
    else:
        status = EpisodeStatus.FAILED

    # Build EpisodeResult
    result = EpisodeResult(
        game=game_name,
        difficulty=DifficultyLevel(difficulty),
        seed=seed,
        started_at=started_at,
        ended_at=ended_at,
        wall_time_ms=int((ended_at - started_at).total_seconds() * 1000),
        status=status,
        steps_taken=valid_moves,
        invalid_actions=invalid_moves,
        hints_used=0,
        optimal_steps=info.get("optimal_steps"),
        reasoning_metrics=env.game.get_reasoning_metrics() if hasattr(env.game, "get_reasoning_metrics") else None,
    )

    return result, stats


async def evaluate_game_with_llm(
    client: OpenAI,
    game_name: str,
    difficulty: str,
    episodes: int,
    config: LLMAgentConfig,
    verbose: bool = False,
) -> tuple[EvaluationReport, dict[str, Any]]:
    """Evaluate a game using the LLM agent."""
    report = EvaluationReport(game=game_name, difficulty=difficulty)
    total_stats = {"api_calls": 0, "total_tokens": 0}

    if verbose:
        print(f"\nEvaluating {game_name} ({difficulty})...")

    for i in range(episodes):
        seed = 42 + i
        result, stats = await run_llm_episode(
            client=client,
            game_name=game_name,
            difficulty=difficulty,
            seed=seed,
            config=config,
            verbose=verbose,
        )
        report.episodes.append(result)
        total_stats["api_calls"] += stats.api_calls
        total_stats["total_tokens"] += stats.total_tokens

    return report, total_stats


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run CHUK-R benchmark with an LLM agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--game",
        help="Single game to evaluate",
    )
    parser.add_argument(
        "--games",
        help="Comma-separated list of games",
    )
    parser.add_argument(
        "--family",
        choices=list(REASONING_FAMILIES.keys()),
        help="Evaluate all games in a family",
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
        default=3,
        help="Episodes per game (default: 3)",
    )
    parser.add_argument(
        "--max-moves",
        type=int,
        default=200,
        help="Max moves per episode (default: 200)",
    )
    parser.add_argument(
        "-o",
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show per-move details",
    )

    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    config = LLMAgentConfig(model=args.model, max_moves=args.max_moves)

    # Determine games to evaluate
    if args.game:
        game_list = [args.game]
    elif args.games:
        game_list = [g.strip() for g in args.games.split(",")]
    elif args.family:
        game_list = REASONING_FAMILIES[args.family]
    else:
        # Default: one game from each family for a quick test
        game_list = ["sudoku", "kenken", "mastermind", "sokoban"]

    # Validate games
    for g in game_list:
        if g not in AVAILABLE_GAMES:
            print(f"Error: Unknown game '{g}'")
            sys.exit(1)

    print(f"CHUK-R Benchmark with {args.model}")
    print(f"Games: {', '.join(game_list)}")
    print(f"Difficulty: {args.difficulty}, Episodes: {args.episodes}")
    print()

    # Run evaluations
    reports = {}
    total_api_calls = 0
    total_tokens = 0

    for game_name in game_list:
        report, stats = await evaluate_game_with_llm(
            client=client,
            game_name=game_name,
            difficulty=args.difficulty,
            episodes=args.episodes,
            config=config,
            verbose=args.verbose,
        )
        reports[game_name] = report
        total_api_calls += stats["api_calls"]
        total_tokens += stats["total_tokens"]

        if not args.verbose:
            solved = sum(1 for e in report.episodes if e.success)
            print(f"  {game_name}: {solved}/{args.episodes} solved")

    # Build CHUK-R result
    result = build_benchmark_result(
        reports=reports,
        difficulty=args.difficulty,
        episodes_per_game=args.episodes,
        solver_config_desc=f"LLM: {args.model}",
    )

    # Output
    if args.output == "json":
        output = json.loads(format_json(result))
        output["llm_stats"] = {
            "model": args.model,
            "api_calls": total_api_calls,
            "total_tokens": total_tokens,
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_text(result))
        print("\nLLM Stats:")
        print(f"  Model:       {args.model}")
        print(f"  API calls:   {total_api_calls}")
        print(f"  Total tokens: {total_tokens}")


if __name__ == "__main__":
    asyncio.run(main())
