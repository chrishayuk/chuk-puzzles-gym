"""Tests for Knapsack puzzle game."""

import pytest

from puzzle_arcade_server.games.knapsack import KnapsackGame


class TestKnapsackGame:
    """Test suite for Knapsack game."""

    def test_initialization_easy(self):
        """Test game initialization with easy difficulty."""
        game = KnapsackGame("easy")
        assert game.difficulty == "easy"
        assert game.num_items == 5
        assert game.name == "Knapsack"
        assert "optimize" in game.description.lower()

    def test_initialization_medium(self):
        """Test game initialization with medium difficulty."""
        game = KnapsackGame("medium")
        assert game.num_items == 8

    def test_initialization_hard(self):
        """Test game initialization with hard difficulty."""
        game = KnapsackGame("hard")
        assert game.num_items == 12

    def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = KnapsackGame("easy")
        game.generate_puzzle()

        assert game.game_started is True
        assert len(game.items) == 5
        assert game.capacity > 0
        assert game.optimal_value > 0
        assert len(game.optimal_selection) == 5
        assert all(not selected for selected in game.selection)

    def test_items_have_valid_attributes(self):
        """Test that generated items have valid weights and values."""
        game = KnapsackGame("easy")
        game.generate_puzzle()

        for item in game.items:
            assert "name" in item
            assert "weight" in item
            assert "value" in item
            assert item["weight"] > 0
            assert item["value"] > 0

    def test_select_item_success(self):
        """Test successfully selecting an item."""
        game = KnapsackGame("easy")
        game.items = [
            {"name": "Item1", "weight": 5, "value": 50},
            {"name": "Item2", "weight": 3, "value": 30},
        ]
        game.capacity = 10
        game.selection = [False, False]
        game.game_started = True

        success, message = game.validate_move("select", 1)
        assert success is True
        assert game.selection[0] is True
        assert "Item1" in message

    def test_select_already_selected(self):
        """Test selecting an already selected item."""
        game = KnapsackGame("easy")
        game.items = [{"name": "Item1", "weight": 5, "value": 50}]
        game.capacity = 10
        game.selection = [True]
        game.game_started = True

        success, message = game.validate_move("select", 1)
        assert success is False
        assert "already selected" in message.lower()

    def test_select_exceeds_capacity(self):
        """Test selecting item that exceeds capacity."""
        game = KnapsackGame("easy")
        game.items = [
            {"name": "Item1", "weight": 5, "value": 50},
            {"name": "Item2", "weight": 8, "value": 80},
        ]
        game.capacity = 10
        game.selection = [True, False]
        game.game_started = True

        success, message = game.validate_move("select", 2)
        assert success is False
        assert "exceed capacity" in message.lower()

    def test_deselect_item_success(self):
        """Test successfully deselecting an item."""
        game = KnapsackGame("easy")
        game.items = [{"name": "Item1", "weight": 5, "value": 50}]
        game.capacity = 10
        game.selection = [True]
        game.game_started = True

        success, message = game.validate_move("deselect", 1)
        assert success is True
        assert game.selection[0] is False

    def test_deselect_not_selected(self):
        """Test deselecting an item that's not selected."""
        game = KnapsackGame("easy")
        game.items = [{"name": "Item1", "weight": 5, "value": 50}]
        game.capacity = 10
        game.selection = [False]
        game.game_started = True

        success, message = game.validate_move("deselect", 1)
        assert success is False
        assert "not currently selected" in message.lower()

    def test_invalid_item_index(self):
        """Test with invalid item index."""
        game = KnapsackGame("easy")
        game.generate_puzzle()

        success, message = game.validate_move("select", 0)
        assert success is False
        assert "Invalid item" in message

        success, message = game.validate_move("select", 10)
        assert success is False
        assert "Invalid item" in message

    def test_invalid_action(self):
        """Test with invalid action."""
        game = KnapsackGame("easy")
        game.generate_puzzle()

        success, message = game.validate_move("invalid", 1)
        assert success is False
        assert "Invalid action" in message

    def test_get_current_weight(self):
        """Test current weight calculation."""
        game = KnapsackGame("easy")
        game.items = [
            {"name": "Item1", "weight": 5, "value": 50},
            {"name": "Item2", "weight": 3, "value": 30},
        ]
        game.selection = [True, True]

        assert game._get_current_weight() == 8

    def test_get_current_value(self):
        """Test current value calculation."""
        game = KnapsackGame("easy")
        game.items = [
            {"name": "Item1", "weight": 5, "value": 50},
            {"name": "Item2", "weight": 3, "value": 30},
        ]
        game.selection = [True, True]

        assert game._get_current_value() == 80

    def test_is_complete_optimal(self):
        """Test completion check when optimal solution is found."""
        game = KnapsackGame("easy")
        game.generate_puzzle()

        # Set selection to optimal
        game.selection = game.optimal_selection.copy()

        assert game.is_complete() is True

    def test_is_complete_not_optimal(self):
        """Test completion check when solution is not optimal."""
        game = KnapsackGame("easy")
        game.generate_puzzle()

        # Set all to False (not optimal)
        game.selection = [False] * len(game.items)

        assert game.is_complete() is False

    def test_get_hint_select(self):
        """Test hint for selecting an item."""
        game = KnapsackGame("easy")
        game.items = [{"name": "Item1", "weight": 5, "value": 50}]
        game.optimal_selection = [True]
        game.selection = [False]

        hint_data, hint_message = game.get_hint()
        assert hint_data == ("select", 1)
        assert "select" in hint_message.lower()

    def test_get_hint_deselect(self):
        """Test hint for deselecting an item."""
        game = KnapsackGame("easy")
        game.items = [{"name": "Item1", "weight": 5, "value": 50}]
        game.optimal_selection = [False]
        game.selection = [True]

        hint_data, hint_message = game.get_hint()
        assert hint_data == ("deselect", 1)
        assert "deselect" in hint_message.lower()

    def test_get_hint_optimal(self):
        """Test hint when already at optimal."""
        game = KnapsackGame("easy")
        game.items = [{"name": "Item1", "weight": 5, "value": 50}]
        game.optimal_selection = [True]
        game.selection = [True]

        result = game.get_hint()
        assert result is None

    def test_render_grid(self):
        """Test grid rendering."""
        game = KnapsackGame("easy")
        game.generate_puzzle()

        grid_str = game.render_grid()
        assert "Capacity" in grid_str
        assert "Weight" in grid_str
        assert "Value" in grid_str
        assert "Optimal" in grid_str

    def test_get_rules(self):
        """Test rules retrieval."""
        game = KnapsackGame("easy")
        game.generate_puzzle()

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

    def test_get_stats(self):
        """Test statistics retrieval."""
        game = KnapsackGame("easy")
        game.generate_puzzle()

        stats = game.get_stats()
        assert "Moves" in stats
        assert "Value" in stats
        assert "Weight" in stats

    def test_moves_counter(self):
        """Test that moves are counted correctly."""
        game = KnapsackGame("easy")
        game.generate_puzzle()

        initial_moves = game.moves_made
        game.validate_move("select", 1)
        assert game.moves_made == initial_moves + 1

    def test_solve_optimal_simple(self):
        """Test optimal solution with simple case."""
        game = KnapsackGame("easy")
        game.items = [
            {"name": "Item1", "weight": 2, "value": 10},
            {"name": "Item2", "weight": 3, "value": 15},
            {"name": "Item3", "weight": 5, "value": 20},
        ]
        game.capacity = 5

        game._solve_optimal()

        # Should select Item2 (weight=3, value=15) and Item1 (weight=2, value=10)
        # Total: weight=5, value=25
        assert game.optimal_value == 25

    @pytest.mark.parametrize("difficulty,expected_items", [("easy", 5), ("medium", 8), ("hard", 12)])
    def test_difficulty_levels(self, difficulty, expected_items):
        """Test different difficulty levels."""
        game = KnapsackGame(difficulty)
        game.generate_puzzle()
        assert len(game.items) == expected_items

    def test_capacity_is_reasonable(self):
        """Test that capacity is a reasonable fraction of total weight."""
        game = KnapsackGame("easy")
        game.generate_puzzle()

        total_weight = sum(item["weight"] for item in game.items)
        assert 0 < game.capacity < total_weight

    def test_optimal_selection_fits_capacity(self):
        """Test that optimal selection doesn't exceed capacity."""
        game = KnapsackGame("easy")
        game.generate_puzzle()

        optimal_weight = sum(game.items[i]["weight"] for i in range(len(game.items)) if game.optimal_selection[i])

        assert optimal_weight <= game.capacity

    def test_selection_state_changes(self):
        """Test that selection state changes correctly."""
        game = KnapsackGame("easy")
        game.items = [{"name": "Item1", "weight": 5, "value": 50}]
        game.capacity = 10
        game.selection = [False]
        game.game_started = True

        # Select
        game.validate_move("select", 1)
        assert game.selection[0] is True

        # Deselect
        game.validate_move("deselect", 1)
        assert game.selection[0] is False
