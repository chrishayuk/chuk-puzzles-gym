"""Graph Coloring puzzle game implementation."""

from collections import deque
from typing import Any

from ...models import DifficultyLevel, DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import GraphColoringConfig

COLOR_NAMES = ["Red", "Blue", "Green", "Yellow", "Orange", "Purple", "Cyan", "Magenta"]


class GraphColoringGame(PuzzleGame):
    """Graph Coloring puzzle - assign colors to nodes with no adjacent conflicts.

    Rules:
    - A graph has N nodes connected by edges
    - Assign one of K colors to each node
    - No two adjacent (connected) nodes may share the same color
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        super().__init__(difficulty, seed, **kwargs)
        self.config = GraphColoringConfig.from_difficulty(self.difficulty)
        self.num_nodes = self.config.num_nodes
        self.num_colors = self.config.num_colors
        self.edges: list[tuple[int, int]] = []
        self.adjacency: dict[int, set[int]] = {}
        self.coloring: dict[int, int] = {}  # Player's assignment: node -> color (0=uncolored)
        self.solution: dict[int, int] = {}
        self.initial_coloring: dict[int, int] = {}  # Pre-colored nodes
        # Grid representation for server compatibility (adjacency matrix)
        self.grid: list[list[int]] = []

    @property
    def name(self) -> str:
        return "Graph Coloring"

    @property
    def description(self) -> str:
        return "Color graph nodes so no adjacent nodes share a color"

    @property
    def constraint_types(self) -> list[str]:
        return ["graph_coloring", "inequality", "global_constraint"]

    @property
    def business_analogies(self) -> list[str]:
        return ["frequency_assignment", "exam_timetabling", "register_allocation", "zone_planning"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        return {
            "reasoning_type": "deductive",
            "search_space": "exponential",
            "constraint_density": "moderate",
        }

    @property
    def complexity_metrics(self) -> dict[str, int | float]:
        uncolored = sum(1 for n in range(1, self.num_nodes + 1) if self.coloring.get(n, 0) == 0)
        return {
            "variable_count": self.num_nodes,
            "constraint_count": len(self.edges),
            "domain_size": self.num_colors,
            "branching_factor": self.num_colors,
            "empty_cells": uncolored,
        }

    @property
    def difficulty_profile(self) -> DifficultyProfile:
        profiles = {
            DifficultyLevel.EASY: DifficultyProfile(
                logic_depth=2, branching_factor=3.0, state_observability=1.0, constraint_density=0.5
            ),
            DifficultyLevel.MEDIUM: DifficultyProfile(
                logic_depth=4, branching_factor=4.0, state_observability=1.0, constraint_density=0.5
            ),
            DifficultyLevel.HARD: DifficultyProfile(
                logic_depth=6, branching_factor=4.0, state_observability=1.0, constraint_density=0.6
            ),
        }
        return profiles[self.difficulty]

    @property
    def optimal_steps(self) -> int | None:
        initial_colored = len(self.initial_coloring)
        return self.num_nodes - initial_colored

    def _ensure_connected(self) -> None:
        """Add edges to make the graph connected if needed."""
        # Find connected components using BFS
        visited: set[int] = set()
        components: list[set[int]] = []

        for node in range(1, self.num_nodes + 1):
            if node in visited:
                continue
            component: set[int] = set()
            queue = deque([node])
            while queue:
                n = queue.popleft()
                if n in visited:
                    continue
                visited.add(n)
                component.add(n)
                for neighbor in self.adjacency.get(n, set()):
                    if neighbor not in visited:
                        queue.append(neighbor)
            components.append(component)

        # Connect components by adding edges between them
        for i in range(1, len(components)):
            # Pick a node from each component
            node_a = self._rng.choice(list(components[i - 1]))
            node_b = self._rng.choice(list(components[i]))
            # Ensure different colors for the edge
            if self.solution[node_a] == self.solution[node_b]:
                # Swap one node's color with an unused color
                for color in range(1, self.num_colors + 1):
                    if color != self.solution[node_a]:
                        conflict = False
                        for neighbor in self.adjacency.get(node_b, set()):
                            if self.solution.get(neighbor, 0) == color:
                                conflict = True
                                break
                        if not conflict:
                            self.solution[node_b] = color
                            break

            edge = (min(node_a, node_b), max(node_a, node_b))
            if edge not in set(self.edges):
                self.edges.append(edge)
                self.adjacency.setdefault(node_a, set()).add(node_b)
                self.adjacency.setdefault(node_b, set()).add(node_a)
            # Merge components
            components[i] = components[i] | components[i - 1]

    async def generate_puzzle(self) -> None:
        """Generate a graph coloring puzzle."""
        n = self.num_nodes
        k = self.num_colors
        density = self.config.edge_density

        # Assign each node a random color (guarantees k-colorability)
        self.solution = {}
        for node in range(1, n + 1):
            self.solution[node] = self._rng.randint(1, k)

        # Generate edges: only between differently colored nodes
        self.edges = []
        self.adjacency = {node: set() for node in range(1, n + 1)}
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                if self.solution[i] != self.solution[j]:
                    if self._rng.random() < density:
                        self.edges.append((i, j))
                        self.adjacency[i].add(j)
                        self.adjacency[j].add(i)

        # Ensure graph is connected
        self._ensure_connected()

        # Pre-color some nodes based on difficulty
        pre_color_map = {
            DifficultyLevel.EASY: 2,
            DifficultyLevel.MEDIUM: 1,
            DifficultyLevel.HARD: 0,
        }
        num_pre = min(pre_color_map[self.difficulty], n)
        nodes = list(range(1, n + 1))
        self._rng.shuffle(nodes)
        self.initial_coloring = {}
        for node in nodes[:num_pre]:
            self.initial_coloring[node] = self.solution[node]

        # Initialize player coloring with pre-colored nodes
        self.coloring = dict.fromkeys(range(1, n + 1), 0)
        for node, color in self.initial_coloring.items():
            self.coloring[node] = color

        # Build adjacency matrix as grid for server compatibility
        self.grid = [[0] * n for _ in range(n)]
        for i, j in self.edges:
            self.grid[i - 1][j - 1] = 1
            self.grid[j - 1][i - 1] = 1

        self.game_started = True

    async def validate_move(self, node: int, color: int) -> MoveResult:
        """Validate assigning a color to a node.

        Args:
            node: Node ID (1-indexed)
            color: Color number (1-K) or 0 to clear
        """
        if not (1 <= node <= self.num_nodes):
            self.record_move((node,), False)
            return MoveResult(success=False, message=f"Node must be between 1 and {self.num_nodes}.")

        if node in self.initial_coloring:
            self.record_move((node,), False)
            return MoveResult(success=False, message="Cannot modify a pre-colored node.")

        if color == 0:
            self.coloring[node] = 0
            self.record_move((node,), True)
            return MoveResult(success=True, message=f"Cleared color from node {node}.", state_changed=True)

        if not (1 <= color <= self.num_colors):
            self.record_move((node,), False)
            return MoveResult(
                success=False,
                message=f"Color must be between 1 and {self.num_colors} ({', '.join(COLOR_NAMES[: self.num_colors])}).",
            )

        # Check for conflicts with adjacent nodes
        for neighbor in self.adjacency.get(node, set()):
            if self.coloring.get(neighbor, 0) == color:
                self.record_move((node,), False)
                color_name = COLOR_NAMES[color - 1] if color <= len(COLOR_NAMES) else str(color)
                return MoveResult(
                    success=False,
                    message=f"Conflict: adjacent node {neighbor} already has color {color_name}.",
                )

        self.coloring[node] = color
        self.record_move((node,), True)
        color_name = COLOR_NAMES[color - 1] if color <= len(COLOR_NAMES) else str(color)
        return MoveResult(success=True, message=f"Colored node {node} with {color_name}.", state_changed=True)

    def is_complete(self) -> bool:
        """Check if all nodes are colored with no conflicts."""
        # All nodes must be colored
        for node in range(1, self.num_nodes + 1):
            if self.coloring.get(node, 0) == 0:
                return False

        # No adjacent nodes share a color
        for i, j in self.edges:
            if self.coloring[i] == self.coloring[j]:
                return False

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Suggest a node to color."""
        if not self.can_use_hint():
            return None
        for node in range(1, self.num_nodes + 1):
            if self.coloring.get(node, 0) == 0:
                color = self.solution[node]
                color_name = COLOR_NAMES[color - 1] if color <= len(COLOR_NAMES) else str(color)
                return (
                    (node, color),
                    f"Try coloring node {node} with {color_name} (color {color}).",
                )
        return None

    def render_grid(self) -> str:
        """Render the graph structure and current coloring."""
        lines = []
        lines.append(f"Graph: {self.num_nodes} nodes, {len(self.edges)} edges, {self.num_colors} colors")
        lines.append("")

        # Color palette
        palette = []
        for i in range(1, self.num_colors + 1):
            name = COLOR_NAMES[i - 1] if i <= len(COLOR_NAMES) else str(i)
            palette.append(f"{i}={name}")
        lines.append("Colors: " + ", ".join(palette))
        lines.append("")

        # Node coloring status
        lines.append("Nodes:")
        for node in range(1, self.num_nodes + 1):
            color = self.coloring.get(node, 0)
            neighbors = sorted(self.adjacency.get(node, set()))
            adj_str = ", ".join(str(n) for n in neighbors)
            if color > 0:
                color_name = COLOR_NAMES[color - 1] if color <= len(COLOR_NAMES) else str(color)
                prefix = "*" if node in self.initial_coloring else " "
                lines.append(f"  {prefix}{node:2d}: [{color_name:>7s}]  adj: {adj_str}")
            else:
                lines.append(f"   {node:2d}: [       ]  adj: {adj_str}")

        colored = sum(1 for n in range(1, self.num_nodes + 1) if self.coloring.get(n, 0) > 0)
        lines.append(f"\nColored: {colored}/{self.num_nodes}")

        return "\n".join(lines)

    def get_stats(self) -> str:
        """Get current game statistics."""
        colored = sum(1 for n in range(1, self.num_nodes + 1) if self.coloring.get(n, 0) > 0)
        return f"Moves: {self.moves_made} | Colored: {colored}/{self.num_nodes} | Edges: {len(self.edges)} | Seed: {self.seed}"

    def get_rules(self) -> str:
        return (
            f"GRAPH COLORING ({self.num_nodes} nodes, {self.num_colors} colors)\n"
            "Assign a color to each node in the graph.\n"
            "No two connected (adjacent) nodes may share the same color.\n"
            "Pre-colored nodes (marked with *) cannot be changed."
        )

    def get_commands(self) -> str:
        color_map = ", ".join(f"{i + 1}={COLOR_NAMES[i]}" for i in range(self.num_colors))
        return (
            "Commands:\n"
            f"  place <node> <color>  - Color a node (number or name)\n"
            f"  Colors: {color_map}\n"
            "  clear <node>          - Remove color from a node\n"
            "  hint                  - Get a hint\n"
            "  check                 - Check if solved\n"
            "  show                  - Show current state\n"
            "  menu                  - Return to menu"
        )
