# Puzzle Arcade Server - Examples

This directory contains example clients demonstrating how to connect to and interact with the Puzzle Arcade Server.

## Available Examples

### 1. Simple Telnet Client (`simple_client.py`)

A straightforward telnet client that demonstrates basic server interaction.

**Usage:**

```bash
# Browse all available games (default)
python examples/simple_client.py

# Run Sudoku example
python examples/simple_client.py sudoku

# Run KenKen example
python examples/simple_client.py kenken

# Browse all games
python examples/simple_client.py browse

# Interactive mode
python examples/simple_client.py interactive
```

**Or use Make commands:**

```bash
make example-telnet              # Browse mode (default)
make example-telnet-sudoku       # Sudoku demo
make example-telnet-kenken       # KenKen demo
make example-telnet-interactive  # Interactive mode
```

### 2. WebSocket Client (`websocket_client.py`)

An async WebSocket client for connecting via WebSocket protocol.

**Requirements:**
```bash
pip install websockets
# or
uv pip install websockets
```

**Usage:**

```bash
# Tour of all games (default)
python examples/websocket_client.py

# Run Sudoku example
python examples/websocket_client.py sudoku

# Run Binary puzzle example
python examples/websocket_client.py binary

# Tour all games
python examples/websocket_client.py tour

# Example with hints
python examples/websocket_client.py solve

# Interactive mode
python examples/websocket_client.py interactive
```

**Or use Make commands:**

```bash
make example-ws              # Tour mode (default)
make example-ws-sudoku       # Sudoku demo
make example-ws-binary       # Binary puzzle demo
make example-ws-tour         # Tour all games
make example-ws-solve        # Solve with hints
make example-ws-interactive  # Interactive mode
```

## Available Games

The Puzzle Arcade Server offers 7 different puzzle types:

1. **Sudoku** - Classic 9x9 number placement puzzle
2. **KenKen** - Arithmetic cage-based puzzle
3. **Kakuro** - Crossword-style mathematical puzzle
4. **Binary** - 0s and 1s placement with adjacency rules
5. **Futoshiki** - Inequality-based number placement
6. **Nonogram** - Picture logic puzzle using line clues
7. **Logic Grid** - Deductive reasoning puzzle

## Server Connection Details

### Telnet/TCP Connections:
- **Telnet**: `telnet localhost 8023`
- **TCP**: `nc localhost 8024` (netcat)

### WebSocket Connections:
- **WebSocket**: `ws://localhost:8025/ws`
- **WS-Telnet**: `ws://localhost:8026/ws`

## Common Commands

Once connected to the server, you can use these commands:

### General Commands
- `help` - Show available commands
- `list` - List all available puzzle games
- `select <game>` - Select a puzzle game (e.g., `select sudoku`)
- `rules` - Show rules for the current game
- `commands` - Show game-specific commands
- `quit` - Disconnect from server

### Game Commands
- `start <difficulty>` - Start a new game (easy/medium/hard)
- `show` - Display the current puzzle grid
- `hint` - Get a hint for the next move
- `check` - Check if the puzzle is complete
- `stats` - Show game statistics
- `place <row> <col> <value>` - Place a number (game-specific)
- `clear <row> <col>` - Clear a cell (game-specific)

## Example Session

```bash
$ python examples/simple_client.py interactive
Connected to localhost:8023
Welcome to Puzzle Arcade Server!
...

Enter command (or 'quit' to exit): list
> list
Available games:
  1. sudoku
  2. kenken
  3. kakuro
  ...

Enter command (or 'quit' to exit): select sudoku
> select sudoku
Selected game: Sudoku

Enter command (or 'quit' to exit): start easy
> start easy
Started easy Sudoku puzzle...

Enter command (or 'quit' to exit): show
> show
    1 2 3   4 5 6   7 8 9
  +-------+-------+-------+
1 | . . 3 | . 2 . | 6 . . |
2 | 9 . . | 3 . 5 | . . 1 |
...

Enter command (or 'quit' to exit): hint
> hint
Hint: Try placing 5 at row 1, column 1

Enter command (or 'quit' to exit): place 1 1 5
> place 1 1 5
Placed 5 at (1, 1)

Enter command (or 'quit' to exit): quit
> quit
Disconnected
```

## Writing Your Own Client

### Telnet/TCP Client Example

```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("localhost", 8023))

# Receive welcome message
welcome = sock.recv(4096).decode("utf-8")
print(welcome)

# Send commands
sock.sendall("select sudoku\n".encode("utf-8"))
response = sock.recv(4096).decode("utf-8")
print(response)

sock.sendall("start easy\n".encode("utf-8"))
response = sock.recv(4096).decode("utf-8")
print(response)

# ... more interactions ...

sock.sendall("quit\n".encode("utf-8"))
sock.close()
```

### WebSocket Client Example

```python
import asyncio
import websockets

async def play_puzzle():
    uri = "ws://localhost:8025/ws"
    async with websockets.connect(uri) as websocket:
        # Receive welcome
        welcome = await websocket.recv()
        print(welcome)

        # Select game
        await websocket.send("select kenken")
        response = await websocket.recv()
        print(response)

        # Start game
        await websocket.send("start medium")
        response = await websocket.recv()
        print(response)

        # ... more interactions ...

        await websocket.send("quit")

asyncio.run(play_puzzle())
```

## Integration with LLMs and MCP

The Puzzle Arcade Server is designed to work with:

- **LLM clients** - Language models can play these puzzles by parsing the text-based grids
- **MCP (Model Context Protocol) solvers** - External solvers can be integrated to solve puzzles
- **Autonomous agents** - Perfect for testing reasoning and problem-solving capabilities

### Example LLM Integration Pattern

```python
# Pseudocode for LLM puzzle solver
async def llm_puzzle_solver():
    client = PuzzleArcadeWebSocketClient()
    await client.connect()

    # Select game
    await client.send_command("select sudoku")
    await client.send_command("start easy")

    while not solved:
        # Get current state
        await client.send_command("show")
        grid_state = await client.receive_response()

        # Send to LLM for analysis
        llm_move = analyze_with_llm(grid_state)

        # Execute move
        await client.send_command(f"place {llm_move.row} {llm_move.col} {llm_move.value}")

        # Check if complete
        await client.send_command("check")
        result = await client.receive_response()
        solved = "complete" in result.lower()
```

## Troubleshooting

### Server not responding

Make sure the server is running:

```bash
make run
```

### WebSocket connection fails

Ensure you have websockets installed:

```bash
pip install websockets
```

### Connection refused

Check that the correct port is being used and the server is listening.

## More Information

- See the main [README.md](../README.md) for server setup and configuration
- Check [config.yaml](../config.yaml) for server port configuration
- Visit the repository for more examples and documentation

## License

MIT - See [LICENSE](../LICENSE) for details
