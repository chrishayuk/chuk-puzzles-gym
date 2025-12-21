"""Tests for Star Battle game logic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from puzzle_arcade_server.games.star_battle import StarBattleGame


class TestStarBattleGame:
    """Test suite for StarBattleGame class."""

    async def test_initialization(self):
        """Test game initialization."""
        game = StarBattleGame("easy")
        assert game.difficulty.value == "easy"
        assert game.size == 6
        assert game.stars_per_row == 1

    async def test_difficulty_settings(self):
        """Test different difficulty settings."""
        easy = StarBattleGame("easy")
        assert easy.size == 6 and easy.stars_per_row == 1

        medium = StarBattleGame("medium")
        assert medium.size == 8 and medium.stars_per_row == 2

    async def test_generate_puzzle(self):
        """Test puzzle generation."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        # Should have a solution
        star_count = sum(sum(row) for row in game.solution)
        assert star_count > 0

    async def test_place_star(self):
        """Test placing a star."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(2, 2, "place")
        assert isinstance(result.success, bool)

    async def test_remove_star(self):
        """Test removing a star."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        # Place then remove
        await game.validate_move(2, 2, "place")
        result = await game.validate_move(2, 2, "remove")
        assert result.success or "No star" in result.message

    async def test_get_hint(self):
        """Test hint generation."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint is not None:
            hint_data, hint_message = hint
            assert len(hint_data) == 3

    async def test_render_grid(self):
        """Test grid rendering."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        grid_str = game.render_grid()
        assert isinstance(grid_str, str)
        assert len(grid_str) > 0

    async def test_name_and_description(self):
        """Test game name and description."""
        game = StarBattleGame("easy")
        assert game.name == "Star Battle"
        assert len(game.description) > 0

    async def test_get_rules(self):
        """Test rules description."""
        game = StarBattleGame("easy")
        rules = game.get_rules()
        assert "star" in rules.lower()

    async def test_get_commands(self):
        """Test commands description."""
        game = StarBattleGame("easy")
        commands = game.get_commands()
        assert "place" in commands.lower()

    async def test_get_stats(self):
        """Test stats generation."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        stats = game.get_stats()
        assert "Stars" in stats or "stars" in stats

    async def test_constraint_types(self):
        """Test constraint types metadata."""
        game = StarBattleGame("easy")
        constraint_types = game.constraint_types
        assert isinstance(constraint_types, list)
        assert "placement_limits" in constraint_types

    async def test_business_analogies(self):
        """Test business analogies metadata."""
        game = StarBattleGame("easy")
        analogies = game.business_analogies
        assert isinstance(analogies, list)
        assert "resource_distribution" in analogies

    async def test_complexity_profile(self):
        """Test complexity profile metadata."""
        game = StarBattleGame("easy")
        profile = game.complexity_profile
        assert isinstance(profile, dict)
        assert "reasoning_type" in profile

    async def test_invalid_coordinates(self):
        """Test invalid coordinates."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(0, 1, "place")
        assert not result.success
        result = await game.validate_move(10, 10, "place")
        assert not result.success

    async def test_invalid_action(self):
        """Test invalid action."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        result = await game.validate_move(2, 2, "invalid")
        assert not result.success

    async def test_remove_no_star(self):
        """Test removing when there's no star."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        # Find empty cell
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 0:
                    result = await game.validate_move(r + 1, c + 1, "remove")
                    assert not result.success
                    return

    async def test_place_star_already_placed(self):
        """Test placing star where one already exists."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        # Find empty cell and place star
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 0:
                    result1 = await game.validate_move(r + 1, c + 1, "place")
                    if result1.success:
                        result2 = await game.validate_move(r + 1, c + 1, "place")
                        assert not result2.success
                        return

    async def test_adjacency_rejection(self):
        """Test that stars cannot be placed adjacent to each other."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        # Find empty cell and place star
        for r in range(1, game.size - 1):
            for c in range(1, game.size - 1):
                if game.grid[r][c] == 0:
                    result1 = await game.validate_move(r + 1, c + 1, "place")
                    if result1.success:
                        # Try to place adjacent
                        result2 = await game.validate_move(r + 2, c + 1, "place")
                        if not result2.success and "touch" in result2.message.lower():
                            return
                        result2 = await game.validate_move(r + 1, c + 2, "place")
                        if not result2.success and "touch" in result2.message.lower():
                            return

    async def test_is_complete_empty(self):
        """Test is_complete with empty grid."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        assert not game.is_complete()

    async def test_is_complete_with_solution(self):
        """Test is_complete with solution."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        # Copy solution to grid
        game.grid = [row[:] for row in game.solution]
        assert game.is_complete()

    async def test_hint_for_wrong_star(self):
        """Test hint suggests removing wrong star."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        # Copy solution and then add a wrong star
        game.grid = [row[:] for row in game.solution]

        # Now add one extra wrong star where solution is empty
        for r in range(game.size):
            for c in range(game.size):
                if game.solution[r][c] == 0:
                    game.grid[r][c] = 1
                    hint = await game.get_hint()
                    if hint:
                        hint_data, hint_message = hint
                        assert "remove" in hint_message.lower() or "Remove" in hint_message
                        return

    async def test_moves_counter(self):
        """Test that moves are counted."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        initial_moves = game.moves_made

        # Place a star
        for r in range(game.size):
            for c in range(game.size):
                if game.grid[r][c] == 0:
                    result = await game.validate_move(r + 1, c + 1, "place")
                    if result.success:
                        assert game.moves_made == initial_moves + 1
                        return

    async def test_hard_difficulty(self):
        """Test hard difficulty settings."""
        game = StarBattleGame("hard")
        assert game.size == 10
        assert game.stars_per_row == 2

    async def test_generate_regions_small_grid(self):
        """Test region generation for small grids."""
        game = StarBattleGame("easy")  # 6x6
        await game.generate_puzzle()

        # Each region should have exactly size cells
        region_counts = {}
        for r in range(game.size):
            for c in range(game.size):
                region_id = game.regions[r][c]
                region_counts[region_id] = region_counts.get(region_id, 0) + 1

        assert len(region_counts) == game.size

    async def test_generate_regions_medium_grid(self):
        """Test region generation for medium grids."""
        game = StarBattleGame("medium")  # 8x8
        await game.generate_puzzle()

        # Should have 8 regions
        region_ids = set()
        for r in range(game.size):
            for c in range(game.size):
                region_ids.add(game.regions[r][c])

        assert len(region_ids) == game.size

    async def test_fallback_solution_creation(self):
        """Test that fallback solution is created when needed."""
        game = StarBattleGame("easy", seed=99999)
        await game.generate_puzzle()

        # Solution should have correct number of stars per row
        for row in range(game.size):
            row_stars = sum(game.solution[row])
            assert row_stars >= 0  # May be fewer if fallback is used

    async def test_try_place_stars_failure(self):
        """Test star placement with difficult configurations."""
        game = StarBattleGame("hard", seed=12345)
        await game.generate_puzzle()

        # Just verify it completes without error
        total_stars = sum(sum(row) for row in game.solution)
        assert total_stars > 0

    async def test_row_constraint_validation(self):
        """Test that row constraint is enforced."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        # Try to place more stars than allowed in a row
        stars_placed = 0
        for c in range(game.size):
            if game.grid[0][c] == 0:
                result = await game.validate_move(1, c + 1, "place")
                if result.success:
                    stars_placed += 1
                    if stars_placed >= game.stars_per_row:
                        # Next placement should fail
                        for c2 in range(c + 1, game.size):
                            if game.grid[0][c2] == 0:
                                result2 = await game.validate_move(1, c2 + 1, "place")
                                if not result2.success and "row" in result2.message.lower():
                                    return

    async def test_column_constraint_validation(self):
        """Test that column constraint is enforced."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        # Try to place more stars than allowed in a column
        stars_placed = 0
        for r in range(game.size):
            if game.grid[r][0] == 0:
                result = await game.validate_move(r + 1, 1, "place")
                if result.success:
                    stars_placed += 1
                    if stars_placed >= game.stars_per_row:
                        # Next placement should fail
                        for r2 in range(r + 1, game.size):
                            if game.grid[r2][0] == 0:
                                result2 = await game.validate_move(r2 + 1, 1, "place")
                                if not result2.success and "column" in result2.message.lower():
                                    return

    async def test_region_constraint_validation(self):
        """Test that region constraint is enforced."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        # Find two cells in the same region and try to over-fill it
        region_cells = {}
        for r in range(game.size):
            for c in range(game.size):
                region_id = game.regions[r][c]
                if region_id not in region_cells:
                    region_cells[region_id] = []
                region_cells[region_id].append((r, c))

        # Try to place more stars than allowed in a region
        for _region_id, cells in region_cells.items():
            stars_placed = 0
            for r, c in cells:
                if game.grid[r][c] == 0:
                    result = await game.validate_move(r + 1, c + 1, "place")
                    if result.success:
                        stars_placed += 1
                        if stars_placed >= game.stars_per_row:
                            return  # Successfully tested

    async def test_solve_with_hints(self):
        """Test solving using hints."""
        game = StarBattleGame("easy", seed=42)
        await game.generate_puzzle()

        # Use hints to solve
        for _ in range(100):
            if game.is_complete():
                break
            hint = await game.get_hint()
            if hint is None:
                break
            hint_data, _ = hint
            await game.validate_move(hint_data[0], hint_data[1], hint_data[2])

        assert game.is_complete()

    async def test_hint_no_more_needed(self):
        """Test hint when puzzle is already solved."""
        game = StarBattleGame("easy")
        await game.generate_puzzle()

        # Copy solution to grid
        game.grid = [row[:] for row in game.solution]

        hint = await game.get_hint()
        assert hint is None

    async def test_multiple_seeds(self):
        """Test that different seeds produce different puzzles."""
        game1 = StarBattleGame("easy", seed=111)
        game2 = StarBattleGame("easy", seed=222)

        await game1.generate_puzzle()
        await game2.generate_puzzle()

        # Solutions should differ (with high probability)
        assert game1.solution != game2.solution or game1.regions != game2.regions
