# Puzzle Arcade Server Roadmap

> **Vision:** Puzzle Arcade Server is a **reasoning & constraint benchmark environment for AI agents** that remains fun and accessible for humans via telnet.

This roadmap prioritizes:
- **Human-first telnet experience** (the fun never goes away)
- Agent evaluation & benchmarking
- Solver vs model comparisons
- Curriculum & difficulty scaling
- Reproducibility
- Real-world constraint analogues

---

## Current State (v0.5)

### What's Already Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| **24 Puzzle Games** | ✅ Complete | All with easy/medium/hard difficulty |
| **Deterministic Seeding** | ✅ Complete | Every game uses `self._rng` for reproducibility |
| **Seed in Commands** | ✅ Complete | `sudoku hard 12345` starts specific puzzle |
| **Seed in Stats** | ✅ Complete | All games show seed in `get_stats()` |
| **Agent Mode** | ✅ Complete | `mode agent` for structured output with markers |
| **Constraint Types** | ✅ Complete | Every game has `constraint_types` property |
| **Business Analogies** | ✅ Complete | Every game has `business_analogies` property |
| **Complexity Profile** | ✅ Complete | Every game has `complexity_profile` property |
| **Multi-Transport** | ✅ Complete | Telnet, TCP, WebSocket, WS-Telnet |
| **Test Suite** | ✅ Complete | 832 tests, 95% coverage |
| **Type Safety** | ✅ Complete | Pydantic v2, MyPy passing |

### Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│                   PuzzleGame (Core Logic)               │
│  generate_puzzle() → validate_move() → is_complete()    │
│  seed, _rng, constraint_types, business_analogies       │
└─────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────┐      ┌─────────────────────┐
│   Human Handler     │      │   Agent Handler     │
│   - ASCII grids     │      │   - Structured out  │
│   - Friendly text   │      │   - Clear markers   │
│   - Telnet default  │      │   - mode agent      │
└─────────────────────┘      └─────────────────────┘
```

---

## Phase 1: Benchmarking & Metrics

**Goal:** Make the server truly measurable for LLM/solver comparison.

### 1.1 Puzzle Complexity Metrics ✅ Complete (Base Implementation)

Add quantifiable metrics to every puzzle instance.

**New Property on PuzzleGame:**

```python
@property
def complexity_metrics(self) -> dict:
    """Quantified complexity for this puzzle instance."""
    return {
        "constraint_count": 0,      # Number of constraints
        "variable_count": 0,        # Number of decision variables
        "domain_size": 0,           # Average domain size
        "branching_factor": 0.0,    # Estimated branching
        "solver_baseline_ms": 0,    # Reference solver time
    }
```

**Human Command:**
```
> stats
Moves made: 12 | Seed: 42
Complexity: 24 constraints, 36 variables
```

### 1.2 Episode Model

Formalize game sessions as episodes for tracking.

```python
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
```

### 1.3 Trace Logging

Store complete episode traces for offline analysis (JSONL format).

```json
{"type": "episode_start", "id": "ep_abc123", "game": "sudoku", "seed": 42, "ts": 1700000000}
{"type": "action", "id": "ep_abc123", "action": "place 1 5 7", "result": "success", "ts": 1700000001}
{"type": "episode_end", "id": "ep_abc123", "status": "solved", "moves": 45, "ts": 1700000010}
```

---

## Phase 2: Agent Evaluation Enhancements

**Goal:** Push agent mode toward proper evaluation infrastructure.

### 2.1 Evaluation Harness CLI ✅ Complete

A utility to run benchmarks repeatedly and collect metrics.

```bash
# Run evaluation against a game
puzzle-arcade-eval sudoku --difficulty medium --episodes 100

# Output formats
puzzle-arcade-eval sudoku --output json|csv|markdown

# With specific seeds
puzzle-arcade-eval sudoku --seeds 1,2,3,4,5
```

**Output:**
```
Sudoku Medium Evaluation (100 episodes)
========================================
Solved:     87/100 (87%)
Avg Moves:  45.3
Avg Time:   12.4s
Invalid:    3.2 avg per episode
```

### 2.2 Solver vs Model Mode

Compare CP-SAT solver outputs with LLM agent suggestions.

```
> compare
Comparison Modes:
  model   - Pure LLM solving (no hints)
  solver  - Direct CP-SAT solving
  hybrid  - LLM + solver suggestions

> compare solver
Solving with CP-SAT...
Solution found in 23ms (42 moves optimal)
```

### 2.3 JSON Protocol Mode

Add JSON mode as a fourth output mode for structured agent communication.

```
> mode json
```

**Server → Agent:**
```json
{"type": "obs", "game": "sudoku", "seed": 42, "grid": [...], "moves": 5, "done": false}
```

**Agent → Server:**
```json
{"type": "action", "cmd": "place", "args": [1, 5, 7]}
```

---

## Phase 3: Curriculum & Learning Paths

**Goal:** Enable progressive difficulty for education and research.

### 3.1 Puzzle Curriculum Graph

Define progression dependencies based on constraint concepts.

```yaml
stages:
  - name: "foundations"
    games: [sudoku:easy, binary:easy, futoshiki:easy]
    concepts: ["all_different", "binary_constraints"]

  - name: "arithmetic"
    requires: ["foundations"]
    games: [kenken:easy, kakuro:easy, killer:easy]
    concepts: ["sum_constraints", "arithmetic_cages"]

  - name: "connectivity"
    requires: ["foundations"]
    games: [bridges:easy, nurikabe:easy, slitherlink:easy]
    concepts: ["graph_connectivity", "loop_constraints"]

  - name: "optimization"
    requires: ["arithmetic"]
    games: [knapsack:medium, scheduler:medium]
    concepts: ["objective_functions", "resource_constraints"]
