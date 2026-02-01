#!/usr/bin/env python3
"""
Example: N-Queens Game Logic

Demonstrates the N-Queens puzzle - place N queens on an NxN board
with no two queens attacking each other.
Generates a puzzle, renders it, solves it step-by-step using hints,
and verifies completion.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.nqueens import NQueensGame


async def main():
    print("=" * 60)
    print("N-Queens Puzzle - Game Logic Example")
    print("=" * 60)

    # Create and generate puzzle
    game = NQueensGame("easy", seed=42)
    await game.generate_puzzle()

    print(f"\nDifficulty:   {game.difficulty.value}")
    print(f"Board size:   {game.size}x{game.size}")
    print(f"Pre-placed:   {game.config.pre_placed} queens")
    print(f"Seed:         {game.seed}")

    # Show rules
    print(f"\nRules:\n{game.get_rules()}")

    # Render initial grid
    print(f"\nInitial board:\n{game.render_grid()}")

    # Count pre-placed queens
    pre_placed = sum(1 for r in range(game.size) for c in range(game.size) if game.initial_grid[r][c] == 1)
    print(f"Queens already placed: {pre_placed}")

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
        print(f"  Move {moves}: Place queen at row {row}, col {col} -> {'OK' if result.success else result.message}")

        if not result.success:
            break

    # Show final state
    print(f"\nFinal board:\n{game.render_grid()}")
    print(f"Completed: {game.is_complete()}")
    print(f"Moves:     {moves}")
    print(f"Stats:     {game.get_stats()}")


if __name__ == "__main__":
    asyncio.run(main())
