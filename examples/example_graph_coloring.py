#!/usr/bin/env python3
"""
Example: Graph Coloring Game Logic

Demonstrates the Graph Coloring puzzle - assign colors to nodes
so no two adjacent nodes share the same color.
Generates a puzzle, renders it, solves it step-by-step using hints,
and verifies completion.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.graph_coloring import GraphColoringGame

COLOR_NAMES = ["Red", "Blue", "Green", "Yellow", "Orange", "Purple", "Cyan", "Magenta"]


async def main():
    print("=" * 60)
    print("Graph Coloring Puzzle - Game Logic Example")
    print("=" * 60)

    # Create and generate puzzle
    game = GraphColoringGame("easy", seed=42)
    await game.generate_puzzle()

    print(f"\nDifficulty: {game.difficulty.value}")
    print(f"Nodes:      {game.num_nodes}")
    print(f"Colors:     {game.num_colors}")
    print(f"Edges:      {len(game.edges)}")
    print(f"Seed:       {game.seed}")

    # Show rules
    print(f"\nRules:\n{game.get_rules()}")

    # Render initial state
    print(f"\nInitial state:\n{game.render_grid()}")

    # Show pre-colored nodes
    if game.initial_coloring:
        print("Pre-colored nodes:")
        for node, color in sorted(game.initial_coloring.items()):
            name = COLOR_NAMES[color - 1] if color <= len(COLOR_NAMES) else str(color)
            print(f"  Node {node}: {name}")

    # Solve using hints
    print("\n--- Solving with hints ---")
    moves = 0
    while not game.is_complete():
        hint = await game.get_hint()
        if hint is None:
            print("No more hints available!")
            break

        hint_data, hint_message = hint
        node, color = hint_data
        color_name = COLOR_NAMES[color - 1] if color <= len(COLOR_NAMES) else str(color)
        result = await game.validate_move(node, color)
        moves += 1
        print(f"  Move {moves}: Color node {node} with {color_name} -> {'OK' if result.success else result.message}")

        if not result.success:
            break

    # Show final state
    print(f"\nFinal state:\n{game.render_grid()}")
    print(f"Completed: {game.is_complete()}")
    print(f"Moves:     {moves}")
    print(f"Stats:     {game.get_stats()}")


if __name__ == "__main__":
    asyncio.run(main())
