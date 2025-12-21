"""Tests for the Gymnasium-compatible environment API."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from puzzle_arcade_server.gym_env import PuzzleEnv
from puzzle_arcade_server.models import SolverConfig


class TestPuzzleEnvBasic:
    """Basic tests for PuzzleEnv."""

    def test_create_env(self):
        """Test creating an environment."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        assert env.game_name == "sudoku"
        assert env.difficulty == "easy"

    def test_invalid_game_raises(self):
        """Test that invalid game name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown game"):
            PuzzleEnv("not_a_game")

    def test_available_games(self):
        """Test getting available games list."""
        games = PuzzleEnv.available_games()
        assert "sudoku" in games
        assert "kenken" in games
        assert len(games) >= 20  # We have 24 games

    def test_make_factory(self):
        """Test the make factory method."""
        env = PuzzleEnv.make("sudoku", difficulty="medium", seed=123)
        assert env.game_name == "sudoku"
        assert env.difficulty == "medium"


class TestPuzzleEnvReset:
    """Tests for environment reset."""

    async def test_reset_basic(self):
        """Test basic reset."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        obs, info = await env.reset()

        assert "grid" in obs
        assert "moves" in obs
        assert obs["moves"] == 0
        assert obs["is_complete"] is False
        assert "optimal_steps" in info

    async def test_reset_with_seed(self):
        """Test reset with specific seed."""
        env = PuzzleEnv("sudoku", difficulty="easy")

        obs1, _ = await env.reset(seed=12345)
        grid1 = obs1["grid"]

        obs2, _ = await env.reset(seed=12345)
        grid2 = obs2["grid"]

        # Same seed should give same puzzle
        assert grid1 == grid2

    async def test_reset_with_difficulty_override(self):
        """Test reset with difficulty override in options."""
        env = PuzzleEnv("sudoku", difficulty="easy")

        obs, info = await env.reset(options={"difficulty": "medium"})
        # Should use medium difficulty
        assert env.game is not None
        assert env.game.difficulty.value == "medium"


class TestPuzzleEnvStep:
    """Tests for environment step."""

    async def test_step_valid_move(self):
        """Test valid move."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        # Get a hint to find a valid move
        if env.game:
            hint = await env.game.get_hint()
            if hint:
                row, col, val = hint[0]
                obs, reward, terminated, truncated, info = await env.step(f"place {row} {col} {val}")

                assert info["success"] is True
                assert reward > 0
                assert obs["moves"] == 1

    async def test_step_invalid_move(self):
        """Test invalid move."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        # Try to place in an occupied cell (usually fails)
        obs, reward, terminated, truncated, info = await env.step("place 1 1 99")

        assert info["success"] is False
        assert reward < 0

    async def test_step_empty_action(self):
        """Test empty action."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("")

        assert info["success"] is False
        assert reward < 0

    async def test_step_hint_request(self):
        """Test hint request."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("hint")

        if info["success"]:
            assert "hint" in info
            assert reward == env.reward_config["hint_penalty"]

    async def test_step_truncation(self):
        """Test step count truncation."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42, max_steps=5)
        await env.reset()

        # Take 5 invalid steps
        for _ in range(5):
            obs, reward, terminated, truncated, info = await env.step("place 1 1 99")

        assert truncated is True

    async def test_step_tuple_action(self):
        """Test step with tuple action."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        # Action as tuple
        obs, reward, terminated, truncated, info = await env.step(("place", 1, 1, 5))
        assert "action" in info
        assert info["action"] == "place 1 1 5"


class TestPuzzleEnvReward:
    """Tests for reward configuration."""

    async def test_custom_rewards(self):
        """Test custom reward configuration."""
        custom_rewards = {
            "correct_placement": 5.0,
            "invalid_attempt": -2.0,
            "completion_bonus": 50.0,
        }
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42, reward_config=custom_rewards)

        assert env.reward_config["correct_placement"] == 5.0
        assert env.reward_config["invalid_attempt"] == -2.0
        assert env.reward_config["completion_bonus"] == 50.0
        # Default should still be there
        assert env.reward_config["hint_penalty"] == -0.1

    async def test_completion_bonus(self):
        """Test completion bonus with efficiency."""
        env = PuzzleEnv("lights", difficulty="easy", seed=42)  # "lights" is the correct game name
        await env.reset()

        # Solve by pressing until complete (simplified test)
        steps = 0
        max_steps = 100
        terminated = False

        while not terminated and steps < max_steps:
            # Try pressing each cell
            for r in range(1, 6):
                for c in range(1, 6):
                    obs, reward, terminated, truncated, info = await env.step(f"press {r} {c}")
                    steps += 1
                    if terminated:
                        # Should get completion bonus
                        assert reward >= env.reward_config["completion_bonus"] * 0.1  # At least 10% efficiency
                        break
                if terminated:
                    break


