# Puzzle Arcade Server Roadmap

> **Vision:** Puzzle Arcade Server is not "a puzzle game" — it's a **reasoning & constraint benchmark environment for AI agents** that remains fun and accessible for humans via telnet.

This roadmap prioritizes:
- **Human-first telnet experience** (the fun never goes away)
- Agent evaluation & benchmarking
- Solver vs model comparisons
- Curriculum & difficulty scaling
- Reproducibility
- Real-world constraint analogues

---

## Design Principle: Dual-Mode Architecture

The server supports two parallel interaction modes:

| Mode | Protocol | Audience | State Format |
|------|----------|----------|--------------|
| **Human** | Telnet (text) | Players, demos | ASCII art, friendly messages |
| **Agent** | Telnet (JSON) or MCP | LLMs, RL agents | Structured observations |

Both modes use the **same game logic** — only the I/O layer differs.

```
┌─────────────────────────────────────────────────────────┐
│                   PuzzleGame (Core Logic)               │
│  reset() → step() → observe() → is_complete()          │
└─────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────┐      ┌─────────────────────┐
│   Human Handler     │      │   Agent Handler     │
│   - ASCII grids     │      │   - JSON messages   │
│   - Friendly text   │      │   - Structured obs  │
│   - Telnet default  │      │   - Metrics output  │
└─────────────────────┘      └─────────────────────┘
```

---

## Current Architecture Summary

| Component | Current State |
|-----------|---------------|
| Base Interface | `PuzzleGame` ABC with 8 abstract methods |
| Games | 24 games in static `AVAILABLE_GAMES` dict |
| Session | Per-connection state in `ArcadeHandler` |
| Protocol | Telnet (text-based), 3 output modes |
| Scoring | `moves_made` counter only |
| Difficulty | `DifficultyLevel` enum (easy/medium/hard) |
| Seeding | Not implemented |
| Episodes | Not tracked |

---

## Phase 1: Harden the Benchmark Core

**Goal:** Make this undeniably useful as a benchmarking harness while keeping human play unchanged.

### 1.1 Deterministic Seeds & Replay

Every puzzle instance should be reproducible. Humans can share seeds to challenge friends!

**Changes Required:**

```python
# puzzle_game.py additions
class PuzzleGame(ABC):
    def __init__(self, difficulty: DifficultyLevel | str = DifficultyLevel.EASY, seed: int | None = None):
        self.seed = seed or self._generate_seed()
        self._rng = random.Random(self.seed)
        # ... existing init

    def _generate_seed(self) -> int:
        return random.randint(0, 2**32 - 1)
```

**New Commands (work in both modes):**
- `seed` - Display current puzzle seed ("Your seed is: 42")
- `sudoku hard 12345` - Start game with specific seed

**Human Experience:**
```
> sudoku hard 12345
Starting Sudoku (hard) with seed 12345...
Share this seed with friends to play the same puzzle!
```

**Files to Modify:**
- `src/puzzle_arcade_server/base/puzzle_game.py` - Add seed support
- `src/puzzle_arcade_server/server.py` - Parse seed from commands
- All 24 game files - Use `self._rng` instead of `random`

---

### 1.2 Standardized Difficulty & Complexity Metrics

Add quantifiable metrics to every puzzle. Optional display for humans, always included for agents.

**New Properties on PuzzleGame:**

```python
@property
def complexity_metrics(self) -> dict:
    """Quantified complexity for this puzzle instance."""
    return {
        "constraint_count": 0,      # Number of constraints
        "variable_count": 0,        # Number of decision variables
        "domain_size": 0,           # Average domain size
        "branching_factor": 0.0,    # Estimated branching
        "search_depth": 0,          # Estimated search depth
    }
```

**Human Command:**
```
> stats
Moves made: 12
Puzzle complexity: 24 constraints, 36 variables
```

**Agent Output (JSON mode):**
```json
{"complexity": {"constraint_count": 24, "variable_count": 36, ...}}
```

**Files to Modify:**
- `src/puzzle_arcade_server/base/puzzle_game.py` - Add property
- All 24 game files - Implement for each game

---

### 1.3 Episode Model

Formalize game sessions as episodes. Invisible to humans, essential for agents.

