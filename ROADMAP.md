# chuk-puzzles-gym — Roadmap

> **Goal:** Become the **default open infrastructure** for reasoning-centric SFT + RL on small models.

---

## Current State (v0.9)

### What's Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| **30 Puzzle Games** | ✅ Complete | All with easy/medium/hard difficulty |
| **Deterministic Seeding** | ✅ Complete | Reproducible puzzles via seed |
| **Agent Mode** | ✅ Complete | Structured output with markers |
| **Constraint Types** | ✅ Complete | Every game has `constraint_types` |
| **Business Analogies** | ✅ Complete | Every game has `business_analogies` |
| **Difficulty Profiles** | ✅ Complete | `logic_depth`, `branching_factor`, etc. |
| **Evaluation Harness** | ✅ Complete | `chuk-puzzles-eval` CLI |
| **Dataset Export** | ✅ Complete | `chuk-puzzles-export` JSONL with traces |
| **Step Traces** | ✅ Complete | chuk-gym-core compatible traces |
| **Gymnasium Env** | ✅ Complete | `PuzzleEnv` for RL |
| **Reasoning Depth Metrics** | ✅ Complete | Backtrack detection, progress steadiness, error patterns |
| **Test Suite** | ✅ Complete | 1323 tests, 94% coverage |
| **Type Safety** | ✅ Complete | Pydantic v2, MyPy passing |

---

## Phase 1 — Lock the Core ✅

**Theme:** Make the current design impossible to misunderstand or misuse.

### ✅ Stabilize the "reasoning ABI"

Frozen schemas (v1):
- **State representation** — Grid-based with solution
- **Action schema** — `place`, `move`, `eliminate` operations
- **Step trace format** — chuk-gym-core `Step` with 7 fields

### ✅ Golden trace tests

- Snapshot tests for puzzle → trace → solution
- CI asserts determinism and legality
- `tests/test_trace_generator.py` (40 tests)

### ✅ README upgrade

- What problem this solves (cold start + RL)
- Why steps > CoT (verifiable reasoning)
- How to use in training loop (Dataset Export section)

---

## Phase 2 — Dataset as a Product ✅

**Theme:** Make it trivial to *use the data* without caring about the gym internals.

### ✅ Standard dataset exports

```bash
# JSONL with full traces
chuk-puzzles-export -o puzzles.jsonl

# Specific games/difficulties
chuk-puzzles-export -g sudoku kenken -d easy medium -n 1000
```

Output includes:
- Problem definition (prompt, initial_state, gold_answer)
- Step-by-step traces (operation, before/after, rule, explanation)
- Constraint metadata and difficulty profiles

### ⏳ Cold-start packs (TODO)

Prebuilt datasets:
- `easy-forced-only` — Single-candidate deductions only
- `medium-no-backtracking` — Forward reasoning, no guessing
- `hard-with-branching` — Requires search/backtracking

Each tagged with:
- Puzzle type and difficulty
- Reasoning skills involved
- Optimal step count

### ✅ Baseline metrics + Reasoning depth

`chuk-puzzles-eval` provides:
- Solve rate
- Average steps / optimal steps
- Invalid move rate
- Wall clock time
- **Reasoning depth metrics**: backtrack rate, progress steadiness, reasoning overhead, error streak analysis, solver distance traces

```bash
chuk-puzzles-eval -g sudoku -n 100 -o json > baseline.json
```

---

## Phase 3 — RL Loop First-Class

**Theme:** Show the *full loop* working, cheaply.

### ✅ Gymnasium Environment

```python
from chuk_puzzles_gym.gym_env import PuzzleEnv

env = PuzzleEnv("sudoku", difficulty="medium", seed=42)
obs, info = env.reset()

while not done:
    action = agent.decide(obs)
    obs, reward, done, truncated, info = env.step(action)
```

### ✅ Verifier-driven rewards

Configurable reward components:
- `correct_placement` — Valid move toward solution
- `invalid_attempt` — Rejected move penalty
- `completion_bonus` — Puzzle solved
- `efficiency_multiplier` — Bonus for optimal steps

```python
from chuk_puzzles_gym.models import SolverConfig

config = SolverConfig(
    solver_enabled=False,  # Pure reasoning mode
    hint_penalty=0.1,
)
```

### ⏳ Reference training loop (TODO)

Minimal example showing:
```
SFT on traces → rollout in env → verifier reward → PPO update
```

### ⏳ Curriculum scheduler (TODO)

Auto-advance difficulty based on:
- Solve rate threshold
- Invalid step rate
- Average branching depth encountered
- Reasoning depth metrics (backtrack rate, progress steadiness, reasoning overhead)

---

## Phase 4 — Ecosystem Integration

**Theme:** Make this slot cleanly into the CHUK stack *and* external workflows.

### ⏳ MCP + Solver bridge (TODO)

- Gym episode ↔ MCP solver calls
- Step traces usable as tool-call supervision
- Connects to `chuk-mcp-solver`

### ⏳ Plugin puzzle API (TODO)

Let others add puzzles via:
- Schema definition
- Solver adapter
- Step explainer

No core changes needed.

### ⏳ Leaderboard (TODO)

Track:
- Tiny models (< 1B params)
- Heuristic agents
- RL-trained agents

Focus on **reasoning quality** (backtrack rate, progress steadiness, reasoning overhead), not just accuracy.

---

## Phase 5 — Research & Splash

**Theme:** Make noise with minimal compute.

### ⏳ "$100 reasoning model" experiment

Train:
- TinyLlama or similar small model
- Only on puzzle data (SFT + short RL)

Compare against:
- Base model (zero-shot)
- Larger general models on puzzles

### ⏳ Positioning paper / blog

> "Why solver-grounded steps beat chain-of-thought"

Use own results to demonstrate.

---

## TL;DR Summary

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Lock core | ✅ Complete |
| 2 | Datasets | ✅ Mostly complete (cold-start packs TODO) |
| 3 | RL loop | ✅ Env done, training loop TODO |
| 4 | Ecosystem | ⏳ Not started |
| 5 | Splash | ⏳ Not started |

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

---

## Related Projects

- **[chuk-gym-core](https://github.com/chrishayuk/chuk-gym-core)** — Shared schemas (Problem, Trace, Step)
- **[chuk-math-gym](https://github.com/chrishayuk/chuk-math-gym)** — Mathematical reasoning gym
- **chuk-mcp-solver** — CP-SAT solver as MCP tool
