# chuk-puzzles-gym

[![PyPI](https://img.shields.io/pypi/v/chuk-puzzles-gym.svg)](https://pypi.org/project/chuk-puzzles-gym/)
[![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)](htmlcov/index.html)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-purple.svg)](https://docs.pydantic.dev/)
[![Type Checked](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

A **multi-game puzzle gym** for **LLM training and benchmarking**, hosting 30 different logic puzzle types with synthetic data generation. Built using chuk-gym-core and chuk-protocol-server.

> This is a demonstration project provided as-is for learning and testing purposes.

**Perfect for:**
- 🤖 **LLM Agent Testing** - Benchmark reasoning capabilities across constraint types
- 🎯 **CP-SAT Education** - Learn constraint programming through progressive puzzles
- 💼 **Business Demos** - Map puzzle patterns to real scheduling, optimization, and allocation problems
- 🔧 **MCP Tool Integration** - Showcase CHUK + constraint solver workflows

Each puzzle demonstrates specific **constraint patterns** (AllDifferent, Optimization, Connectivity, Boolean SAT, etc.) and maps to **business use cases** (scheduling, resource allocation, routing, etc.).

## Try It Now

### Run Locally with uvx

No installation required - run directly with [uvx](https://docs.astral.sh/uv/guides/tools/):

```bash
# Start the puzzle server
uvx chuk-puzzles-gym

# Generate training datasets
uvx --from chuk-puzzles-gym chuk-puzzles-export -g sudoku -n 100 -o data.jsonl

# Benchmark an agent
uvx --from chuk-puzzles-gym chuk-puzzles-eval -g sudoku -n 10

# Run CHUK-R aggregate benchmark
uvx --from chuk-puzzles-gym chuk-puzzles-benchmark -d easy -n 5
```

### Connect to Live Demo

A live demo server is running on Fly.io:

```bash
# Connect via Telnet (IPv6)
telnet 2a09:8280:1::b8:79f4:0 8023

# WebSocket connections
ws://chuk-puzzles-gym.fly.dev:8025/ws
```

Once connected, type `help` to see available games, or `sudoku easy` to start playing!

## Features

- **30 Puzzle Games** with three difficulty levels each (easy, medium, hard)
  - **7 Classic Logic Puzzles** - Sudoku, KenKen, Kakuro, Binary, Futoshiki, Nonogram, Logic Grid
  - **7 Advanced CP-SAT Puzzles** - Killer Sudoku, Lights Out, Mastermind, Slitherlink, Bridges, Hitori, Shikaku
  - **5 Specialized Constraint Puzzles** - Hidato, Tents and Trees, Fillomino, Star Battle, Sokoban
  - **2 Optimization Challenges** - Knapsack, Task Scheduler
  - **3 Advanced Reasoning Puzzles** - Nurikabe, Einstein's Puzzle, Minesweeper
  - **6 Combinatorial & Search Puzzles** - Skyscrapers, N-Queens, Numberlink, Graph Coloring, Cryptarithmetic, Rush Hour
- **Agent-Friendly Mode** - Structured output with clear markers for AI agents and tools
  - Enable with `mode agent` command
  - Machine-parseable grid format with clear start/end markers
  - Compact output optimized for LLM tool integration
- **Reasoning Depth Metrics** - Measure *how* agents reason, not just if they succeed
  - Backtrack detection (did the agent revise previous placements?)
  - Progress steadiness (monotonic advance toward solution?)
  - Error streak analysis (isolated mistakes vs. clustered confusion?)
  - Reasoning overhead (wasted work relative to optimal path)
  - Solver distance traces (remaining work after each valid move)
  - Available in all paths: Gym env, eval harness, and server (telnet/WebSocket)
- **Evaluation Harness** (`chuk-puzzles-eval`) - Built-in benchmarking CLI
  - Batch evaluation with configurable episodes
  - Multiple output formats (JSON, CSV, Markdown)
  - Metrics: moves, invalid moves, hints, solve time, reasoning depth
  - Reproducible with deterministic seeds
- **CHUK-R Benchmark** (`chuk-puzzles-benchmark`) - Aggregate reasoning score
  - Single 0-100 score across all 30 games
  - 4 reasoning families: Logic, Constraint, Search, Planning
  - Weighted scoring: efficiency, errors, backtracks, steadiness, hint independence
  - LLM agent testing with OpenAI models (gpt-4o-mini, gpt-4o)
- **Dataset Export** (`chuk-puzzles-export`) - Synthetic data generation for LLM training
  - JSONL output with complete problem definitions and solutions
  - Step-by-step reasoning traces for teacher-forcing
  - Constraint metadata and difficulty profiles
  - Compatible with chuk-gym-core schema
- **Multiple transport protocols:**
  - **Telnet** (port 8023) - Classic telnet protocol
  - **TCP** (port 8024) - Raw TCP connections
  - **WebSocket** (port 8025) - Modern WebSocket protocol
  - **WebSocket-Telnet** (port 8026) - WebSocket with telnet negotiation
- **Interactive menu-driven interface** with game selection
- **Hint system** for when you're stuck
- **Solution checker** and auto-solver for all games
- **Clean ASCII art grids** - perfectly aligned for easy parsing
- **Deterministic seeding** - Replay any puzzle with the same seed
- **Gymnasium-compatible RL Environment** (`PuzzleEnv`) for training agents
- **Comprehensive test suite** (1323 tests, 94% coverage)
- **Modern Python best practices:**
  - **Pydantic v2 native** - All models use ConfigDict for type safety
  - **Async native** - Full async/await support throughout
  - **Type-safe** - No dict["key"] patterns, only typed models
  - **Enum-based** - No magic strings, proper enum constants
- **Modern Python packaging** with pyproject.toml
- **Docker and Fly.io deployment** ready

## Available Games

### Classic Logic Puzzles

| Game | Grid Size | Constraint Types | Status |
|------|-----------|------------------|--------|
| **Sudoku** | 9×9 | AllDifferent (rows, cols, boxes) | ✅ Complete |
| **KenKen** | 4×4 to 6×6 | Arithmetic cages + AllDifferent | ✅ Complete |
| **Kakuro** | 5×5 to 8×8 | Sum constraints + AllDifferent | ✅ Complete |
| **Binary Puzzle** | 6×6 to 10×10 | Adjacency limits + Equal counts | ✅ Complete |
| **Futoshiki** | 4×4 to 6×6 | Inequalities + AllDifferent | ✅ Complete |
| **Nonogram** | 5×5 to 10×10 | Line sum constraints + Blocks | ✅ Complete |
| **Logic Grid** | Variable | Category associations + Logic | ✅ Complete |

### Advanced CP-SAT Puzzles

| Game | Grid Size | Constraint Types | Status |
|------|-----------|------------------|--------|
| **Killer Sudoku** | 9×9 | Linear constraints + AllDifferent + Cages | ✅ Complete |
| **Lights Out** | 5×5 to 7×7 | Boolean XOR constraints (SAT) | ✅ Complete |
| **Mastermind** | 4-6 pegs | Deduction + Feedback constraints | ✅ Complete |
| **Slitherlink** | 5×5 to 10×10 | Global loop + Edge constraints | ✅ Complete |
| **Bridges** | 7×7 to 11×11 | Connectivity + Degree constraints | ✅ Complete |
| **Hitori** | 5×5 to 9×9 | AllDifferent + Adjacency + Connectivity | ✅ Complete |
| **Shikaku** | 6×6 to 10×10 | Area partitioning + Rectangle covering | ✅ Complete |

### Specialized Constraint Puzzles

| Game | Grid Size | Constraint Types | Status |
|------|-----------|------------------|--------|
| **Hidato** | 5×5 to 9×9 | Sequential adjacency + Hamiltonian path | ✅ Complete |
| **Tents and Trees** | 6×6 to 10×10 | Bipartite matching + Adjacency avoidance | ✅ Complete |
| **Fillomino** | 6×6 to 10×10 | Region growth + Self-referential constraints | ✅ Complete |
| **Star Battle** | 6×6 to 10×10 | Multi-region placement + Adjacency avoidance | ✅ Complete |
| **Sokoban** | 6×6 to 10×10 | Spatial planning + Irreversible actions (optimization) | ✅ Complete |

### Optimization Challenges

| Game | Problem Size | Constraint Types | Status |
|------|-------------|------------------|--------|
| **Knapsack** | 5-12 items | Value maximization + Capacity constraint | ✅ Complete |
| **Task Scheduler** | 4-8 tasks | Makespan minimization + Dependencies + Resources | ✅ Complete |

### Advanced Reasoning Puzzles

| Game | Grid Size | Constraint Types | Status |
|------|-----------|------------------|--------|
| **Nurikabe** | 6×6 to 10×10 | Connectivity + Island sizes + No 2×2 blocks | ✅ Complete |
| **Einstein's Puzzle** | 5 houses × 5 attributes | Multi-attribute deduction + Logic chains | ✅ Complete |
| **Minesweeper** | 6×6 to 10×10 | Probabilistic reasoning + Safe deduction | ✅ Complete |

### Combinatorial & Search Puzzles

| Game | Grid Size | Constraint Types | Status |
|------|-----------|------------------|--------|
| **Skyscrapers** | 4×4 to 6×6 | Latin square + Visibility clues from 4 borders | ✅ Complete |
| **N-Queens** | 6×6 to 12×12 | Placement + Row/Column/Diagonal attack avoidance | ✅ Complete |
| **Numberlink** | 5×5 to 9×9 | Path connectivity + Non-crossing + Space filling | ✅ Complete |
| **Graph Coloring** | 6-15 nodes | Graph coloring + Inequality + Global constraint | ✅ Complete |
| **Cryptarithmetic** | 3-5 digit words | Arithmetic + AllDifferent + Carry propagation | ✅ Complete |
| **Rush Hour** | 6×6 | Sequential planning + Spatial blocking + Search | ✅ Complete |

## Solver Profiles & Business Mapping

Each game includes metadata for **constraint types**, **business analogies**, and **complexity profiles**, making it easy to:

- **Select puzzles by constraint pattern** - Need to demonstrate Boolean SAT? → Lights Out
- **Map to business use cases** - Task Scheduler → Sprint Planning, Knapsack → Portfolio Selection
- **Benchmark LLM reasoning** - Compare model performance across different constraint densities

### Example: Query Games by Profile

```python
from chuk_puzzles_gym.games import AVAILABLE_GAMES

# Find all optimization problems
optimization_games = [
    name for name, game_class in AVAILABLE_GAMES.items()
    if "optimization" in game_class().constraint_types
]
# → ['knapsack', 'scheduler']

# Find games that model resource allocation
resource_games = [
    name for name, game_class in AVAILABLE_GAMES.items()
    if "resource_allocation" in game_class().business_analogies
]
# → ['scheduler', 'knapsack']
```

### Quick Reference: Constraint Types to Business Problems

| Constraint Pattern | Puzzle Examples | Business Use Cases |
|-------------------|-----------------|-------------------|
| **Optimization** | Knapsack, Scheduler | Portfolio selection, Sprint planning, Budget allocation |
| **Precedence** | Scheduler | Project dependencies, Workflow sequencing |
| **Sequential Adjacency** | Hidato | Path planning, Route sequencing, Tour optimization |
| **Hamiltonian Path** | Hidato | Traveling salesman, Circuit design |
| **Bipartite Matching** | Tents and Trees | Job assignment, Resource pairing |
| **Region Growth** | Fillomino | Territory expansion, Cluster formation |
| **Spatial Planning** | Sokoban | Warehouse logistics, Movement planning |
| **Connectivity** | Nurikabe, Slitherlink | Network design, Routing, Zone planning |
| **Global Loop** | Slitherlink | Circuit design, Path finding |
| **Boolean SAT** | Lights Out | Feature dependencies, Toggle systems |
| **Cage Sums** | Killer Sudoku, Kakuro | Team budgets, Grouped constraints |
| **AllDifferent** | Sudoku, KenKen, Skyscrapers | Resource uniqueness, Assignment problems |
| **Visibility/Ordering** | Skyscrapers | Priority ranking, Stack-based processing |
| **Attack Avoidance** | N-Queens, Star Battle | Non-conflicting resource placement |
| **Path Connectivity** | Numberlink, Nurikabe | Network routing, Cable layout |
| **Graph Coloring** | Graph Coloring | Frequency assignment, Register allocation, Scheduling |
| **Arithmetic Deduction** | Cryptarithmetic, KenKen | Code breaking, Constraint propagation |
| **Sequential Planning** | Rush Hour, Sokoban | Logistics planning, Deadlock resolution |

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [UV](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

#### Using uvx (No Installation Required)

Run directly without installing using [uvx](https://docs.astral.sh/uv/guides/tools/):

```bash
# Run the puzzle server
uvx chuk-puzzles-gym

# Generate synthetic datasets
uvx --from chuk-puzzles-gym chuk-puzzles-export -o puzzles.jsonl

# Run evaluation harness
uvx --from chuk-puzzles-gym chuk-puzzles-eval -g sudoku -n 10
```

#### From PyPI

```bash
# Install with pip
pip install chuk-puzzles-gym

# Or with uv
uv pip install chuk-puzzles-gym

# Then run commands directly
chuk-puzzles-server          # Start the server
chuk-puzzles-export          # Generate datasets
chuk-puzzles-eval            # Run evaluation
```

#### From Source (Development)

##### Using UV (Recommended)

```bash
cd chuk-puzzles-gym

# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install development dependencies
make dev-install

# Run the server
make run
```

##### Using pip

```bash
cd chuk-puzzles-gym

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
docker build -t chuk-puzzles-gym .
docker run -p 8023:8023 -p 8024:8024 -p 8025:8025 -p 8026:8026 chuk-puzzles-gym
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

CLASSIC LOGIC PUZZLES:
  1) Sudoku          - Classic logic puzzle - fill 9x9 grid with digits 1-9
  2) KenKen          - Arithmetic cage puzzle - combine math and logic
  3) Kakuro          - Crossword math puzzle - fill runs with unique digits that sum to clues
  4) Binary Puzzle   - Fill grid with 0s and 1s - no three in a row, equal counts
  5) Futoshiki       - Inequality number puzzle - fill grid with constraints
  6) Nonogram        - Picture logic puzzle - reveal image from number clues
  7) Logic Grid      - Deductive reasoning puzzle - match attributes using logic

ADVANCED CP-SAT PUZZLES:
  8) Killer Sudoku   - Sudoku + Kakuro - regions must sum to targets
  9) Lights Out      - Toggle lights to turn all off - XOR constraint puzzle
 10) Mastermind      - Code-breaking with logical deduction and feedback
 11) Slitherlink     - Draw a single loop - numbers show edge counts
 12) Bridges         - Connect islands with bridges - satisfy all numbers
 13) Hitori          - Shade cells to eliminate duplicates - no adjacent shading
 14) Shikaku         - Divide grid into rectangles matching areas

SPECIALIZED CONSTRAINT PUZZLES:
 15) Hidato          - Sequential path puzzle - connect numbers adjacently
 16) Tents           - Place tents next to trees - bipartite matching puzzle
 17) Fillomino       - Fill regions with numbers matching region size
 18) Star Battle     - Place stars avoiding adjacency - multi-region placement
 19) Sokoban         - Push boxes to targets - spatial planning puzzle

OPTIMIZATION CHALLENGES:
 20) Knapsack        - Maximize value within capacity constraints
 21) Task Scheduler  - Minimize makespan with dependencies and resources

ADVANCED REASONING PUZZLES:
 22) Nurikabe        - Island and sea puzzle - connectivity constraints
 23) Einstein's Puzzle - Who owns the fish? Multi-attribute deduction
 24) Minesweeper     - Find all mines using logical deduction

COMBINATORIAL & SEARCH PUZZLES:
 25) Skyscrapers     - Latin square with visibility clues from borders
 26) N-Queens        - Place queens with no row/column/diagonal conflicts
 27) Numberlink      - Connect pairs with non-crossing paths filling the grid
 28) Graph Coloring  - Color nodes so no adjacent pair shares a color
 29) Cryptarithmetic - Assign digits to letters to satisfy an equation
 30) Rush Hour       - Slide vehicles to free the target car to the exit

Commands:
  <number>  - Select game by number
  <name>    - Select game by name (e.g., 'sudoku')
  help      - Show this menu again
  quit      - Exit the server
==================================================
```

## Agent-Friendly Mode

The server includes a special **agent mode** designed for AI tools and LLM integration:

### Enabling Agent Mode

```
> mode agent
Output mode set to: agent
```

### Agent Mode Features

**Structured Output** - Grid data is wrapped with clear start/end markers:
```
---GAME-START---
GAME: Sudoku
DIFFICULTY: medium
MOVES: 3
---GRID-START---
  | 1 2 3 | 4 5 6 | 7 8 9 |
  -------------------------
1 | . . 3 | . 2 . | 6 . . |
...
---GRID-END---
---GAME-END---
```

**Benefits for AI Agents:**
- Easy parsing with regex: `---GRID-START---(.*?)---GRID-END---`
- Consistent metadata format (GAME, DIFFICULTY, MOVES)
- No decorative text or banners to filter out
- Minimal token usage compared to normal mode

**Switching Modes:**
- `mode normal` - Human-friendly output (default)
- `mode agent` - Machine-parseable structured output
- `mode compact` - Reserved for future use

## Gymnasium-Compatible RL Environment

The project includes a **Gymnasium-compatible environment** for training reinforcement learning agents:

### Quick Start

```python
from chuk_puzzles_gym.gym_env import PuzzleEnv

# Create environment for any of the 30 games
env = PuzzleEnv("sudoku", difficulty="easy", seed=42)

# Reset to start a new episode
obs, info = await env.reset()

# Take actions (text commands or tuples)
obs, reward, terminated, truncated, info = await env.step("place 1 1 5")

# Or use tuple format
obs, reward, terminated, truncated, info = await env.step(("place", 1, 1, 5))

# Get available games
games = PuzzleEnv.available_games()
# → ['sudoku', 'kenken', 'minesweeper', ...]
```

### Features

- **All 30 games** accessible through unified API
- **Configurable rewards** for correct moves, invalid attempts, completion bonuses
- **Reasoning depth metrics** tracking backtracks, progress steadiness, error patterns
- **Hint system** with optional budget limits
- **Solver-free mode** for pure reasoning benchmarks
- **Efficiency scoring** based on optimal step counts
- **Deterministic seeding** for reproducible experiments

### Observation Space

```python
obs = {
    "game": "sudoku",
    "difficulty": "easy",
    "seed": 42,
    "moves": 5,
    "invalid_moves": 1,
    "hints_used": 2,
    "hints_remaining": 98,
    "is_complete": False,
    "grid": [[4, 0, 8, ...], ...],  # Game-specific state
    "render": "  | 1 2 3 | ...",     # ASCII grid
}

# Info dict includes reasoning metrics and difficulty profile
info = {
    "optimal_steps": 45,
    "difficulty_profile": {"logic_depth": 2, "branching_factor": 2.0, ...},
    "reasoning_metrics": {
        "backtrack_count": 0,
        "backtrack_rate": 0.0,
        "progress_velocity": 1.0,
        "progress_steadiness": 1.0,
        "reasoning_overhead": 1.0,
        "error_streak_max": 0,
        "solver_distance_trace": [44, 43, 42, ...],
    },
}
```

### Reward Configuration

```python
env = PuzzleEnv("kenken", reward_config={
    "correct_placement": 1.0,      # Reward for valid moves
    "invalid_attempt": -0.5,       # Penalty for invalid moves
    "completion_bonus": 10.0,      # Bonus for solving
    "hint_penalty": -0.1,          # Penalty for using hints
    "efficiency_multiplier": 2.0,  # Scales completion bonus by efficiency
})
```

### Solver Configuration

```python
from chuk_puzzles_gym.models import SolverConfig

# Solver-free mode (no hints allowed)
config = SolverConfig.solver_free()
env = PuzzleEnv("sudoku", solver_config=config)

# Limited hints
config = SolverConfig(hint_budget=5, hint_penalty=0.1)
env = PuzzleEnv("sudoku", solver_config=config)
```

## Reasoning Depth Metrics

Beyond binary success/failure, the system measures **how** an agent reasons through puzzles. These metrics are available in all interaction paths: the Gym environment, the evaluation harness, and the telnet/WebSocket server.

### Metrics

| Metric | Description | Perfect Score |
|--------|-------------|---------------|
| `backtrack_count` | Times the agent revised a previous placement | 0 |
| `backtrack_rate` | Fraction of valid moves that were backtracks | 0% |
| `progress_velocity` | Average cells solved per step | 1.0 |
| `progress_steadiness` | How monotonically remaining work decreases (1.0 = never stalls) | 100% |
| `reasoning_overhead` | Total actions / optimal path length (1.0 = no waste) | 1.0x |
| `error_streak_max` | Longest run of consecutive invalid moves | 0 |
| `avg_error_streak` | Average length of error bursts | 0.0 |
| `solver_distance_trace` | Remaining positions after each valid move | Monotonically decreasing |

### Usage in Gym Environment

```python
from chuk_puzzles_gym.gym_env import PuzzleEnv

env = PuzzleEnv("sudoku", difficulty="easy", seed=42)
obs, info = await env.reset()

# Reasoning metrics available in info after reset
print(info["reasoning_metrics"])

# ... agent plays ...
obs, reward, terminated, truncated, info = await env.step("place 1 1 5")

# On episode end, info includes full reasoning metrics
if terminated:
    metrics = info["reasoning_metrics"]
    print(f"Backtrack rate: {metrics['backtrack_rate']:.0%}")
    print(f"Overhead: {metrics['reasoning_overhead']:.1f}x")
    print(f"Steadiness: {metrics['progress_steadiness']:.0%}")
```

### Usage in Server (Telnet/WebSocket)

Reasoning metrics are included automatically in server output:

- **JSON mode**: `reasoning_metrics` dict in every state response and completion message
- **STRICT mode**: `BT=`, `OH=`, `ST=` fields appended to STATS and COMPLETE messages
- **Normal mode**: "Reasoning Depth" section shown on completion and in `stats` command

```
> mode json
> place 1 1 5
{"type":"result","success":true,...,"state":{...,"reasoning_metrics":{"backtrack_count":0,...}}}

> stats
{"type":"stats",...,"reasoning_metrics":{"backtrack_count":0,"backtrack_rate":0.0,...}}
```

### Usage in Evaluation Harness

```bash
# Reasoning metrics included in all output formats
chuk-puzzles-eval sudoku -d easy -n 10 -o json
```

```python
from chuk_puzzles_gym.eval import evaluate_game

report = await evaluate_game("sudoku", difficulty="easy", episodes=10)
report.print_summary()  # Includes "Reasoning Depth" section

# Aggregate metrics
print(f"Avg backtrack rate: {report.avg_backtrack_rate:.0%}")
print(f"Avg overhead: {report.avg_reasoning_overhead:.1f}x")
print(f"Avg steadiness: {report.avg_progress_steadiness:.0%}")
```

### What the Metrics Reveal

A **perfect solver** shows: 0 backtracks, 1.0x overhead, 100% steadiness, 1.0 velocity.

A **struggling agent** shows: high backtrack rate (revising decisions), error streaks (clustered confusion), low steadiness (stalling progress), and high overhead (wasted work).

These patterns are visible even when two agents both eventually solve a puzzle — the metrics expose the **quality of the reasoning path**, not just the outcome.

## Evaluation Harness

The project includes a built-in **evaluation harness** for benchmarking puzzle-solving agents:

### Quick Start

```bash
# List all available games
chuk-puzzles-eval --list-games

# Evaluate a specific game (10 episodes, medium difficulty)
chuk-puzzles-eval sudoku -d medium -n 10 -v

# Evaluate all games (5 episodes each)
chuk-puzzles-eval --all -d easy -n 5

# Output as JSON for analysis
chuk-puzzles-eval sudoku -n 20 -o json > results.json
```

### Using Make Targets

```bash
make eval           # Quick evaluation (3 episodes per game)
make eval-sudoku    # Evaluate Sudoku (10 episodes)
make eval-all       # Evaluate all games (10 episodes each)
make eval-json      # Output as JSON
make list-games     # List available games
```

### Sample Output

```
Sudoku Medium Evaluation (10 episodes)
==================================================
Solved:     10/10 (100.0%)
Avg Moves:  45.3
Avg Invalid: 0.0
Avg Time:   12ms
```

### Output Formats

- **text** (default) - Human-readable summary
- **json** - Structured JSON for programmatic analysis
- **csv** - Spreadsheet-compatible format
- **markdown** - Documentation-ready tables

### Metrics Collected

| Metric | Description |
|--------|-------------|
| `solved` | Whether the puzzle was solved |
| `moves_made` | Number of valid moves |
| `invalid_moves` | Number of rejected moves |
| `hints_used` | Number of hints requested |
| `wall_time_ms` | Time to solve in milliseconds |
| `seed` | Puzzle seed for reproducibility |
| `backtrack_count` | Times agent revised a previous placement |
| `backtrack_rate` | Fraction of valid moves that were backtracks |
| `progress_steadiness` | How monotonically progress advances (1.0 = perfect) |
| `reasoning_overhead` | Total actions / optimal path (1.0 = no waste) |
| `error_streak_max` | Longest run of consecutive invalid moves |
| `progress_velocity` | Average cells solved per step |

## CHUK-R Reasoning Benchmark

The **CHUK Reasoning Score (CHUK-R)** is a single aggregate benchmark (0-100) measuring reasoning capabilities across all 30 puzzle games, organized into 4 reasoning families:

| Family | Games | Focus |
|--------|-------|-------|
| **Logic** | 10 | Pure deduction, grid uniqueness, pattern recognition |
| **Constraint** | 12 | Multi-constraint interaction, sums, connectivity, topology |
| **Search** | 4 | Feedback-driven, iterative refinement, path-finding |
| **Planning** | 4 | Sequential actions, irreversible decisions, optimization |

### Scoring Formula

Each solved episode scores 0-100 based on weighted components:

| Component | Weight | Formula |
|-----------|--------|---------|
| Efficiency | 40% | `optimal_steps / steps_taken` |
| Error rate | 15% | `1 - (invalid / total)` |
| Backtrack | 15% | `1 - backtrack_rate` |
| Steadiness | 15% | `progress_steadiness` |
| Hint independence | 15% | `1 - hint_dependency` |

Unsolved episodes score **0**. Aggregation: episode → game (mean) → family (mean) → **CHUK-R** (mean of 4 families).

### CLI Usage

```bash
# Full benchmark (all 30 games)
chuk-puzzles-benchmark -d easy -n 5 -v

# Single family
chuk-puzzles-benchmark --family Logic -n 10

# Specific games
chuk-puzzles-benchmark --games sudoku,kenken,mastermind -o json

# List game-to-family mapping
chuk-puzzles-benchmark --list-families

# Solver-free mode (pure model reasoning, no hints)
chuk-puzzles-benchmark --solver-free
```

### Sample Output

```
================================================================
  CHUK REASONING SCORE (CHUK-R)
================================================================
  Difficulty:     Easy
  Episodes/game:  5
  Solver:         hints (budget=100, penalty=0.0)
  Coverage:       100% (30/30 games)

----------------------------------------------------------------
  Family            Score    Games   Solve%
----------------------------------------------------------------
  Logic             82.3    10/10      93%
  Constraint        74.6    12/12      87%
  Search            69.1     4/4       80%
  Planning          58.2     4/4       65%
----------------------------------------------------------------
  CHUK-R            71.1
================================================================
```

### LLM Agent Benchmark

Test actual LLMs (GPT-4o-mini, GPT-4o, etc.) against the CHUK-R benchmark:

```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Quick test on one game
python examples/llm_benchmark_agent.py --game sudoku --episodes 3 -v

# Test multiple games
python examples/llm_benchmark_agent.py --games sudoku,binary,kenken --episodes 2

# Full family benchmark
python examples/llm_benchmark_agent.py --family Logic --episodes 2

# Use different model
python examples/llm_benchmark_agent.py --model gpt-4o --game sudoku
```

The LLM agent receives puzzle state and rules, decides moves autonomously, and produces a CHUK-R score for comparison against baselines.

## Dataset Export

Generate synthetic puzzle datasets for training and benchmarking LLMs and constraint solvers. The export system produces JSONL files with complete problem definitions, solutions, and step-by-step reasoning traces.

### CLI Usage

```bash
# Generate 100 puzzles per game/difficulty for all 30 games
chuk-puzzles-export -o puzzles.jsonl

# Specific games only
chuk-puzzles-export -g sudoku kenken einstein -n 100 -o selected.jsonl

# Single difficulty level
chuk-puzzles-export -d easy -n 50 -o easy_puzzles.jsonl

# Multiple difficulties
chuk-puzzles-export -d easy medium -n 100 -o train_data.jsonl

# Reproducible generation with seed
chuk-puzzles-export -g sudoku -s 0 -n 1000 -o sudoku_seed0.jsonl

# Without step-by-step traces (smaller files)
chuk-puzzles-export --no-trace -n 500 -o compact.jsonl

# List all available games
chuk-puzzles-export --list-games
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output file path | `puzzles.jsonl` |
| `-g, --games` | Games to include (space-separated) | All games |
| `-n, --count` | Problems per game/difficulty combo | 100 |
| `-d, --difficulties` | Difficulty levels to include | easy, medium, hard |
| `-s, --seed` | Starting seed for reproducibility | 0 |
| `--no-trace` | Exclude step-by-step solution traces | False |
| `--list-games` | List available games and exit | - |

### Python API

```python
import asyncio
from chuk_puzzles_gym.export import DatasetExporter, generate_dataset
from chuk_gym_core import DifficultyLevel

# Quick generation with async function
async def generate():
    total = await generate_dataset(
        output_path="data.jsonl",
        games=["sudoku", "kenken", "einstein"],
        count_per_game=100,
        difficulties=["easy", "medium", "hard"],
        include_trace=True,
    )
    print(f"Generated {total} problems")

asyncio.run(generate())

# Fine-grained control with context manager
async def export_custom():
    with DatasetExporter("puzzles.jsonl", include_trace=True) as exporter:
        # Export specific game
        await exporter.export_game(
            game_name="sudoku",
            count=500,
            difficulty=DifficultyLevel.MEDIUM,
            start_seed=0,
        )

        # Export all games
        await exporter.export_all_games(
            count_per_game=50,
            difficulties=[DifficultyLevel.EASY, DifficultyLevel.HARD],
        )

        print(f"Total exported: {exporter.count}")

asyncio.run(export_custom())
```

### Output Format

Each line in the JSONL file contains a complete problem definition:

```json
{
  "id": "sudoku_medium_42",
  "seed": 42,
  "domain": "sudoku",
  "difficulty": "medium",
  "prompt": "Sudoku: Classic 9x9 logic puzzle...\n\nRULES:\n...\n\n[grid]",
  "initial_state": [[0,0,3,...], ...],
  "gold_answer": "[[4,8,3,...], ...]",
  "constraint_types": ["all_different_rows", "all_different_columns", "all_different_boxes"],
  "business_analogies": ["resource_allocation", "scheduling", "assignment_problems"],
  "difficulty_profile": {
    "logic_depth": 45,
    "branching_factor": 3.2,
    "state_observability": 0.88,
    "constraint_density": 0.75
  },
  "operation_count": 47,
  "tags": ["sudoku", "medium"]
}
```

### Solution Traces

When `include_trace=True` (default), each problem includes step-by-step solution traces for teacher-forcing training:

```json
{
  "problem": { ... },
  "trace": {
    "problem_id": "sudoku_medium_42",
    "steps": [
      {
        "index": 0,
        "operation": "PLACE",
        "before_state": "cell(r1,c1)=empty",
        "after_state": "cell(r1,c1)=4",
        "output_value": 4,
        "position": [1, 1],
        "rule_applied": "naked_single_row",
        "explanation": "Place 4 at row 1, column 1. This is the only valid digit considering row 1, column 1, and box 1 constraints."
      },
      {
        "index": 1,
        "operation": "PLACE",
        "before_state": "cell(r1,c3)=empty",
        "after_state": "cell(r1,c3)=7",
        "output_value": 7,
        "position": [1, 3],
        "rule_applied": "naked_single_box",
        "explanation": "Place 7 at row 1, column 3..."
      }
    ],
    "checkpoints": [0, 12, 24, 47]
  }
}
```

### Trace Operations

| Operation | Description | Used By |
|-----------|-------------|---------|
| `PLACE` | Place a value in a cell | Sudoku, KenKen, Nonogram, etc. |
| `ELIMINATE` | Mark a cell as excluded/shaded | Hitori, Minesweeper |
| `DEDUCE` | Logical deduction step | Einstein, Logic Grid, Mastermind |

### Rule Types by Game

| Game | Rules Applied |
|------|--------------|
| Sudoku | `naked_single_row`, `naked_single_column`, `naked_single_box`, `elimination` |
| Binary | `balance_constraint` |
| KenKen/Kakuro | `arithmetic_constraint` |
| Nonogram | `line_constraint` |
| Einstein | `logical_deduction` |
| Hitori | `duplicate_elimination` |
| Bridges | `connectivity_constraint` |
| Slitherlink | `loop_constraint` |
| Graph Coloring | `graph_coloring_constraint` |
| Cryptarithmetic | `arithmetic_constraint` |
| Rush Hour | `sequential_planning` |
| Others | `constraint_propagation` |

### Example: Generate Training Data

```bash
# Generate large training dataset
chuk-puzzles-export \
    -g sudoku kenken kakuro binary futoshiki \
    -n 1000 \
    -d easy medium hard \
    -s 0 \
    -o training_data.jsonl

# Generate evaluation set (different seed range)
chuk-puzzles-export \
    -g sudoku kenken kakuro binary futoshiki \
    -n 100 \
    -d easy medium hard \
    -s 100000 \
    -o eval_data.jsonl
```

### Dataset Statistics

With default settings (`-n 100` per game/difficulty):

| Configuration | Problems Generated |
|--------------|-------------------|
| All games, all difficulties | 30 games × 3 difficulties × 100 = 9,000 |
| Single game, all difficulties | 1 × 3 × 100 = 300 |
| All games, single difficulty | 30 × 1 × 100 = 3,000 |

### Integration with chuk-gym-core

The export system uses [chuk-gym-core](https://pypi.org/project/chuk-gym-core/) for consistent output format, compatible with:

- **chuk-math-gym** - Mathematical reasoning datasets
- **Teacher-forcing training** - Step-by-step trace supervision
- **Evaluation pipelines** - Standardized problem/solution schema

## Universal Game Commands

All games support these commands:

### Starting and Managing Games
- `<number> [difficulty]` - Select game by number (e.g., `1 medium`)
- `<name> [difficulty]` - Select game by name (e.g., `sudoku hard`)
- `show` - Display the current grid
- `mode <normal|agent|compact>` - Set output mode
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

This server is built on the chuk-protocol-server framework, which provides:

- Multiple transport protocol support (Telnet, TCP, WebSocket, WS-Telnet)
- Telnet protocol negotiation (IAC, WILL, WONT, DO, DONT)
- WebSocket handling with ping/pong keepalive
- Connection management and monitoring
- Asynchronous I/O with Python asyncio

### Game Architecture

Each game is a **self-contained module** with all logic co-located:

```
games/
├── _base/              # Base classes
│   ├── game.py         # PuzzleGame ABC
│   └── commands.py     # GameCommandHandler ABC
├── sudoku/
│   ├── __init__.py     # Exports SudokuGame
│   ├── game.py         # Game logic
│   ├── config.py       # SudokuConfig
│   └── commands.py     # Command handler
├── minesweeper/
│   ├── __init__.py
│   ├── game.py
│   └── config.py
└── ... (24 games total)
```

All games extend the `PuzzleGame` abstract base class with **deterministic seeding**:

```python
from chuk_puzzles_gym.games._base import PuzzleGame

class PuzzleGame(ABC):
    def __init__(self, difficulty: str = "easy", seed: int | None = None):
        self.seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        self._rng = random.Random(self.seed)  # Deterministic RNG
        # ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def constraint_types(self) -> list[str]: ...

    @property
    @abstractmethod
    def business_analogies(self) -> list[str]: ...

    @abstractmethod
    async def generate_puzzle(self) -> None: ...

    @abstractmethod
    async def validate_move(self, *args) -> MoveResult: ...

    @abstractmethod
    def is_complete(self) -> bool: ...

    @abstractmethod
    def render_grid(self) -> str: ...
```

### Handler Architecture

The `ArcadeHandler` class manages:
- Menu-driven game selection
- Command parsing and routing (delegating to game-specific handlers)
- Grid display with proper formatting
- Game state management per connection
- Multi-game support

## Development

### Setup Development Environment

```bash
cd chuk-puzzles-gym

# Install development dependencies (with UV)
make dev-install

# Or with pip
pip install -e ".[dev]"
```

### Testing

The project has comprehensive test coverage (94%, 1323 tests):

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

### Coverage by Module

```
src/chuk_puzzles_gym/games/_base/             86%   # Base classes (abstract defaults)
src/chuk_puzzles_gym/games/sudoku/            92%   # Sudoku module
src/chuk_puzzles_gym/games/kenken/            90%   # KenKen module
src/chuk_puzzles_gym/games/minesweeper/       96%   # Minesweeper module
src/chuk_puzzles_gym/games/sokoban/           83%   # Sokoban (complex pathfinding)
src/chuk_puzzles_gym/games/.../               90%+  # All other games
src/chuk_puzzles_gym/gym_env.py               90%   # Gymnasium environment
src/chuk_puzzles_gym/models/                  90%+  # Pydantic models
------------------------------------------------------
TOTAL                                              94%  🎯
```

**Most modules meet the 90%+ coverage threshold.** The remaining gaps are in abstract base class defaults and complex pathfinding algorithms.

### Code Quality

The project follows modern Python best practices with a **9.8/10 compliance score**:

#### Tooling
- **Ruff**: Fast linter and formatter (replaces black + flake8)
- **MyPy**: Static type checking
- **Pytest**: Testing framework with async support
- **Bandit**: Security vulnerability scanning

#### Code Standards
- ✅ **Pydantic v2 Native** (10/10) - All models use `ConfigDict`, zero deprecation warnings
- ✅ **Async Native** (9.5/10) - All I/O operations use async/await properly
- ✅ **Type-Safe** (10/10) - No `dict["key"]` patterns, only typed Pydantic models
- ✅ **No Magic Strings** (10/10) - All constants use enums or typed constants
- ✅ **Test Coverage** (9.5/10) - 94% overall, most files ≥90%

#### Quality Metrics
- **1323 tests** - All passing ✅
- **94% coverage** - Exceeds 90% threshold ✅
- **Zero linting errors** - Clean codebase ✅
- **Full type safety** - MyPy passes ✅
- **Deterministic seeding** - Reproducible puzzles ✅

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

### CI/CD

The project includes GitHub Actions workflows:

- **test.yml**: Runs tests on Ubuntu, Windows, macOS with Python 3.11, 3.12, 3.13
- **publish.yml**: Publishes to PyPI on release
- **release.yml**: Creates GitHub releases
- **fly-deploy.yml**: Auto-deploys to Fly.io on main branch push

Coverage threshold is set to 90% - builds fail if coverage drops below this.

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
chuk-puzzles-gym/
├── src/
│   └── chuk_puzzles_gym/
│       ├── __init__.py           # Package initialization
│       ├── server.py             # Main arcade handler
│       ├── constants.py          # Game constants
│       ├── models/               # Pydantic models
│       │   ├── __init__.py
│       │   ├── base.py           # GridPosition, MoveResult
│       │   ├── config.py         # Base GameConfig
│       │   ├── enums.py          # DifficultyLevel, GameCommand, etc.
│       │   ├── evaluation.py     # ReasoningMetrics, EpisodeResult, EvaluationSummary
│       │   └── games.py          # Game-specific models (Cage, Task, etc.)
│       └── games/                # Self-contained game modules
│           ├── __init__.py       # AVAILABLE_GAMES registry
│           ├── _base/            # Base classes
│           │   ├── __init__.py
│           │   ├── game.py       # PuzzleGame ABC + ReasoningTracker
│           │   └── commands.py   # GameCommandHandler ABC
│           ├── sudoku/           # Example game module
│           │   ├── __init__.py   # Exports SudokuGame
│           │   ├── game.py       # SudokuGame class
│           │   ├── config.py     # SudokuConfig
│           │   └── commands.py   # SudokuCommandHandler
│           ├── minesweeper/      # Each game is self-contained
│           │   ├── __init__.py
│           │   ├── game.py
│           │   └── config.py
│           └── ... (30 games total)
├── tests/
│   ├── test_puzzle_game.py       # Base class tests
│   ├── test_deterministic_seeding.py  # Seeding tests
│   ├── test_sudoku_game.py       # Sudoku tests
│   ├── test_minesweeper.py       # Minesweeper tests
│   └── ... (tests for all 24 games)
├── examples/
│   ├── simple_client.py          # Telnet client example
│   ├── websocket_client.py       # WebSocket client example
│   ├── example_skyscrapers.py    # Skyscrapers game logic demo
│   ├── example_nqueens.py        # N-Queens game logic demo
│   ├── example_numberlink.py     # Numberlink game logic demo
│   ├── example_graph_coloring.py # Graph Coloring game logic demo
│   ├── example_cryptarithmetic.py# Cryptarithmetic game logic demo
│   ├── example_rush_hour.py      # Rush Hour game logic demo
│   ├── example_reasoning_metrics.py # Reasoning depth metrics demo
│   └── README.md                 # Example usage guide
├── .github/workflows/            # CI/CD workflows
├── pyproject.toml                # Modern Python project config
├── config.yaml                   # Multi-transport server configuration
├── Dockerfile                    # Docker build instructions
├── fly.toml                      # Fly.io deployment config
├── Makefile                      # Development commands (50+ targets)
└── README.md                     # This file
```

### Key Statistics

- **Test Coverage**: 94% overall (1323 tests, all passing)
- **Code Quality Score**: 9.8/10 (near perfect compliance)
- **Games Implemented**: 30 complete puzzle types
  - 7 Classic Logic Puzzles
  - 7 Advanced CP-SAT Puzzles
  - 5 Specialized Constraint Puzzles
  - 2 Optimization Challenges
  - 3 Advanced Reasoning Puzzles
  - 6 Combinatorial & Search Puzzles
- **Supported Transports**: 4 (Telnet, TCP, WebSocket, WS-Telnet)
- **Agent-Friendly Mode**: Structured output for AI tools
- **Gymnasium API**: RL-compatible environment for all games
- **Deterministic Seeding**: Reproducible puzzles for testing

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

- **30 different puzzle types** demonstrating various constraint types:
  - AllDifferent constraints (Sudoku, KenKen, Futoshiki)
  - Arithmetic constraints (KenKen, Kakuro, Killer Sudoku)
  - Boolean/SAT constraints (Lights Out, Binary Puzzle)
  - Loop/Edge constraints (Slitherlink)
  - Deduction constraints (Mastermind, Logic Grid, Einstein's Puzzle)
  - Optimization objectives (Knapsack, Task Scheduler)
  - Temporal reasoning (Task Scheduler)
  - Connectivity constraints (Nurikabe, Slitherlink)
  - Probabilistic reasoning (Minesweeper)
  - Graph coloring (Graph Coloring)
  - Arithmetic deduction (Cryptarithmetic)
  - Sequential planning (Rush Hour)
  - Visibility constraints (Skyscrapers)
  - Attack avoidance (N-Queens)
  - Path connectivity (Numberlink)
- **Well-documented code** showing puzzle generation algorithms
- **Comprehensive tests** (1323 tests, 94% coverage) demonstrating validation
- **Deterministic seeding** - Reproduce any puzzle for debugging/testing
- **Type-safe** - Full Pydantic v2 and MyPy compliance
- **Modular architecture** - Each game is self-contained in its own folder

## Adding New Puzzle Games

1. Create a new game folder in `src/chuk_puzzles_gym/games/`:

```
games/
└── my_puzzle/
    ├── __init__.py     # Export the game class
    ├── game.py         # Game logic
    └── config.py       # Game configuration
```

2. Create the config in `config.py`:

```python
from pydantic import Field
from ...models import DifficultyLevel, GameConfig

class MyPuzzleConfig(GameConfig):
    grid_size: int = Field(default=5, description="Grid size")

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "MyPuzzleConfig":
        sizes = {DifficultyLevel.EASY: 5, DifficultyLevel.MEDIUM: 7, DifficultyLevel.HARD: 9}
        return cls(difficulty=difficulty, grid_size=sizes[difficulty])
```

3. Create the game in `game.py`:

```python
from .._base import PuzzleGame
from ...models import MoveResult
from .config import MyPuzzleConfig

class MyPuzzleGame(PuzzleGame):
    def __init__(self, difficulty: str = "easy", seed: int | None = None):
        super().__init__(difficulty, seed)
        self.config = MyPuzzleConfig.from_difficulty(self.difficulty)
        # Use self._rng for all randomness (deterministic seeding)

    @property
    def name(self) -> str:
        return "My Puzzle"

    @property
    def constraint_types(self) -> list[str]:
        return ["all_different", "sum_constraint"]

    @property
    def business_analogies(self) -> list[str]:
        return ["resource_allocation", "scheduling"]

    async def generate_puzzle(self) -> None:
        # Use self._rng.randint(), self._rng.choice(), etc.
        self.game_started = True

    async def validate_move(self, row: int, col: int, num: int) -> MoveResult:
        # Validate and apply move
        return MoveResult(success=True, message="Number placed!")

    def is_complete(self) -> bool:
        return all(cell != 0 for row in self.grid for cell in row)

    def render_grid(self) -> str:
        return "  | 1 | 2 | 3 |\n" + ...

    def get_stats(self) -> str:
        return f"Moves: {self.moves_made} | Seed: {self.seed}"
```

4. Export in `__init__.py`:

```python
from .game import MyPuzzleGame
__all__ = ["MyPuzzleGame"]
```

5. Register in `src/chuk_puzzles_gym/games/__init__.py`:

```python
from .my_puzzle import MyPuzzleGame

AVAILABLE_GAMES = {
    # ... other games
    "mypuzzle": MyPuzzleGame,
}
```

6. Add tests in `tests/test_my_puzzle_game.py`:

```python
from chuk_puzzles_gym.games.my_puzzle import MyPuzzleGame

class TestMyPuzzleGame:
    async def test_deterministic_seeding(self):
        game1 = MyPuzzleGame("easy", seed=12345)
        game2 = MyPuzzleGame("easy", seed=12345)
        await game1.generate_puzzle()
        await game2.generate_puzzle()
        assert game1.render_grid() == game2.render_grid()

    def test_seed_in_stats(self):
        game = MyPuzzleGame("easy", seed=42)
        assert "Seed: 42" in game.get_stats()
```

7. Run tests and verify:

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

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full development roadmap.

### Highlights

**Benchmarking & Metrics**
- ~~Puzzle complexity metrics~~ (implemented: constraint count, variable count, branching factor)
- ~~Episode model for tracking game sessions~~ (implemented: EpisodeResult with ReasoningMetrics)
- ~~Reasoning depth metrics~~ (implemented: backtrack detection, progress steadiness, error patterns)
- ~~Trace logging for offline analysis~~ (implemented: solver distance traces in all output paths)

**Agent Evaluation Tools**
- Batch evaluation harness CLI
- Solver vs Model comparison mode
- JSON protocol for structured agent communication

**Learning & Curriculum**
- Constraint concept progression graph
- Tagged puzzle sets for educators
- Difficulty scaling based on constraint complexity

**Ecosystem Integrations**
- MCP native mode for agent frameworks
- Python client library
- REST/WebSocket API documentation

**UX & Community**
- Interactive web viewer with replay mode
- Public benchmark packs (versioned, citable)
- Community leaderboards

## License

Apache License 2.0 - See LICENSE for details.

## Credits

- Built using chuk-protocol-server
- Puzzle generation algorithms based on backtracking and constraint propagation
- Uses modern Python tooling: UV, Ruff, MyPy, Pytest

## Links

- [UV](https://github.com/astral-sh/uv) - Fast Python package manager
- [Ruff](https://github.com/astral-sh/ruff) - Fast Python linter and formatter
- [Fly.io](https://fly.io) - Cloud deployment platform

---

**Ready to test your solver?** Connect now and start solving! 🎮
