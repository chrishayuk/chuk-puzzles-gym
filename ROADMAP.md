# Puzzle Arcade Server Roadmap

> **North Star:** Puzzle Arcade should become the **"Gymnasium + ARC + SWE-Bench" of symbolic and logical reasoning** — with tool usage as a first-class dimension.

This roadmap positions Puzzle Arcade Server as a *serious reasoning gym for agents*, not just a game server. Every phase is designed for **credibility, usefulness, and future leverage for training and evaluation**.

---

## Current State (v0.5)

### What's Already Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| **24 Puzzle Games** | ✅ Complete | All with easy/medium/hard difficulty |
| **Deterministic Seeding** | ✅ Complete | Every game uses `self._rng` for reproducibility |
| **Seed in Commands** | ✅ Complete | `sudoku hard 12345` starts specific puzzle |
| **Agent Mode** | ✅ Complete | `mode agent` for structured output with markers |
| **Constraint Types** | ✅ Complete | Every game has `constraint_types` property |
| **Business Analogies** | ✅ Complete | Every game has `business_analogies` property |
| **Complexity Profile** | ✅ Complete | Every game has `complexity_profile` property |
| **Evaluation Harness** | ✅ Complete | `puzzle-arcade-eval` CLI for batch evaluation |
| **Multi-Transport** | ✅ Complete | Telnet, TCP, WebSocket, WS-Telnet |
| **Test Suite** | ✅ Complete | 832 tests, 95% coverage |
| **Type Safety** | ✅ Complete | Pydantic v2, MyPy passing |

---

## Phase 1: Make it a *Serious* Reasoning Gym

**Goal:** Transform from "fun puzzle server" to "measurable agent benchmark"

### 1.1 Standardised Evaluation & Scoring

Right now it's great for interaction, but agents need *measurable outcomes*.

**Deterministic Scoring Schema (per puzzle):**

```python
class EpisodeResult(BaseModel):
    # Core outcomes
    success: bool                    # Solved or not
    steps_taken: int                 # Valid moves made
    invalid_actions: int             # Rejected moves
    retries: int                     # Attempts on same cell
    time_to_solve_ms: int            # Wall clock time

    # Normalised metrics
    efficiency_score: float          # steps_taken / optimal_steps
    reasoning_depth: float           # Derived from backtracking patterns
    error_recovery_rate: float       # Successful corrections / errors

    # Reproducibility
    seed: int
    difficulty: str
    game: str
```

**One-line Episode Summary (JSON):**

```json
{"game":"sudoku","seed":42,"difficulty":"medium","success":true,"steps":45,"invalid":2,"efficiency":0.92,"time_ms":12400}
```

This instantly turns Puzzle Arcade into:
- A **benchmark** (comparable scores)
- An **RL environment** (reward signals)
- A **regression test suite** for agents

### 1.2 Difficulty Ladders (Curriculum)

Not just "easy / medium / hard" — explicit **skill ladders** per puzzle.

**New Difficulty Metadata:**

```python
@property
def difficulty_profile(self) -> dict:
    return {
        "logic_depth": 3,           # Steps of deduction required
        "branching_factor": 4.2,    # Average choices per step
        "state_observability": 1.0, # 1.0 = fully observable
        "constraint_density": 0.7,  # Ratio of constrained cells
    }
```

**Benefits:**
- **Curriculum learning** — agents progress through skill levels
- **Automated training runs** — reproducible difficulty scaling
- **Fair comparisons** — models compared on identical difficulty profiles

**Deterministic Seeds for Reproducibility:**

```bash
# Generate benchmark pack with reproducible seeds
puzzle-arcade-eval sudoku --difficulty-ladder --seeds 1-100 -o benchmark.json
```

### 1.3 Strict vs Natural Language Modes

Make the interaction mode an explicit experimental variable.

| Mode | Description | Use Case |
|------|-------------|----------|
| `mode strict` | Fixed grammar, symbolic inputs, machine-verifiable | RL training, formal benchmarks |
| `mode natural` | Conversational, ambiguous, noisy instructions | Robustness testing, prompt sensitivity |
| `mode agent` | Structured output with markers (current) | Tool integration |

**Strict Mode Example:**
```
> place 1 5 7
OK
> place 1 5 9
ERR:OCCUPIED
```

