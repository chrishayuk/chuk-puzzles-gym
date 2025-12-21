"""Gymnasium-compatible environment API for Puzzle Arcade.

This module provides a standard RL environment interface for puzzle games,
compatible with Gymnasium (the maintained fork of OpenAI Gym).

Usage:
    from puzzle_arcade_server.gym_env import PuzzleEnv

    env = PuzzleEnv("sudoku", difficulty="medium", seed=42)
    obs, info = env.reset()

    while not done:
        action = agent.decide(obs)
        obs, reward, terminated, truncated, info = env.step(action)

    env.close()
"""

from typing import Any, SupportsFloat

from .games import AVAILABLE_GAMES
from .games._base import PuzzleGame
from .models import SolverConfig


class PuzzleEnv:
    """Gymnasium-compatible environment for puzzle games.

    This provides a standard RL interface for puzzle games with:
    - Discrete action space (game-specific commands)
    - Dictionary observation space with grid and metadata
    - Configurable reward shaping
    - Solver configuration as experimental variable

    Attributes:
        game_name: Name of the puzzle game
        difficulty: Difficulty level (easy, medium, hard)
        seed: Random seed for puzzle generation
        solver_config: Configuration for hint/solver usage
        reward_config: Configuration for reward shaping
    """

    # Reward configuration defaults
    DEFAULT_REWARDS = {
        "correct_placement": 1.0,
        "invalid_attempt": -0.5,
        "hint_penalty": -0.1,
        "completion_bonus": 10.0,
        "efficiency_multiplier": 1.0,
    }

    def __init__(
        self,
        game_name: str,
        difficulty: str = "easy",
        seed: int | None = None,
        solver_config: SolverConfig | None = None,
        reward_config: dict[str, float] | None = None,
        max_steps: int = 1000,
    ):
        """Initialize the puzzle environment.

        Args:
            game_name: Name of the puzzle game (e.g., 'sudoku', 'kenken')
            difficulty: Difficulty level ('easy', 'medium', 'hard')
            seed: Random seed for reproducible puzzles
            solver_config: Solver/hint configuration
            reward_config: Custom reward values (merged with defaults)
            max_steps: Maximum steps before truncation
        """
        if game_name not in AVAILABLE_GAMES:
            available = ", ".join(sorted(AVAILABLE_GAMES.keys()))
            raise ValueError(f"Unknown game '{game_name}'. Available: {available}")

        self.game_name = game_name
        self.difficulty = difficulty
        self._initial_seed = seed
        self.solver_config = solver_config or SolverConfig()
        self.max_steps = max_steps

        # Merge reward config with defaults
        self.reward_config = self.DEFAULT_REWARDS.copy()
        if reward_config:
            self.reward_config.update(reward_config)

        # Game state
        self._game: PuzzleGame | None = None
        self._step_count = 0
        # AVAILABLE_GAMES contains concrete subclasses of PuzzleGame
        self._game_class: type[PuzzleGame] = AVAILABLE_GAMES[game_name]  # type: ignore[type-abstract]

    @property
    def unwrapped(self) -> "PuzzleEnv":
        """Return the base environment (Gymnasium compatibility)."""
        return self

    async def reset(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Reset the environment to a new puzzle.

        Args:
            seed: Optional seed for this episode (overrides init seed)
            options: Additional options (e.g., difficulty override)

        Returns:
            Tuple of (observation, info)
        """
        # Use provided seed, or fall back to initial seed, or generate random
        episode_seed = seed if seed is not None else self._initial_seed

        # Allow difficulty override in options
        difficulty = self.difficulty
        if options and "difficulty" in options:
            difficulty = options["difficulty"]

        # Create and initialize the game
        self._game = self._game_class(
            difficulty=difficulty,
            seed=episode_seed,
            solver_config=self.solver_config,
        )
        await self._game.generate_puzzle()
        self._step_count = 0

        return self._get_observation(), self._get_info()

    async def step(
        self,
        action: str | tuple[str, ...] | list[Any],
    ) -> tuple[dict[str, Any], SupportsFloat, bool, bool, dict[str, Any]]:
        """Take a step in the environment.

        Args:
            action: Action to take. Can be:
                - str: Full command string (e.g., "place 1 5 7")
                - tuple/list: Command parts (e.g., ("place", 1, 5, 7))

        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        if self._game is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        # Parse action
        if isinstance(action, str):
            action_str = action
        else:
            action_str = " ".join(str(x) for x in action)

        # Execute action
        parts = action_str.strip().split()
        if not parts:
            # Empty action
            reward = self.reward_config["invalid_attempt"]
            self._game.invalid_moves += 1
            return (
                self._get_observation(),
                reward,
                False,
                self._step_count >= self.max_steps,
                {"action": action_str, "success": False, "message": "Empty action"},
            )

        # Only lowercase the command, preserve case for arguments
        # (important for games like logic/einstein with named values)
        cmd = parts[0].lower()
        args = parts[1:]

        # Handle hint request
        if cmd == "hint":
            if self._game.record_hint():
                hint_result = await self._game.get_hint()
                if hint_result:
                    hint_data, hint_message = hint_result
                    reward = self.reward_config["hint_penalty"]
                    return (
                        self._get_observation(),
                        reward,
                        False,
                        False,
                        {"action": action_str, "success": True, "hint": hint_message, "hint_data": hint_data},
                    )
            reward = self.reward_config["invalid_attempt"]
            return (
                self._get_observation(),
                reward,
                False,
                False,
                {"action": action_str, "success": False, "message": "Hint not available"},
            )

        # Execute game-specific action
        try:
            result = await self._execute_action(cmd, args)
        except Exception as e:
            self._game.invalid_moves += 1
            return (
                self._get_observation(),
                self.reward_config["invalid_attempt"],
                False,
                self._step_count >= self.max_steps,
                {"action": action_str, "success": False, "error": str(e)},
            )

        self._step_count += 1

        # Calculate reward
        if result.success:
            reward = self.reward_config["correct_placement"]

            # Check for completion
            terminated = self._game.is_complete()
            if terminated:
                # Add completion bonus with efficiency multiplier
                optimal = self._game.optimal_steps
                if optimal and self._game.moves_made > 0:
                    efficiency = min(1.0, optimal / self._game.moves_made)
                else:
                    efficiency = 1.0
                reward += (
                    self.reward_config["completion_bonus"] * efficiency * self.reward_config["efficiency_multiplier"]
                )
        else:
            reward = self.reward_config["invalid_attempt"]
            self._game.invalid_moves += 1
            terminated = False

        truncated = self._step_count >= self.max_steps

        info = {
            "action": action_str,
            "success": result.success,
            "message": result.message,
            "moves": self._game.moves_made,
            "invalid_moves": self._game.invalid_moves,
            "hints_used": self._game.hints_used,
        }

        return self._get_observation(), reward, terminated, truncated, info

    async def _execute_action(self, cmd: str, args: list[str]) -> Any:
        """Execute a game-specific action.

        This maps commands to game methods based on the game type.
        """
        if self._game is None:
            raise RuntimeError("No game initialized")

        # Common commands for grid-based puzzles
        if cmd in ("place", "p"):
            if len(args) >= 3:
                row, col, val = int(args[0]), int(args[1]), int(args[2])
                return await self._game.validate_move(row, col, val)

        if cmd in ("clear", "c"):
            if len(args) >= 2:
                row, col = int(args[0]), int(args[1])
                return await self._game.validate_move(row, col, 0)

        # Game-specific commands
        game_name = self.game_name.lower()

        if game_name == "lights_out" and cmd == "press":
            row, col = int(args[0]), int(args[1])
            return await self._game.validate_move(row, col)

        if game_name == "sokoban" and cmd == "move":
            return await self._game.validate_move(args[0])

        if game_name == "minesweeper":
            if cmd == "reveal":
                row, col = int(args[0]), int(args[1])
                return await self._game.validate_move("reveal", row, col)
            if cmd == "flag":
                row, col = int(args[0]), int(args[1])
                return await self._game.validate_move("flag", row, col)

        if game_name == "mastermind" and cmd == "guess":
            guess = [int(x) for x in args]
            return await self._game.validate_move(*guess)

        if game_name == "einstein":
            # Einstein uses assign <house> <attribute> <value>
            # Value may contain spaces (e.g., "Blue Master")
            if cmd == "assign":
                house, attribute = int(args[0]), args[1]
                value = " ".join(args[2:])  # Join remaining args for multi-word values
                return await self._game.validate_move(house, attribute, value)

        if game_name == "logic":
            # Logic grid uses connect <person_name> <category> <value> (3 args)
            # which maps to validate_move("person", person_name, category, value, True)
            # or connect <cat1> <val1> <cat2> <val2> (4 args)
            if cmd == "connect":
                if len(args) == 3:
                    # Shorthand: connect <person_name> <category> <value>
                    # e.g., connect Alice color Blue -> ("person", "Alice", "color", "Blue", True)
                    return await self._game.validate_move("person", args[0], args[1], args[2], True)
                elif len(args) >= 4:
                    return await self._game.validate_move(args[0], args[1], args[2], args[3], True)
            if cmd == "exclude":
                if len(args) == 3:
                    return await self._game.validate_move("person", args[0], args[1], args[2], False)
                elif len(args) >= 4:
                    return await self._game.validate_move(args[0], args[1], args[2], args[3], False)

        if game_name == "bridges" and cmd == "bridge":
            r1, c1, r2, c2, count = int(args[0]), int(args[1]), int(args[2]), int(args[3]), int(args[4])
            return await self._game.validate_move(r1, c1, r2, c2, count)

        if game_name == "shikaku" and cmd == "rect":
            # Shikaku uses rect <r1> <c1> <r2> <c2>
            r1, c1, r2, c2 = int(args[0]), int(args[1]), int(args[2]), int(args[3])
            return await self._game.validate_move(r1, c1, r2, c2)

        if game_name == "nonogram":
            # Nonogram uses fill/mark <row> <col> [value]
            if cmd == "fill":
                row, col = int(args[0]), int(args[1])
                return await self._game.validate_move(row, col, 1)
            if cmd == "mark":
                row, col = int(args[0]), int(args[1])
                return await self._game.validate_move(row, col, 0)
            if cmd == "clear":
                row, col = int(args[0]), int(args[1])
                return await self._game.validate_move(row, col, -1)
            if cmd == "set":
                row, col, cell_val = int(args[0]), int(args[1]), int(args[2])
                return await self._game.validate_move(row, col, cell_val)

        if game_name == "slither" and cmd == "set":
            edge_type, row, col, state = args[0], int(args[1]), int(args[2]), int(args[3])
            return await self._game.validate_move(edge_type, row, col, state)

        if game_name == "nurikabe" and cmd == "mark":
            row, col, color = int(args[0]), int(args[1]), args[2]
            return await self._game.validate_move(row, col, color)

        if game_name == "hitori" and cmd == "shade":
            row, col = int(args[0]), int(args[1])
            return await self._game.validate_move(row, col, "shade")

        if game_name == "knapsack":
            if cmd == "select":
                return await self._game.validate_move("select", int(args[0]))
            if cmd == "deselect":
                return await self._game.validate_move("deselect", int(args[0]))

        if game_name == "scheduler":
            if cmd == "assign":
                task, worker, start = int(args[0]), int(args[1]), int(args[2])
                return await self._game.validate_move(task, worker, start)
            if cmd == "unassign":
                return await self._game.validate_move(int(args[0]), 0, -1)

        # Default: try validate_move with parsed args
        parsed_args: list[int | str] = []
        for arg in args:
            try:
                parsed_args.append(int(arg))
            except ValueError:
                parsed_args.append(arg)

        return await self._game.validate_move(*parsed_args)

    def _get_observation(self) -> dict[str, Any]:
        """Get the current observation."""
        if self._game is None:
            return {"error": "no_game"}

        obs = {
            "game": self._game.name,
            "difficulty": self._game.difficulty.value,
            "seed": self._game.seed,
            "moves": self._game.moves_made,
            "invalid_moves": self._game.invalid_moves,
            "hints_used": self._game.hints_used,
            "hints_remaining": self._game.hints_remaining,
            "is_complete": self._game.is_complete(),
        }

        # Add grid if available
        if hasattr(self._game, "grid"):
            obs["grid"] = self._game.grid

        # Add rendered view
        obs["render"] = self._game.render_grid()

        return obs

    def _get_info(self) -> dict[str, Any]:
        """Get additional info about the environment state."""
        if self._game is None:
            return {}

        profile = self._game.difficulty_profile
        return {
            "optimal_steps": self._game.optimal_steps,
            "difficulty_profile": {
                "logic_depth": profile.logic_depth,
                "branching_factor": profile.branching_factor,
                "state_observability": profile.state_observability,
                "constraint_density": profile.constraint_density,
            },
            "constraint_types": self._game.constraint_types,
            "solver_config": {
                "solver_allowed": self.solver_config.solver_allowed,
                "hint_budget": self.solver_config.hint_budget,
                "hint_penalty": self.solver_config.hint_penalty,
            },
        }

    def render(self, mode: str = "ansi") -> str | None:
        """Render the environment.

        Args:
            mode: Render mode ('ansi' for text output)

        Returns:
            Rendered string if mode is 'ansi', None otherwise
        """
        if self._game is None:
            return None

        if mode == "ansi":
            return self._game.render_grid()
        return None

    def close(self) -> None:
        """Clean up environment resources."""
        self._game = None

    @property
    def game(self) -> PuzzleGame | None:
        """Access the underlying game instance."""
        return self._game

    @classmethod
    def available_games(cls) -> list[str]:
        """Get list of available game names."""
        return sorted(AVAILABLE_GAMES.keys())

    @classmethod
    def make(
        cls,
        game_name: str,
        difficulty: str = "easy",
        seed: int | None = None,
        **kwargs: Any,
    ) -> "PuzzleEnv":
        """Factory method to create an environment (Gymnasium-style).

        Args:
            game_name: Name of the puzzle game
            difficulty: Difficulty level
            seed: Random seed
            **kwargs: Additional arguments passed to __init__

        Returns:
            Configured PuzzleEnv instance
        """
        return cls(game_name, difficulty=difficulty, seed=seed, **kwargs)
