#!/usr/bin/env python3
"""
Example: Numberlink Game Logic

Demonstrates the Numberlink puzzle - connect numbered pairs with
non-crossing paths that fill the entire grid.
Generates a puzzle, renders it, solves it step-by-step using hints,
and verifies completion.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.numberlink import NumberlinkGame


async def main():
    print("=" * 60)
    print("Numberlink Puzzle - Game Logic Example")
    print("=" * 60)

    # Create and generate puzzle
    game = NumberlinkGame("easy", seed=42)
    await game.generate_puzzle()

    print(f"\nDifficulty: {game.difficulty.value}")
    print(f"Grid size:  {game.size}x{game.size}")
    print(f"Pairs:      {game.num_pairs}")
    print(f"Seed:       {game.seed}")

    # Show rules
    print(f"\nRules:\n{game.get_rules()}")

    # Render initial grid
    print(f"\nInitial grid:\n{game.render_grid()}")

    # Show endpoints
    for pair_id, pts in sorted(game.endpoints.items()):
        (r1, c1), (r2, c2) = pts
        print(f"  Pair {pair_id}: ({r1+1},{c1+1}) <-> ({r2+1},{c2+1})")

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
        if moves <= 10 or game.is_complete():
            print(f"  Move {moves}: Place {val} at row {row}, col {col} -> {'OK' if result.success else result.message}")
        elif moves == 11:
            print("  ... (continuing)")

        if not result.success:
            break

    # Show final state
    print(f"\nFinal grid:\n{game.render_grid()}")
    print(f"Completed: {game.is_complete()}")
    print(f"Moves:     {moves}")
    print(f"Stats:     {game.get_stats()}")


if __name__ == "__main__":
    asyncio.run(main())