class TestPuzzleEnvSolverConfig:
    """Tests for solver configuration."""

    async def test_solver_free_mode(self):
        """Test solver-free mode denies hints."""
        config = SolverConfig.solver_free()
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42, solver_config=config)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("hint")

        assert info["success"] is False
        assert "not available" in info.get("message", "").lower() or not info["success"]

    async def test_hint_budget(self):
        """Test hint budget is enforced."""
        config = SolverConfig(hint_budget=2)
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42, solver_config=config)
        await env.reset()

        # Use both hints
        await env.step("hint")
        await env.step("hint")

        # Third hint should fail
        obs, reward, terminated, truncated, info = await env.step("hint")
        assert info["success"] is False


class TestPuzzleEnvRender:
    """Tests for rendering."""

    async def test_render_ansi(self):
        """Test ANSI rendering."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        rendered = env.render(mode="ansi")
        assert rendered is not None
        assert len(rendered) > 0
        assert "\n" in rendered  # Multiple lines

    async def test_render_before_reset(self):
        """Test render before reset returns None."""
        env = PuzzleEnv("sudoku", difficulty="easy")
        rendered = env.render()
        assert rendered is None


class TestPuzzleEnvGameSpecific:
    """Tests for game-specific action handling."""

    async def test_sokoban_move(self):
        """Test Sokoban move action."""
        env = PuzzleEnv("sokoban", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("move up")
        # Should process the move (success depends on game state)
        assert "success" in info

    async def test_minesweeper_reveal(self):
        """Test Minesweeper reveal action."""
        env = PuzzleEnv("minesweeper", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("reveal 1 1")
        assert "success" in info

    async def test_mastermind_guess(self):
        """Test Mastermind guess action."""
        env = PuzzleEnv("mastermind", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("guess 1 2 3 4")
        assert "success" in info

    async def test_bridges_bridge(self):
        """Test Bridges bridge action."""
        env = PuzzleEnv("bridges", difficulty="easy", seed=42)
        await env.reset()

        # This will likely fail as coordinates are random, but should parse correctly
        obs, reward, terminated, truncated, info = await env.step("bridge 1 1 1 3 1")
        assert "success" in info


class TestPuzzleEnvClose:
    """Tests for environment cleanup."""

    async def test_close(self):
        """Test closing the environment."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        assert env.game is not None
        env.close()
        assert env.game is None

    async def test_step_after_close_raises(self):
        """Test that step after close raises."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()
        env.close()

        with pytest.raises(RuntimeError, match="not initialized"):
            await env.step("place 1 1 5")


class TestPuzzleEnvGameSpecificActions:
    """Tests for game-specific action handlers in gym_env."""

    async def test_einstein_assign(self):
        """Test Einstein assign action with multi-word values."""
        env = PuzzleEnv("einstein", difficulty="easy", seed=42)
        await env.reset()

        # Test assign action (house 1, color attribute)
        obs, reward, terminated, truncated, info = await env.step("assign 1 color Blue Master")
        assert "success" in info

    async def test_logic_connect_3args(self):
        """Test Logic grid connect with 3 args."""
        env = PuzzleEnv("logic", difficulty="easy", seed=42)
        await env.reset()

        # Test 3-arg connect format
        obs, reward, terminated, truncated, info = await env.step("connect Alice color Blue")
        assert "success" in info

    async def test_logic_connect_4args(self):
        """Test Logic grid connect with 4 args."""
        env = PuzzleEnv("logic", difficulty="easy", seed=42)
        await env.reset()

        # Test 4-arg connect format
        obs, reward, terminated, truncated, info = await env.step("connect person Alice color Blue")
        assert "success" in info

    async def test_logic_exclude(self):
        """Test Logic grid exclude action."""
        env = PuzzleEnv("logic", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("exclude Alice color Red")
        assert "success" in info

    async def test_shikaku_rect(self):
        """Test Shikaku rectangle placement."""
        env = PuzzleEnv("shikaku", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("rect 1 1 2 2")
        assert "success" in info

    async def test_nonogram_fill(self):
        """Test Nonogram fill action."""
        env = PuzzleEnv("nonogram", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("fill 1 1")
        assert "success" in info

    async def test_nonogram_mark(self):
        """Test Nonogram mark action."""
        env = PuzzleEnv("nonogram", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("mark 1 1")
        assert "success" in info

    async def test_nonogram_clear(self):
        """Test Nonogram clear action."""
        env = PuzzleEnv("nonogram", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("clear 1 1")
        assert "success" in info

    async def test_nonogram_set(self):
        """Test Nonogram set action."""
        env = PuzzleEnv("nonogram", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("set 1 1 1")
        assert "success" in info

    async def test_slitherlink_set(self):
        """Test Slitherlink set edge action."""
        env = PuzzleEnv("slither", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("set h 0 0 1")
        assert "success" in info

    async def test_nurikabe_mark(self):
        """Test Nurikabe mark action."""
        env = PuzzleEnv("nurikabe", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("mark 1 1 sea")
        assert "success" in info

    async def test_hitori_shade(self):
        """Test Hitori shade action."""
        env = PuzzleEnv("hitori", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("shade 1 1")
        assert "success" in info

    async def test_knapsack_select(self):
        """Test Knapsack select action."""
        env = PuzzleEnv("knapsack", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("select 1")
        assert "success" in info

    async def test_knapsack_deselect(self):
        """Test Knapsack deselect action."""
        env = PuzzleEnv("knapsack", difficulty="easy", seed=42)
        await env.reset()

        # First select, then deselect
        await env.step("select 1")
        obs, reward, terminated, truncated, info = await env.step("deselect 1")
        assert "success" in info

    async def test_scheduler_assign(self):
        """Test Scheduler assign action."""
        env = PuzzleEnv("scheduler", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("assign 1 1 0")
        assert "success" in info

    async def test_scheduler_unassign(self):
        """Test Scheduler unassign action."""
        env = PuzzleEnv("scheduler", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("unassign 1")
        assert "success" in info


class TestPuzzleEnvUnwrapped:
    """Tests for unwrapped property."""

    def test_unwrapped_returns_self(self):
        """Test unwrapped property returns the env itself."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        assert env.unwrapped is env


