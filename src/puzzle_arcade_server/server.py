#!/usr/bin/env python3
"""
Puzzle Arcade Server

A multi-game telnet server hosting various logic puzzle games.
LLMs with MCP solver access can telnet in and solve these puzzles.
"""

import asyncio
import json
import logging
import os
import sys

# Add the chuk-protocol-server to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "chuk-protocol-server", "src"))

from chuk_protocol_server.handlers.telnet_handler import TelnetHandler
from chuk_protocol_server.servers.telnet_server import TelnetServer

from .games import AVAILABLE_GAMES, GAME_COMMAND_HANDLERS
from .games._base import GameCommandHandler, PuzzleGame
from .models import DifficultyLevel, GameCommand, OutputMode

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger("puzzle-arcade")


class ArcadeHandler(TelnetHandler):
    """Handler for Puzzle Arcade telnet sessions."""

    async def on_connect(self) -> None:
        """Initialize state when a client connects."""
        await super().on_connect()
        self.current_game: PuzzleGame | None = None
        self.game_handler: GameCommandHandler | None = None
        self.in_menu = True
        self.output_mode = OutputMode.NORMAL

    async def send_result(self, success: bool, message: str, code: str = "") -> None:
        """Send a result message based on current output mode.

        Args:
            success: Whether the operation succeeded
            message: Human-readable message
            code: Short code for strict/json mode (e.g., 'PLACED', 'INVALID_MOVE')
        """
        if self.output_mode == OutputMode.JSON:
            response = {"type": "result", "success": success, "code": code, "message": message}
            if self.current_game:
                response["state"] = self.get_game_state_dict()
            await self.send_json_response(**response)
        elif self.output_mode == OutputMode.STRICT:
            prefix = "OK" if success else "ERR"
            await self.send_line(f"{prefix}:{code}" if code else prefix)
        else:
            await self.send_line(message)

    async def send_game_complete(self) -> None:
        """Send game completion message based on output mode."""
        if not self.current_game:
            return

        if self.output_mode == OutputMode.JSON:
            await self.send_json_response(
                type="complete",
                success=True,
                game=self.current_game.name,
                moves=self.current_game.moves_made,
                invalid_moves=self.current_game.invalid_moves,
                hints_used=self.current_game.hints_used,
                optimal_steps=self.current_game.optimal_steps,
            )
        elif self.output_mode == OutputMode.STRICT:
            await self.send_line(
                f"COMPLETE:{self.current_game.moves_made}:{self.current_game.invalid_moves}:"
                f"{self.current_game.hints_used}"
            )
        else:
            await self.send_line("\n" + "=" * 50)
            await self.send_line("CONGRATULATIONS! YOU SOLVED IT!")
            await self.send_line("=" * 50)
            await self.send_line(self.current_game.get_stats())
            await self.send_line("\nType 'menu' to play another game.")
            await self.send_line("=" * 50 + "\n")

    async def send_json_response(self, **kwargs) -> None:
        """Send a JSON-formatted response for RL integration."""
        await self.send_line(json.dumps(kwargs, separators=(",", ":")))

    def get_game_state_dict(self) -> dict:
        """Get current game state as a dictionary for JSON mode."""
        if not self.current_game:
            return {"error": "no_game"}

        # Get grid representation
        grid = None
        if hasattr(self.current_game, "grid"):
            grid = self.current_game.grid

        # Get difficulty profile
        profile = self.current_game.difficulty_profile
        profile_dict = {
            "logic_depth": profile.logic_depth,
            "branching_factor": profile.branching_factor,
            "state_observability": profile.state_observability,
            "constraint_density": profile.constraint_density,
        }

        return {
            "game": self.current_game.name,
            "difficulty": self.current_game.difficulty.value,
            "seed": self.current_game.seed,
            "moves": self.current_game.moves_made,
            "invalid_moves": self.current_game.invalid_moves,
            "hints_used": self.current_game.hints_used,
            "hints_remaining": self.current_game.hints_remaining,
            "optimal_steps": self.current_game.optimal_steps,
            "is_complete": self.current_game.is_complete(),
            "difficulty_profile": profile_dict,
            "grid": grid,
        }

    async def show_main_menu(self) -> None:
        """Display the main game selection menu."""
        await self.send_line("\n" + "=" * 50)
        await self.send_line("       WELCOME TO THE PUZZLE ARCADE!        ")
        await self.send_line("=" * 50)
        await self.send_line("\nSelect a game:\n")

        # List available games
        game_list = list(AVAILABLE_GAMES.items())
        for idx, (_game_id, game_class) in enumerate(game_list, 1):
            # Create a temporary instance to get name and description
            temp_game = game_class("easy")  # type: ignore[abstract]
            await self.send_line(f"  {idx}) {temp_game.name:15s} - {temp_game.description}")

        await self.send_line("\nCommands:")
        await self.send_line("  <number> [difficulty] [seed]  - Select by number")
        await self.send_line("  <name> [difficulty] [seed]    - Select by name")
        await self.send_line("  help                          - Show this menu again")
        await self.send_line("  quit                          - Exit the server")
        await self.send_line("\nExamples:")
        await self.send_line("  sudoku hard          - Random hard Sudoku puzzle")
        await self.send_line("  sudoku hard 12345    - Specific puzzle (shareable)")
        await self.send_line("=" * 50 + "\n")

    async def show_game_help(self) -> None:
        """Display help for the current game."""
        if not self.current_game:
            await self.send_line("No game in progress. Returning to menu...")
            self.in_menu = True
            await self.show_main_menu()
            return

        await self.send_line("")
        await self.send_line("=" * 50)
        await self.send_line(f"{self.current_game.name.upper()} - HELP")
        await self.send_line("=" * 50)

        # Send rules line by line, stripping trailing empty lines
        rules_lines = self.current_game.get_rules().rstrip("\n").split("\n")
        for line in rules_lines:
            await self.send_line(line)

        await self.send_line("")

        # Send commands line by line, stripping trailing empty lines
        commands_lines = self.current_game.get_commands().rstrip("\n").split("\n")
        for line in commands_lines:
            await self.send_line(line)

        await self.send_line("=" * 50)
        await self.send_line("")

    async def start_game(self, game_id: str, difficulty: str = "easy", seed: int | None = None) -> None:
        """Start a specific game.

        Args:
            game_id: The game identifier (e.g., 'sudoku', 'kenken')
            difficulty: Game difficulty (easy, medium, hard)
            seed: Optional seed for deterministic puzzle generation
        """
        game_class = AVAILABLE_GAMES.get(game_id.lower())
        if not game_class:
            await self.send_line(f"Unknown game: {game_id}")
            return

        # Validate difficulty
        valid_difficulties = [d.value for d in DifficultyLevel]
        if difficulty not in valid_difficulties:
            await self.send_line(f"Invalid difficulty. Choose from: {', '.join(valid_difficulties)}")
            difficulty = DifficultyLevel.EASY.value

        # Create and initialize the game with optional seed
        self.current_game = game_class(difficulty, seed=seed)  # type: ignore[abstract]
        await self.current_game.generate_puzzle()
        self.in_menu = False

        # Set up command handler if available for this game
        handler_class = GAME_COMMAND_HANDLERS.get(game_id.lower())
        if handler_class:
            self.game_handler = handler_class(self.current_game)
        else:
            self.game_handler = None

        seed_info = f", seed={seed}" if seed is not None else ""
        logger.info(f"Started {game_id} ({difficulty}{seed_info}) for {self.addr}")

        # Show game header
        await self.send_line("")
        await self.send_line("=" * 50)
        await self.send_line(f"{self.current_game.name.upper()} - {difficulty.upper()} MODE")
        await self.send_line(f"Seed: {self.current_game.seed}")
        await self.send_line("=" * 50)

        # Send rules line by line, stripping trailing empty lines
        rules_lines = self.current_game.get_rules().rstrip("\n").split("\n")
        for line in rules_lines:
            await self.send_line(line)

        await self.send_line("")
        await self.send_line("Type 'help' for commands or 'hint' for a clue.")
        await self.send_line("=" * 50)
        await self.send_line("")

        # Show the initial puzzle
        await self.display_puzzle()

    async def display_puzzle(self) -> None:
        """Display the current puzzle state."""
        if not self.current_game:
            if self.output_mode == OutputMode.JSON:
                await self.send_json_response(type="error", code="NO_GAME", message="No game in progress")
            elif self.output_mode == OutputMode.STRICT:
                await self.send_line("ERR:NO_GAME")
            else:
                await self.send_line("No game in progress. Type 'menu' to select a game.")
            return

        if self.output_mode == OutputMode.JSON:
            # JSON mode: full state as JSON for RL agents
            state = self.get_game_state_dict()
            state["type"] = "observation"
            state["grid_display"] = self.current_game.render_grid()
            await self.send_json_response(**state)
        elif self.output_mode == OutputMode.STRICT:
            # Strict mode: terse, machine-verifiable output
            # Format: STATE:<game>:<difficulty>:<seed>:<moves>:<status>
            status = "complete" if self.current_game.is_complete() else "active"
            await self.send_line(
                f"STATE:{self.current_game.name}:{self.current_game.difficulty.value}:"
                f"{self.current_game.seed}:{self.current_game.moves_made}:{status}"
            )
            # Grid as compact lines
            grid_lines = self.current_game.render_grid().rstrip("\n").split("\n")
            for line in grid_lines:
                await self.send_line(line)
        elif self.output_mode == OutputMode.AGENT:
            # Agent-friendly output with clear markers
            await self.send_line("---GAME-START---")
            await self.send_line(f"GAME: {self.current_game.name}")
            await self.send_line(f"DIFFICULTY: {self.current_game.difficulty.value}")
            await self.send_line(f"MOVES: {self.current_game.moves_made}")
            await self.send_line("---GRID-START---")
            grid_lines = self.current_game.render_grid().rstrip("\n").split("\n")
            for line in grid_lines:
                await self.send_line(line)
            await self.send_line("---GRID-END---")
            await self.send_line("---GAME-END---")
        else:
            # Normal/natural human-friendly output
            await self.send_line("")
            await self.send_line("=" * 50)

            # Send grid line by line, stripping trailing empty lines
            grid_lines = self.current_game.render_grid().rstrip("\n").split("\n")
            for line in grid_lines:
                await self.send_line(line)

            await self.send_line(self.current_game.get_stats())
            await self.send_line("=" * 50)
            await self.send_line("")

    async def handle_menu_command(self, command: str) -> None:
        """Process a command when in the main menu.

        Args:
            command: The command string
        """
        parts = command.strip().lower().split()
        if not parts:
            return

        cmd = parts[0]

        # Try to match command to enum
        try:
            cmd_enum = GameCommand(cmd)
            if cmd_enum in (GameCommand.QUIT, GameCommand.EXIT, GameCommand.Q):
                await self.send_line("Thanks for visiting the Puzzle Arcade! Goodbye!")
                await self.end_session()
                return

            if cmd_enum == GameCommand.HELP:
                await self.show_main_menu()
                return
        except ValueError:
            pass  # Not a GameCommand enum, continue to game selection

        # Helper to parse difficulty and seed from parts
        def parse_game_args(parts: list[str]) -> tuple[str, int | None]:
            """Parse difficulty and optional seed from command parts.

            Args:
                parts: Command parts after game name/number

            Returns:
                Tuple of (difficulty, seed or None)
            """
            difficulty = "easy"
            seed = None

            if len(parts) >= 1:
                difficulty = parts[0]
            if len(parts) >= 2:
                try:
                    seed = int(parts[1])
                except ValueError:
                    pass  # Ignore invalid seed, will generate random

            return difficulty, seed

        # Try to parse as game number
        if cmd.isdigit():
            game_idx = int(cmd) - 1
            game_list = list(AVAILABLE_GAMES.keys())
            if 0 <= game_idx < len(game_list):
                game_id = game_list[game_idx]
                difficulty, seed = parse_game_args(parts[1:])
                await self.start_game(game_id, difficulty, seed)
                return
            else:
                await self.send_line(f"Invalid game number. Choose 1-{len(game_list)}.")
                return

        # Try to parse as game name
        if cmd in AVAILABLE_GAMES:
            difficulty, seed = parse_game_args(parts[1:])
            await self.start_game(cmd, difficulty, seed)
            return

        await self.send_line("Unknown command. Type 'help' to see available options.")

    async def handle_game_command(self, command: str) -> None:
        """Process a command when playing a game.

        Args:
            command: The command string
        """
        if not self.current_game:
            await self.send_line("No game in progress.")
            self.in_menu = True
            await self.show_main_menu()
            return

        parts = command.strip().lower().split()
        if not parts:
            return

        cmd = parts[0]

        # Try to match command to enum
        try:
            cmd_enum = GameCommand(cmd)
        except ValueError:
            await self.send_line(f"Unknown command '{cmd}'. Type 'help' for available commands.")
            return

        # Global commands
        if cmd_enum in (GameCommand.QUIT, GameCommand.EXIT, GameCommand.Q):
            await self.send_line("Thanks for playing! Goodbye!")
            await self.end_session()
            return

        if cmd_enum in (GameCommand.MENU, GameCommand.M):
            await self.send_line("Returning to main menu...\n")
            self.current_game = None
            self.game_handler = None
            self.in_menu = True
            await self.show_main_menu()
            return

        if cmd_enum in (GameCommand.HELP, GameCommand.H):
            await self.show_game_help()
            return

        if cmd_enum in (GameCommand.SHOW, GameCommand.S):
            await self.display_puzzle()
            return

        if cmd_enum == GameCommand.MODE:
            if len(parts) != 2:
                await self.send_line("Usage: mode <normal|agent|compact|strict|natural|json>")
                return

            mode_str = parts[1].lower()
            try:
                new_mode = OutputMode(mode_str)
                self.output_mode = new_mode
                if new_mode == OutputMode.JSON:
                    await self.send_json_response(type="mode", mode="json", success=True)
                elif new_mode == OutputMode.STRICT:
                    await self.send_line("OK:MODE=strict")
                else:
                    await self.send_line(f"Output mode set to: {new_mode.value}")
            except ValueError:
                if self.output_mode == OutputMode.JSON:
                    await self.send_json_response(type="error", code="INVALID_MODE", mode=mode_str)
                elif self.output_mode == OutputMode.STRICT:
                    await self.send_line(f"ERR:INVALID_MODE:{mode_str}")
                else:
                    await self.send_line(
                        f"Invalid mode '{mode_str}'. Choose: normal, agent, compact, strict, natural, or json"
                    )
            return

        if cmd_enum == GameCommand.SEED:
            await self.send_line(f"Current puzzle seed: {self.current_game.seed}")
            await self.send_line("To replay this exact puzzle, use:")
            game_name = self.current_game.name.lower().replace(" ", "_")
            await self.send_line(f"  {game_name} {self.current_game.difficulty.value} {self.current_game.seed}")
            return

        if cmd_enum == GameCommand.STATS:
            # Show detailed stats including difficulty profile
            profile = self.current_game.difficulty_profile
            optimal = self.current_game.optimal_steps

            if self.output_mode == OutputMode.JSON:
                await self.send_json_response(
                    type="stats",
                    game=self.current_game.name,
                    difficulty=self.current_game.difficulty.value,
                    seed=self.current_game.seed,
                    moves=self.current_game.moves_made,
                    invalid_moves=self.current_game.invalid_moves,
                    hints_used=self.current_game.hints_used,
                    optimal_steps=optimal,
                    difficulty_profile={
                        "logic_depth": profile.logic_depth,
                        "branching_factor": profile.branching_factor,
                        "state_observability": profile.state_observability,
                        "constraint_density": profile.constraint_density,
                    },
                )
            elif self.output_mode == OutputMode.STRICT:
                await self.send_line(
                    f"STATS:{self.current_game.moves_made}:{self.current_game.invalid_moves}:"
                    f"{self.current_game.hints_used}:{optimal or 0}"
                )
            else:
                await self.send_line("")
                await self.send_line("=" * 50)
                await self.send_line(f"GAME STATISTICS - {self.current_game.name}")
                await self.send_line("=" * 50)
                await self.send_line(f"Difficulty: {self.current_game.difficulty.value}")
                await self.send_line(f"Seed: {self.current_game.seed}")
                await self.send_line("")
                await self.send_line("Progress:")
                await self.send_line(f"  Moves made: {self.current_game.moves_made}")
                await self.send_line(f"  Invalid attempts: {self.current_game.invalid_moves}")
                await self.send_line(f"  Hints used: {self.current_game.hints_used}")
                if optimal:
                    efficiency = (
                        min(1.0, optimal / max(1, self.current_game.moves_made))
                        if self.current_game.moves_made > 0
                        else 0
                    )
                    await self.send_line(f"  Optimal steps: {optimal}")
                    await self.send_line(f"  Current efficiency: {efficiency:.1%}")
                await self.send_line("")
                await self.send_line("Difficulty Profile:")
                await self.send_line(f"  Logic depth: {profile.logic_depth}")
                await self.send_line(f"  Branching factor: {profile.branching_factor:.1f}")
                await self.send_line(f"  State observability: {profile.state_observability:.0%}")
                await self.send_line(f"  Constraint density: {profile.constraint_density:.0%}")
                await self.send_line("=" * 50)
            return

        if cmd_enum == GameCommand.COMPARE:
            # Compare current progress with solver solution
            if not hasattr(self.current_game, "solution"):
                await self.send_result(False, "Comparison not available for this game type.", "COMPARE_UNAVAILABLE")
                return

            optimal = self.current_game.optimal_steps or 0
            moves = self.current_game.moves_made
            is_complete = self.current_game.is_complete()

            # Calculate comparison metrics
            if moves > 0 and optimal > 0:
                efficiency = min(1.0, optimal / moves)
            else:
                efficiency = 0.0

            error_rate = 0.0
            total_actions = moves + self.current_game.invalid_moves
            if total_actions > 0:
                error_rate = self.current_game.invalid_moves / total_actions

            if self.output_mode == OutputMode.JSON:
                await self.send_json_response(
                    type="comparison",
                    complete=is_complete,
                    your_moves=moves,
                    optimal_moves=optimal,
                    efficiency=round(efficiency, 3),
                    invalid_moves=self.current_game.invalid_moves,
                    error_rate=round(error_rate, 3),
                    hints_used=self.current_game.hints_used,
                )
            elif self.output_mode == OutputMode.STRICT:
                status = "complete" if is_complete else "incomplete"
                await self.send_line(f"COMPARE:{status}:{moves}:{optimal}:{efficiency:.3f}:{error_rate:.3f}")
            else:
                await self.send_line("")
                await self.send_line("=" * 50)
                await self.send_line("SOLVER COMPARISON")
                await self.send_line("=" * 50)
                await self.send_line(f"Status: {'SOLVED' if is_complete else 'IN PROGRESS'}")
                await self.send_line("")
                await self.send_line("Your Performance:")
                await self.send_line(f"  Moves made: {moves}")
                await self.send_line(f"  Invalid attempts: {self.current_game.invalid_moves}")
                await self.send_line(f"  Hints used: {self.current_game.hints_used}")
                await self.send_line("")
                await self.send_line("Solver Reference:")
                await self.send_line(f"  Optimal moves: {optimal}")
                await self.send_line("")
                await self.send_line("Metrics:")
                await self.send_line(f"  Efficiency: {efficiency:.1%}")
                await self.send_line(f"  Error rate: {error_rate:.1%}")
                if is_complete:
                    adjusted = efficiency * (
                        1
                        - self.current_game.solver_config.hint_penalty * (self.current_game.hints_used / max(1, moves))
                    )
                    await self.send_line(f"  Adjusted score: {adjusted:.1%}")
                await self.send_line("=" * 50)
            return

        if cmd_enum == GameCommand.HINT:
            # Check if hints are allowed (via solver config)
            if not self.current_game.record_hint():
                await self.send_result(
                    False, "Hints not available (budget exhausted or solver-free mode)", "HINT_DENIED"
                )
                return

            hint_result = await self.current_game.get_hint()
            if hint_result:
                _, hint_message = hint_result
                if self.output_mode == OutputMode.STRICT:
                    await self.send_line(f"HINT:{hint_message}")
                else:
                    await self.send_line(f"Hint: {hint_message}")
            else:
                await self.send_result(True, "No hints available. Puzzle is complete!", "HINT_NONE")
            return

        if cmd_enum == GameCommand.CHECK:
            if self.current_game.is_complete():
                await self.send_game_complete()
            else:
                if self.output_mode == OutputMode.STRICT:
                    await self.send_line(f"INCOMPLETE:{self.current_game.moves_made}")
                else:
                    await self.send_line("Puzzle not yet complete. Keep going!")
                    await self.send_line(self.current_game.get_stats())
            return

        if cmd_enum == GameCommand.RESET:
            # Reset the game to its initial state
            if hasattr(self.current_game, "initial_grid"):
                self.current_game.grid = [row[:] for row in self.current_game.initial_grid]  # type: ignore[attr-defined]
                self.current_game.moves_made = 0
                self.current_game.invalid_moves = 0
                self.current_game.hints_used = 0
                await self.send_result(True, "Puzzle reset to initial state.", "RESET")
                await self.display_puzzle()
            else:
                await self.send_result(False, "Reset not available for this game.", "RESET_UNAVAILABLE")
            return

        # Delegate to game-specific command handler if available
        if self.game_handler and cmd_enum in self.game_handler.supported_commands:
            result = await self.game_handler.handle_command(cmd_enum, parts[1:])

            # Track invalid moves
            if not result.result.success:
                self.current_game.invalid_moves += 1

            # Send result based on output mode
            code = "OK" if result.result.success else "INVALID"
            await self.send_result(result.result.success, result.result.message, code)

            if result.should_display:
                await self.display_puzzle()

            if result.is_game_over:
                await self.send_game_complete()
            return

        # Legacy game-specific commands (for non-migrated games)
        if cmd_enum == GameCommand.PLACE:
            if len(parts) != 4:
                await self.send_result(False, "Usage: place <row> <col> <num>", "USAGE")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])
                num = int(parts[3])

                result = await self.current_game.validate_move(row, col, num)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(result.success, result.message, "PLACED" if result.success else "INVALID_MOVE")

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_game_complete()

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only.", "PARSE_ERROR")
            return

        if cmd_enum == GameCommand.CLEAR:
            if len(parts) != 3:
                await self.send_result(False, "Usage: clear <row> <col>", "USAGE")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])

                result = await self.current_game.validate_move(row, col, 0)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(result.success, result.message, "CLEARED" if result.success else "INVALID_CLEAR")

                if result.success:
                    await self.display_puzzle()

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only.", "PARSE_ERROR")
            return

        if cmd_enum == GameCommand.SOLVE:
            # Copy solution to grid (game-specific)
            if hasattr(self.current_game, "solution"):
                self.current_game.grid = [row[:] for row in self.current_game.solution]  # type: ignore[attr-defined]
                if self.output_mode == OutputMode.STRICT:
                    await self.send_line("OK:SOLVED")
                else:
                    await self.send_line("\nShowing solution...\n")
                await self.display_puzzle()
                if self.output_mode != OutputMode.STRICT:
                    await self.send_line("Type 'menu' to play another game.")
            else:
                await self.send_result(False, "Solve not implemented for this game.", "SOLVE_UNAVAILABLE")
            return

        # Lights Out specific command
        if cmd_enum == GameCommand.PRESS:
            if len(parts) != 3:
                await self.send_result(False, "Usage: press <row> <col>", "USAGE")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])

                result = await self.current_game.validate_move(row, col)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(result.success, result.message, "PRESSED" if result.success else "INVALID_PRESS")

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_game_complete()

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only.", "PARSE_ERROR")
            return

        # Logic Grid specific commands
        if cmd_enum == GameCommand.CONNECT:
            if len(parts) != 5:
                await self.send_result(False, "Usage: connect <cat1> <val1> <cat2> <val2>", "USAGE")
                return

            cat1, val1, cat2, val2 = parts[1], parts[2], parts[3], parts[4]
            result = await self.current_game.validate_move(cat1, val1, cat2, val2, True)

            if not result.success:
                self.current_game.invalid_moves += 1

            await self.send_result(result.success, result.message, "CONNECTED" if result.success else "INVALID_CONNECT")
            if result.success:
                await self.display_puzzle()
                if self.current_game.is_complete():
                    await self.send_game_complete()
            return

        if cmd_enum == GameCommand.EXCLUDE:
            if len(parts) != 5:
                await self.send_result(False, "Usage: exclude <cat1> <val1> <cat2> <val2>", "USAGE")
                return

            cat1, val1, cat2, val2 = parts[1], parts[2], parts[3], parts[4]
            result = await self.current_game.validate_move(cat1, val1, cat2, val2, False)

            if not result.success:
                self.current_game.invalid_moves += 1

            await self.send_result(result.success, result.message, "EXCLUDED" if result.success else "INVALID_EXCLUDE")
            if result.success:
                await self.display_puzzle()
                if self.current_game.is_complete():
                    await self.send_game_complete()
            return

        # Minesweeper commands
        if cmd_enum == GameCommand.REVEAL:
            if len(parts) != 3:
                await self.send_result(False, "Usage: reveal <row> <col>", "USAGE")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])

                result = await self.current_game.validate_move("reveal", row, col)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(
                    result.success, result.message, "REVEALED" if result.success else "INVALID_REVEAL"
                )

                if result.success:
                    await self.display_puzzle()

                    if result.game_over:
                        if self.current_game.is_complete():
                            await self.send_game_complete()
                        else:
                            if self.output_mode == OutputMode.STRICT:
                                await self.send_line(f"GAMEOVER:MINE:{self.current_game.moves_made}")
                            else:
                                await self.send_line("\n" + "=" * 50)
                                await self.send_line("GAME OVER! You hit a mine!")
                                await self.send_line("=" * 50)
                                await self.send_line("\nType 'menu' to play another game.")
                                await self.send_line("=" * 50 + "\n")

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only.", "PARSE_ERROR")
            return

        if cmd_enum == GameCommand.FLAG:
            if len(parts) != 3:
                await self.send_result(False, "Usage: flag <row> <col>", "USAGE")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])

                result = await self.current_game.validate_move("flag", row, col)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(result.success, result.message, "FLAGGED" if result.success else "INVALID_FLAG")

                if result.success:
                    await self.display_puzzle()

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only.", "PARSE_ERROR")
            return

        # Slitherlink command
        if cmd_enum == GameCommand.SET:
            if len(parts) != 5:
                await self.send_result(False, "Usage: set <h|v> <row> <col> <state>", "USAGE")
                return

            try:
                edge_type = parts[1].lower()
                row = int(parts[2])
                col = int(parts[3])
                state = int(parts[4])

                result = await self.current_game.validate_move(edge_type, row, col, state)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(result.success, result.message, "SET" if result.success else "INVALID_SET")

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_game_complete()

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only for row, col, state.", "PARSE_ERROR")
            return

        # Mastermind command
        if cmd_enum == GameCommand.GUESS:
            if len(parts) < 2:
                await self.send_result(False, "Usage: guess <color1> <color2> ... <colorN>", "USAGE")
                return

            try:
                guess = [int(p) for p in parts[1:]]

                result = await self.current_game.validate_move(*guess)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(result.success, result.message, "GUESSED" if result.success else "INVALID_GUESS")

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_game_complete()

                if result.game_over and not self.current_game.is_complete():
                    if self.output_mode == OutputMode.STRICT:
                        await self.send_line(f"GAMEOVER:OUT_OF_GUESSES:{self.current_game.moves_made}")
                    else:
                        await self.send_line("\n" + "=" * 50)
                        await self.send_line("GAME OVER! Out of guesses!")
                        await self.send_line("=" * 50)
                        await self.send_line("\nType 'menu' to play another game.")
                        await self.send_line("=" * 50 + "\n")

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only.", "PARSE_ERROR")
            return

        # Knapsack commands
        if cmd_enum == GameCommand.SELECT:
            if len(parts) != 2:
                await self.send_result(False, "Usage: select <item_number>", "USAGE")
                return

            try:
                item_index = int(parts[1])

                result = await self.current_game.validate_move("select", item_index)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(
                    result.success, result.message, "SELECTED" if result.success else "INVALID_SELECT"
                )

                if result.success:
                    await self.display_puzzle()

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only.", "PARSE_ERROR")
            return

        if cmd_enum == GameCommand.DESELECT:
            if len(parts) != 2:
                await self.send_result(False, "Usage: deselect <item_number>", "USAGE")
                return

            try:
                item_index = int(parts[1])

                result = await self.current_game.validate_move("deselect", item_index)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(
                    result.success, result.message, "DESELECTED" if result.success else "INVALID_DESELECT"
                )

                if result.success:
                    await self.display_puzzle()

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only.", "PARSE_ERROR")
            return

        # Nurikabe command
        if cmd_enum == GameCommand.MARK:
            if len(parts) != 4:
                await self.send_result(False, "Usage: mark <row> <col> <white|black|clear>", "USAGE")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])
                color = parts[3].lower()

                result = await self.current_game.validate_move(row, col, color)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(result.success, result.message, "MARKED" if result.success else "INVALID_MARK")

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_game_complete()

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Row and col must be numbers.", "PARSE_ERROR")
            return

        # Hitori command
        if cmd_enum == GameCommand.SHADE:
            if len(parts) != 3:
                await self.send_result(False, "Usage: shade <row> <col>", "USAGE")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])

                result = await self.current_game.validate_move(row, col, "shade")

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(result.success, result.message, "SHADED" if result.success else "INVALID_SHADE")

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_game_complete()

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only.", "PARSE_ERROR")
            return

        # Bridges command
        if cmd_enum == GameCommand.BRIDGE:
            if len(parts) != 6:
                await self.send_result(False, "Usage: bridge <r1> <c1> <r2> <c2> <count>", "USAGE")
                return

            try:
                r1 = int(parts[1])
                c1 = int(parts[2])
                r2 = int(parts[3])
                c2 = int(parts[4])
                count = int(parts[5])

                result = await self.current_game.validate_move(r1, c1, r2, c2, count)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(
                    result.success, result.message, "BRIDGED" if result.success else "INVALID_BRIDGE"
                )

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_game_complete()

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only.", "PARSE_ERROR")
            return

        # Sokoban command
        if cmd_enum == GameCommand.MOVE:
            if len(parts) != 2:
                await self.send_result(False, "Usage: move <direction>", "USAGE")
                return

            direction = parts[1].lower()

            result = await self.current_game.validate_move(direction)

            if not result.success:
                self.current_game.invalid_moves += 1

            await self.send_result(result.success, result.message, "MOVED" if result.success else "INVALID_MOVE")

            if result.success:
                await self.display_puzzle()

                if self.current_game.is_complete():
                    await self.send_game_complete()

            return

        # Scheduler commands
        if cmd_enum == GameCommand.ASSIGN:
            if len(parts) != 4:
                await self.send_result(False, "Usage: assign <task_id> <worker_id> <start_time>", "USAGE")
                return

            try:
                task_id = int(parts[1])
                worker_id = int(parts[2])
                start_time = int(parts[3])

                result = await self.current_game.validate_move(task_id, worker_id, start_time)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(
                    result.success, result.message, "ASSIGNED" if result.success else "INVALID_ASSIGN"
                )

                if result.success:
                    await self.display_puzzle()
                    if self.current_game.is_complete():
                        await self.send_game_complete()

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only.", "PARSE_ERROR")
            return

        if cmd_enum == GameCommand.UNASSIGN:
            if len(parts) != 2:
                await self.send_result(False, "Usage: unassign <task_id>", "USAGE")
                return

            try:
                task_id = int(parts[1])

                result = await self.current_game.validate_move(task_id, 0, -1)

                if not result.success:
                    self.current_game.invalid_moves += 1

                await self.send_result(
                    result.success, result.message, "UNASSIGNED" if result.success else "INVALID_UNASSIGN"
                )

                if result.success:
                    await self.display_puzzle()

            except ValueError:
                self.current_game.invalid_moves += 1
                await self.send_result(False, "Invalid input. Use numbers only.", "PARSE_ERROR")
            return

        await self.send_result(False, "Unknown command. Type 'help' for available commands.", "UNKNOWN_CMD")

    async def on_command_submitted(self, command: str) -> None:
        """Process a command from the player.

        Args:
            command: The command string
        """
        if self.in_menu:
            await self.handle_menu_command(command)
        else:
            await self.handle_game_command(command)

    async def send_welcome(self) -> None:
        """Send a welcome message to the player."""
        await self.show_main_menu()

    async def process_line(self, line: str) -> bool:
        """Process a line of input from the client.

        Args:
            line: The line to process

        Returns:
            True to continue processing, False to terminate
        """
        logger.debug(f"ArcadeHandler process_line => {line!r}")

        # Check for exit commands
        if line.lower() in ["quit", "exit", "q"]:
            await self.send_line("Thanks for visiting the Puzzle Arcade! Goodbye!")
            await self.end_session()
            return False

        # Process the command
        await self.on_command_submitted(line)

        return True


async def main():
    """Main entry point for the Puzzle Arcade server."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    host, port = "0.0.0.0", 8023
    server = TelnetServer(host, port, ArcadeHandler)

    try:
        logger.info(f"Starting Puzzle Arcade Server on {host}:{port}")
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Server shutdown initiated by user.")
    except Exception as e:
        logger.error(f"Error running server: {e}")
    finally:
        logger.info("Server has shut down.")


def run_server():
    """CLI entry point for running the server."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt.")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
    finally:
        logger.info("Server process exiting.")


if __name__ == "__main__":
    run_server()
