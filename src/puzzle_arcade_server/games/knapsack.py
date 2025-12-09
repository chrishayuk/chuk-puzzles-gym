"""Knapsack optimization puzzle game implementation."""

import random
from typing import Any

from ..base.puzzle_game import PuzzleGame


class KnapsackGame(PuzzleGame):
    """Knapsack optimization puzzle game.

    Classic optimization problem: select items to maximize value
    while staying within weight capacity.
    Demonstrates objective optimization (not just constraint satisfaction).
    """

    def __init__(self, difficulty: str = "easy"):
        """Initialize a new Knapsack game.

        Args:
            difficulty: Game difficulty level (easy/medium/hard)
        """
        super().__init__(difficulty)

        # Difficulty affects number of items and complexity
        config = {
            "easy": {"num_items": 5, "capacity_factor": 0.6},
            "medium": {"num_items": 8, "capacity_factor": 0.5},
            "hard": {"num_items": 12, "capacity_factor": 0.4},
        }
        self.config = config.get(difficulty, config["easy"])

        self.num_items: int = int(self.config["num_items"])
        self.capacity_factor: float = float(self.config["capacity_factor"])

        # Item properties
        self.items: list[dict[str, str | int]] = []
        self.capacity: int = 0

        # Player's selection (True = selected, False = not selected)
        self.selection: list[bool] = []

        # Solution tracking
        self.optimal_value = 0
        self.optimal_selection: list[bool] = []

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Knapsack"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Optimize item selection to maximize value within weight limit"

    def generate_puzzle(self) -> None:
        """Generate a new Knapsack puzzle."""
        # Generate random items with weights and values
        item_names = [
            "Gold Bar",
            "Diamond",
            "Ruby",
            "Emerald",
            "Sapphire",
            "Platinum",
            "Silver",
            "Jade",
            "Opal",
            "Pearl",
            "Topaz",
            "Amethyst",
            "Garnet",
            "Quartz",
            "Obsidian",
        ]

        self.items = []
        total_weight = 0

        for i in range(self.num_items):
            name = item_names[i] if i < len(item_names) else f"Item {i + 1}"
            weight = random.randint(1, 10)
            # Value roughly correlates with weight but with variance
            value = random.randint(weight * 5, weight * 15)

            self.items.append({"name": name, "weight": weight, "value": value})
            total_weight += weight

        # Set capacity as a fraction of total weight
        self.capacity = int(total_weight * self.capacity_factor)
        if self.capacity < 5:
            self.capacity = 5  # Minimum capacity

        # Initialize empty selection
        self.selection = [False] * self.num_items

        # Calculate optimal solution using dynamic programming
        self._solve_optimal()

        self.moves_made = 0
        self.game_started = True

    def _solve_optimal(self) -> None:
        """Solve the knapsack problem optimally using dynamic programming."""
        n = len(self.items)
        capacity = self.capacity

        # DP table: dp[i][w] = max value using first i items with capacity w
        dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]

        # Fill the DP table
        for i in range(1, n + 1):
            item = self.items[i - 1]
            weight = int(item["weight"])
            value = int(item["value"])

            for w in range(capacity + 1):
                # Don't take item i
                dp[i][w] = dp[i - 1][w]

                # Take item i if it fits
                if weight <= w:
                    dp[i][w] = max(dp[i][w], dp[i - 1][w - weight] + value)

        # Backtrack to find which items to select
        self.optimal_value = dp[n][capacity]
        self.optimal_selection = [False] * n

        w = capacity
        for i in range(n, 0, -1):
            if dp[i][w] != dp[i - 1][w]:
                self.optimal_selection[i - 1] = True
                w -= int(self.items[i - 1]["weight"])

    def validate_move(self, action: str, item_index: int) -> tuple[bool, str]:
        """Toggle item selection.

        Args:
            action: 'select' or 'deselect'
            item_index: Item number (1-indexed, user-facing)

        Returns:
            Tuple of (success, message)
        """
        # Convert to 0-indexed
        item_index -= 1

        # Validate item index
        if not (0 <= item_index < len(self.items)):
            return False, f"Invalid item number. Use 1-{len(self.items)}."

        action = action.lower()

        if action == "select":
            if self.selection[item_index]:
                return False, "Item is already selected."

            # Check if adding this item exceeds capacity
            current_weight = self._get_current_weight()
            item_weight = int(self.items[item_index]["weight"])

            if current_weight + item_weight > self.capacity:
                return (
                    False,
                    f"Cannot select - would exceed capacity! (Current: {current_weight}, Item: {item_weight}, Capacity: {self.capacity})",
                )

            self.selection[item_index] = True
            self.moves_made += 1
            item_name = self.items[item_index]["name"]
            return True, f"Selected {item_name} (weight: {item_weight}, value: ${self.items[item_index]['value']})"

        elif action == "deselect":
            if not self.selection[item_index]:
                return False, "Item is not currently selected."

            self.selection[item_index] = False
            self.moves_made += 1
            item_name = self.items[item_index]["name"]
            return True, f"Deselected {item_name}"

        else:
            return False, "Invalid action. Use 'select' or 'deselect'."

    def _get_current_weight(self) -> int:
        """Calculate total weight of currently selected items."""
        return sum(int(self.items[i]["weight"]) for i in range(len(self.items)) if self.selection[i])

    def _get_current_value(self) -> int:
        """Calculate total value of currently selected items."""
        return sum(int(self.items[i]["value"]) for i in range(len(self.items)) if self.selection[i])

    def is_complete(self) -> bool:
        """Check if the solution is optimal.

        For optimization problems, we consider it complete if the player
        has achieved the optimal value.
        """
        return self._get_current_value() == self.optimal_value

    def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None
        """
        # Suggest selecting an item that's in the optimal solution but not selected
        for i in range(len(self.items)):
            if self.optimal_selection[i] and not self.selection[i]:
                hint_data = ("select", i + 1)
                hint_message = f"Try selecting item {i + 1} ({self.items[i]['name']})"
                return hint_data, hint_message

        # Suggest deselecting an item that's not in the optimal solution but is selected
        for i in range(len(self.items)):
            if not self.optimal_selection[i] and self.selection[i]:
                hint_data = ("deselect", i + 1)
                hint_message = f"Try deselecting item {i + 1} ({self.items[i]['name']})"
                return hint_data, hint_message

        return None

    def render_grid(self) -> str:
        """Render the current game state as ASCII art.

        Returns:
            String representation of the puzzle
        """
        lines = []

        lines.append(f"Knapsack Capacity: {self.capacity} kg")
        lines.append(f"Current Weight: {self._get_current_weight()} kg")
        lines.append(f"Current Value: ${self._get_current_value()}")
        lines.append(f"Optimal Value: ${self.optimal_value}")
        lines.append("")

        # Items table
        lines.append("  # | Item          | Weight | Value  | Selected")
        lines.append("  --+---------------+--------+--------+---------")

        for i, item in enumerate(self.items):
            selected = "✓" if self.selection[i] else " "
            lines.append(
                f"  {i + 1:2d} | {item['name']:<13s} | {item['weight']:4d}kg | ${item['value']:5d} |    {selected}"
            )

        lines.append("")
        lines.append(f"Space Remaining: {self.capacity - self._get_current_weight()} kg")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Knapsack.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return f"""KNAPSACK RULES:
- Select items to maximize total value
- Cannot exceed capacity of {self.capacity}kg
- Each item can be selected at most once
- Goal: Achieve optimal value of ${self.optimal_value}
- This is an OPTIMIZATION problem - find the best solution!"""

    def get_commands(self) -> str:
        """Get the available commands for Knapsack.

        Returns:
            Multi-line string describing available commands
        """
        return """KNAPSACK COMMANDS:
  select <number>    - Select an item (e.g., 'select 3')
  deselect <number>  - Deselect an item (e.g., 'deselect 2')
  show               - Display current selection
  hint               - Get a hint for optimization
  check              - Check if you've found the optimal solution
  solve              - Show the optimal solution (ends game)
  menu               - Return to game selection
  quit               - Exit the server"""

    def get_stats(self) -> str:
        """Get current game statistics.

        Returns:
            String with game stats
        """
        current_value = self._get_current_value()
        current_weight = self._get_current_weight()
        optimality = (current_value / self.optimal_value * 100) if self.optimal_value > 0 else 0

        return f"Moves: {self.moves_made} | Value: ${current_value}/${self.optimal_value} ({optimality:.0f}%) | Weight: {current_weight}/{self.capacity}kg"
