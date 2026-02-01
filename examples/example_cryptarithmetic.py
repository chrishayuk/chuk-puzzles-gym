#!/usr/bin/env python3
"""
Example: Cryptarithmetic Game Logic

Demonstrates the Cryptarithmetic puzzle - assign unique digits to letters
so the arithmetic equation holds (e.g., SEND + MORE = MONEY).
Generates a puzzle, renders it, solves it step-by-step using hints,
and verifies completion.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.cryptarithmetic import CryptarithmeticGame


async def main():
    print("=" * 60)
    print("Cryptarithmetic Puzzle - Game Logic Example")
    print("=" * 60)

    # Create and generate puzzle
    game = CryptarithmeticGame("easy", seed=42)
    await game.generate_puzzle()

    print(f"\nDifficulty:      {game.difficulty.value}")
    print(f"Equation:        {game.equation}")
    print(f"Letters:         {', '.join(game.letters)}")
    print(f"Leading letters: {', '.join(sorted(game.leading_letters))}")
    print(f"Seed:            {game.seed}")

    # Show rules
    print(f"\nRules:\n{game.get_rules()}")

    # Render initial state
    print(f"\nInitial state:\n{game.render_grid()}")

    # Show pre-assigned letters
    if game.initial_mapping:
        print("Pre-assigned:")
        for letter, digit in sorted(game.initial_mapping.items()):
            print(f"  {letter} = {digit}")

    # Solve using hints
    print("\n--- Solving with hints ---")
    moves = 0
    while not game.is_complete():
        hint = await game.get_hint()
        if hint is None:
            print("No more hints available!")
            break

        hint_data, hint_message = hint
        letter, digit = hint_data
        result = await game.validate_move(letter, digit)
        moves += 1
        print(f"  Move {moves}: Assign {letter} = {digit} -> {'OK' if result.success else result.message}")

        if not result.success:
            break

    # Show final state
    print(f"\nFinal state:\n{game.render_grid()}")

    # Verify the solution
    print("\nVerification:")
    operand_vals = []
    for word in game.operands:
        val = int("".join(str(game.player_mapping[ch]) for ch in word))
        operand_vals.append(val)
        print(f"  {word} = {val}")
    result_val = int("".join(str(game.player_mapping[ch]) for ch in game.result_word))
    print(f"  {game.result_word} = {result_val}")
    print(
        f"  {' + '.join(str(v) for v in operand_vals)} = {sum(operand_vals)} {'==' if sum(operand_vals) == result_val else '!='} {result_val}"
    )

    print(f"\nCompleted: {game.is_complete()}")
    print(f"Moves:     {moves}")
    print(f"Stats:     {game.get_stats()}")


if __name__ == "__main__":
    asyncio.run(main())
