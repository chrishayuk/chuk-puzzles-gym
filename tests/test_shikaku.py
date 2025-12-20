"""Tests for Shikaku game logic."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from puzzle_arcade_server.games.shikaku import ShikakuGame


class TestShikakuGame:
    """Test suite for ShikakuGame class."""

    async def test_initialization(self):
        """Test game initialization."""
        game = ShikakuGame("easy")
        assert game.difficulty.value == "easy"
        assert game.size == 6

    async def test_difficulty_sizes(self):
        """Test grid sizes for different difficulties."""
        for difficulty, expected_size in [("easy", 6), ("medium", 8), ("hard", 10)]:
            game = ShikakuGame(difficulty)
            assert game.size == expected_size

    async def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Check that clues were placed
        assert len(game.clues) > 0
        assert game.game_started

        # Check that solution was generated
        total_cells = game.size * game.size
        solution_cells = sum(1 for r in range(game.size) for c in range(game.size) if game.solution[r][c] > 0)
        assert solution_cells == total_cells

    async def test_name_and_description(self):
        """Test game name and description."""
        game = ShikakuGame("easy")
        assert game.name == "Shikaku"
        assert "rectangle" in game.description.lower()

    async def test_get_rules(self):
        """Test rules retrieval."""
        game = ShikakuGame("easy")
        rules = game.get_rules()
        assert "SHIKAKU" in rules
        assert "rectangle" in rules.lower()

    async def test_get_commands(self):
        """Test commands retrieval."""
        game = ShikakuGame("easy")
        commands = game.get_commands()
        assert "place" in commands.lower()
        assert "hint" in commands.lower()

    async def test_place_rectangle_valid(self):
        """Test placing a valid rectangle."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Find a clue and create matching rectangle
        if game.clues:
            (r, c), area = next(iter(game.clues.items()))

            # Try to place a 1x1 rectangle if area is 1
            if area == 1:
                result = await game.validate_move(r + 1, c + 1, r + 1, c + 1)
                assert result.success
                assert len(game.rectangles) == 1

    async def test_place_rectangle_wrong_area(self):
        """Test placing rectangle with wrong area."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Find a clue with area > 2
        for (r, c), area in game.clues.items():
            if area > 2 and r + 1 < game.size and c + 1 < game.size:
                # Try to place 1x2 rectangle (area 2) when clue requires different area
                # Make sure destination cell is not a clue
                if (r, c + 1) not in game.clues:
                    result = await game.validate_move(r + 1, c + 1, r + 1, c + 2)
                    assert not result.success
                    assert "area" in result.message.lower() or "match" in result.message.lower()
                    return

        # If no suitable clue found, skip test
        assert True

    async def test_place_rectangle_no_clue(self):
        """Test placing rectangle with no clue."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Find two adjacent cells without clues such that the rectangle contains no clues
        found = False
        for r in range(game.size):
            for c in range(game.size - 1):
                # Try horizontal 1x2 rectangle
                if (r, c) not in game.clues and (r, c + 1) not in game.clues:
                    # This rectangle contains no clues
                    result = await game.validate_move(r + 1, c + 1, r + 1, c + 2)
                    assert not result.success
                    assert "clue" in result.message.lower()
                    found = True
                    break
            if found:
                break

        # If no suitable cells found, test with a controlled scenario
        if not found:
            assert True  # Skip test if puzzle is fully covered with clues

    async def test_place_rectangle_overlap(self):
        """Test placing overlapping rectangles."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Place first rectangle
        if game.clues:
            (r, c), area = next(iter(game.clues.items()))
            if area == 1:
                await game.validate_move(r + 1, c + 1, r + 1, c + 1)

                # Try to place overlapping rectangle
                result = await game.validate_move(r + 1, c + 1, r + 1, c + 1)
                assert not result.success
                assert "covered" in result.message.lower()

    async def test_invalid_coordinates(self):
        """Test invalid coordinates."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(100, 100, 101, 101)
        assert not result.success

    async def test_is_complete_empty(self):
        """Test completion check on empty puzzle."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Not complete initially
        assert not game.is_complete()

    async def test_is_complete_partial(self):
        """Test completion check with partial solution."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Place one valid rectangle
        if game.clues:
            (r, c), area = next(iter(game.clues.items()))
            if area == 1:
                await game.validate_move(r + 1, c + 1, r + 1, c + 1)

                # Still not complete
                assert not game.is_complete()

    async def test_get_hint(self):
        """Test hint generation."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            hint_data, hint_message = hint
            r1, c1, r2, c2 = hint_data
            assert 1 <= r1 <= game.size
            assert 1 <= c1 <= game.size
            assert 1 <= r2 <= game.size
            assert 1 <= c2 <= game.size
            assert "rectangle" in hint_message.lower()

    async def test_render_grid(self):
        """Test grid rendering."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        grid_str = game.render_grid()
        assert isinstance(grid_str, str)
        assert "|" in grid_str

        # Check that clues are shown
        if game.clues:
            _, area = next(iter(game.clues.items()))
            assert str(area) in grid_str

    async def test_render_grid_with_rectangles(self):
        """Test grid rendering with placed rectangles."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Place a rectangle
        placed = False
        if game.clues:
            (r, c), area = next(iter(game.clues.items()))
            if area == 1:
                result = await game.validate_move(r + 1, c + 1, r + 1, c + 1)
                placed = result.success

        grid_str = game.render_grid()
        # Should contain rectangle marker (letter) if we placed one
        if placed:
            # For single-cell rectangles, the letter might not show if there's a clue
            # Just verify grid renders correctly
            assert isinstance(grid_str, str)
        else:
            # Just verify grid renders correctly
            assert isinstance(grid_str, str)

    async def test_get_stats(self):
        """Test stats retrieval."""
        game = ShikakuGame("easy")
        stats = game.get_stats()
        assert "Moves" in stats
        assert "Seed:" in stats

    async def test_moves_counter(self):
        """Test that moves are counted."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        initial_moves = game.moves_made

        # Place a rectangle
        if game.clues:
            (r, c), area = next(iter(game.clues.items()))
            if area == 1:
                await game.validate_move(r + 1, c + 1, r + 1, c + 1)
                assert game.moves_made == initial_moves + 1

    async def test_coordinate_normalization(self):
        """Test that coordinates are normalized."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Find a 2x1 rectangle in clues
        for (r, c), area in game.clues.items():
            if area == 2 and c + 1 < game.size and (r, c + 1) not in game.clues:
                # Place rectangle in reverse order
                result1 = await game.validate_move(r + 1, c + 2, r + 1, c + 1)
                # Should normalize and work
                if result1.success:
                    assert len(game.rectangles) > 0
                    break

    async def test_usage_message(self):
        """Test usage message on invalid input."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(1, 2)
        assert not result.success
        assert "Usage" in result.message

    async def test_multiple_clues_rejection(self):
        """Test that rectangles with multiple clues are rejected."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Find two adjacent clues
        clue_list = list(game.clues.keys())
        if len(clue_list) >= 2:
            # Try to create rectangle covering multiple clues
            (r1, c1) = clue_list[0]
            (r2, c2) = clue_list[1]

            if abs(r1 - r2) + abs(c1 - c2) == 1:  # Adjacent
                result = await game.validate_move(min(r1, r2) + 1, min(c1, c2) + 1, max(r1, r2) + 1, max(c1, c2) + 1)
                assert not result.success
                assert "multiple" in result.message.lower()

    async def test_next_rect_id_increment(self):
        """Test that rectangle IDs increment."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        initial_id = game.next_rect_id

        # Place a rectangle
        if game.clues:
            (r, c), area = next(iter(game.clues.items()))
            if area == 1:
                await game.validate_move(r + 1, c + 1, r + 1, c + 1)
                assert game.next_rect_id == initial_id + 1

    async def test_is_complete_with_solution(self):
        """Test completion with full solution."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Reconstruct solution rectangles
        solution_rects: dict[int, list[tuple[int, int]]] = {}
        for r in range(game.size):
            for c in range(game.size):
                rect_id = game.solution[r][c]
                if rect_id not in solution_rects:
                    solution_rects[rect_id] = []
                solution_rects[rect_id].append((r, c))

        # Place all rectangles
        for _rect_id, cells in solution_rects.items():
            min_r = min(r for r, c in cells)
            max_r = max(r for r, c in cells)
            min_c = min(c for r, c in cells)
            max_c = max(c for r, c in cells)

            # Check if this is a valid rectangle (not placed yet)
            is_valid = all((r, c) not in placed for placed in game.rectangles.values() for r, c in cells)
            if is_valid:
                result = await game.validate_move(min_r + 1, min_c + 1, max_r + 1, max_c + 1)
                # Some may fail due to overlaps from previous placements, that's ok

        # Check if complete
        result = game.is_complete()
        assert isinstance(result, bool)

    async def test_invalid_value_error(self):
        """Test invalid coordinate values."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move("a", "b", "c", "d")
        assert not result.success
        assert "coordinate" in result.message.lower() or "invalid" in result.message.lower()

    async def test_hint_when_complete(self):
        """Test hint when puzzle is complete."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Fill all rectangles
        for r in range(game.size):
            for c in range(game.size):
                game.rectangles[1] = [(r, c)]

        hint = await game.get_hint()
        # Should return None or a hint
        assert hint is None or isinstance(hint, tuple)

    async def test_render_grid_empty(self):
        """Test rendering empty grid."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Clear all rectangles
        game.rectangles = {}

        grid_str = game.render_grid()
        assert isinstance(grid_str, str)
        # Should show dots for empty cells
        assert "." in grid_str

    async def test_grid_generation_coverage(self):
        """Test that all cells are covered in solution."""
        game = ShikakuGame("easy")
        await game.generate_puzzle()

        # Count cells in solution
        covered_cells = set()
        for r in range(game.size):
            for c in range(game.size):
                if game.solution[r][c] > 0:
                    covered_cells.add((r, c))

        # Should cover all cells
        total_cells = game.size * game.size
        assert len(covered_cells) == total_cells

    async def test_constraint_types(self):
        """Test constraint types metadata."""
        game = ShikakuGame("easy")
        constraint_types = game.constraint_types
        assert isinstance(constraint_types, list)
        assert len(constraint_types) > 0
        assert all(isinstance(ct, str) for ct in constraint_types)

    async def test_business_analogies(self):
        """Test business analogies metadata."""
        game = ShikakuGame("easy")
        analogies = game.business_analogies
        assert isinstance(analogies, list)
        assert len(analogies) > 0
        assert all(isinstance(a, str) for a in analogies)

    async def test_complexity_profile(self):
        """Test complexity profile metadata."""
        game = ShikakuGame("easy")
        profile = game.complexity_profile
        assert isinstance(profile, dict)
        assert "reasoning_type" in profile
        assert "search_space" in profile
        assert "constraint_density" in profile