**Natural Mode Example:**
```
> put a 7 in the middle of row 1
I've placed 7 at row 1, column 5.
> actually make that a 9
That cell is already filled. Would you like to clear it first?
```

This is *huge* for testing:
- Prompt sensitivity
- Robustness to paraphrasing
- Tool grounding failures

---

## Phase 2: Solver & Tool Synergy

**Goal:** Make solver usage a *first-class experimental variable* — this is our unfair advantage.

### 2.1 Solver-Assisted vs Solver-Free Flags

```python
class GameConfig(BaseModel):
    solver_allowed: bool = True      # Can agent request hints?
    solver_call_budget: int = 10     # Max solver invocations
    solver_latency_penalty: float = 0.1  # Score penalty per call
    partial_hints: bool = True       # Hints reveal one cell vs strategy
```

**Commands:**
```
> config solver_allowed false
Solver hints disabled for this session.

> config solver_budget 5
You have 5 solver calls remaining.
```

**Research Value:**

> "Small model + tools > big model without tools"

...now measurable in a controlled environment.

### 2.2 Step-Level Ground Truth

Some puzzles have solvable structure — lean into it.

**Add to each puzzle:**

```python
@property
def canonical_solution(self) -> list[Move]:
    """Optimal solution trace from solver."""
    return self._solver.get_solution_trace()

@property
def minimal_steps(self) -> int:
    """Minimum moves to solve."""
    return len(self.canonical_solution)

@property
def alternative_paths(self) -> list[list[Move]]:
    """Other valid solution orderings."""
    return self._solver.enumerate_orderings(limit=10)
```

