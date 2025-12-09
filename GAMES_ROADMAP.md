# Puzzle Arcade Server - Games Roadmap

This document outlines the current and planned puzzle games for the Puzzle Arcade Server, organized by the constraint solving features they demonstrate.

## Currently Implemented ✅

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

**Total Implemented: 16 games**

---

## Planned Games - Future Phases

### Advanced CP-SAT Puzzles

#### **Masyu**
- **Constraint Type**: Loop paths, directional constraints
- **Grid Size**: 6×6 to 10×10
- **Demonstrates**:
  - Edge-based loop constraints
  - Forced turns through white circles
  - Forced straight through black circles
  - Similar to Slitherlink with different rules
- **Solver Value**: ⭐⭐⭐⭐ (Directional constraints)
- **Implementation Complexity**: Medium-High

#### **Hitori**
- **Constraint Type**: Elimination + adjacency
- **Grid Size**: 6×6 to 10×10
- **Demonstrates**:
  - Cell elimination (shaded/visible)
  - AllDifferent on visible cells per row/col
  - No adjacent shaded cells
  - All visible cells connected
- **Solver Value**: ⭐⭐⭐ (Hybrid constraints)
- **Implementation Complexity**: Medium

### Optimization Challenges

#### **Bin Packing**
- **Type**: Assignment optimization
- **Demonstrates**:
  - Item-to-bin assignment
  - Capacity constraints per bin
  - **Objective**: Minimize number of bins
- **Solver Value**: ⭐⭐⭐⭐ (Resource allocation)
- **Implementation Complexity**: Medium
- **Example**:
  ```
  Items: 6, 5, 4, 3, 3, 2, 2
  Bin capacity: 10
  Goal: Use minimum bins
  ```

### Extended Variants

**Larger/Harder Variants of Existing Games:**

- **Latin Squares** (generalized Sudoku, N×N)
- **Magic Squares** (sum constraints everywhere)
- **Futoshiki XL** (9×9 or 12×12 versions)
- **Nonogram XL** (15×15+ grids)
- **Calcudoku** (KenKen variant with more operators)
- **Kakurasu** (weighted row/col sums, binary grid)

### Logic/Detective Puzzles

**Extended Logic Grid Variants:**

- **Murder Mystery** (who, where, weapon, time)
- **Logic Detective** (solve crimes with clues)
- **Office Assignment** (people, desks, departments, floors)

These demonstrate **business rule reasoning** - showing how the solver can handle real-world logical deduction problems.

---

## Current Menu Organization

The game menu is now organized into four categories showcasing different solver capabilities:

```
==================================================
       WELCOME TO THE PUZZLE ARCADE!
==================================================

CLASSIC LOGIC PUZZLES (7 games)
  1) Sudoku          - 9×9 AllDifferent constraints
  2) KenKen          - Arithmetic cages + logic
  3) Kakuro          - Crossword math sums
  4) Binary Puzzle   - Adjacency + parity rules
  5) Futoshiki       - Inequality constraints
  6) Nonogram        - Line clue deduction
  7) Logic Grid      - Category associations

ADVANCED CP-SAT PUZZLES (4 games)
  8) Killer Sudoku   - Hybrid constraints
  9) Lights Out      - Boolean SAT solving
 10) Mastermind      - Deductive reasoning
 11) Slitherlink     - Global loop constraints

OPTIMIZATION CHALLENGES (2 games)
 12) Knapsack        - Maximize value
 13) Task Scheduler  - Minimize completion time

ADVANCED REASONING PUZZLES (3 games)
 14) Nurikabe        - Island and sea puzzle
 15) Einstein's Puzzle - Who owns the fish?
 16) Minesweeper     - Find all mines
==================================================
```

---

## Future Implementation Priority

### Next Phase: Additional Puzzles
1. **Bin Packing** - Resource allocation optimization
2. **Masyu** - Loop puzzle variations
3. **Hitori** - Elimination logic puzzles
4. **Extended Variants** - Larger versions of existing games
5. **Logic Grid Scenarios** - More detective-style puzzles

---

## Constraint Mapping Reference

For each game type, here's how they map to CP-SAT JSON models:

### Binary/Boolean Games
- **Variables**: Boolean (0/1) or Binary choices
- **Constraints**: Boolean logic, XOR, adjacency
- **Examples**: Lights Out, Binary Puzzle, Nonogram

### AllDifferent + Arithmetic
- **Variables**: Integer domains (1-N)
- **Constraints**: AllDifferent, Sum, Product, Division
- **Examples**: Sudoku, KenKen, Kakuro, Killer Sudoku

### Graph/Loop Constraints
- **Variables**: Edge states (on/off)
- **Constraints**: Connectivity, degree constraints, loops
- **Examples**: Slitherlink, Masyu

### Optimization Problems
- **Variables**: Integer choices or assignments
- **Constraints**: Capacity, time, dependencies
- **Objective**: Minimize or maximize a function
- **Examples**: Scheduler, Knapsack, Bin Packing

### Deduction/Logic
- **Variables**: Categorical assignments
- **Constraints**: Implication, exclusion, association
- **Examples**: Mastermind, Logic Grid, Murder Mystery

---

## Success Metrics - Current Status

The Puzzle Arcade Server now achieves:

✅ **All major CP-SAT constraint types** demonstrated
✅ **Optimization capabilities** (Knapsack, Task Scheduler)
✅ **Real-world applications** (scheduling, resource allocation)
✅ **SAT, CSP, and optimization** problem classes covered
✅ **Probabilistic reasoning** (Minesweeper)
✅ **Temporal reasoning** (Task Scheduler)
✅ **Connectivity constraints** (Nurikabe, Slitherlink)
✅ **Comprehensive constraint solver showcase** with 16 diverse games

---

## Contributing

Want to add a new game? Follow this process:

1. Choose from the roadmap or propose a new puzzle
2. Identify the constraint types it demonstrates
3. Implement the game extending `PuzzleGame` base class
4. Add comprehensive tests (>90% coverage)
5. Document the constraint mapping
6. Submit a PR!

See [README.md](README.md) for implementation details.

---

**Last Updated**: December 2025
**Current Games**: 16 implemented
**Future Expansion**: 5+ additional games planned
**Status**: All major constraint types now covered! 🎉
