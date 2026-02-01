#!/usr/bin/env python3
"""
Example: Skyscrapers Game Logic

Demonstrates the Skyscrapers puzzle - a Latin square with visibility clues.
Generates a puzzle, renders it, solves it step-by-step using hints,
and verifies completion.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.skyscrapers import SkyscrapersGame


async def main():
    print("=" * 60)
    print("Skyscrapers Puzzle - Game Logic Example")
    print("=" * 60)

    # Create and generate puzzle
    game = SkyscrapersGame("easy", seed=42)
    await game.generate_puzzle()

    print(f"\nDifficulty: {game.difficulty.value}")
    print(f"Grid size:  {game.size}x{game.size}")
    print(f"Seed:       {game.seed}")

    # Show rules
    print(f"\nRules:\n{game.get_rules()}")

    # Render initial grid
    print(f"\nInitial grid:\n{game.render_grid()}")

    # Show clues
    print(f"Top clues:    {game.clues['top']}")
    print(f"Bottom clues: {game.clues['bottom']}")
    print(f"Left clues:   {game.clues['left']}")
    print(f"Right clues:  {game.clues['right']}")

    # Solve using hints
    print("\n--- Solving with hints ---")
    moves = 0
    while not game.is_complete():
        hint = await game.get_hint()
        if hint is None:
            print("No more hints available!")
            break

        hint_data, hint_message = hint
        row, col, val = hint_data
        result = await game.validate_move(row, col, val)
        moves += 1
        print(f"  Move {moves}: Place {val} at row {row}, col {col} -> {'OK' if result.success else result.message}")

        if not result.success:
            break

    # Show final state
    print(f"\nFinal grid:\n{game.render_grid()}")
    print(f"Completed: {game.is_complete()}")
    print(f"Moves:     {moves}")
    print(f"Stats:     {game.get_stats()}")


if __name__ == "__main__":
    asyncio.run(main())
