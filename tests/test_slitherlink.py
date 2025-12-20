"""Tests for Slitherlink puzzle game."""

import pytest

from puzzle_arcade_server.games.slitherlink import SlitherlinkGame


class TestSlitherlinkGame:
    """Test suite for Slitherlink game."""

    async def test_initialization_easy(self):
        """Test game initialization with easy difficulty."""
        game = SlitherlinkGame("easy")
        assert game.difficulty == "easy"
        assert game.size == 5
        assert game.name == "Slitherlink"
        assert "loop" in game.description.lower()

    async def test_initialization_medium(self):
        """Test game initialization with medium difficulty."""
        game = SlitherlinkGame("medium")
        assert game.size == 7

    async def test_initialization_hard(self):
        """Test game initialization with hard difficulty."""
        game = SlitherlinkGame("hard")
        assert game.size == 10

    async def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        assert game.game_started is True
        assert game.moves_made == 0

        # Check grids are initialized
        assert len(game.h_edges) == game.size + 1
        assert len(game.v_edges) == game.size

        # Check some clues were placed
        clue_count = sum(1 for row in game.clues for cell in row if cell != -1)
        assert clue_count > 0

    async def test_generate_simple_loop(self):
        """Test simple loop generation."""
        game = SlitherlinkGame("easy")
        game._generate_simple_loop()

        # Check border edges are set
        for col in range(game.size):
            assert game.solution_h_edges[0][col] == 1  # Top
            assert game.solution_h_edges[game.size][col] == 1  # Bottom

        for row in range(game.size):
            assert game.solution_v_edges[row][0] == 1  # Left
            assert game.solution_v_edges[row][game.size] == 1  # Right

    async def test_count_edges_around_cell(self):
        """Test counting edges around a cell."""
        game = SlitherlinkGame("easy")
        game.h_edges = [[0 for _ in range(5)] for _ in range(6)]
        game.v_edges = [[0 for _ in range(6)] for _ in range(5)]

        # Set all edges around cell (1, 1)
        game.h_edges[1][1] = 1  # Top
        game.h_edges[2][1] = 1  # Bottom
        game.v_edges[1][1] = 1  # Left
        game.v_edges[1][2] = 1  # Right

        count = game._count_edges_around_cell(1, 1, game.h_edges, game.v_edges)
        assert count == 4

    async def test_count_edges_around_cell_none(self):
        """Test counting edges with no edges set."""
        game = SlitherlinkGame("easy")
        game.h_edges = [[0 for _ in range(5)] for _ in range(6)]
        game.v_edges = [[0 for _ in range(6)] for _ in range(5)]

        count = game._count_edges_around_cell(2, 2, game.h_edges, game.v_edges)
        assert count == 0

    async def test_validate_move_horizontal_success(self):
        """Test setting a horizontal edge."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move("h", 1, 1, 1)
        success, message = result.success, result.message
        assert success is True
        assert "horizontal" in message.lower()
        assert game.h_edges[0][0] == 1

    async def test_validate_move_vertical_success(self):
        """Test setting a vertical edge."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move("v", 1, 1, 1)
        success, message = result.success, result.message
        assert success is True
        assert "vertical" in message.lower()
        assert game.v_edges[0][0] == 1

    async def test_validate_move_clear_edge(self):
        """Test clearing an edge."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        # Set then clear
        await game.validate_move("h", 1, 1, 1)
        result = await game.validate_move("h", 1, 1, 0)
        success, message = result.success, result.message
        assert success is True
        assert "cleared" in message.lower()
        assert game.h_edges[0][0] == 0

    async def test_validate_move_mark_x(self):
        """Test marking an edge as X (not part of loop)."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move("h", 1, 1, 2)
        success, _message = result.success, result.message
        assert success is True
        assert game.h_edges[0][0] == 2

    async def test_validate_move_invalid_state(self):
        """Test with invalid state value."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move("h", 1, 1, 3)
        success, message = result.success, result.message
        assert success is False
        assert "Invalid state" in message

    async def test_validate_move_invalid_edge_type(self):
        """Test with invalid edge type."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move("x", 1, 1, 1)
        success, message = result.success, result.message
        assert success is False
        assert "Invalid edge type" in message

    async def test_validate_move_invalid_coordinates_horizontal(self):
        """Test with invalid coordinates for horizontal edge."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move("h", 0, 0, 1)
        success, message = result.success, result.message
        assert success is False
        assert "Invalid" in message

        result = await game.validate_move("h", 10, 10, 1)
        success, message = result.success, result.message
        assert success is False
        assert "Invalid" in message

    async def test_validate_move_invalid_coordinates_vertical(self):
        """Test with invalid coordinates for vertical edge."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move("v", 0, 0, 1)
        success, message = result.success, result.message
        assert success is False
        assert "Invalid" in message

        result = await game.validate_move("v", 10, 10, 1)
        success, message = result.success, result.message
        assert success is False
        assert "Invalid" in message

    async def test_is_complete_empty(self):
        """Test completion check with empty grid."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        assert game.is_complete() is False

    async def test_is_complete_clue_not_satisfied(self):
        """Test completion with unsatisfied clue."""
        game = SlitherlinkGame("easy")
        game.clues = [[-1 for _ in range(5)] for _ in range(5)]
        game.clues[0][0] = 3  # Expect 3 edges
        game.h_edges = [[0 for _ in range(5)] for _ in range(6)]
        game.v_edges = [[0 for _ in range(6)] for _ in range(5)]

        # Only set 2 edges around cell
        game.h_edges[0][0] = 1
        game.v_edges[0][0] = 1

        assert game.is_complete() is False

    async def test_is_complete_valid_loop(self):
        """Test completion with valid simple loop."""
        game = SlitherlinkGame("easy")
        game.clues = [[-1 for _ in range(5)] for _ in range(5)]
        game.h_edges = [[0 for _ in range(5)] for _ in range(6)]
        game.v_edges = [[0 for _ in range(6)] for _ in range(5)]

        # Create simple rectangle loop
        for col in range(5):
            game.h_edges[0][col] = 1  # Top
            game.h_edges[5][col] = 1  # Bottom

        for row in range(5):
            game.v_edges[row][0] = 1  # Left
            game.v_edges[row][5] = 1  # Right

        # All vertices should have 0 or 2 edges
        assert game.is_complete() is True

    async def test_is_complete_branch_detected(self):
        """Test completion fails with branching."""
        game = SlitherlinkGame("easy")
        game.clues = [[-1 for _ in range(5)] for _ in range(5)]
        game.h_edges = [[0 for _ in range(5)] for _ in range(6)]
        game.v_edges = [[0 for _ in range(6)] for _ in range(5)]

        # Create a T-junction (3 edges at one vertex)
        game.h_edges[0][0] = 1
        game.v_edges[0][0] = 1
        game.v_edges[0][1] = 1

        assert game.is_complete() is False

    async def test_get_hint(self):
        """Test hint generation."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        hint_data, hint_message = await game.get_hint()
        assert hint_data is not None
        assert len(hint_data) == 4  # (type, row, col, state)
        assert "setting" in hint_message.lower()

    async def test_get_hint_no_hints(self):
        """Test hint when all edges are set correctly."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        # Copy solution to player grid
        game.h_edges = [row[:] for row in game.solution_h_edges]
        game.v_edges = [row[:] for row in game.solution_v_edges]

        result = await game.get_hint()
        assert result is None

    async def test_render_grid(self):
        """Test grid rendering."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        grid_str = game.render_grid()
        assert "+" in grid_str
        assert "|" in grid_str or " " in grid_str

    async def test_render_grid_with_edges(self):
        """Test grid rendering with edges set."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()
        game.h_edges[0][0] = 1
        game.v_edges[0][0] = 1

        grid_str = game.render_grid()
        assert "---" in grid_str
        assert "|" in grid_str

    async def test_render_grid_with_x_marks(self):
        """Test grid rendering with X marks."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()
        game.h_edges[0][0] = 2
        game.v_edges[0][0] = 2

        grid_str = game.render_grid()
        assert "X" in grid_str

    async def test_get_rules(self):
        """Test rules retrieval."""
        game = SlitherlinkGame("easy")
        rules = game.get_rules()

        assert "SLITHERLINK" in rules
        assert "loop" in rules.lower()
        assert "continuous" in rules.lower()

    async def test_get_commands(self):
        """Test commands retrieval."""
        game = SlitherlinkGame("easy")
        commands = game.get_commands()

        assert "set h" in commands.lower()
        assert "set v" in commands.lower()
        assert "show" in commands.lower()

    async def test_get_stats(self):
        """Test statistics retrieval."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        stats = game.get_stats()
        assert "Moves:" in stats or "Moves made:" in stats
        assert "Lines" in stats
        assert "Clues:" in stats
        assert "Seed:" in stats

    async def test_moves_counter(self):
        """Test that moves are counted correctly."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        initial_moves = game.moves_made
        await game.validate_move("h", 1, 1, 1)
        assert game.moves_made == initial_moves + 1

        await game.validate_move("v", 1, 1, 1)
        assert game.moves_made == initial_moves + 2

    @pytest.mark.parametrize("difficulty,expected_size", [("easy", 5), ("medium", 7), ("hard", 10)])
    async def test_difficulty_levels(self, difficulty, expected_size):
        """Test different difficulty levels."""
        game = SlitherlinkGame(difficulty)
        assert game.size == expected_size

    async def test_clue_values_valid(self):
        """Test that clues are valid (0-3 or -1)."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        for row in game.clues:
            for clue in row:
                assert -1 <= clue <= 3

    async def test_solution_clues_match(self):
        """Test that clues match the solution."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        for row in range(game.size):
            for col in range(game.size):
                if game.clues[row][col] != -1:
                    expected_count = game.clues[row][col]
                    actual_count = game._count_edges_around_cell(row, col, game.solution_h_edges, game.solution_v_edges)
                    assert actual_count == expected_count

    async def test_edge_grid_dimensions(self):
        """Test that edge grids have correct dimensions."""
        game = SlitherlinkGame("easy")
        await game.generate_puzzle()

        # Horizontal edges: (size+1) rows x size columns
        assert len(game.h_edges) == game.size + 1
        assert all(len(row) == game.size for row in game.h_edges)

        # Vertical edges: size rows x (size+1) columns
        assert len(game.v_edges) == game.size
        assert all(len(row) == game.size + 1 for row in game.v_edges)

    async def test_constraint_types(self):
        """Test constraint types metadata."""
        game = SlitherlinkGame("easy")
        constraint_types = game.constraint_types
        assert isinstance(constraint_types, list)
        assert len(constraint_types) > 0
        assert all(isinstance(ct, str) for ct in constraint_types)

    async def test_business_analogies(self):
        """Test business analogies metadata."""
        game = SlitherlinkGame("easy")
        analogies = game.business_analogies
        assert isinstance(analogies, list)
        assert len(analogies) > 0
        assert all(isinstance(a, str) for a in analogies)

    async def test_complexity_profile(self):
        """Test complexity profile metadata."""
        game = SlitherlinkGame("easy")
        profile = game.complexity_profile
        assert isinstance(profile, dict)
        assert "reasoning_type" in profile
        assert "search_space" in profile
        assert "constraint_density" in profile
