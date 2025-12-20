#!/usr/bin/env python3
"""
Puzzle Arcade Server

A multi-game telnet server hosting various logic puzzle games.
LLMs with MCP solver access can telnet in and solve these puzzles.
"""

import asyncio
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
            await self.send_line("No game in progress. Type 'menu' to select a game.")
            return

        if self.output_mode == OutputMode.AGENT:
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
            # Normal human-friendly output
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
                await self.send_line("Usage: mode <normal|agent|compact>")
                return

            mode_str = parts[1].lower()
            try:
                new_mode = OutputMode(mode_str)
                self.output_mode = new_mode
                await self.send_line(f"Output mode set to: {new_mode.value}")
            except ValueError:
                await self.send_line(f"Invalid mode '{mode_str}'. Choose: normal, agent, or compact")
            return

        if cmd_enum == GameCommand.SEED:
            await self.send_line(f"Current puzzle seed: {self.current_game.seed}")
            await self.send_line("To replay this exact puzzle, use:")
            game_name = self.current_game.name.lower().replace(" ", "_")
            await self.send_line(f"  {game_name} {self.current_game.difficulty.value} {self.current_game.seed}")
            return

        if cmd_enum == GameCommand.HINT:
            hint_result = await self.current_game.get_hint()
            if hint_result:
                _, hint_message = hint_result
                await self.send_line(f"Hint: {hint_message}")
            else:
                await self.send_line("No hints available. Puzzle is complete!")
            return

        if cmd_enum == GameCommand.CHECK:
            if self.current_game.is_complete():
                await self.send_line("\n" + "=" * 50)
                await self.send_line("CONGRATULATIONS! PUZZLE SOLVED!")
                await self.send_line("=" * 50)
                await self.send_line(self.current_game.get_stats())
                await self.send_line("\nType 'menu' to select another game.")
                await self.send_line("=" * 50 + "\n")
            else:
                await self.send_line("Puzzle not yet complete. Keep going!")
                await self.send_line(self.current_game.get_stats())
            return

        if cmd_enum == GameCommand.RESET:
            # Reset the game to its initial state
            if hasattr(self.current_game, "initial_grid"):
                self.current_game.grid = [row[:] for row in self.current_game.initial_grid]  # type: ignore[attr-defined]
                self.current_game.moves_made = 0
                await self.send_line("Puzzle reset to initial state.")
                await self.display_puzzle()
            else:
                await self.send_line("Reset not available for this game.")
            return

        # Delegate to game-specific command handler if available
        if self.game_handler and cmd_enum in self.game_handler.supported_commands:
            result = await self.game_handler.handle_command(cmd_enum, parts[1:])
            await self.send_line(result.result.message)

            if result.should_display:
                await self.display_puzzle()

            if result.is_game_over:
                await self.send_line("\n" + "=" * 50)
                await self.send_line("CONGRATULATIONS! YOU SOLVED IT!")
                await self.send_line("=" * 50)
                await self.send_line(self.current_game.get_stats())
                await self.send_line("\nType 'menu' to play another game.")
                await self.send_line("=" * 50 + "\n")
            return

        # Legacy game-specific commands (for non-migrated games)
        if cmd_enum == GameCommand.PLACE:
            if len(parts) != 4:
                await self.send_line("Usage: place <row> <col> <num>")
                await self.send_line("Example: place 1 5 7")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])
                num = int(parts[3])

                result = await self.current_game.validate_move(row, col, num)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_line("\n" + "=" * 50)
                        await self.send_line("CONGRATULATIONS! YOU SOLVED IT!")
                        await self.send_line("=" * 50)
                        await self.send_line(self.current_game.get_stats())
                        await self.send_line("\nType 'menu' to play another game.")
                        await self.send_line("=" * 50 + "\n")

            except ValueError:
                await self.send_line("Invalid input. Use numbers only.")
            return

        if cmd_enum == GameCommand.CLEAR:
            if len(parts) != 3:
                await self.send_line("Usage: clear <row> <col>")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])

                result = await self.current_game.validate_move(row, col, 0)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

            except ValueError:
                await self.send_line("Invalid input. Use numbers only.")
            return

        if cmd_enum == GameCommand.SOLVE:
            await self.send_line("\nShowing solution...\n")
            # Copy solution to grid (game-specific)
            if hasattr(self.current_game, "solution"):
                self.current_game.grid = [row[:] for row in self.current_game.solution]  # type: ignore[attr-defined]
                await self.display_puzzle()
                await self.send_line("Type 'menu' to play another game.")
            else:
                await self.send_line("Solve not implemented for this game.")
            return

        # Lights Out specific command
        if cmd_enum == GameCommand.PRESS:
            if len(parts) != 3:
                await self.send_line("Usage: press <row> <col>")
                await self.send_line("Example: press 2 3")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])

                result = await self.current_game.validate_move(row, col)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_line("\n" + "=" * 50)
                        await self.send_line("CONGRATULATIONS! ALL LIGHTS OFF!")
                        await self.send_line("=" * 50)
                        await self.send_line(self.current_game.get_stats())
                        await self.send_line("\nType 'menu' to play another game.")
                        await self.send_line("=" * 50 + "\n")

            except ValueError:
                await self.send_line("Invalid input. Use numbers only.")
            return

        # Logic Grid specific commands
        if cmd_enum == GameCommand.CONNECT:
            if len(parts) != 5:
                await self.send_line("Usage: connect <cat1> <val1> <cat2> <val2>")
                await self.send_line("Example: connect person Alice color Red")
                return

            cat1, val1, cat2, val2 = parts[1], parts[2], parts[3], parts[4]
            result = await self.current_game.validate_move(cat1, val1, cat2, val2, True)
            await self.send_line(result.message)
            if result.success:
                await self.display_puzzle()
            return

        if cmd_enum == GameCommand.EXCLUDE:
            if len(parts) != 5:
                await self.send_line("Usage: exclude <cat1> <val1> <cat2> <val2>")
                await self.send_line("Example: exclude person Bob pet Cat")
                return

            cat1, val1, cat2, val2 = parts[1], parts[2], parts[3], parts[4]
            result = await self.current_game.validate_move(cat1, val1, cat2, val2, False)
            await self.send_line(result.message)
            if result.success:
                await self.display_puzzle()
            return

        # Minesweeper commands
        if cmd_enum == GameCommand.REVEAL:
            if len(parts) != 3:
                await self.send_line("Usage: reveal <row> <col>")
                await self.send_line("Example: reveal 3 4")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])

                result = await self.current_game.validate_move("reveal", row, col)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

                    if result.game_over:
                        await self.send_line("\n" + "=" * 50)
                        if self.current_game.is_complete():
                            await self.send_line("CONGRATULATIONS! YOU WIN!")
                        else:
                            await self.send_line("GAME OVER! You hit a mine!")
                        await self.send_line("=" * 50)
                        await self.send_line("\nType 'menu' to play another game.")
                        await self.send_line("=" * 50 + "\n")

            except ValueError:
                await self.send_line("Invalid input. Use numbers only.")
            return

        if cmd_enum == GameCommand.FLAG:
            if len(parts) != 3:
                await self.send_line("Usage: flag <row> <col>")
                await self.send_line("Example: flag 3 4")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])

                result = await self.current_game.validate_move("flag", row, col)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

            except ValueError:
                await self.send_line("Invalid input. Use numbers only.")
            return

        # Slitherlink command
        if cmd_enum == GameCommand.SET:
            if len(parts) != 5:
                await self.send_line("Usage: set <h|v> <row> <col> <state>")
                await self.send_line("Example: set h 1 2 1  (set horizontal edge at row 1, col 2 to line)")
                await self.send_line("States: 0=empty, 1=line, 2=X")
                return

            try:
                edge_type = parts[1].lower()
                row = int(parts[2])
                col = int(parts[3])
                state = int(parts[4])

                result = await self.current_game.validate_move(edge_type, row, col, state)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_line("\n" + "=" * 50)
                        await self.send_line("CONGRATULATIONS! LOOP COMPLETE!")
                        await self.send_line("=" * 50)
                        await self.send_line(self.current_game.get_stats())
                        await self.send_line("\nType 'menu' to play another game.")
                        await self.send_line("=" * 50 + "\n")

            except ValueError:
                await self.send_line("Invalid input. Use numbers only for row, col, state.")
            return

        # Mastermind command
        if cmd_enum == GameCommand.GUESS:
            if len(parts) < 2:
                await self.send_line("Usage: guess <color1> <color2> ... <colorN>")
                await self.send_line("Example: guess 1 2 3 4")
                return

            try:
                guess = [int(p) for p in parts[1:]]

                result = await self.current_game.validate_move(*guess)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_line("\n" + "=" * 50)
                        await self.send_line("CONGRATULATIONS! CODE CRACKED!")
                        await self.send_line("=" * 50)
                        await self.send_line(self.current_game.get_stats())
                        await self.send_line("\nType 'menu' to play another game.")
                        await self.send_line("=" * 50 + "\n")

                if result.game_over and not self.current_game.is_complete():
                    await self.send_line("\n" + "=" * 50)
                    await self.send_line("GAME OVER! Out of guesses!")
                    await self.send_line("=" * 50)
                    await self.send_line("\nType 'menu' to play another game.")
                    await self.send_line("=" * 50 + "\n")

            except ValueError:
                await self.send_line("Invalid input. Use numbers only.")
            return

        # Knapsack commands
        if cmd_enum == GameCommand.SELECT:
            if len(parts) != 2:
                await self.send_line("Usage: select <item_number>")
                await self.send_line("Example: select 3")
                return

            try:
                item_index = int(parts[1])

                result = await self.current_game.validate_move("select", item_index)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

            except ValueError:
                await self.send_line("Invalid input. Use numbers only.")
            return

        if cmd_enum == GameCommand.DESELECT:
            if len(parts) != 2:
                await self.send_line("Usage: deselect <item_number>")
                await self.send_line("Example: deselect 3")
                return

            try:
                item_index = int(parts[1])

                result = await self.current_game.validate_move("deselect", item_index)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

            except ValueError:
                await self.send_line("Invalid input. Use numbers only.")
            return

        # Nurikabe command
        if cmd_enum == GameCommand.MARK:
            if len(parts) != 4:
                await self.send_line("Usage: mark <row> <col> <white|black|clear>")
                await self.send_line("Example: mark 2 3 black")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])
                color = parts[3].lower()

                result = await self.current_game.validate_move(row, col, color)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_line("\n" + "=" * 50)
                        await self.send_line("CONGRATULATIONS! PUZZLE SOLVED!")
                        await self.send_line("=" * 50)
                        await self.send_line(self.current_game.get_stats())
                        await self.send_line("\nType 'menu' to play another game.")
                        await self.send_line("=" * 50 + "\n")

            except ValueError:
                await self.send_line("Invalid input. Row and col must be numbers.")
            return

        # Hitori command
        if cmd_enum == GameCommand.SHADE:
            if len(parts) != 3:
                await self.send_line("Usage: shade <row> <col>")
                await self.send_line("Example: shade 2 3")
                return

            try:
                row = int(parts[1])
                col = int(parts[2])

                result = await self.current_game.validate_move(row, col, "shade")
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_line("\n" + "=" * 50)
                        await self.send_line("CONGRATULATIONS! PUZZLE SOLVED!")
                        await self.send_line("=" * 50)
                        await self.send_line(self.current_game.get_stats())
                        await self.send_line("\nType 'menu' to play another game.")
                        await self.send_line("=" * 50 + "\n")

            except ValueError:
                await self.send_line("Invalid input. Use numbers only.")
            return

        # Bridges command
        if cmd_enum == GameCommand.BRIDGE:
            if len(parts) != 6:
                await self.send_line("Usage: bridge <r1> <c1> <r2> <c2> <count>")
                await self.send_line("Example: bridge 1 1 1 5 2  (double bridge from (1,1) to (1,5))")
                await self.send_line("Use count=0 to remove a bridge")
                return

            try:
                r1 = int(parts[1])
                c1 = int(parts[2])
                r2 = int(parts[3])
                c2 = int(parts[4])
                count = int(parts[5])

                result = await self.current_game.validate_move(r1, c1, r2, c2, count)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

                    if self.current_game.is_complete():
                        await self.send_line("\n" + "=" * 50)
                        await self.send_line("CONGRATULATIONS! ALL ISLANDS CONNECTED!")
                        await self.send_line("=" * 50)
                        await self.send_line(self.current_game.get_stats())
                        await self.send_line("\nType 'menu' to play another game.")
                        await self.send_line("=" * 50 + "\n")

            except ValueError:
                await self.send_line("Invalid input. Use numbers only.")
            return

        # Sokoban command
        if cmd_enum == GameCommand.MOVE:
            if len(parts) != 2:
                await self.send_line("Usage: move <direction>")
                await self.send_line("Directions: up, down, left, right (or u, d, l, r)")
                return

            direction = parts[1].lower()

            result = await self.current_game.validate_move(direction)
            await self.send_line(result.message)

            if result.success:
                await self.display_puzzle()

                if self.current_game.is_complete():
                    await self.send_line("\n" + "=" * 50)
                    await self.send_line("CONGRATULATIONS! ALL BOXES ON TARGETS!")
                    await self.send_line("=" * 50)
                    await self.send_line(self.current_game.get_stats())
                    await self.send_line("\nType 'menu' to play another game.")
                    await self.send_line("=" * 50 + "\n")

            return

        # Scheduler commands
        if cmd_enum == GameCommand.ASSIGN:
            if len(parts) != 4:
                await self.send_line("Usage: assign <task_id> <worker_id> <start_time>")
                await self.send_line("Example: assign 1 2 0")
                return

            try:
                task_id = int(parts[1])
                worker_id = int(parts[2])
                start_time = int(parts[3])

                result = await self.current_game.validate_move(task_id, worker_id, start_time)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

            except ValueError:
                await self.send_line("Invalid input. Use numbers only.")
            return

        if cmd_enum == GameCommand.UNASSIGN:
            if len(parts) != 2:
                await self.send_line("Usage: unassign <task_id>")
                await self.send_line("Example: unassign 1")
                return

            try:
                task_id = int(parts[1])

                result = await self.current_game.validate_move(task_id, 0, -1)
                await self.send_line(result.message)

                if result.success:
                    await self.display_puzzle()

            except ValueError:
                await self.send_line("Invalid input. Use numbers only.")
            return

        await self.send_line("Unknown command. Type 'help' for available commands.")

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
