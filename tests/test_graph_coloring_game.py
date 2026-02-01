"""Tests for Graph Coloring puzzle game."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.graph_coloring import GraphColoringCommandHandler, GraphColoringGame
from chuk_puzzles_gym.models import GameCommand


class TestGraphColoringGame:
    """Test suite for GraphColoringGame."""

    async def test_initialization(self):
        game = GraphColoringGame("easy")
        assert game.num_nodes == 6
        assert game.num_colors == 3
        assert game.name == "Graph Coloring"

    @pytest.mark.parametrize(
        "difficulty,expected_nodes,expected_colors",
        [("easy", 6, 3), ("medium", 10, 4), ("hard", 15, 4)],
    )
    async def test_difficulty_levels(self, difficulty, expected_nodes, expected_colors):
        game = GraphColoringGame(difficulty, seed=42)
        await game.generate_puzzle()
        assert game.num_nodes == expected_nodes
        assert game.num_colors == expected_colors

    async def test_generate_puzzle(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        assert game.game_started
        assert len(game.edges) > 0
        # All nodes should be in solution
        for node in range(1, game.num_nodes + 1):
            assert node in game.solution
            assert 1 <= game.solution[node] <= game.num_colors

    async def test_graph_connected(self):
        """Verify the generated graph is connected."""
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        from collections import deque

        visited = set()
        queue = deque([1])
        visited.add(1)
        while queue:
            node = queue.popleft()
            for neighbor in game.adjacency.get(node, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        assert len(visited) == game.num_nodes

    async def test_solution_valid(self):
        """Verify the solution has no adjacent same-color conflicts."""
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        for i, j in game.edges:
            assert game.solution[i] != game.solution[j], f"Nodes {i} and {j} have same color in solution"

    async def test_color_node_valid(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        # Find an uncolored node and color it with solution color
        for node in range(1, game.num_nodes + 1):
            if game.coloring.get(node, 0) == 0:
                color = game.solution[node]
                result = await game.validate_move(node, color)
                assert result.success
                assert game.coloring[node] == color
                return

    async def test_color_node_conflict(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        # Color two adjacent nodes with the same color
        for i, j in game.edges:
            if i not in game.initial_coloring and j not in game.initial_coloring:
                # Find a color that works for node i (no neighbor conflict)
                for color in range(1, game.num_colors + 1):
                    has_conflict = False
                    for neighbor in game.adjacency.get(i, set()):
                        if game.coloring.get(neighbor, 0) == color:
                            has_conflict = True
                            break
                    if not has_conflict:
                        result_i = await game.validate_move(i, color)
                        if result_i.success:
                            result = await game.validate_move(j, color)
                            assert not result.success
                            assert "conflict" in result.message.lower() or "adjacent" in result.message.lower()
                            return
                # Clear i if we colored it
                await game.validate_move(i, 0)

    async def test_cannot_modify_pre_colored(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        for node in game.initial_coloring:
            result = await game.validate_move(node, 1)
            assert not result.success
            return

    async def test_clear_color(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        for node in range(1, game.num_nodes + 1):
            if game.coloring.get(node, 0) == 0:
                await game.validate_move(node, game.solution[node])
                result = await game.validate_move(node, 0)
                assert result.success
                assert game.coloring[node] == 0
                return

    async def test_invalid_node(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        result = await game.validate_move(0, 1)
        assert not result.success
        result = await game.validate_move(game.num_nodes + 1, 1)
        assert not result.success

    async def test_invalid_color(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        for node in range(1, game.num_nodes + 1):
            if game.coloring.get(node, 0) == 0:
                result = await game.validate_move(node, game.num_colors + 1)
                assert not result.success
                return

    async def test_is_complete(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        assert not game.is_complete()
        # Set all colors to solution
        for node in range(1, game.num_nodes + 1):
            game.coloring[node] = game.solution[node]
        assert game.is_complete()

    async def test_get_hint(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        hint = await game.get_hint()
        assert hint is not None
        hint_data, hint_message = hint
        node, color = hint_data
        assert game.solution[node] == color

    async def test_render_grid(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        rendered = game.render_grid()
        assert isinstance(rendered, str)
        assert "adj:" in rendered

    async def test_get_rules(self):
        game = GraphColoringGame("easy")
        assert "color" in game.get_rules().lower()

    async def test_get_commands(self):
        game = GraphColoringGame("easy")
        assert "place" in game.get_commands().lower()

    async def test_constraint_types(self):
        game = GraphColoringGame("easy")
        assert "graph_coloring" in game.constraint_types

    async def test_business_analogies(self):
        game = GraphColoringGame("easy")
        assert len(game.business_analogies) > 0

    async def test_complexity_profile(self):
        game = GraphColoringGame("easy")
        profile = game.complexity_profile
        assert "reasoning_type" in profile

    async def test_deterministic_seeding(self):
        game1 = GraphColoringGame("easy", seed=12345)
        await game1.generate_puzzle()
        game2 = GraphColoringGame("easy", seed=12345)
        await game2.generate_puzzle()
        assert game1.grid == game2.grid
        assert game1.solution == game2.solution
        assert game1.edges == game2.edges

    async def test_command_handler_place(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        handler = GraphColoringCommandHandler(game)
        assert GameCommand.PLACE in handler.supported_commands
        # Find uncolored node
        for node in range(1, game.num_nodes + 1):
            if game.coloring.get(node, 0) == 0:
                color = game.solution[node]
                result = await handler.handle_command(GameCommand.PLACE, [str(node), str(color)])
                assert result.result.success
                return

    async def test_command_handler_clear(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        handler = GraphColoringCommandHandler(game)
        assert GameCommand.CLEAR in handler.supported_commands
        for node in range(1, game.num_nodes + 1):
            if game.coloring.get(node, 0) == 0:
                await game.validate_move(node, game.solution[node])
                result = await handler.handle_command(GameCommand.CLEAR, [str(node)])
                assert result.result.success
                return

    async def test_command_handler_bad_args(self):
        game = GraphColoringGame("easy", seed=42)
        await game.generate_puzzle()
        handler = GraphColoringCommandHandler(game)
        result = await handler.handle_command(GameCommand.PLACE, ["1"])
        assert not result.result.success
