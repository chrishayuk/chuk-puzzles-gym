# Puzzle Arcade Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)](htmlcov/index.html)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A multi-game puzzle server hosting 7 different logic puzzle types, built using the [chuk-protocol-server](https://github.com/chrishayuk/chuk-protocol-server) framework. Perfect for demonstrating LLM reasoning capabilities and constraint solver generality!

## Try It Now

A live demo server is running on Fly.io. Try it instantly:

```bash
# Connect via Telnet (IPv6)
telnet 2a09:8280:1::b8:79f4:0 8023

# WebSocket connections
ws://puzzle-arcade-server.fly.dev:8025/ws
```

Once connected, type `help` to see available games, or `sudoku easy` to start playing!

## Features

- **7 Classic Puzzle Games** with three difficulty levels each (easy, medium, hard)
- **Multiple transport protocols:**
  - **Telnet** (port 8023) - Classic telnet protocol
  - **TCP** (port 8024) - Raw TCP connections
  - **WebSocket** (port 8025) - Modern WebSocket protocol
  - **WebSocket-Telnet** (port 8026) - WebSocket with telnet negotiation
- **Interactive menu-driven interface** with game selection
- **Hint system** for when you're stuck
- **Solution checker** and auto-solver for all games
- **Clean ASCII art grids** - perfectly aligned for easy parsing
- **Comprehensive test suite** (129 tests, 94% coverage)
- **Modern Python packaging** with pyproject.toml
- **Docker and Fly.io deployment** ready

## Available Games