**New Model:**

```python
# models/episode.py
from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class Episode(BaseModel):
    id: str                          # Unique episode ID
    game: str                        # Game identifier
    difficulty: str                  # easy/medium/hard
    seed: int                        # Reproducible seed
    started_at: datetime
    ended_at: datetime | None = None
    status: Literal["in_progress", "solved", "failed", "abandoned"]

    # Metrics
    moves_made: int = 0
    invalid_moves: int = 0
    hints_used: int = 0
    wall_time_ms: int | None = None

    # Trace (optional)
    trace: list[dict] | None = None  # List of {action, result, timestamp}
```

**Human Experience:** Unchanged — episode tracking happens silently in background.

**Files to Create:**
- `src/puzzle_arcade_server/models/episode.py`

**Files to Modify:**
- `src/puzzle_arcade_server/server.py` - Create episode on game start

---

### 1.4 Trace Logging

Store complete episode traces for offline analysis.

**Trace Format (JSONL):**

```json
{"type": "episode_start", "id": "ep_abc123", "game": "sudoku", "difficulty": "medium", "seed": 42, "ts": 1700000000}
{"type": "action", "id": "ep_abc123", "action": {"cmd": "place", "args": [1, 5, 7]}, "result": {"success": true}, "ts": 1700000001}
{"type": "episode_end", "id": "ep_abc123", "status": "solved", "metrics": {"moves": 45}, "ts": 1700000010}
```

**Configuration:**

```python
# Optional trace directory (disabled by default for humans)
TRACE_DIR = os.environ.get("PUZZLE_ARCADE_TRACE_DIR", None)
```

**Files to Create:**
- `src/puzzle_arcade_server/tracing.py` - Trace writer

---

## Phase 2: Agent-First Features

**Goal:** Add structured agent support alongside human telnet.

### 2.1 JSON Protocol Mode

Add JSON mode as a fourth output mode. Telnet remains the default.

**Mode Selection:**
```
> mode json
Output mode set to: json
```

**Protocol Messages (JSON mode only):**

**Server → Agent:**
```json
{"type": "obs", "episode_id": "ep_123", "game": "sudoku", "obs": {"grid": [...], "moves": 5}, "done": false}
```

**Agent → Server:**
```json
{"type": "action", "action": {"cmd": "place", "args": [1, 5, 7]}}
```

**Human modes remain unchanged:**
- `normal` - ASCII art, friendly messages (default)
- `agent` - Current marker-based format
- `compact` - Minimal output
- `json` - New structured format

**Files to Modify:**
- `src/puzzle_arcade_server/models/enums.py` - Add JSON mode
- `src/puzzle_arcade_server/server.py` - JSON output path

---

### 2.2 Gym-Style Methods (Internal)

Add formal step/reset methods internally. Existing commands remain the interface.

**Base Class Extension:**

```python
class PuzzleGame(ABC):
    # Existing methods stay the same...

    # New internal methods for agent harness
    async def reset(self, seed: int | None = None) -> dict:
        """Reset game and return initial observation."""
        self.seed = seed or self._generate_seed()
        self._rng = random.Random(self.seed)
        await self.generate_puzzle()
        return self.get_observation()

    async def step(self, action: dict) -> tuple[dict, float, bool, dict]:
        """Execute action, return (obs, reward, done, info)."""
        result = await self._execute_action(action)
        obs = self.get_observation()
        reward = 1.0 if self.is_complete() else 0.0
        done = self.is_complete() or result.game_over
        info = {"valid": result.success, "message": result.message}
        return obs, reward, done, info

    def get_observation(self) -> dict:
        """Return current state as structured observation."""
        return {
            "grid": self._serialize_grid(),
            "moves": self.moves_made,
            "complete": self.is_complete(),
        }
```

**Human Interface:** Unchanged — humans use `place`, `mark`, etc.

**Agent Interface (JSON mode):**
```json
{"type": "action", "action": {"cmd": "place", "args": [1, 5, 7]}}
```

---

### 2.3 Built-in Evaluation Metrics

Add evaluation output for completed games.

