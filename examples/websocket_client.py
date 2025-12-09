#!/usr/bin/env python3
"""
WebSocket Client for Puzzle Arcade Server

This example demonstrates how to connect to the Puzzle Arcade server
via WebSocket and interact with it.

Requirements:
    pip install websockets
"""

import asyncio
import sys

try:
    import websockets
except ImportError:
    print("This example requires the 'websockets' library.")
    print("Install it with: pip install websockets")
    sys.exit(1)


class PuzzleArcadeWebSocketClient:
    """WebSocket client for the Puzzle Arcade server."""

    def __init__(self, uri: str = "ws://localhost:8025/ws"):
        """Initialize the client.

        Args:
            uri: WebSocket URI
        """
        self.uri = uri
        self.websocket = None

    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.uri)
            print(f"Connected to {self.uri}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    async def send_command(self, command: str):
        """Send a command to the server.

        Args:
            command: Command to send
        """
        if self.websocket:
            await self.websocket.send(command)
            print(f"> {command}")

    async def receive_response(self, timeout: float = 2.0):
        """Receive a response from the server.

        Args:
            timeout: Timeout in seconds

        Returns:
            Response string
        """
        if not self.websocket:
            return ""

        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            return response
        except TimeoutError:
            return ""
        except Exception as e:
            print(f"Error receiving: {e}")
            return ""

    async def disconnect(self):
        """Disconnect from the server."""
        if self.websocket:
            try:
                await self.send_command("quit")
                await asyncio.sleep(0.5)
                await self.websocket.close()
                print("Disconnected")
            except Exception as e:
                print(f"Error disconnecting: {e}")

    async def interactive_mode(self):
        """Run in interactive mode."""
        if not await self.connect():
            return

        # Receive welcome message
        welcome = await self.receive_response()
        print(welcome)

        try:
            while True:
                # Get user input (this is tricky in async, using run_in_executor)
                loop = asyncio.get_event_loop()
                command = await loop.run_in_executor(
                    None, lambda: input("\nEnter command (or 'quit' to exit): ").strip()
                )

                if not command:
                    continue

                await self.send_command(command)

                if command.lower() in ["quit", "exit", "q"]:
                    break

                response = await self.receive_response(timeout=2.0)
                print(response)

        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await self.disconnect()


async def example_sudoku_game():
    """Example of playing Sudoku via WebSocket."""
    print("=" * 60)
    print("EXAMPLE: Sudoku Game via WebSocket")
    print("=" * 60)

    client = PuzzleArcadeWebSocketClient()

    if not await client.connect():
        return

    # Receive welcome message
    response = await client.receive_response()
    print(response)

    # Select Sudoku
    print("\n[Selecting Sudoku]")
    await client.send_command("select sudoku")
    response = await client.receive_response()
    print(response)

    # Start an easy game
    print("\n[Starting easy game]")
    await client.send_command("start easy")
    response = await client.receive_response()
    print(response)

    # Get a hint
    print("\n[Requesting hint]")
    await client.send_command("hint")
    response = await client.receive_response()
    print(response)

    # Place a number
    print("\n[Placing a number]")
    await client.send_command("place 1 1 5")
    response = await client.receive_response()
    print(response)

    # Show the grid
    print("\n[Showing grid]")
    await client.send_command("show")
    response = await client.receive_response()
    print(response)

    # Check progress
    print("\n[Checking progress]")
    await client.send_command("check")
    response = await client.receive_response()
    print(response)

    # Disconnect
    await client.disconnect()


async def example_binary_puzzle():
    """Example of playing Binary puzzle via WebSocket."""
    print("=" * 60)
    print("EXAMPLE: Binary Puzzle Game via WebSocket")
    print("=" * 60)

    client = PuzzleArcadeWebSocketClient()

    if not await client.connect():
        return

    # Receive welcome
    await client.receive_response()

    # Select Binary puzzle
    print("\n[Selecting Binary Puzzle]")
    await client.send_command("select binary")
    response = await client.receive_response()
    print(response)

    # Get rules
    print("\n[Getting rules]")
    await client.send_command("rules")
    response = await client.receive_response()
    print(response)

    # Start an easy game
    print("\n[Starting easy game]")
    await client.send_command("start easy")
    response = await client.receive_response()
    print(response)

    # Show the grid
    print("\n[Showing grid]")
    await client.send_command("show")
    response = await client.receive_response()
    print(response)

    # Get a hint
    print("\n[Requesting hint]")
    await client.send_command("hint")
    response = await client.receive_response()
    print(response)

    # Get commands
    print("\n[Getting available commands]")
    await client.send_command("commands")
    response = await client.receive_response()
    print(response)

    # Disconnect
    await client.disconnect()


async def example_game_tour():
    """Example showing multiple games."""
    print("=" * 60)
    print("EXAMPLE: Tour of All Puzzle Games")
    print("=" * 60)

    client = PuzzleArcadeWebSocketClient()

    if not await client.connect():
        return

    # Receive welcome
    await client.receive_response()

    # List available games
    print("\n[Listing available games]")
    await client.send_command("list")
    response = await client.receive_response()
    print(response)

    # Tour each game
    games = [
        ("sudoku", "Classic 9x9 Sudoku"),
        ("kenken", "Arithmetic cage puzzle"),
        ("kakuro", "Crossword-style math puzzle"),
        ("binary", "0s and 1s placement"),
        ("futoshiki", "Inequality-based puzzle"),
        ("nonogram", "Picture logic puzzle"),
        ("logic_grid", "Deductive reasoning puzzle"),
    ]

    for game_name, description in games:
        print(f"\n{'=' * 60}")
        print(f"Game: {game_name.upper()} - {description}")
        print("=" * 60)

        # Select game
        print(f"\n[Selecting {game_name}]")
        await client.send_command(f"select {game_name}")
        response = await client.receive_response()
        print(response)

        # Get rules
        print(f"\n[Rules for {game_name}]")
        await client.send_command("rules")
        response = await client.receive_response()
        print(response)

        # Start easy game
        print(f"\n[Starting easy {game_name} game]")
        await client.send_command("start easy")
        response = await client.receive_response()
        print(response)

        # Show initial grid
        print(f"\n[Initial {game_name} grid]")
        await client.send_command("show")
        response = await client.receive_response()
        print(response)

        await asyncio.sleep(1)

    # Get overall help
    print("\n[Getting general help]")
    await client.send_command("help")
    response = await client.receive_response()
    print(response)

    # Disconnect
    await client.disconnect()


async def example_solve_with_hints():
    """Example showing how to use hints to solve a puzzle."""
    print("=" * 60)
    print("EXAMPLE: Solving with Hints")
    print("=" * 60)

    client = PuzzleArcadeWebSocketClient()

    if not await client.connect():
        return

    # Receive welcome
    await client.receive_response()

    # Select Sudoku
    print("\n[Selecting Sudoku]")
    await client.send_command("select sudoku")
    await client.receive_response()

    # Start an easy game
    print("\n[Starting easy game]")
    await client.send_command("start easy")
    response = await client.receive_response()
    print(response)

    # Get 10 hints
    print("\n[Getting 10 hints]")
    for i in range(10):
        await client.send_command("hint")
        hint = await client.receive_response()
        print(f"\nHint {i + 1}: {hint}")

        # In a real implementation, you would parse the hint
        # and automatically place the number
        # Example hint: "Hint: Try placing 5 at row 1, column 3"
        # You would extract: row=1, col=3, num=5
        # Then: await client.send_command('place 1 3 5')

        await asyncio.sleep(0.3)

    # Show current state
    print("\n[Showing current grid]")
    await client.send_command("show")
    response = await client.receive_response()
    print(response)

    # Check progress
    print("\n[Checking progress]")
    await client.send_command("check")
    response = await client.receive_response()
    print(response)

    # Disconnect
    await client.disconnect()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

        if mode == "interactive":
            print("Starting interactive WebSocket mode...")
            client = PuzzleArcadeWebSocketClient()
            asyncio.run(client.interactive_mode())

        elif mode == "sudoku":
            asyncio.run(example_sudoku_game())

        elif mode == "binary":
            asyncio.run(example_binary_puzzle())

        elif mode == "tour":
            asyncio.run(example_game_tour())

        elif mode == "solve":
            asyncio.run(example_solve_with_hints())

        elif mode == "help":
            print("Usage: python websocket_client.py [mode]")
            print("\nModes:")
            print("  interactive - Interactive command-line mode")
            print("  sudoku      - Run Sudoku example session")
            print("  binary      - Run Binary puzzle example")
            print("  tour        - Tour of all available games")
            print("  solve       - Example using hints to solve")
            print("  help        - Show this help")
            print("\nDefault: tour")
            print("\nRequires: pip install websockets")

        else:
            print(f"Unknown mode: {mode}")
            print("Use 'help' for usage information")

    else:
        # Default: tour of games
        asyncio.run(example_game_tour())


if __name__ == "__main__":
    main()
