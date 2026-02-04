# Creating a New Game

This guide walks through adding a new puzzle game to chuk-puzzles-gym, from initial scaffolding to registration and testing.

## Overview

A puzzle game in this framework is a self-contained module that:

- **Generates** a puzzle with a unique solution (deterministically, given a seed)
- **Validates** player moves and tracks metrics
- **Renders** the puzzle state as ASCII text
- **Provides** hints from the stored solution

There are two game types:

| Type | Commands | Example |
|------|----------|---------|
| **Grid-based** | Uses standard `PLACE` / `CLEAR` commands parsed by the server | `binary`, `sudoku` |
| **Custom command** | Needs its own `GameCommandHandler` for non-standard argument parsing | `graph_coloring`, `rush_hour` |

Grid-based games only need `config.py` and `game.py`. Custom-command games also add a `commands.py` file. Games with domain-specific data structures can add a `models.py`.

---

## Directory Structure

Create a new directory under `src/chuk_puzzles_gym/games/`:

```
src/chuk_puzzles_gym/games/your_game/
    __init__.py       # Module exports
    config.py         # Pydantic config with from_difficulty()
    game.py           # PuzzleGame subclass
    commands.py       # (optional) GameCommandHandler subclass
    models.py         # (optional) Domain-specific Pydantic models
```

---

## Step-by-Step Implementation

### Step 1: Config (`config.py`)

Define a Pydantic model with a `from_difficulty()` classmethod that maps each difficulty level to concrete parameters.

```python
"""Configuration for Your Game puzzle."""

from pydantic import BaseModel, Field

from ...models import DifficultyLevel


class YourGameConfig(BaseModel):
    """Configuration for Your Game."""

    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY)
    size: int = Field(ge=4, le=20, description="Grid size")
    # Add game-specific parameters here

    @classmethod
    def from_difficulty(cls, difficulty: DifficultyLevel) -> "YourGameConfig":
        """Create config from difficulty level."""
        config_map = {
            DifficultyLevel.EASY: {"size": 6},
            DifficultyLevel.MEDIUM: {"size": 8},
            DifficultyLevel.HARD: {"size": 10},
        }
        return cls(difficulty=difficulty, **config_map[difficulty])
```

Real example: `games/graph_coloring/config.py` uses `num_nodes`, `num_colors`, and `edge_density` parameters scaled by difficulty.

---

### Step 2: Game Class (`game.py`)

Subclass `PuzzleGame` and implement all abstract methods.

#### Required abstract methods (9 total)

| Method | Async | Return Type | Purpose |
|--------|-------|-------------|---------|
| `generate_puzzle()` | Yes | `None` | Create puzzle, store solution, set `game_started = True` |
| `validate_move(*args)` | Yes | `MoveResult` | Validate a player move, call `record_move()` |
| `is_complete()` | No | `bool` | Check if puzzle is fully and correctly solved |
| `get_hint()` | Yes | `tuple[Any, str] \| None` | Return `(hint_data, message)` or `None` |
| `render_grid()` | No | `str` | ASCII representation of current state |
| `get_rules()` | No | `str` | Multi-line rules description |
| `get_commands()` | No | `str` | Multi-line available commands description |
| `name` (property) | - | `str` | Display name (e.g. `"Graph Coloring"`) |
| `description` (property) | - | `str` | One-line description |

#### Optional overrides

| Property | Return Type | Purpose |
|----------|-------------|---------|
| `constraint_types` | `list[str]` | Constraint categories (e.g. `"all_different"`, `"graph_coloring"`) |
| `business_analogies` | `list[str]` | Real-world problem analogies (e.g. `"scheduling"`) |
| `complexity_profile` | `dict[str, str]` | `reasoning_type`, `search_space`, `constraint_density` |
| `complexity_metrics` | `dict[str, int \| float]` | `variable_count`, `constraint_count`, `domain_size`, `branching_factor`, `empty_cells` |
| `difficulty_profile` | `DifficultyProfile` | `logic_depth`, `branching_factor`, `state_observability`, `constraint_density` |
| `optimal_steps` | `int \| None` | Minimum steps to solve |
| `get_stats()` | `str` | Override for custom stats (must include `Seed: {self.seed}`) |

#### Skeleton

