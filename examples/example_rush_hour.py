#!/usr/bin/env python3
"""
Example: Rush Hour Game Logic

Demonstrates the Rush Hour puzzle - slide vehicles on a 6x6 grid
to free the target car (X) to reach the exit.
Generates a puzzle, renders it, solves it step-by-step using hints,
and verifies completion.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.rush_hour import RushHourGame


async def main():
    print("=" * 60)
    print("Rush Hour Puzzle - Game Logic Example")
    print("=" * 60)

    # Create and generate puzzle
    game = RushHourGame("easy", seed=42)
    await game.generate_puzzle()

    print(f"\nDifficulty:    {game.difficulty.value}")
    print(f"Board size:    {game.size}x{game.size}")
    print(f"Vehicles:      {len(game.vehicles)}")
    print(f"Min solution:  {game.min_solution_moves} moves")
    print(f"Exit row:      {game.exit_row + 1}")
    print(f"Seed:          {game.seed}")

    # Show rules
    print(f"\nRules:\n{game.get_rules()}")

    # Render initial grid
    print(f"\nInitial board:\n{game.render_grid()}")

    # Show vehicles
    print("Vehicles:")
    for vid, v in sorted(game.vehicles.items()):
        orient = "horizontal" if v.orientation == "h" else "vertical"
        print(f"  {vid}: row {v.row+1}, col {v.col+1}, length {v.length}, {orient}")

    # Solve using hints
    print("\n--- Solving with hints ---")
    moves = 0
    max_moves = 100
    while not game.is_complete() and moves < max_moves:
        hint = await game.get_hint()
        if hint is None:
            print("No more hints available!")
            break

        hint_data, hint_message = hint
        vid, direction = hint_data
        result = await game.validate_move(vid, direction)
        moves += 1
        status = "OK" if result.success else result.message
        print(f"  Move {moves}: Move {vid} {direction} -> {status}")

        if result.game_over:
            print("  >>> Puzzle solved! Car X reached the exit!")
            break

        if not result.success:
            break

    # Show final state
    print(f"\nFinal board:\n{game.render_grid()}")
    print(f"Completed: {game.is_complete()}")
    print(f"Moves:     {moves}")
    print(f"Stats:     {game.get_stats()}")


if __name__ == "__main__":
    asyncio.run(main())