**Human Experience:**
```
CONGRATULATIONS! PUZZLE SOLVED!
==================================
Moves made: 45
Invalid moves: 3
Hints used: 0
Time: 2m 34s
```

**Agent Experience (JSON mode):**
```json
{
  "type": "episode_complete",
  "episode_id": "ep_123",
  "solved": true,
  "metrics": {
    "moves_made": 45,
    "invalid_moves": 3,
    "hints_used": 0,
    "wall_time_ms": 154000
  }
}
```

---

### 2.4 Rate Limits & Timeouts (Optional)

Server-enforced limits for benchmarking. Disabled by default for casual play.

**Configuration:**

```python
# Environment variables (not set = no limits)
MAX_STEPS = os.environ.get("PUZZLE_ARCADE_MAX_STEPS", None)
MAX_INVALID = os.environ.get("PUZZLE_ARCADE_MAX_INVALID", None)
TIMEOUT_SEC = os.environ.get("PUZZLE_ARCADE_TIMEOUT", None)
```

**Human Experience:** No limits unless explicitly configured.

**Agent Benchmark Mode:** Limits enforced for fair comparison.

---

### 2.5 Solver vs Model Comparison Mode

The killer feature given `chuk-mcp-solver`.

**New Command (works in all modes):**

```
> compare
Available comparison modes:
  - model: Pure LLM solving
  - solver: Direct CP-SAT solving
  - hybrid: LLM + MCP solver tools

Use: compare <mode>
```

**Implementation:**
- Record solving approach in episode metadata
- Generate comparison reports

---

## Phase 3: Curriculum & Learning

**Goal:** Enable progressive difficulty for both humans and agents.

### 3.1 Puzzle Curriculum Graph

Define progression dependencies.

**Human Experience:**
```
> curriculum
Your Progress:
  [x] Foundations (3/3 complete)
  [ ] Arithmetic (1/3 complete)
  [ ] Optimization (0/2 complete)

Recommended next: kakuro easy
```

**Agent Experience:** Curriculum exposed as metadata for training.

**Curriculum Definition:**

```yaml
# curriculum.yaml
stages:
  - name: "foundations"
    games: [sudoku:easy, binary:easy, futoshiki:easy]
    concepts: ["all_different", "binary_constraints"]

  - name: "arithmetic"
    requires: ["foundations"]
    games: [kenken:easy, kakuro:easy]
    concepts: ["arithmetic_cages", "sum_constraints"]

  - name: "optimization"
    requires: ["arithmetic"]
    games: [knapsack:medium, scheduler:medium]
    concepts: ["objective_functions"]
```

---

### 3.2 Reward Shaping Profiles (Agent Only)

Support multiple reward functions for RL.

**Profiles:**
- `sparse` - +1 solve, -1 fail, 0 otherwise
- `dense` - Progress toward solution
- `efficiency` - Penalize moves, reward speed

**Configuration:** Set via environment for agent runs.

---

## Phase 4: New Puzzle Classes

**Goal:** Add categories that stress-test different reasoning types.

### 4.1 Temporal Puzzles

Multi-step dependencies and ordering. Great for humans who like logic puzzles!

**New Games:**
- **Timeline** - Order events with before/after constraints
- **Sequencer** - Determine action sequences from outcomes

### 4.2 Optimization-Only Challenges

Not "solve", but optimize. Humans compete for high scores!

**New Games:**
- **Portfolio** - Select investments with risk/return trade-offs
- **Routing** - TSP-style path optimization

### 4.3 Mixed-Domain Puzzles

Combine constraint types. The ultimate challenge for both humans and agents.

**New Games:**
- **Factory** - Grid layout + scheduling + resource constraints
- **Detective** - Logic grid + temporal + probability

---

## Phase 5: Ecosystem & Visibility

**Goal:** Make this widely usable and referenced.

### 5.1 MCP Native Mode

Expose puzzles as MCP tools for agent frameworks.

**MCP Tools:**
- `puzzle_arcade_list_games` - Available games
- `puzzle_arcade_new` - Start new game
- `puzzle_arcade_action` - Execute action
- `puzzle_arcade_observe` - Get current state

**Files to Create:**
- `src/puzzle_arcade_server/mcp_server.py`

---