```python
"""Your Game puzzle implementation."""

from typing import Any

from ...models import DifficultyLevel, MoveResult
from .._base import PuzzleGame
from .config import YourGameConfig


class YourGame(PuzzleGame):
    """Your Game - one-line description of the puzzle."""

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        super().__init__(difficulty, seed, **kwargs)
        self.config = YourGameConfig.from_difficulty(self.difficulty)
        # Initialize game-specific state
        self.grid: list[list[int]] = []
        self.solution: list[list[int]] = []

    @property
    def name(self) -> str:
        return "Your Game"

    @property
    def description(self) -> str:
        return "One-line description of the puzzle"

    async def generate_puzzle(self) -> None:
        """Generate a new puzzle with a unique solution."""
        # Use self._rng for ALL random operations (deterministic seeding)
        # Example: self._rng.randint(1, 10), self._rng.shuffle(items)

        # ... generate puzzle and solution ...

        self.game_started = True

    async def validate_move(self, row: int, col: int, value: int) -> MoveResult:
        """Validate a player's move."""
        # Validate input bounds
        if not (1 <= row <= self.config.size):
            self.record_move((row, col), False)
            return MoveResult(success=False, message="Row out of range.")

        # Check game-specific rules
        # ...

        # Apply the move
        self.grid[row - 1][col - 1] = value
        self.record_move((row, col), True)
        return MoveResult(success=True, message="Move accepted.", state_changed=True)

    def is_complete(self) -> bool:
        """Check if the puzzle is completely and correctly solved."""
        return self.grid == self.solution

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move."""
        if not self.can_use_hint():
            return None
        # Find first empty cell and return its solution value
        for r in range(self.config.size):
            for c in range(self.config.size):
                if self.grid[r][c] == 0:
                    val = self.solution[r][c]
                    self.record_hint()
                    return ((r + 1, c + 1, val), f"Try placing {val} at row {r+1}, col {c+1}.")
        return None

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art."""
        lines = []
        for row in self.grid:
            lines.append(" ".join(str(v) if v != 0 else "." for v in row))
        return "\n".join(lines)

    def get_rules(self) -> str:
        return "YOUR GAME\nRule 1: ...\nRule 2: ..."

    def get_commands(self) -> str:
        return (
            "Commands:\n"
            "  place <row> <col> <value>  - Place a value\n"
            "  clear <row> <col>          - Clear a cell\n"
            "  hint                       - Get a hint\n"
            "  show                       - Show current state\n"
            "  menu                       - Return to menu"
        )
```

#### Key patterns

**Deterministic seeding** -- Always use `self._rng` instead of the `random` module:

```python
# Good - deterministic
value = self._rng.randint(1, 10)
self._rng.shuffle(items)

# Bad - non-deterministic
value = random.randint(1, 10)
```

**Metrics tracking** -- Call `record_move()` in every `validate_move()` path. This feeds both the basic counters (`moves_made`, `invalid_moves`) and the reasoning depth tracker (backtrack detection, solver distance, error streaks):

```python
async def validate_move(self, node: int, color: int) -> MoveResult:
    if not valid:
        self.record_move((node,), False)   # Records invalid_moves + error streak
        return MoveResult(success=False, message="...")
    self.record_move((node,), True)        # Records moves_made + solver distance
    return MoveResult(success=True, message="...", state_changed=True)
```

The reasoning tracker automatically detects backtracks (placing at a previously-placed position), tracks solver distance (via `optimal_steps`), and records error streak patterns. No additional code needed in your game -- just call `record_move()` consistently.

**Hint budget** -- Use `can_use_hint()` to check and `record_hint()` to consume:

```python
async def get_hint(self) -> tuple[Any, str] | None:
    if not self.can_use_hint():
        return None
    # ... compute hint ...
    self.record_hint()
    return (hint_data, hint_message)
```

---

### Step 3: Command Handler (`commands.py`, optional)

You need a command handler when your game uses non-standard argument parsing (e.g., accepting color names in addition to numbers, or a `MOVE` command with direction arguments).

Grid-based games that only use `PLACE <row> <col> <value>` and `CLEAR <row> <col>` do **not** need a custom handler -- the server handles these.