**Scoring agents on:**
- Correctness (solved or not)
- *Distance from optimal reasoning* (step efficiency)
- Hallucinated steps (actions that don't advance solution)

This is **rare and extremely valuable** for training data.

### 2.3 Solver Comparison Mode

Compare agent outputs directly with CP-SAT solver.

```
> compare
Comparison Modes:
  model   - Pure LLM solving (no hints)
  solver  - Direct CP-SAT solving
  hybrid  - LLM + solver suggestions

> compare solver
Solving with CP-SAT...
Solution found in 23ms (42 moves optimal)
Your solution: 48 moves (87.5% efficiency)
```

---

## Phase 3: Multi-Agent & Adversarial Reasoning

**Goal:** Move beyond single-agent solving.

### 3.1 Adversarial Puzzles

One agent creates constraints, another solves.

**New Game Modes:**

| Mode | Description |
|------|-------------|
| `adversarial` | Agent A generates puzzle, Agent B solves |
| `hidden-info` | Solver has incomplete state observation |
| `sabotage` | Turn-based puzzle corruption vs solving |
| `red-team` | Create unsolvable-looking puzzles |

**Example: Adversarial Sudoku**
```
> mode adversarial
Agent A: Generate a valid Sudoku with minimal given cells.
Agent B: Solve under time pressure.
Score: A wins if B fails, B wins if solves efficiently.
```

**Tests:**
- Deception and misdirection
- Planning under uncertainty
- Robustness to adversarial input

### 3.2 Collaborative Solving

Two or more agents solving together.

**Collaboration Constraints:**

```python
class CollaborativeConfig(BaseModel):
    agents: int = 2
    shared_blackboard: bool = True   # Can see each other's moves
    partial_knowledge: bool = False  # Each sees subset of grid
    communication_budget: int = 10   # Messages allowed
```

**Scoring:**
- Coordination efficiency
- Redundancy (wasted overlapping work)
- Convergence speed

**Alignment with ecosystem:** Perfect fit for MCP + agent orchestration work.

### 3.3 Turn-Based Logic Games

Beyond puzzles — actual two-player reasoning games.

| Game | Description |
|------|-------------|
| **Nim variants** | Mathematical strategy |
| **Tic-tac-toe extensions** | Perfect information games |
| **Blokus-style** | Spatial competition |
| **Logic duel** | Constraint construction competition |

---

## Phase 4: Training & Research Mode

**Goal:** Make it a proper RL-ready environment.

### 4.1 RL-Ready Environment API (Gymnasium-compatible)

Formalise as a proper gym environment.

```python
from puzzle_arcade import PuzzleEnv

env = PuzzleEnv("sudoku", difficulty="medium", seed=42)

obs, info = env.reset()
while not done:
    action = agent.decide(obs)
    obs, reward, done, truncated, info = env.step(action)
```

**Observation Space Schema:**

```python
ObservationSpace = {
    "grid": Box(0, 9, shape=(9, 9)),      # Current state
    "valid_actions": MultiBinary(729),     # Action mask
    "moves_made": Discrete(100),
    "hints_remaining": Discrete(10),
}
```

**Reward Shaping Options:**

```python
class RewardConfig(BaseModel):
    correct_placement: float = 1.0
    invalid_attempt: float = -0.5
    hint_penalty: float = -0.1
    completion_bonus: float = 10.0
    efficiency_multiplier: float = 1.0  # Bonus for optimal steps
```

**Benefits:**
- Plug-and-play for RL research
- Usable beyond MCP-CLI
- Attractive to researchers

### 4.2 Synthetic Reasoning Dataset Generation

Turn gameplay into training data.

**Export Capabilities:**

```bash
# Export solved episodes as training data
puzzle-arcade-export --games sudoku,kenken --episodes 10000 \
    --format cot  # Chain-of-thought traces
    --output reasoning_data.jsonl

# Generate difficulty-balanced datasets
puzzle-arcade-export --difficulty-balanced \
    --per-level 1000 \
    --include-failures
```

**Output Formats:**

| Format | Description |
|--------|-------------|
| `cot` | Chain-of-thought synthetic traces |
| `sft` | Supervised fine-tuning pairs (state → action) |
| `preference` | Correct vs incorrect action pairs (DPO) |
| `trace` | Full episode with reasoning annotations |

**Label Reasoning Failures:**

```json
{
  "state": "...",
  "action": "place 1 5 9",
  "correct": false,
  "failure_type": "constraint_violation",
  "violated_constraint": "row_uniqueness",
  "correct_action": "place 1 5 7"
}
```

This feeds:
- Fine-tuning
- Distillation
- Evaluation datasets

### 4.3 Episode Trace Logging

Store complete episode traces for offline analysis.

```json
{"type": "episode_start", "id": "ep_abc123", "game": "sudoku", "seed": 42, "ts": 1700000000}
{"type": "observation", "id": "ep_abc123", "grid": [...], "valid_actions": [...]}
{"type": "action", "id": "ep_abc123", "action": "place 1 5 7", "result": "success"}
{"type": "reasoning", "id": "ep_abc123", "thought": "Row 1 needs 7, only valid in col 5"}
{"type": "episode_end", "id": "ep_abc123", "status": "solved", "moves": 45, "efficiency": 0.92}
```

---

## Phase 5: Positioning & Ecosystem

**Goal:** Build credibility and community.

### 5.1 Leaderboard & Model Cards

```bash
# Submit benchmark run
puzzle-arcade-bench submit \
    --model "gpt-4-turbo" \
    --config benchmark-v1.yaml \
    --results results.json
```

**Leaderboard Tracks:**
- `solver-free` — Pure model reasoning
- `solver-assisted` — Model + hint budget
- `adversarial` — Red-team generated puzzles
- `curriculum` — Progressive difficulty completion

**Model Cards Generated from Runs:**

```yaml
model: gpt-4-turbo
benchmark: puzzle-arcade-v1
date: 2024-01-15
results:
  sudoku_medium:
    solve_rate: 0.94
    avg_steps: 47.2
    efficiency: 0.89
  kenken_hard:
    solve_rate: 0.76
    avg_steps: 23.1
    efficiency: 0.82
```

### 5.2 Benchmark Packs

Versioned, citable puzzle sets for research.

```
benchmarks/
  reasoning-v1/
    manifest.json         # Metadata, seeds, expected difficulty
    baseline-solver.json  # CP-SAT reference metrics
    baseline-gpt4.json    # GPT-4 baseline (optional)
    puzzles/
      sudoku-easy-001.json
      sudoku-easy-002.json
      ...
```

**Citation Format:**
```
@misc{puzzle-arcade-reasoning-v1,
  title={Puzzle Arcade Reasoning Benchmark v1},
  author={...},
  year={2024},
  url={https://github.com/...}
}
```

### 5.3 Puzzle Authoring Toolkit

Let others extend safely — turn Puzzle Arcade into a **platform**.

**Puzzle DSL:**

```yaml
# custom_puzzle.yaml
name: "My Custom Logic Puzzle"
type: grid
size: 6x6
constraints:
  - type: all_different
    scope: rows
  - type: all_different
    scope: columns
  - type: sum_equals
    regions: [[0,0], [0,1], [1,0]]
    target: 10
generator:
  method: constraint_propagation
  difficulty_scaling:
    easy: {given_ratio: 0.5}
    hard: {given_ratio: 0.25}
```

**Toolkit Features:**
- Validation checks (solvability, uniqueness)
- Difficulty estimators
- Automated test generation
- Solver integration

---

## Phase 6: Curriculum & Learning Paths

**Goal:** Enable progressive difficulty for education and research.

### 6.1 Puzzle Curriculum Graph

Define progression dependencies based on constraint concepts.

```yaml
curriculum:
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

    - name: "multi-constraint"
      requires: ["arithmetic", "connectivity"]
      games: [einstein:medium, logic_grid:hard]
      concepts: ["multi_attribute_deduction", "complex_inference"]
```

### 6.2 Skill Ladder API

```python
from puzzle_arcade import Curriculum

curriculum = Curriculum.load("reasoning-v1")

# Get next appropriate puzzle for agent's skill level
next_puzzle = curriculum.next_for_agent(
    agent_profile={"solved": ["sudoku:easy", "binary:easy"]},
    strategy="zone_of_proximal_development"
)
```

---

## Implementation Priority

### Immediate (v0.6) — High Impact, Medium Effort

| Task | Effort | Impact | Notes |
|------|--------|--------|-------|
| Standardised scoring schema | Medium | **Very High** | Unlocks benchmarking |
| Strict vs Natural modes | Low | High | Easy win for robustness testing |
| Solver-allowed flag | Low | High | First-class experimental variable |
| Step-level ground truth | Medium | **Very High** | Rare and valuable |

### Near-term (v0.7) — Research Infrastructure

| Task | Effort | Impact | Notes |
|------|--------|--------|-------|
| JSON protocol mode | Medium | High | Better agent integration |
| RL-ready API | High | **Very High** | Opens RL research |
| Episode trace logging | Low | Medium | Enables offline analysis |
| Solver comparison mode | Medium | High | Key differentiator |

### Future (v1.0) — Platform & Community

| Task | Effort | Impact | Notes |
|------|--------|--------|-------|
| Adversarial puzzles | High | High | Unique capability |
| Collaborative solving | High | High | Aligns with MCP work |
| Benchmark packs | Medium | High | Research credibility |
| Puzzle authoring DSL | High | Medium | Platform play |
| Leaderboard | Medium | Medium | Community building |

---

## What We're NOT Prioritising

These don't differentiate the project:

- Fancy UIs (we have telnet, that's the point)
- Human gameplay polish
- Visual themes
- Random puzzle dumping without structure
- Mobile apps

---

## Success Metrics

The roadmap succeeds when:

**Already Done:**
- [x] Humans can `telnet localhost 8023` and play any of 24 puzzles
- [x] Humans can share seeds to challenge friends
- [x] Any puzzle can be replayed with same seed
- [x] Every game has constraint_types and business_analogies
- [x] Agent mode provides structured, parseable output
- [x] Evaluation harness can batch-run episodes

**Phase 1-2 Success:**
- [ ] Every episode produces comparable efficiency score
- [ ] Solver usage is a tracked experimental variable
- [ ] Step-level ground truth available for all puzzles
- [ ] Strict/natural modes test robustness

**Phase 3-4 Success:**
- [ ] Gymnasium-compatible API works with standard RL libraries
- [ ] Adversarial puzzles stress-test agent robustness
- [ ] Synthetic datasets generated for fine-tuning
- [ ] Traces exportable for offline analysis

**Phase 5-6 Success:**
- [ ] Published benchmark packs cited in papers
- [ ] Leaderboard with multiple model submissions
- [ ] Curriculum enables progressive agent training
- [ ] External contributors creating puzzles via DSL

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

This roadmap aligns with:

- **chuk-mcp-solver** — CP-SAT solver as MCP tool (solver-assisted mode)
- **mcp-cli** — Agent orchestration (collaborative solving)
- **Training infrastructure** — Dataset generation feeds fine-tuning pipelines
