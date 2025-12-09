"""Tests for Nurikabe puzzle game."""

import pytest

from puzzle_arcade_server.games.nurikabe import NurikabeGame


class TestNurikabeGame:
    """Test suite for Nurikabe game."""

    def test_initialization_easy(self):
        """Test game initialization with easy difficulty."""
        game = NurikabeGame("easy")
        assert game.difficulty == "easy"
        assert game.size == 6
        assert game.num_islands == 3
        assert game.name == "Nurikabe"
        assert "island" in game.description.lower()

    def test_initialization_medium(self):
        """Test game initialization with medium difficulty."""
        game = NurikabeGame("medium")
        assert game.size == 8
        assert game.num_islands == 4

    def test_initialization_hard(self):
        """Test game initialization with hard difficulty."""
        game = NurikabeGame("hard")
        assert game.size == 10
        assert game.num_islands == 5

    def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        assert game.game_started is True
        assert len(game.grid) == 6
        assert len(game.grid[0]) == 6
        assert len(game.islands) == 3

        # Check that islands have valid positions and sizes
        for pos, size in game.islands:
            row, col = pos
            assert 0 <= row < 6
            assert 0 <= col < 6
            assert size > 0

    def test_islands_have_given_cells(self):
        """Test that island cells are marked as given."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        # Each island should have at least one given cell
        for pos, _size in game.islands:
            assert pos in game.given_cells

    def test_mark_cell_white_success(self):
        """Test successfully marking a cell white."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        # Find a cell that's not given
        for row in range(game.size):
            for col in range(game.size):
                if (row, col) not in game.given_cells and game.grid[row][col] == 0:
                    success, message = game.validate_move(row + 1, col + 1, "white")
                    assert success is True
                    assert game.grid[row][col] == 1
                    return

    def test_mark_cell_black_success(self):
        """Test successfully marking a cell black."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        # Find a cell that's not given
        for row in range(game.size):
            for col in range(game.size):
                if (row, col) not in game.given_cells and game.grid[row][col] == 0:
                    success, message = game.validate_move(row + 1, col + 1, "black")
                    assert success is True
                    assert game.grid[row][col] == 2
                    return

    def test_mark_given_cell(self):
        """Test that given cells cannot be marked."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        # Try to mark a given cell
        if len(game.given_cells) > 0:
            row, col = list(game.given_cells)[0]
            success, message = game.validate_move(row + 1, col + 1, "black")
            assert success is False
            assert "given" in message.lower() or "cannot" in message.lower()

    def test_clear_cell_success(self):
        """Test clearing a marked cell."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        # Find and mark a non-given cell
        for row in range(game.size):
            for col in range(game.size):
                if (row, col) not in game.given_cells:
                    game.grid[row][col] = 1  # Mark as white
                    success, message = game.validate_move(row + 1, col + 1, "clear")
                    assert success is True
                    assert game.grid[row][col] == 0
                    return

    def test_clear_unmarked_cell(self):
        """Test clearing an already unmarked cell."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        # Find an unmarked, non-given cell
        for row in range(game.size):
            for col in range(game.size):
                if (row, col) not in game.given_cells and game.grid[row][col] == 0:
                    success, message = game.validate_move(row + 1, col + 1, "clear")
                    assert success is False
                    assert "already" in message.lower()
                    return

    def test_invalid_coordinates(self):
        """Test with invalid coordinates."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        success, message = game.validate_move(0, 1, "white")
        assert success is False
        assert "invalid" in message.lower()

        success, message = game.validate_move(10, 1, "white")
        assert success is False
        assert "invalid" in message.lower()

    def test_invalid_color(self):
        """Test with invalid color."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        success, message = game.validate_move(1, 1, "red")
        assert success is False
        assert "invalid" in message.lower()

    def test_get_island_from_cell(self):
        """Test getting island cells from a white cell."""
        game = NurikabeGame("easy")
        game.grid = [
            [1, 1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ]
        game.size = 6

        island = game._get_island_from_cell(0, 0)
        assert len(island) == 3
        assert (0, 0) in island
        assert (0, 1) in island
        assert (1, 0) in island

    def test_check_black_connected_true(self):
        """Test black connectivity check when connected."""
        game = NurikabeGame("easy")
        game.grid = [
            [2, 2, 1, 0, 0, 0],
            [2, 2, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ]
        game.size = 6

        assert game._check_black_connected() is True

    def test_check_black_connected_false(self):
        """Test black connectivity check when disconnected."""
        game = NurikabeGame("easy")
        game.grid = [
            [2, 1, 2, 0, 0, 0],
            [1, 1, 1, 0, 0, 0],
            [2, 1, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ]
        game.size = 6

        assert game._check_black_connected() is False

    def test_has_2x2_black_true(self):
        """Test 2x2 black block detection when present."""
        game = NurikabeGame("easy")
        game.grid = [
            [2, 2, 1, 0, 0, 0],
            [2, 2, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ]
        game.size = 6

        assert game._has_2x2_black() is True

    def test_has_2x2_black_false(self):
        """Test 2x2 black block detection when absent."""
        game = NurikabeGame("easy")
        game.grid = [
            [2, 1, 2, 0, 0, 0],
            [1, 2, 1, 0, 0, 0],
            [2, 1, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ]
        game.size = 6

        assert game._has_2x2_black() is False

    def test_is_complete_valid_solution(self):
        """Test completion check with valid solution."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        # Set grid to solution
        game.grid = [row[:] for row in game.solution]

        assert game.is_complete() is True

    def test_is_complete_incomplete_grid(self):
        """Test completion check with incomplete grid."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        # Leave some cells unmarked
        for row in range(game.size):
            for col in range(game.size):
                if (row, col) not in game.given_cells:
                    game.grid[row][col] = 0
                    break

        assert game.is_complete() is False

    def test_is_complete_wrong_island_size(self):
        """Test completion check with wrong island sizes."""
        game = NurikabeGame("easy")
        game.islands = [((0, 0), 3), ((2, 2), 2)]
        game.given_cells = {(0, 0), (2, 2)}
        game.grid = [
            [1, 1, 2, 2, 2, 2],
            [2, 2, 2, 2, 2, 2],
            [2, 2, 1, 1, 1, 2],
            [2, 2, 2, 2, 2, 2],
            [2, 2, 2, 2, 2, 2],
            [2, 2, 2, 2, 2, 2],
        ]
        game.size = 6
        game.solution = [[0] * 6 for _ in range(6)]

        # Island at (0,0) should have size 3 but only has 2 cells
        assert game.is_complete() is False

    def test_is_complete_has_2x2_black(self):
        """Test completion check fails with 2x2 black block."""
        game = NurikabeGame("easy")
        game.islands = [((0, 0), 2)]
        game.given_cells = {(0, 0)}
        game.grid = [
            [1, 1, 2, 2, 2, 2],
            [2, 2, 2, 2, 2, 2],
            [2, 2, 2, 2, 2, 2],
            [2, 2, 2, 2, 2, 2],
            [2, 2, 2, 2, 2, 2],
            [2, 2, 2, 2, 2, 2],
        ]
        game.size = 6
        game.solution = [[0] * 6 for _ in range(6)]

        # Has 2x2 black block at (1,0)
        assert game.is_complete() is False

    def test_is_complete_black_not_connected(self):
        """Test completion check fails when black cells not connected."""
        game = NurikabeGame("easy")
        game.islands = [((0, 0), 2), ((4, 4), 2)]
        game.given_cells = {(0, 0), (4, 4)}
        game.grid = [
            [1, 1, 2, 0, 0, 0],
            [2, 2, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 2, 2],
            [0, 0, 0, 0, 1, 1],
            [0, 0, 0, 0, 2, 2],
        ]
        game.size = 6
        game.solution = [[0] * 6 for _ in range(6)]

        # Black cells are in two separate groups
        assert game.is_complete() is False

    def test_get_hint_mark_white(self):
        """Test hint for marking a cell white."""
        game = NurikabeGame("easy")
        game.solution = [
            [1, 1, 2, 0, 0, 0],
            [2, 2, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ]
        game.grid = [
            [1, 0, 2, 0, 0, 0],  # (0,1) should be white
            [2, 2, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ]
        game.size = 6

        hint_data, hint_message = game.get_hint()
        assert hint_data == (1, 2, "white")
        assert "white" in hint_message.lower()

    def test_get_hint_mark_black(self):
        """Test hint for marking a cell black."""
        game = NurikabeGame("easy")
        game.solution = [
            [1, 1, 2, 0, 0, 0],
            [2, 2, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ]
        game.grid = [
            [1, 1, 0, 0, 0, 0],  # (0,2) should be black
            [2, 2, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ]
        game.size = 6

        hint_data, hint_message = game.get_hint()
        assert hint_data == (1, 3, "black")
        assert "black" in hint_message.lower()

    def test_get_hint_already_solved(self):
        """Test hint when puzzle is already solved."""
        game = NurikabeGame("easy")
        game.generate_puzzle()
        game.grid = [row[:] for row in game.solution]

        result = game.get_hint()
        assert result is None

    def test_render_grid(self):
        """Test grid rendering."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        grid_str = game.render_grid()
        assert "Nurikabe" in grid_str
        assert "Islands" in grid_str

    def test_get_rules(self):
        """Test rules retrieval."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        rules = game.get_rules()
        assert "NURIKABE" in rules.upper()
        assert "island" in rules.lower()
        assert "connected" in rules.lower()
        assert "2×2" in rules or "2x2" in rules.lower()

    def test_get_commands(self):
        """Test commands retrieval."""
        game = NurikabeGame("easy")
        commands = game.get_commands()

        assert "mark" in commands.lower()
        assert "white" in commands.lower()
        assert "black" in commands.lower()
        assert "clear" in commands.lower()

    def test_get_stats(self):
        """Test statistics retrieval."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        stats = game.get_stats()
        assert "Moves" in stats
        assert "Marked" in stats
        assert "Islands" in stats

    def test_moves_counter(self):
        """Test that moves are counted correctly."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        initial_moves = game.moves_made
        # Find a non-given cell to mark
        for row in range(game.size):
            for col in range(game.size):
                if (row, col) not in game.given_cells:
                    game.validate_move(row + 1, col + 1, "white")
                    assert game.moves_made == initial_moves + 1
                    return

    @pytest.mark.parametrize(
        "difficulty,expected_size,expected_islands", [("easy", 6, 3), ("medium", 8, 4), ("hard", 10, 5)]
    )
    def test_difficulty_levels(self, difficulty, expected_size, expected_islands):
        """Test different difficulty levels."""
        game = NurikabeGame(difficulty)
        game.generate_puzzle()
        assert game.size == expected_size
        assert len(game.islands) == expected_islands

    def test_solution_is_valid(self):
        """Test that generated solution is valid."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        # Check solution has no 2x2 black blocks
        temp_grid = game.grid
        game.grid = game.solution
        assert game._has_2x2_black() is False

        # Check black cells are connected
        assert game._check_black_connected() is True

        # Check island sizes
        for pos, expected_size in game.islands:
            island_cells = game._get_island_from_cell(pos[0], pos[1])
            assert len(island_cells) == expected_size

        game.grid = temp_grid

    def test_islands_do_not_touch(self):
        """Test that white islands don't touch each other."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        # Get all white island groups
        islands_found = []
        visited = set()

        for row in range(game.size):
            for col in range(game.size):
                if game.solution[row][col] == 1 and (row, col) not in visited:
                    island = game._get_island_from_cell(row, col)
                    islands_found.append(island)
                    visited.update(island)

        # Check that no two islands share an edge
        for i, island1 in enumerate(islands_found):
            for island2 in islands_found[i + 1 :]:
                for r1, c1 in island1:
                    for r2, c2 in island2:
                        # Check if adjacent (not diagonal)
                        if abs(r1 - r2) + abs(c1 - c2) == 1:
                            pytest.fail(f"Islands touch at ({r1},{c1}) and ({r2},{c2})")

    def test_all_cells_assigned_in_solution(self):
        """Test that solution assigns all cells."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        for row in range(game.size):
            for col in range(game.size):
                assert game.solution[row][col] in [1, 2], f"Cell ({row},{col}) not assigned"

    def test_given_cells_match_solution(self):
        """Test that given cells are white in the solution."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        for row, col in game.given_cells:
            assert game.solution[row][col] == 1, f"Given cell ({row},{col}) is not white in solution"

    def test_mark_alternate_colors(self):
        """Test marking a cell with different colors."""
        game = NurikabeGame("easy")
        game.generate_puzzle()

        # Find a non-given cell
        for row in range(game.size):
            for col in range(game.size):
                if (row, col) not in game.given_cells:
                    # Mark white
                    success, _ = game.validate_move(row + 1, col + 1, "white")
                    assert success is True
                    assert game.grid[row][col] == 1

                    # Clear it
                    success, _ = game.validate_move(row + 1, col + 1, "clear")
                    assert success is True
                    assert game.grid[row][col] == 0

                    # Mark black
                    success, _ = game.validate_move(row + 1, col + 1, "black")
                    assert success is True
                    assert game.grid[row][col] == 2

                    return
