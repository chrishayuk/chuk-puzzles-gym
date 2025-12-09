"""Tests for Einstein's Puzzle (Zebra Puzzle) game."""

import pytest

from puzzle_arcade_server.games.einstein import EinsteinGame


class TestEinsteinGame:
    """Test suite for Einstein's Puzzle."""

    def test_initialization_easy(self):
        """Test game initialization with easy difficulty."""
        game = EinsteinGame("easy")
        assert game.difficulty == "easy"
        assert game.num_houses == 5
        assert game.name == "Einstein's Puzzle"
        assert "fish" in game.description.lower() or "logic" in game.description.lower()

    def test_initialization_medium(self):
        """Test game initialization with medium difficulty."""
        game = EinsteinGame("medium")
        assert game.num_houses == 5

    def test_initialization_hard(self):
        """Test game initialization with hard difficulty."""
        game = EinsteinGame("hard")
        assert game.num_houses == 5

    def test_attribute_lists(self):
        """Test that all attribute lists have 5 items."""
        game = EinsteinGame("easy")
        assert len(game.colors) == 5
        assert len(game.nationalities) == 5
        assert len(game.drinks) == 5
        assert len(game.smokes) == 5
        assert len(game.pets) == 5

    def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        assert game.game_started is True
        assert len(game.solution) == 5
        assert len(game.clues) > 0
        assert len(game.assignments) == 5

    def test_solution_has_all_attributes(self):
        """Test that solution assigns all attributes to all houses."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        for house in game.solution:
            assert "color" in house
            assert "nationality" in house
            assert "drink" in house
            assert "smoke" in house
            assert "pet" in house
            assert house["color"] is not None
            assert house["nationality"] is not None
            assert house["drink"] is not None
            assert house["smoke"] is not None
            assert house["pet"] is not None

    def test_solution_is_valid(self):
        """Test that solution has no duplicate attributes."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        # Check each attribute type
        for attr in ["color", "nationality", "drink", "smoke", "pet"]:
            values = [house[attr] for house in game.solution]
            assert len(values) == len(set(values)), f"Duplicate {attr} in solution"

    def test_assignments_start_empty(self):
        """Test that assignments start with all None values."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        for house in game.assignments:
            assert house["color"] is None
            assert house["nationality"] is None
            assert house["drink"] is None
            assert house["smoke"] is None
            assert house["pet"] is None

    def test_clues_generated(self):
        """Test that clues are generated."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        assert len(game.clues) >= 2  # At least starter clues
        # Check that all clues are strings
        for clue in game.clues:
            assert isinstance(clue, str)
            assert len(clue) > 0

    def test_assign_attribute_success(self):
        """Test successfully assigning an attribute."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        success, message = game.validate_move(1, "color", "Red")
        assert success is True
        assert game.assignments[0]["color"] == "Red"
        assert "assigned" in message.lower()

    def test_assign_attribute_case_insensitive(self):
        """Test that attribute and value are case-insensitive."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        success, message = game.validate_move(1, "COLOR", "red")
        assert success is True
        assert game.assignments[0]["color"] == "Red"  # Capitalized

        success, message = game.validate_move(2, "nationality", "BRITISH")
        assert success is True
        assert game.assignments[1]["nationality"] == "British"

    def test_reassign_attribute(self):
        """Test reassigning an attribute to a house."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        game.validate_move(1, "color", "Red")
        success, message = game.validate_move(1, "color", "Blue")
        assert success is True
        assert game.assignments[0]["color"] == "Blue"
        assert "changed" in message.lower()

    def test_assign_duplicate_value(self):
        """Test that duplicate values across houses are rejected."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        game.validate_move(1, "color", "Red")
        success, message = game.validate_move(2, "color", "Red")
        assert success is False
        assert "already assigned" in message.lower()

    def test_invalid_house_number(self):
        """Test with invalid house number."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        success, message = game.validate_move(0, "color", "Red")
        assert success is False
        assert "invalid house" in message.lower()

        success, message = game.validate_move(6, "color", "Red")
        assert success is False
        assert "invalid house" in message.lower()

    def test_invalid_attribute(self):
        """Test with invalid attribute type."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        success, message = game.validate_move(1, "age", "25")
        assert success is False
        assert "invalid attribute" in message.lower()

    def test_invalid_value(self):
        """Test with invalid attribute value."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        success, message = game.validate_move(1, "color", "Purple")
        assert success is False
        assert "invalid" in message.lower()

        success, message = game.validate_move(1, "nationality", "American")
        assert success is False
        assert "invalid" in message.lower()

    def test_assign_all_attributes_to_house(self):
        """Test assigning all attributes to a single house."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        game.validate_move(1, "color", "Red")
        game.validate_move(1, "nationality", "British")
        game.validate_move(1, "drink", "Tea")
        game.validate_move(1, "smoke", "Pall Mall")
        game.validate_move(1, "pet", "Dog")

        assert game.assignments[0]["color"] == "Red"
        assert game.assignments[0]["nationality"] == "British"
        assert game.assignments[0]["drink"] == "Tea"
        assert game.assignments[0]["smoke"] == "Pall Mall"
        assert game.assignments[0]["pet"] == "Dog"

    def test_is_complete_when_correct(self):
        """Test completion check when solution is correct."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        # Copy solution to assignments
        for i in range(game.num_houses):
            game.assignments[i] = game.solution[i].copy()

        assert game.is_complete() is True

    def test_is_complete_when_incomplete(self):
        """Test completion check when not all cells assigned."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        # Assign only some attributes
        game.assignments[0]["color"] = game.solution[0]["color"]
        game.assignments[0]["nationality"] = game.solution[0]["nationality"]

        assert game.is_complete() is False

    def test_is_complete_when_incorrect(self):
        """Test completion check when solution is wrong."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        # Fill all houses but with wrong values
        for i in range(game.num_houses):
            game.assignments[i] = {
                "color": game.colors[i],
                "nationality": game.nationalities[i],
                "drink": game.drinks[i],
                "smoke": game.smokes[i],
                "pet": game.pets[i],
            }

        # This is very unlikely to match the solution
        if game.is_complete():
            # If by chance it matches, swap two values to make it wrong
            game.assignments[0]["color"], game.assignments[1]["color"] = (
                game.assignments[1]["color"],
                game.assignments[0]["color"],
            )
            assert game.is_complete() is False

    def test_get_hint(self):
        """Test hint generation."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        hint_data, hint_message = game.get_hint()
        house, attr, value = hint_data

        assert 1 <= house <= 5
        assert attr in ["color", "nationality", "drink", "smoke", "pet"]
        assert value is not None
        assert "assign" in hint_message.lower()

    def test_get_hint_already_solved(self):
        """Test hint when puzzle is already solved."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        # Copy solution to assignments
        for i in range(game.num_houses):
            game.assignments[i] = game.solution[i].copy()

        result = game.get_hint()
        assert result is None

    def test_render_grid(self):
        """Test grid rendering."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        grid_str = game.render_grid()
        assert "Einstein" in grid_str
        assert "House" in grid_str
        assert "Color" in grid_str
        assert "Nationality" in grid_str
        assert "Clues" in grid_str

    def test_get_rules(self):
        """Test rules retrieval."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        rules = game.get_rules()
        assert "EINSTEIN" in rules.upper()
        assert "5 houses" in rules.lower() or "5 house" in rules.lower()
        assert "fish" in rules.lower()

    def test_get_commands(self):
        """Test commands retrieval."""
        game = EinsteinGame("easy")
        commands = game.get_commands()

        assert "assign" in commands.lower()
        assert "color" in commands.lower()
        assert "nationality" in commands.lower()

    def test_get_stats(self):
        """Test statistics retrieval."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        stats = game.get_stats()
        assert "Moves" in stats
        assert "Assigned" in stats
        assert "Clues" in stats

    def test_moves_counter(self):
        """Test that moves are counted correctly."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        initial_moves = game.moves_made
        game.validate_move(1, "color", "Red")
        assert game.moves_made == initial_moves + 1

        game.validate_move(1, "nationality", "British")
        assert game.moves_made == initial_moves + 2

    @pytest.mark.parametrize("difficulty,expected_max_clues", [("easy", 12), ("medium", 10), ("hard", 8)])
    def test_difficulty_levels(self, difficulty, expected_max_clues):
        """Test different difficulty levels have appropriate clue counts."""
        game = EinsteinGame(difficulty)
        game.generate_puzzle()
        assert len(game.clues) <= expected_max_clues

    def test_clues_always_include_norwegian_and_milk(self):
        """Test that starter clues are always included."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        # Check that there's a clue about Norwegian
        has_norwegian_clue = any("norwegian" in clue.lower() for clue in game.clues)
        assert has_norwegian_clue is True

        # Check that there's a clue about Milk
        has_milk_clue = any("milk" in clue.lower() for clue in game.clues)
        assert has_milk_clue is True

    def test_all_attributes_present_in_solution(self):
        """Test that all possible attribute values appear in solution."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        # Collect all values from solution
        colors = {house["color"] for house in game.solution}
        nationalities = {house["nationality"] for house in game.solution}
        drinks = {house["drink"] for house in game.solution}
        smokes = {house["smoke"] for house in game.solution}
        pets = {house["pet"] for house in game.solution}

        assert colors == set(game.colors)
        assert nationalities == set(game.nationalities)
        assert drinks == set(game.drinks)
        assert smokes == set(game.smokes)
        assert pets == set(game.pets)

    def test_assign_multiple_houses(self):
        """Test assigning attributes to multiple houses."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        game.validate_move(1, "color", "Red")
        game.validate_move(2, "color", "Blue")
        game.validate_move(3, "color", "Green")

        assert game.assignments[0]["color"] == "Red"
        assert game.assignments[1]["color"] == "Blue"
        assert game.assignments[2]["color"] == "Green"

    def test_stats_count_assignments(self):
        """Test that stats correctly count assignments."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        game.validate_move(1, "color", "Red")
        game.validate_move(1, "nationality", "British")
        game.validate_move(2, "drink", "Coffee")

        stats = game.get_stats()
        # Should show 3 assigned out of 25 total (5 houses × 5 attributes)
        assert "3/25" in stats or "3 / 25" in stats

    def test_reassignment_counts_as_move(self):
        """Test that reassigning an attribute counts as a move."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        initial_moves = game.moves_made
        game.validate_move(1, "color", "Red")
        game.validate_move(1, "color", "Blue")

        assert game.moves_made == initial_moves + 2

    def test_partial_solution(self):
        """Test partial solution is not complete."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        # Assign correct values to first 3 houses
        for i in range(3):
            for attr in ["color", "nationality", "drink", "smoke", "pet"]:
                game.assignments[i][attr] = game.solution[i][attr]

        assert game.is_complete() is False

    def test_hint_gives_next_unassigned(self):
        """Test that hint gives the next unassigned attribute."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        # Assign first house completely
        for attr in ["color", "nationality", "drink", "smoke", "pet"]:
            game.assignments[0][attr] = game.solution[0][attr]

        hint_data, hint_message = game.get_hint()
        house, attr, value = hint_data

        # Hint should point to a different house or attribute
        if house == 1:
            assert game.assignments[0][attr] != value
        else:
            assert house > 1

    def test_clues_reference_valid_attributes(self):
        """Test that clues reference valid attribute values."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        all_values = set(game.colors + game.nationalities + game.drinks + game.smokes + game.pets)

        for clue in game.clues:
            # Extract capitalized words (attribute values)
            words = clue.split()
            for word in words:
                if word[0].isupper() and word not in ["The", "A", "An", "House", "In"]:
                    # Remove punctuation
                    clean_word = word.rstrip(".,!?;:")
                    if clean_word.isalpha() and len(clean_word) > 2:
                        # Should be a valid attribute value or house number
                        if not clean_word.isdigit() and clean_word not in [
                            "House",
                            "Milk",
                            "Norwegian",
                            "next",
                        ]:
                            assert clean_word in all_values or clean_word.lower() in [
                                "house",
                                "milk",
                                "norwegian",
                            ]

    def test_zero_indexed_vs_one_indexed(self):
        """Test that internal 0-indexing converts correctly to 1-indexed user input."""
        game = EinsteinGame("easy")
        game.generate_puzzle()

        # User passes house 1 (1-indexed)
        game.validate_move(1, "color", "Red")
        # Should be stored in assignments[0] (0-indexed)
        assert game.assignments[0]["color"] == "Red"
        assert game.assignments[1]["color"] is None