### 5.2 Public Benchmark Packs

Versioned, citable datasets for research.

**Benchmark Structure:**

```
benchmarks/
  logic-easy-v1/
    manifest.json     # Metadata
    seeds.json        # List of seeds for each game
```

**Manifest:**

```json
{
  "name": "logic-easy-v1",
  "version": "1.0.0",
  "games": ["sudoku", "binary", "futoshiki"],
  "difficulty": "easy",
  "seeds": [1, 2, 3, ..., 100]
}
```

---

### 5.3 CLI Evaluation Runner

Batch evaluation tool for agents.

**Usage:**

```bash
# Run benchmark pack
puzzle-arcade-eval --benchmark logic-easy-v1 --agent openai:gpt-4

# Output formats
puzzle-arcade-eval ... --output json|csv|markdown
```

---

## Implementation Priority

### High Impact, Low Effort
1. **Deterministic seeds** (Phase 1.1) - Benefits humans and agents
2. **Episode model** (Phase 1.3) - Internal tracking
3. **JSON protocol mode** (Phase 2.1) - Agent support
4. **Complexity metrics** (Phase 1.2) - Richer stats

### High Impact, Medium Effort
5. Trace logging (Phase 1.4)
6. Gym-style methods (Phase 2.2)
7. Evaluation metrics (Phase 2.3)
8. MCP native mode (Phase 5.1)

### High Impact, High Effort
9. Solver vs model comparison (Phase 2.5)
10. Curriculum graph (Phase 3.1)
11. New puzzle classes (Phase 4.x)
12. Public benchmark packs (Phase 5.2)

---

## Killer Differentiators

If you do *just a few* things, make them these:

1. **Solver vs Model comparison mode** - Unique to CHUK ecosystem
2. **Deterministic puzzle replay** - Essential for reproducibility + fun for humans
3. **Quantified difficulty & constraints** - Enables curriculum
4. **Agent-first evaluation metrics** - Makes it a real benchmark
5. **Curriculum graph** - Enables learning + guides human progression

---

## Interface Evolution

### Current Interface (PuzzleGame)

```python
class PuzzleGame(ABC):
    async generate_puzzle()
    async validate_move(*args, **kwargs) -> MoveResult
    is_complete() -> bool
    async get_hint() -> tuple | None
    render_grid() -> str
    get_rules() -> str
    get_commands() -> str

    @property name, description
    @property constraint_types, business_analogies, complexity_profile
```

### Target Interface (PuzzleGame v2)

Extends existing interface — no breaking changes:

```python
class PuzzleGame(ABC):
    # === Existing methods (unchanged) ===
    async generate_puzzle()
    async validate_move(*args, **kwargs) -> MoveResult
    is_complete() -> bool
    async get_hint() -> tuple | None
    render_grid() -> str           # Human rendering
    get_rules() -> str
    get_commands() -> str

    @property name, description
    @property constraint_types, business_analogies, complexity_profile

    # === New methods (additions) ===
    seed: int
    _rng: random.Random

    async reset(seed: int | None = None) -> dict
    async step(action: dict) -> tuple[dict, float, bool, dict]
    def get_observation(self) -> dict
    def valid_actions(self) -> list[dict] | None

    @property complexity_metrics -> dict
```

---

## Migration Path

All versions maintain human telnet compatibility:

1. **v0.2.0** - Add seeds, episode model, trace logging
2. **v0.3.0** - Add JSON mode, complexity metrics
3. **v0.4.0** - Add Gym-style methods (internal)
4. **v0.5.0** - Add evaluation harness, comparison mode
5. **v1.0.0** - Full agent-first interface

---

## Success Metrics

The roadmap succeeds when:

- [ ] Humans can still `telnet localhost 8023` and play sudoku
- [ ] Humans can share seeds to challenge friends
- [ ] Any puzzle can be replayed with the same seed → identical instance
- [ ] Every puzzle has quantified complexity metrics
- [ ] Agents can connect via JSON protocol and run episodes
- [ ] Traces are logged and can be replayed
- [ ] Benchmark packs are versioned and citable
- [ ] Solver vs model comparisons are one command away
- [ ] Curriculum enables progressive learning for humans and agents