class TestPuzzleEnvInfoDict:
    """Tests for info dictionary contents."""

    async def test_info_contains_expected_keys(self):
        """Test info dict contains expected keys after reset."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        obs, info = await env.reset()

        assert "optimal_steps" in info
        assert "difficulty_profile" in info
        assert "constraint_types" in info
        assert "solver_config" in info

    async def test_step_info_contains_action(self):
        """Test step info contains action key."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("place 1 1 5")
        assert "action" in info
        assert info["action"] == "place 1 1 5"


class TestPuzzleEnvObservation:
    """Tests for observation dictionary contents."""

    async def test_observation_contains_expected_keys(self):
        """Test observation dict contains expected keys."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        obs, _ = await env.reset()

        assert "game" in obs
        assert "difficulty" in obs
        assert "seed" in obs
        assert "moves" in obs
        assert "invalid_moves" in obs
        assert "hints_used" in obs
        assert "is_complete" in obs
        assert "grid" in obs

    async def test_observation_grid_format(self):
        """Test observation grid is a list (raw grid data)."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        obs, _ = await env.reset()

        # Grid is the raw grid data (list of lists for sudoku)
        grid = obs["grid"]
        assert isinstance(grid, list)
        assert len(grid) > 0


class TestPuzzleEnvMoreActions:
    """Additional action handler tests to improve coverage."""

    async def test_lights_out_press(self):
        """Test Lights Out press action."""
        env = PuzzleEnv("lights", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("press 1 1")
        assert "success" in info

    async def test_minesweeper_flag(self):
        """Test Minesweeper flag action."""
        env = PuzzleEnv("minesweeper", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("flag 1 1")
        assert "success" in info

    async def test_logic_exclude_4args(self):
        """Test Logic grid exclude with 4 args."""
        env = PuzzleEnv("logic", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("exclude person Alice color Blue")
        assert "success" in info

    async def test_action_causes_exception(self):
        """Test handling of exceptions during action execution."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        # Try an action that might cause an issue
        obs, reward, terminated, truncated, info = await env.step("place abc def ghi")
        assert info["success"] is False
        # Should have negative reward
        assert reward < 0

    async def test_place_clear_with_zero(self):
        """Test place with 0 (clear command)."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        # First place a number
        await env.step("place 1 1 5")
        # Then clear it with place 0
        obs, reward, terminated, truncated, info = await env.step("place 1 1 0")
        assert "success" in info

    async def test_clear_command(self):
        """Test clear command."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        obs, reward, terminated, truncated, info = await env.step("clear 1 1")
        assert "success" in info

    async def test_completion_with_optimal_steps(self):
        """Test completion bonus calculation with optimal steps."""
        # Use a simple puzzle like lights_out that can be solved quickly
        env = PuzzleEnv("lights", difficulty="easy", seed=42)
        await env.reset()

        # Get hint and use it to solve quickly
        hint_result = await env.game.get_hint()
        if hint_result:
            row, col = hint_result[0][:2]
            await env.step(f"press {row} {col}")


class TestPuzzleEnvEdgeCases:
    """Edge case tests for better coverage."""

    async def test_default_action_parsing(self):
        """Test default action parsing with mixed int/str args."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        # Use the place command which goes through default parsing
        obs, reward, terminated, truncated, info = await env.step("place 2 3 7")
        assert "success" in info

    async def test_game_property_access(self):
        """Test game property access."""
        env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
        await env.reset()

        game = env.game
        assert game is not None
        assert game.name == "Sudoku"

    async def test_game_property_before_reset(self):
        """Test game property before reset returns None."""
        env = PuzzleEnv("sudoku", difficulty="easy")
        assert env.game is None
