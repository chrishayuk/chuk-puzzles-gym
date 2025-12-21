#!/usr/bin/env python3
"""
Simple Telnet Client for Puzzle Arcade Server

This example demonstrates how to connect to the Puzzle Arcade server
and interact with it programmatically.
"""

import socket
import sys
import time


class PuzzleArcadeClient:
    """Simple client for connecting to the Puzzle Arcade telnet server."""

    def __init__(self, host: str = "localhost", port: int = 8023):
        """Initialize the client.

        Args:
            host: Server hostname
            port: Server port
        """
        self.host = host
        self.port = port
        self.sock = None

    def connect(self) -> bool:
        """Connect to the server.

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def send_command(self, command: str) -> None:
        """Send a command to the server.

        Args:
            command: Command string to send
        """
        if self.sock:
            self.sock.sendall((command + "\n").encode("utf-8"))
            print(f"> {command}")

    def receive_response(self, timeout: float = 1.0) -> str:
        """Receive response from the server.

        Args:
            timeout: Timeout in seconds

        Returns:
            Response string from server
        """
        if not self.sock:
            return ""

        self.sock.settimeout(timeout)
        response = ""
        try:
            while True:
                chunk = self.sock.recv(4096).decode("utf-8", errors="ignore")
                if not chunk:
                    break
                response += chunk
        except TimeoutError:
            pass
        except Exception as e:
            print(f"Error receiving: {e}")

        return response

    def disconnect(self) -> None:
        """Disconnect from the server."""
        if self.sock:
            try:
                self.send_command("quit")
                time.sleep(0.5)
                self.sock.close()
                print("Disconnected")
            except Exception as e:
                print(f"Error disconnecting: {e}")
            finally:
                self.sock = None

    def interactive_mode(self) -> None:
        """Run in interactive mode, allowing user input."""
        if not self.connect():
            return

        # Read welcome message
        welcome = self.receive_response()
        print(welcome)

        try:
            while True:
                command = input("\nEnter command (or 'quit' to exit): ").strip()
                if not command:
                    continue

                self.send_command(command)

                if command.lower() in ["quit", "exit", "q"]:
                    break

                response = self.receive_response(timeout=2.0)
                print(response)

        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.disconnect()


def example_sudoku_game():
    """Example of playing Sudoku."""
    print("=" * 60)
    print("EXAMPLE: Sudoku Game Session")
    print("=" * 60)

    client = PuzzleArcadeClient()

    if not client.connect():
        return

    # Read welcome message
    response = client.receive_response()
    print(response)

    # Start Sudoku game (game name + difficulty in one command)
    print("\n[Starting Sudoku easy game]")
    client.send_command("sudoku easy")
    time.sleep(0.5)
    response = client.receive_response(timeout=2.0)
    print(response)

    # Get a hint
    print("\n[Requesting hint]")
    client.send_command("hint")
    time.sleep(0.3)
    response = client.receive_response()
    print(response)

    # Place a number based on the hint
    print("\n[Placing a number]")
    client.send_command("place 1 1 5")
    time.sleep(0.3)
    response = client.receive_response(timeout=2.0)
    print(response)

    # Show the grid
    print("\n[Showing grid]")
    client.send_command("show")
    time.sleep(0.3)
    response = client.receive_response(timeout=2.0)
    print(response)

    # Check progress
    print("\n[Checking progress]")
    client.send_command("check")
    time.sleep(0.3)
    response = client.receive_response()
    print(response)

    # Disconnect
    client.disconnect()


def example_kenken_game():
    """Example of playing KenKen."""
    print("=" * 60)
    print("EXAMPLE: KenKen Game Session")
    print("=" * 60)

    client = PuzzleArcadeClient()

    if not client.connect():
        return

    # Read welcome message
    response = client.receive_response()
    print(response)

    # Start KenKen game (game name + difficulty in one command)
    print("\n[Starting KenKen medium game]")
    client.send_command("kenken medium")
    time.sleep(0.5)
    response = client.receive_response(timeout=2.0)
    print(response)

    # Show the grid
    print("\n[Showing grid]")
    client.send_command("show")
    time.sleep(0.3)
    response = client.receive_response(timeout=2.0)
    print(response)

    # Get a hint
    print("\n[Requesting hint]")
    client.send_command("hint")
    time.sleep(0.3)
    response = client.receive_response()
    print(response)

    # Disconnect
    client.disconnect()


def example_game_selection():
    """Example of browsing available games."""
    print("=" * 60)
    print("EXAMPLE: Browsing Available Games")
    print("=" * 60)

    client = PuzzleArcadeClient()

    if not client.connect():
        return

    # Read welcome message (also shows game list)
    response = client.receive_response()
    print(response)

    # Get help (shows game list again)
    print("\n[Getting help]")
    client.send_command("help")
    time.sleep(0.3)
    response = client.receive_response(timeout=2.0)
    print(response)

    # Try a few games - start them, show rules, then return to menu
    games = ["sudoku", "kenken", "kakuro", "binary"]

    for game in games:
        print(f"\n[Starting {game}]")
        client.send_command(f"{game} easy")
        time.sleep(0.3)
        response = client.receive_response(timeout=2.0)
        print(response)

        # Get rules for this game
        print(f"\n[Getting rules for {game}]")
        client.send_command("rules")
        time.sleep(0.3)
        response = client.receive_response()
        print(response)

        # Return to menu
        print("\n[Returning to menu]")
        client.send_command("menu")
        time.sleep(0.3)
        response = client.receive_response()
        print(response)

    # Disconnect
    client.disconnect()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

        if mode == "interactive":
            print("Starting interactive mode...")
            client = PuzzleArcadeClient()
            client.interactive_mode()

        elif mode == "sudoku":
            example_sudoku_game()

        elif mode == "kenken":
            example_kenken_game()

        elif mode == "browse":
            example_game_selection()

        elif mode == "help":
            print("Usage: python simple_client.py [mode]")
            print("\nModes:")
            print("  interactive - Interactive command-line mode")
            print("  sudoku      - Run Sudoku example session")
            print("  kenken      - Run KenKen example session")
            print("  browse      - Browse all available games")
            print("  help        - Show this help")
            print("\nDefault: browse")

        else:
            print(f"Unknown mode: {mode}")
            print("Use 'help' for usage information")

    else:
        # Default: browse games
        example_game_selection()


if __name__ == "__main__":
    main()