```

### 3.2 Concept Tags

Label puzzles with constraint concepts for filtering.

```python
# Find all optimization problems
optimization_games = [
    name for name, cls in AVAILABLE_GAMES.items()
    if "optimization" in cls().constraint_types
]
```

---

## Phase 4: Integration & Tooling

**Goal:** Strengthen ecosystem fit and use cases.

### 4.1 MCP Tool Examples

Add real agent workflows demonstrating LLM + solver integration.

**MCP Tools:**
- `puzzle_arcade_list_games` - Available games
- `puzzle_arcade_new` - Start new game with seed
- `puzzle_arcade_action` - Execute action
- `puzzle_arcade_observe` - Get current state
- `puzzle_arcade_hint` - Get solver hint

### 4.2 REST/WebSocket API Docs

Document the protocol for easy integration into UIs or RL agents.

### 4.3 Python Client Library

```python
from puzzle_arcade import PuzzleClient

async with PuzzleClient("localhost:8023") as client:
    await client.start("sudoku", "medium", seed=42)

    while not client.done:
        obs = await client.observe()
        action = my_agent.decide(obs)
        result = await client.act(action)
```

---

## Phase 5: UX & Community Outreach

**Goal:** Make the project more discoverable and usable.

### 5.1 Interactive Web Viewer

Visual puzzle display with step-through mode.

- HTML frontend connecting via WebSocket
- Replay mode for episode traces
- Side-by-side solver vs agent view

### 5.2 Public Benchmark Packs

Versioned, citable puzzle sets for research.

```
benchmarks/
  logic-easy-v1/
    manifest.json     # Metadata + seeds
    baseline.json     # Reference solver metrics
```

### 5.3 Leaderboard

Community submissions for puzzle solving metrics.

---

## Implementation Priority

### Immediate (v0.6)

| Task | Effort | Impact |
|------|--------|--------|
| Complexity metrics | Medium | High |
| Evaluation harness CLI | Medium | High |
| Episode model | Low | Medium |

### Near-term (v0.7)

| Task | Effort | Impact |
|------|--------|--------|
| JSON protocol mode | Medium | High |
| Trace logging | Low | Medium |
| Solver comparison mode | High | High |

### Future (v1.0)

| Task | Effort | Impact |
|------|--------|--------|
| Curriculum graph | Medium | High |
| MCP native mode | High | High |
| Benchmark packs | Medium | High |
| Web viewer | High | Medium |

---

## Success Metrics

The roadmap succeeds when:

- [x] Humans can `telnet localhost 8023` and play any of 24 puzzles
- [x] Humans can share seeds to challenge friends (`sudoku hard 12345`)
- [x] Any puzzle can be replayed with same seed → identical instance
- [x] Every game has constraint_types and business_analogies
- [x] Agent mode provides structured, parseable output
- [x] Base complexity_metrics property on PuzzleGame (implemented for Sudoku)
- [x] Evaluation harness can batch-run episodes (`puzzle-arcade-eval`)
- [ ] All games have full complexity_metrics implementation
- [ ] Traces are logged and can be replayed
- [ ] Benchmark packs are versioned and citable
- [ ] Solver vs model comparisons are one command away
- [ ] Curriculum enables progressive learning

---

## Quick Reference: Constraint Types to Business Problems

| Constraint Pattern | Puzzle Examples | Business Use Cases |
|-------------------|-----------------|-------------------|
| **AllDifferent** | Sudoku, KenKen, Futoshiki | Resource uniqueness, Assignment |
| **Sum Constraints** | Kakuro, Killer Sudoku | Budget allocation, Team sizing |
| **Arithmetic Cages** | KenKen | Department budgets |
| **Boolean SAT** | Lights Out, Binary | Feature toggles, Dependencies |
| **Connectivity** | Bridges, Nurikabe | Network design, Routing |
| **Global Loop** | Slitherlink | Circuit design, Path planning |
| **Bipartite Matching** | Tents and Trees | Job assignment, Pairing |
| **Region Growth** | Fillomino | Territory planning |
| **Spatial Planning** | Sokoban | Warehouse logistics |
| **Optimization** | Knapsack, Scheduler | Portfolio selection, Sprint planning |
| **Precedence** | Scheduler | Project dependencies |
| **Sequential Path** | Hidato | Route sequencing |
| **Probabilistic** | Minesweeper | Risk assessment |
| **Multi-attribute Deduction** | Einstein, Logic Grid | Requirements analysis |