| Game | Grid Size | Constraint Types | Status |
|------|-----------|------------------|--------|
| **Sudoku** | 9×9 | AllDifferent (rows, cols, boxes) | ✅ Complete |
| **KenKen** | 4×4 to 6×6 | Arithmetic cages + AllDifferent | ✅ Complete |
| **Kakuro** | 5×5 to 8×8 | Sum constraints + AllDifferent | ✅ Complete |
| **Binary Puzzle** | 6×6 to 10×10 | Adjacency limits + Equal counts | ✅ Complete |
| **Futoshiki** | 4×4 to 6×6 | Inequalities + AllDifferent | ✅ Complete |
| **Nonogram** | 5×5 to 10×10 | Line sum constraints + Blocks | ✅ Complete |
| **Logic Grid** | Variable | Category associations + Logic | ✅ Complete |

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [UV](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

#### From Source (Development)

##### Using UV (Recommended)

```bash
# Clone the repository
git clone https://github.com/chrishayuk/puzzle-arcade-server.git
cd puzzle-arcade-server

# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install development dependencies
make dev-install

# Run the server
make run
```

##### Using pip

```bash
# Clone the repository
git clone https://github.com/chrishayuk/puzzle-arcade-server.git
cd puzzle-arcade-server

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run the server
PYTHONPATH=. uv run --with chuk-protocol-server chuk-protocol-server server-launcher -c config.yaml
```

### Using Make (All Commands)

```bash
# See all available commands
make help

# Development workflow
make dev-install      # Install dev dependencies
make run              # Run the server
make test             # Run tests
make test-cov         # Run tests with coverage report
make check            # Run linting and type checking
make format           # Format code with ruff
make security         # Run security checks

# Docker workflow
make docker-build     # Build Docker image
make docker-run       # Run in Docker container

# Examples
make example-telnet              # Browse games via telnet
make example-telnet-sudoku       # Sudoku demo
make example-telnet-kenken       # KenKen demo
make example-ws                  # WebSocket tour
make example-ws-interactive      # Interactive WebSocket mode

# Deployment
make fly-deploy       # Deploy to Fly.io
make fly-logs         # View Fly.io logs
```

### Docker Setup

Build and run with Docker:

```bash
# Using Make
make docker-run

# Or manually
docker build -t puzzle-arcade-server .
docker run -p 8023:8023 -p 8024:8024 -p 8025:8025 -p 8026:8026 puzzle-arcade-server
```

## Connecting to the Server

### Local Development

**Via Telnet:**
```bash
telnet localhost 8023
```

**Via Netcat (TCP):**
```bash
nc localhost 8024
```

**Via WebSocket:**
```
ws://localhost:8025/ws
ws://localhost:8026/ws
```

## Game Menu

When you connect, you'll see the main menu:

```
==================================================
       WELCOME TO THE PUZZLE ARCADE!
==================================================

Select a game:

  1) Sudoku          - Classic logic puzzle - fill 9x9 grid with digits 1-9
  2) KenKen          - Arithmetic cage puzzle - combine math and logic
  3) Kakuro          - Crossword math puzzle - fill runs with unique digits that sum to clues
  4) Binary Puzzle   - Fill grid with 0s and 1s - no three in a row, equal counts
  5) Futoshiki       - Inequality number puzzle - fill grid with constraints
  6) Nonogram        - Picture logic puzzle - reveal image from number clues
  7) Logic Grid      - Deductive reasoning puzzle - match attributes using logic

Commands:
  <number>  - Select game by number
  <name>    - Select game by name (e.g., 'sudoku')
  help      - Show this menu again
  quit      - Exit the server
==================================================
```

## Universal Game Commands

All games support these commands:

### Starting and Managing Games
- `<number> [difficulty]` - Select game by number (e.g., `1 medium`)
- `<name> [difficulty]` - Select game by name (e.g., `sudoku hard`)
- `show` - Display the current grid
- `help` - Show game-specific commands and rules
- `menu` - Return to main menu
- `quit` - Exit the server

### Playing Games
- `place <row> <col> <value>` - Place a number/value on the grid
  - Example: `place 1 5 7` (places 7 at row 1, column 5)
- `clear <row> <col>` - Clear a cell you've filled
- `hint` - Get a hint for the next move
- `check` - Check your progress
- `solve` - Show the solution (ends current game)

### Special Commands (Game-Specific)
- **Logic Grid**: `connect` and `exclude` commands for associations
- See in-game `help` for game-specific commands

## Example Gameplay Sessions

### Sudoku

```
> sudoku medium

==================================================
SUDOKU - MEDIUM MODE
==================================================
Fill the grid so that every row, column, and 3x3 box
contains the digits 1-9 without repetition.

Type 'help' for commands or 'hint' for a clue.
==================================================

  | 1 2 3 | 4 5 6 | 7 8 9 |
  -------------------------
1 | . . 3 | . 2 . | 6 . . |
2 | 9 . . | 3 . 5 | . . 1 |
3 | . . 1 | 8 . 6 | 4 . . |
  -------------------------
4 | . . 8 | 1 . 2 | 9 . . |
5 | 7 . . | . . . | . . 8 |
6 | . . 6 | 7 . 8 | 2 . . |
  -------------------------
7 | . . 2 | 6 . 9 | 5 . . |
8 | 8 . . | 2 . 3 | . . 9 |
9 | . . 5 | . 1 . | 3 . . |
  -------------------------
Moves made: 0
==================================================

> hint
Hint: Try placing 4 at row 1, column 1

> place 1 1 4
Number placed successfully!

> check
Puzzle not yet complete. Keep going!
Moves made: 1
```

### KenKen

```
> kenken easy

==================================================
KENKEN - EASY MODE
==================================================
KENKEN RULES:
- Fill 4x4 grid with 1-4
- No repeats in rows or columns
- Satisfy cage arithmetic constraints
- Operations: + - * /
==================================================

  | 1  | 2  | 3  | 4  |
  +----+----+----+----+
1 | .8+| .  | .3 | .2 |
  +----+----+----+----+
2 | .  | .6+| .  | .3-|
  +----+----+----+----+
3 | .2 | .6+| .8+| .  |
  +----+----+----+----+
4 | .  | .  | .  | .  |
  +----+----+----+----+

Cages:
  8+: (1,1), (1,2), (2,1)
  3: (1,3)
  2: (1,4)
  ...

> place 1 3 3
Number placed successfully!
```

## Architecture

This server is built on the [chuk-protocol-server](https://github.com/chrishayuk/chuk-protocol-server) framework, which provides:

- Multiple transport protocol support (Telnet, TCP, WebSocket, WS-Telnet)
- Telnet protocol negotiation (IAC, WILL, WONT, DO, DONT)
- WebSocket handling with ping/pong keepalive
- Connection management and monitoring
- Asynchronous I/O with Python asyncio

### Game Architecture

All games extend the `PuzzleGame` abstract base class:

```python
class PuzzleGame(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def generate_puzzle(self) -> None: ...

    @abstractmethod
    def validate_move(self, *args) -> tuple[bool, str]: ...

    @abstractmethod
    def is_complete(self) -> bool: ...

    @abstractmethod
    def render_grid(self) -> str: ...

    def get_hint(self) -> tuple[Any, str] | None: ...
    def get_rules(self) -> str: ...
    def get_commands(self) -> str: ...
```

### Handler Architecture

The `ArcadeHandler` class manages:
- Menu-driven game selection
- Command parsing and routing
- Grid display with proper formatting
- Game state management per connection
- Multi-game support

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/chrishayuk/puzzle-arcade-server.git
cd puzzle-arcade-server

# Install development dependencies (with UV)
make dev-install

# Or with pip
pip install -e ".[dev]"
```

### Testing

The project has comprehensive test coverage (94%, 129 tests):

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov

# Run tests in watch mode
make test-watch

# View coverage report in browser
make serve-coverage
```

### Coverage by File

```
src/puzzle_arcade_server/base/puzzle_game.py      100%
src/puzzle_arcade_server/games/__init__.py        100%
src/puzzle_arcade_server/games/binary.py           99%
src/puzzle_arcade_server/games/futoshiki.py        98%
src/puzzle_arcade_server/games/kakuro.py           95%
src/puzzle_arcade_server/games/nonogram.py         93%
src/puzzle_arcade_server/games/sudoku.py           92%
src/puzzle_arcade_server/games/kenken.py           91%
src/puzzle_arcade_server/games/logic_grid.py       90%
------------------------------------------------------
TOTAL                                               94%
```

### Code Quality

The project uses modern Python tooling:

- **Ruff**: Fast linter and formatter (replaces black + flake8)
- **MyPy**: Static type checking
- **Pytest**: Testing framework with async support
- **Bandit**: Security vulnerability scanning

```bash
# Run all checks (lint + typecheck + test + security)
make check

# Run linter
make lint

# Format code
make format

# Type checking
make typecheck

# Security scanning
make security
```

### Running Example Clients

```bash
# Telnet client examples
make example-telnet              # Browse all games
make example-telnet-sudoku       # Sudoku demo
make example-telnet-kenken       # KenKen demo
make example-telnet-interactive  # Interactive mode

# WebSocket client examples
make example-ws                  # Tour all games
make example-ws-sudoku           # Sudoku demo
make example-ws-binary           # Binary puzzle demo
make example-ws-solve            # Solve with hints
make example-ws-interactive      # Interactive mode
```

## Deployment to Fly.io

### Using Make (Recommended)

```bash
# Deploy to Fly.io
make fly-deploy

# Check status
make fly-status

# View logs
make fly-logs
```

### Manual Deployment

1. Install the Fly CLI: https://fly.io/docs/hands-on/install-flyctl/

2. Login to Fly:
```bash
fly auth login
```

3. Create and deploy the app:
```bash
# First deployment (creates the app)
fly launch --config fly.toml --now

# Subsequent deployments
fly deploy
```

4. **Important:** Allocate a public IPv6 address for TCP services:
```bash
# Allocate IPv6 (free)
fly ips allocate-v6

# Verify IP is allocated
fly ips list
```

5. Check the status:
```bash
fly status
```

6. View logs:
```bash
fly logs
```

7. Connect to your Puzzle Arcade server:
```bash
# Get your app's IPv6 address
fly ips list

# Connect via telnet using IPv6 (free tier)
telnet <your-ipv6> 8023

# WebSocket connections work with hostname
# ws://<your-app>.fly.dev:8025/ws
```

**Note:** TCP services (Telnet, raw TCP) require a public IP address on Fly.io. We use IPv6 which is free. IPv4 costs $2/month and is not needed for most users.

## Project Structure

```
puzzle-arcade-server/
├── src/
│   └── puzzle_arcade_server/
│       ├── __init__.py           # Package initialization
│       ├── server.py             # Main arcade handler (354 lines)
│       ├── base/
│       │   ├── __init__.py       # Base package
│       │   └── puzzle_game.py    # Abstract base class (35 lines)
│       ├── games/
│       │   ├── __init__.py       # Game registry (AVAILABLE_GAMES)
│       │   ├── sudoku.py         # Sudoku (9×9, 121 lines, 92% coverage)
│       │   ├── kenken.py         # KenKen (4×4-6×6, 216 lines, 91% coverage)
│       │   ├── kakuro.py         # Kakuro (5×5-8×8, 134 lines, 95% coverage)
│       │   ├── binary.py         # Binary (6×6-10×10, 154 lines, 99% coverage)
│       │   ├── futoshiki.py      # Futoshiki (4×4-6×6, 160 lines, 98% coverage)
│       │   ├── nonogram.py       # Nonogram (5×5-10×10, 116 lines, 93% coverage)
│       │   └── logic_grid.py     # Logic Grid (117 lines, 90% coverage)
│       └── utils/
│           └── __init__.py       # Utility functions
├── tests/
│   ├── test_puzzle_game.py       # Base class tests (4 tests)
│   ├── test_sudoku_game.py       # Sudoku tests (11 tests)
│   ├── test_kenken_game.py       # KenKen tests (25 tests)
│   ├── test_kakuro_game.py       # Kakuro tests (12 tests)
│   ├── test_binary_game.py       # Binary tests (27 tests)
│   ├── test_futoshiki_game.py    # Futoshiki tests (25 tests)
│   ├── test_nonogram_game.py     # Nonogram tests (12 tests)
│   └── test_logic_grid_game.py   # Logic Grid tests (13 tests)
├── examples/
│   ├── simple_client.py          # Telnet client example
│   ├── websocket_client.py       # WebSocket client example
│   └── README.md                 # Example usage guide
├── .github/
│   └── workflows/                # CI/CD workflows (coming soon)
├── pyproject.toml                # Modern Python project config
├── config.yaml                   # Multi-transport server configuration
├── Dockerfile                    # Docker build instructions
├── fly.toml                      # Fly.io deployment config
├── Makefile                      # Development commands (50+ targets)
├── MANIFEST.in                   # Package distribution files
└── README.md                     # This file
```

### Key Statistics

- **Total Lines of Code**: ~1,038 statements in src/
- **Test Coverage**: 94% overall (129 tests)
- **Games Implemented**: 7 complete puzzle types
- **Supported Transports**: 4 (Telnet, TCP, WebSocket, WS-Telnet)
- **Make Targets**: 50+ development commands

## Use Cases

### 1. LLM Reasoning Demonstration

Perfect for demonstrating LLM reasoning capabilities:

1. **LLM connects** via telnet: `telnet localhost 8023`
2. **Selects a puzzle**: `sudoku hard`
3. **Receives puzzle** in clean ASCII format
4. **Analyzes constraints** and generates solution
5. **Submits moves**: `place 1 5 7`
6. **Server validates** each move
7. **Puzzle solved!** Proof of reasoning capability

### 2. Constraint Solver Testing

Test the generality of constraint solvers (like MCP solvers):

- **Different puzzle types** → Same underlying solver
- **Clean ASCII output** → Easy for solver parsing
- **Simple interface** → Focus on solving, not UI
- **Pure validation** → Server validates, doesn't solve

### 3. Educational Tool

Learn about constraint satisfaction problems:

- **7 different CSP types** with varying constraints
- **Well-documented code** showing puzzle generation
- **Comprehensive tests** demonstrating validation
- **Clean architecture** for adding new puzzles

## Adding New Puzzle Games

1. Create a new game file in `src/puzzle_arcade_server/games/`:

```python
from ..base.puzzle_game import PuzzleGame

class MyPuzzleGame(PuzzleGame):
    @property
    def name(self) -> str:
        return "My Puzzle"

    @property
    def description(self) -> str:
        return "A cool puzzle game"

    def generate_puzzle(self) -> None:
        # Generate puzzle with unique solution
        self.grid = [[0] * self.size for _ in range(self.size)]
        # ... your generation logic
        self.game_started = True

    def validate_move(self, row: int, col: int, num: int) -> tuple[bool, str]:
        # Validate and apply move
        if not self._is_valid(row, col, num):
            return False, "Invalid move!"
        self.grid[row][col] = num
        self.moves_made += 1
        return True, "Number placed successfully!"

    def is_complete(self) -> bool:
        # Check if puzzle is solved
        return all(cell != 0 for row in self.grid for cell in row)

    def render_grid(self) -> str:
        # Return ASCII art representation
        return "  | 1 | 2 | 3 |\n" + ...

    def get_rules(self) -> str:
        return "MY PUZZLE RULES:\n- Rule 1\n- Rule 2"

    def get_commands(self) -> str:
        return "MY PUZZLE COMMANDS:\n  place <row> <col> <num>"
```

2. Register it in `src/puzzle_arcade_server/games/__init__.py`:

```python
from .my_puzzle import MyPuzzleGame

AVAILABLE_GAMES = {
    "sudoku": SudokuGame,
    "kenken": KenKenGame,
    # ... other games
    "mypuzzle": MyPuzzleGame,  # Add your game
}
```

3. Add tests in `tests/test_my_puzzle_game.py`:

```python
from puzzle_arcade_server.games.my_puzzle import MyPuzzleGame

class TestMyPuzzleGame:
    def test_initialization(self):
        game = MyPuzzleGame("easy")
        assert game.name == "My Puzzle"

    def test_generate_puzzle(self):
        game = MyPuzzleGame("easy")
        game.generate_puzzle()
        assert game.game_started

    # ... more tests (aim for >90% coverage)
```

4. Run tests and verify:

```bash
make test-cov
make check
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-puzzle`)
3. Make your changes
4. Run tests and checks (`make check`)
5. Ensure coverage stays above 90% (`make test-cov`)
6. Commit your changes (`git commit -m 'Add amazing puzzle'`)
7. Push to the branch (`git push origin feature/amazing-puzzle`)
8. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide (enforced by ruff)
- Add type hints to all functions
- Write tests for new features (>90% coverage)
- Update documentation as needed
- Ensure all grid headers align properly with rows

## Troubleshooting

### Server won't start
- Ensure chuk-protocol-server is installed: `uv pip install chuk-protocol-server`
- Check ports aren't already in use: `lsof -i :8023,8024,8025,8026`
- Verify Python version is 3.11+: `python --version`

### Tests failing
- Install dev dependencies: `make dev-install`
- Clear cache: `make clean`
- Check Python version compatibility

### Coverage too low
- Run coverage report: `make test-cov`
- View HTML report: `make serve-coverage`
- Add tests for uncovered code

### Grid alignment issues
- All grid headers must align with row pipes
- Use the format `"  |"` for headers to match row format `"N |"`
- Test visually: `make example-telnet-kenken`

## License

MIT License - see the main chuk-protocol-server project for details.

## Credits

- Built using the [chuk-protocol-server](https://github.com/chrishayuk/chuk-protocol-server) framework
- Puzzle generation algorithms based on backtracking and constraint propagation
- Uses modern Python tooling: UV, Ruff, MyPy, Pytest

## Links

- [chuk-protocol-server](https://github.com/chrishayuk/chuk-protocol-server) - Multi-transport server framework
- [sudoku-telnet-server](https://github.com/chrishayuk/sudoku-telnet-server) - Original single-game implementation
- [UV](https://github.com/astral-sh/uv) - Fast Python package manager
- [Ruff](https://github.com/astral-sh/ruff) - Fast Python linter and formatter
- [Fly.io](https://fly.io) - Cloud deployment platform

---

**Ready to test your solver?** Connect now and start solving! 🎮