```python
"""Command handler for Your Game."""

from typing import TYPE_CHECKING

from ...models import GameCommand, MoveResult
from .._base import CommandResult, GameCommandHandler

if TYPE_CHECKING:
    from .game import YourGame


class YourGameCommandHandler(GameCommandHandler):
    """Handles commands for Your Game."""

    game: "YourGame"

    @property
    def supported_commands(self) -> set[GameCommand]:
        return {GameCommand.PLACE, GameCommand.CLEAR}

    async def handle_command(self, cmd: GameCommand, args: list[str]) -> CommandResult:
        if cmd == GameCommand.PLACE:
            return await self._handle_place(args)
        elif cmd == GameCommand.CLEAR:
            return await self._handle_clear(args)
        return self.error_result(f"Unknown command: {cmd}")

    async def _handle_place(self, args: list[str]) -> CommandResult:
        if len(args) != 2:
            return CommandResult(
                result=MoveResult(success=False, message="Usage: place <target> <value>"),
                should_display=False,
            )

        target = self.parse_int(args[0], "target")
        value = self.parse_int(args[1], "value")

        if target is None:
            return self.error_result("Target must be an integer.")
        if value is None:
            return self.error_result("Value must be an integer.")

        result = await self.game.validate_move(target, value)
        return CommandResult(
            result=result,
            should_display=result.success,
            is_game_over=result.success and self.game.is_complete(),
        )

    async def _handle_clear(self, args: list[str]) -> CommandResult:
        if len(args) != 1:
            return CommandResult(
                result=MoveResult(success=False, message="Usage: clear <target>"),
                should_display=False,
            )

        target = self.parse_int(args[0], "target")
        if target is None:
            return self.error_result("Target must be an integer.")

        result = await self.game.validate_move(target, 0)
        return CommandResult(
            result=result,
            should_display=result.success,
        )
```

**Base class helpers available:**
- `self.parse_int(value, name)` -- Parse a string to `int`, returns `None` on failure
- `self.error_result(message)` -- Create a failed `CommandResult`

---

### Step 4: Module Init (`__init__.py`)

Export the game class, config, and optionally the command handler and models.

**Without command handler** (grid-based game):

```python
"""Your Game puzzle game module."""

from .config import YourGameConfig
from .game import YourGame

__all__ = ["YourGame", "YourGameConfig"]
```

**With command handler:**

```python
"""Your Game puzzle game."""

from .commands import YourGameCommandHandler
from .config import YourGameConfig
from .game import YourGame

__all__ = ["YourGame", "YourGameConfig", "YourGameCommandHandler"]
```

**With custom models** (see `rush_hour/__init__.py`):

```python
"""Your Game puzzle game."""

from .commands import YourGameCommandHandler
from .config import YourGameConfig
from .game import YourGame
from .models import CustomModel

__all__ = ["YourGame", "YourGameConfig", "YourGameCommandHandler", "CustomModel"]
```

---

### Step 5: Register the Game (`games/__init__.py`)

Edit `src/chuk_puzzles_gym/games/__init__.py` to import and register your game.

**1. Add the import:**

```python
from .your_game import YourGame
# If you have a command handler:
from .your_game import YourGameCommandHandler
```

**2. Add to `AVAILABLE_GAMES`:**

```python
AVAILABLE_GAMES = {
    # ... existing games ...
    "your_game": YourGame,
}
```

**3. (If applicable) Add to `GAME_COMMAND_HANDLERS`:**

```python
GAME_COMMAND_HANDLERS = {
    # ... existing handlers ...
    "your_game": YourGameCommandHandler,
}
```

**4. Add to `__all__`:**

```python
__all__ = [
    # ... existing exports ...
    "YourGame",
    # "YourGameCommandHandler",  # if applicable
]
```

---

### Step 6: Write Tests (`tests/test_your_game.py`)

Create `tests/test_your_game.py`. The standard test checklist covers roughly 20 tests:

```python
"""Tests for Your Game puzzle."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.games.your_game import YourGame
from chuk_puzzles_gym.models import GameCommand


class TestYourGame:
    """Test suite for YourGame."""

    # --- Initialization ---

    async def test_initialization(self):
        game = YourGame("easy")
        assert game.name == "Your Game"

    @pytest.mark.parametrize(
        "difficulty,expected_size",
        [("easy", 6), ("medium", 8), ("hard", 10)],
    )
    async def test_difficulty_levels(self, difficulty, expected_size):
        game = YourGame(difficulty, seed=42)
        await game.generate_puzzle()
        assert game.config.size == expected_size

    # --- Puzzle generation ---

    async def test_generate_puzzle(self):
        game = YourGame("easy", seed=42)
        await game.generate_puzzle()
        assert game.game_started

    async def test_solution_valid(self):
        """Verify the generated solution satisfies all constraints."""
        game = YourGame("easy", seed=42)
        await game.generate_puzzle()
        # Assert solution-specific invariants

    # --- Move validation ---

    async def test_valid_move(self):
        game = YourGame("easy", seed=42)
        await game.generate_puzzle()
        # Make a correct move from the solution
        result = await game.validate_move(...)
        assert result.success

    async def test_invalid_move(self):
        game = YourGame("easy", seed=42)
        await game.generate_puzzle()
        # Make an invalid move
        result = await game.validate_move(...)
        assert not result.success

    async def test_out_of_bounds(self):
        game = YourGame("easy", seed=42)
        await game.generate_puzzle()
        result = await game.validate_move(0, 0, 1)  # Out of bounds
        assert not result.success

    async def test_cannot_modify_initial(self):
        """Test that pre-filled cells cannot be changed."""
        game = YourGame("easy", seed=42)
        await game.generate_puzzle()
        # Try to modify a pre-filled cell
        # assert not result.success

    async def test_clear_cell(self):
        game = YourGame("easy", seed=42)
        await game.generate_puzzle()
        # Place then clear
        # assert result.success

    # --- Completion ---

    async def test_is_complete(self):
        game = YourGame("easy", seed=42)
        await game.generate_puzzle()
        assert not game.is_complete()
        # Set all cells to solution values
        # assert game.is_complete()

    # --- Hints ---

    async def test_get_hint(self):
        game = YourGame("easy", seed=42)
        await game.generate_puzzle()
        hint = await game.get_hint()
        assert hint is not None
        hint_data, hint_message = hint

    # --- Rendering ---

    async def test_render_grid(self):
        game = YourGame("easy", seed=42)
        await game.generate_puzzle()
        rendered = game.render_grid()
        assert isinstance(rendered, str)
        assert len(rendered) > 0

    async def test_get_rules(self):
        game = YourGame("easy")
        assert len(game.get_rules()) > 0

    async def test_get_commands(self):
        game = YourGame("easy")
        assert "place" in game.get_commands().lower()

    # --- Properties ---

    async def test_constraint_types(self):
        game = YourGame("easy")
        assert len(game.constraint_types) > 0

    async def test_business_analogies(self):
        game = YourGame("easy")
        assert len(game.business_analogies) > 0

    async def test_complexity_profile(self):
        game = YourGame("easy")
        profile = game.complexity_profile
        assert "reasoning_type" in profile

    # --- Deterministic seeding ---

    async def test_deterministic_seeding(self):
        game1 = YourGame("easy", seed=12345)
        await game1.generate_puzzle()
        game2 = YourGame("easy", seed=12345)
        await game2.generate_puzzle()
        assert game1.grid == game2.grid
        assert game1.solution == game2.solution

    # --- Command handler (if applicable) ---

    # async def test_command_handler_place(self):
    #     game = YourGame("easy", seed=42)
    #     await game.generate_puzzle()
    #     handler = YourGameCommandHandler(game)
    #     assert GameCommand.PLACE in handler.supported_commands
    #     result = await handler.handle_command(GameCommand.PLACE, ["1", "2"])
    #     assert result.result.success

    # async def test_command_handler_bad_args(self):
    #     game = YourGame("easy", seed=42)
    #     await game.generate_puzzle()
    #     handler = YourGameCommandHandler(game)
    #     result = await handler.handle_command(GameCommand.PLACE, ["1"])
    #     assert not result.result.success
```

#### Integration test updates

After adding your game, update these existing integration tests:

**`tests/test_deterministic_seeding.py`** -- Add your game ID to `GRID_GAMES` (if grid-based) or `NON_GRID_GAMES`:

```python
GRID_GAMES = [
    # ... existing ...
    "your_game",
]
```

If your game uses non-standard state (not `grid`, `cells`, `secret_code`, etc.), add a case to the `get_game_state()` helper.

**`tests/test_game_configs.py`** -- Add a config test class:

```python
from chuk_puzzles_gym.games.your_game.config import YourGameConfig

class TestYourGameConfig:
    def test_from_difficulty_easy(self):
        config = YourGameConfig.from_difficulty(DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY
        assert config.size == 6

    def test_from_difficulty_medium(self):
        config = YourGameConfig.from_difficulty(DifficultyLevel.MEDIUM)
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.size == 8

    def test_from_difficulty_hard(self):
        config = YourGameConfig.from_difficulty(DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD
        assert config.size == 10
```

---

### Step 7: Verify

Run the full check suite:

```bash
make check    # lint + typecheck + tests
```

For manual testing, start the server and connect via telnet:

```bash
make run
# In another terminal:
telnet localhost 8023
```

---

## Quick Reference

### GameCommand Enum Values

All values from `src/chuk_puzzles_gym/models/enums.py`:

| Command | Value | Typical Use |
|---------|-------|-------------|
| `PLACE` | `"place"` | Place a value on the grid/board |
| `CLEAR` | `"clear"` | Clear/remove a placed value |
| `PRESS` | `"press"` | Toggle (e.g. Lights Out) |
| `CONNECT` | `"connect"` | Connect elements (e.g. Bridges) |
| `EXCLUDE` | `"exclude"` | Mark as excluded |
| `REVEAL` | `"reveal"` | Reveal a cell (e.g. Minesweeper) |
| `FLAG` | `"flag"` | Flag a cell |
| `SELECT` | `"select"` | Select an item |
| `DESELECT` | `"deselect"` | Deselect an item |
| `ASSIGN` | `"assign"` | Assign a resource |
| `UNASSIGN` | `"unassign"` | Remove an assignment |
| `MARK` | `"mark"` | Mark a cell |
| `GUESS` | `"guess"` | Submit a guess (e.g. Mastermind) |
| `SET` | `"set"` | Set a value |
| `SHADE` | `"shade"` | Shade a cell (e.g. Hitori) |
| `BRIDGE` | `"bridge"` | Build a bridge |
| `MOVE` | `"move"` | Move a piece (e.g. Rush Hour, Sokoban) |

System commands (`QUIT`, `HELP`, `SHOW`, `HINT`, `CHECK`, `SOLVE`, `RESET`, `MENU`, `MODE`, `SEED`, `COMPARE`, `STATS`) are handled by the server and should not appear in your `supported_commands`.

### Base Class Utilities

From `PuzzleGame` (inherited by your game):

| Method/Property | Description |
|----------------|-------------|
| `self._rng` | Seeded `random.Random` instance -- use for all randomness |
| `self.seed` | The seed value (always set, even if auto-generated) |
| `self.difficulty` | `DifficultyLevel` enum |
| `self.solver_config` | `SolverConfig` with hint budget settings |
| `self.game_started` | Set to `True` at end of `generate_puzzle()` |
| `record_move(position, success)` | Track move metrics and feed reasoning tracker (call from `validate_move`) |
| `record_hint()` | Consume a hint from the budget; returns `bool` |
| `can_use_hint()` | Check if hints remain without consuming one |
| `hints_remaining` | Number of hints left in budget |
| `reasoning_tracker` | `ReasoningTracker` instance -- tracks backtracks, error streaks, solver distance |
| `get_reasoning_metrics()` | Returns `ReasoningMetrics` snapshot (backtrack rate, progress steadiness, etc.) |
| `get_stats()` | Default stats string (override for custom stats) |
| `get_solution_efficiency(steps)` | Calculate efficiency vs optimal |

From `GameCommandHandler` (inherited by your command handler):

| Method | Description |
|--------|-------------|
| `self.game` | The `PuzzleGame` instance |
| `parse_int(value, name)` | Parse string to `int`, returns `None` on failure |
| `error_result(message)` | Create a failed `CommandResult` |

---

## Reference Games

Use these as examples when building your own:

| Complexity | Game | Path | Notes |
|-----------|------|------|-------|
| Simple grid | `binary` | `games/binary/` | Minimal config + game, no command handler |
| Complex with handler | `graph_coloring` | `games/graph_coloring/` | Custom command handler, non-grid topology |
| Custom models | `rush_hour` | `games/rush_hour/` | `models.py` with `Vehicle` Pydantic model |
| Full test suite | `graph_coloring` | `tests/test_graph_coloring_game.py` | ~20 tests covering all aspects |
