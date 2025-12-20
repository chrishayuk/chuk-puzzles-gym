"""Tests for Knapsack puzzle game."""

import pytest

from puzzle_arcade_server.games.knapsack import KnapsackGame
from puzzle_arcade_server.games.knapsack.models import Item


class TestKnapsackGame:
    """Test suite for Knapsack game."""

    def test_initialization_easy(self):
        """Test game initialization with easy difficulty."""
        game = KnapsackGame("easy")
        assert game.difficulty == "easy"
        assert game.config.num_items == 5
        assert game.name == "Knapsack"
        assert "optimize" in game.description.lower()

    def test_initialization_medium(self):
        """Test game initialization with medium difficulty."""
        game = KnapsackGame("medium")
        assert game.config.num_items == 8

    def test_initialization_hard(self):
        """Test game initialization with hard difficulty."""
        game = KnapsackGame("hard")
        assert game.config.num_items == 12

    async def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = KnapsackGame("easy")
        await game.generate_puzzle()

        assert game.game_started is True
        assert len(game.items) == 5
        assert game.capacity > 0
        assert game.optimal_value > 0
        assert len(game.optimal_selection) == 5
        assert all(not selected for selected in game.selection)

    async def test_items_have_valid_attributes(self):
        """Test that generated items have valid weights and values."""
        game = KnapsackGame("easy")
        await game.generate_puzzle()

        for item in game.items:
            assert item.name
            assert item.weight > 0
            assert item.value > 0

    async def test_select_item_success(self):
        """Test successfully selecting an item."""
        game = KnapsackGame("easy")
        game.items = [
            Item(name="Item1", weight=5, value=50),
            Item(name="Item2", weight=3, value=30),
        ]
        game.capacity = 10
        game.selection = [False, False]
        game.game_started = True

        result = await game.validate_move("select", 1)
        assert result.success is True
        assert game.selection[0] is True
        assert "Item1" in result.message

    async def test_select_already_selected(self):
        """Test selecting an already selected item."""
        game = KnapsackGame("easy")
        game.items = [Item(name="Item1", weight=5, value=50)]
        game.capacity = 10
        game.selection = [True]
        game.game_started = True

        result = await game.validate_move("select", 1)
        assert result.success is False
        assert "already selected" in result.message.lower()

    async def test_select_exceeds_capacity(self):
        """Test selecting item that exceeds capacity."""
        game = KnapsackGame("easy")
        game.items = [
            Item(name="Item1", weight=5, value=50),
            Item(name="Item2", weight=8, value=80),
        ]
        game.capacity = 10
        game.selection = [True, False]
        game.game_started = True

        result = await game.validate_move("select", 2)
        assert result.success is False
        assert "exceed capacity" in result.message.lower()

    async def test_deselect_item_success(self):
        """Test successfully deselecting an item."""
        game = KnapsackGame("easy")
        game.items = [Item(name="Item1", weight=5, value=50)]
        game.capacity = 10
        game.selection = [True]
        game.game_started = True

        result = await game.validate_move("deselect", 1)
        assert result.success is True
        assert game.selection[0] is False

    async def test_deselect_not_selected(self):
        """Test deselecting an item that's not selected."""
        game = KnapsackGame("easy")
        game.items = [Item(name="Item1", weight=5, value=50)]
        game.capacity = 10
        game.selection = [False]
        game.game_started = True

        result = await game.validate_move("deselect", 1)
        assert result.success is False
        assert "not currently selected" in result.message.lower()

    async def test_invalid_item_index(self):
        """Test with invalid item index."""
        game = KnapsackGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move("select", 0)
        assert result.success is False
        assert "Invalid item" in result.message

        result = await game.validate_move("select", 10)
        assert result.success is False
        assert "Invalid item" in result.message

    async def test_invalid_action(self):
        """Test with invalid action."""
        game = KnapsackGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move("invalid", 1)
        assert result.success is False
        assert "Invalid action" in result.message

    def test_get_current_weight(self):
        """Test current weight calculation."""
        game = KnapsackGame("easy")
        game.items = [
            Item(name="Item1", weight=5, value=50),
            Item(name="Item2", weight=3, value=30),
        ]
        game.selection = [True, True]

        assert game._get_current_weight() == 8

    def test_get_current_value(self):
        """Test current value calculation."""
        game = KnapsackGame("easy")
        game.items = [
            Item(name="Item1", weight=5, value=50),
            Item(name="Item2", weight=3, value=30),
        ]
        game.selection = [True, True]

        assert game._get_current_value() == 80

    async def test_is_complete_optimal(self):
        """Test completion check when optimal solution is found."""
        game = KnapsackGame("easy")
        await game.generate_puzzle()

        # Set selection to optimal
        game.selection = game.optimal_selection.copy()

        assert game.is_complete() is True

    async def test_is_complete_not_optimal(self):
        """Test completion check when solution is not optimal."""
        game = KnapsackGame("easy")
        await game.generate_puzzle()

        # Set all to False (not optimal)
        game.selection = [False] * len(game.items)

        assert game.is_complete() is False

    async def test_get_hint_select(self):
        """Test hint for selecting an item."""
        game = KnapsackGame("easy")
        game.items = [Item(name="Item1", weight=5, value=50)]
        game.optimal_selection = [True]
        game.selection = [False]

        result = await game.get_hint()
        hint_data, hint_message = result
        assert hint_data == ("select", 1)
        assert "select" in hint_message.lower()

    async def test_get_hint_deselect(self):
        """Test hint for deselecting an item."""
        game = KnapsackGame("easy")
        game.items = [Item(name="Item1", weight=5, value=50)]
        game.optimal_selection = [False]
        game.selection = [True]

        result = await game.get_hint()
        hint_data, hint_message = result
        assert hint_data == ("deselect", 1)
        assert "deselect" in hint_message.lower()

    async def test_get_hint_optimal(self):
        """Test hint when already at optimal."""
        game = KnapsackGame("easy")
        game.items = [Item(name="Item1", weight=5, value=50)]
        game.optimal_selection = [True]
        game.selection = [True]

        result = await game.get_hint()
        assert result is None

    async def test_render_grid(self):
        """Test grid rendering."""
        game = KnapsackGame("easy")
        await game.generate_puzzle()

        grid_str = game.render_grid()
        assert "Capacity" in grid_str
        assert "Weight" in grid_str
        assert "Value" in grid_str
        assert "Optimal" in grid_str

    async def test_get_rules(self):
        """Test rules retrieval."""
        game = KnapsackGame("easy")
        await game.generate_puzzle()

        rules = game.get_rules()
        assert "KNAPSACK" in rules
        assert "capacity" in rules.lower()
        assert "optimize" in rules.lower() or "optimal" in rules.lower()

    def test_get_commands(self):
        """Test commands retrieval."""
        game = KnapsackGame("easy")
        commands = game.get_commands()

        assert "select" in commands.lower()
        assert "deselect" in commands.lower()
        assert "show" in commands.lower()

    async def test_get_stats(self):
        """Test statistics retrieval."""
        game = KnapsackGame("easy")
        await game.generate_puzzle()

        stats = game.get_stats()
        assert "Moves" in stats
        assert "Value" in stats
        assert "Weight" in stats

    async def test_moves_counter(self):
        """Test that moves are counted correctly."""
        game = KnapsackGame("easy")
        await game.generate_puzzle()

        initial_moves = game.moves_made
        await game.validate_move("select", 1)
        assert game.moves_made == initial_moves + 1

    def test_solve_optimal_simple(self):
        """Test optimal solution with simple case."""
        game = KnapsackGame("easy")
        game.items = [
            Item(name="Item1", weight=2, value=10),
            Item(name="Item2", weight=3, value=15),
            Item(name="Item3", weight=5, value=20),
        ]
        game.capacity = 5

        game._solve_optimal()

        # Should select Item2 (weight=3, value=15) and Item1 (weight=2, value=10)
        # Total: weight=5, value=25
        assert game.optimal_value == 25

    @pytest.mark.parametrize("difficulty,expected_items", [("easy", 5), ("medium", 8), ("hard", 12)])
    async def test_difficulty_levels(self, difficulty, expected_items):
        """Test different difficulty levels."""
        game = KnapsackGame(difficulty)
        await game.generate_puzzle()
        assert len(game.items) == expected_items

    async def test_capacity_is_reasonable(self):
        """Test that capacity is a reasonable fraction of total weight."""
        game = KnapsackGame("easy")
        await game.generate_puzzle()

        total_weight = sum(item.weight for item in game.items)
        assert 0 < game.capacity < total_weight

    async def test_optimal_selection_fits_capacity(self):
        """Test that optimal selection doesn't exceed capacity."""
        game = KnapsackGame("easy")
        await game.generate_puzzle()

        optimal_weight = sum(game.items[i].weight for i in range(len(game.items)) if game.optimal_selection[i])

        assert optimal_weight <= game.capacity

    async def test_selection_state_changes(self):
        """Test that selection state changes correctly."""
        game = KnapsackGame("easy")
        game.items = [Item(name="Item1", weight=5, value=50)]
        game.capacity = 10
        game.selection = [False]
        game.game_started = True

        # Select
        await game.validate_move("select", 1)
        assert game.selection[0] is True

        # Deselect
        await game.validate_move("deselect", 1)
        assert game.selection[0] is False

    async def test_constraint_types(self):
        """Test constraint types metadata."""
        game = KnapsackGame("easy")
        constraint_types = game.constraint_types
        assert isinstance(constraint_types, list)
        assert len(constraint_types) > 0
        assert all(isinstance(ct, str) for ct in constraint_types)

    async def test_business_analogies(self):
        """Test business analogies metadata."""
        game = KnapsackGame("easy")
        analogies = game.business_analogies
        assert isinstance(analogies, list)
        assert len(analogies) > 0
        assert all(isinstance(a, str) for a in analogies)

    async def test_complexity_profile(self):
        """Test complexity profile metadata."""
        game = KnapsackGame("easy")
        profile = game.complexity_profile
        assert isinstance(profile, dict)
        assert "reasoning_type" in profile
        assert "search_space" in profile
        assert "constraint_density" in profile
