"""Logic Grid puzzle game implementation."""

import random
from typing import Any

from ..base.puzzle_game import PuzzleGame


class LogicGridGame(PuzzleGame):
    """Logic Grid puzzle game (like Einstein's Riddle or Zebra Puzzle).

    Use logical deduction to determine which attributes belong together.
    Each person/house has exactly one of each attribute type.
    """

    def __init__(self, difficulty: str = "easy"):
        """Initialize a new Logic Grid game.

        Args:
            difficulty: Game difficulty level (easy=3x3, medium=4x4, hard=5x5)
        """
        super().__init__(difficulty)

        # Number of items/people based on difficulty
        self.size = {"easy": 3, "medium": 4, "hard": 5}.get(difficulty, 3)

        # Categories and their values
        self.categories = {
            "person": ["Alice", "Bob", "Carol", "Dave", "Eve"][: self.size],
            "color": ["Red", "Blue", "Green", "Yellow", "Purple"][: self.size],
            "pet": ["Cat", "Dog", "Bird", "Fish", "Rabbit"][: self.size],
            "drink": ["Coffee", "Tea", "Juice", "Water", "Milk"][: self.size],
        }

        # Solution: dict mapping person -> {category: value}
        self.solution: dict[str, dict[str, str]] = {}

        # Player grid: dict of (category1, value1, category2, value2) -> bool | None
        # True = definitely connected, False = definitely not connected, None = unknown
        self.player_grid: dict[tuple[str, str, str, str], bool | None] = {}

        # Clues: list of clue strings
        self.clues: list[str] = []

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Logic Grid"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Deductive reasoning puzzle - match attributes using logic"

    def _generate_solution(self) -> None:
        """Generate a random valid solution."""
        people = self.categories["person"]

        # Randomly assign each attribute to each person
        colors = self.categories["color"][:]
        pets = self.categories["pet"][:]
        drinks = self.categories["drink"][:]

        random.shuffle(colors)
        random.shuffle(pets)
        random.shuffle(drinks)

        self.solution = {}
        for i, person in enumerate(people):
            self.solution[person] = {
                "color": colors[i],
                "pet": pets[i],
                "drink": drinks[i],
            }

    def _generate_clues(self) -> None:
        """Generate clues from the solution."""
        self.clues = []
        people = self.categories["person"]

        # Generate direct association clues
        num_direct = self.size - 1
        for i in range(num_direct):
            person = people[i]
            attrs = self.solution[person]

            # Choose two attributes to reveal
            cat1, cat2 = random.sample(["color", "pet", "drink"], 2)
            clue = f"{person} has the {attrs[cat1]} {cat1} and drinks {attrs[cat2]}"
            self.clues.append(clue)

        # Generate relative/constraint clues
        for _ in range(self.size):
            p1, p2 = random.sample(people, 2)
            cat = random.choice(["color", "pet", "drink"])

            clue = f"{p1} does not have the {self.solution[p2][cat]} {cat}"
            self.clues.append(clue)

    def generate_puzzle(self) -> None:
        """Generate a new Logic Grid puzzle."""
        self._generate_solution()
        self._generate_clues()

        # Initialize player grid (all unknown)
        self.player_grid = {}

        self.moves_made = 0
        self.game_started = True

    def validate_move(self, cat1: str, val1: str, cat2: str, val2: str, state: bool) -> tuple[bool, str]:
        """Mark a connection in the logic grid.

        Args:
            cat1: First category
            val1: First value
            cat2: Second category
            val2: Second value
            state: True = connected, False = not connected

        Returns:
            Tuple of (success, message)
        """
        # Normalize categories
        cat1 = cat1.lower()
        cat2 = cat2.lower()

        # Validate categories
        if cat1 not in self.categories or cat2 not in self.categories:
            return False, f"Invalid category. Use: {', '.join(self.categories.keys())}"

        if cat1 == cat2:
            return False, "Cannot connect values from the same category"

        # Validate values
        if val1 not in self.categories[cat1]:
            return False, f"Invalid {cat1}. Choose from: {', '.join(self.categories[cat1])}"

        if val2 not in self.categories[cat2]:
            return False, f"Invalid {cat2}. Choose from: {', '.join(self.categories[cat2])}"

        # Store the connection (normalize order)
        key = (cat1, val1, cat2, val2) if cat1 < cat2 else (cat2, val2, cat1, val1)
        self.player_grid[key] = state
        self.moves_made += 1

        return True, f"Marked {val1} ({cat1}) and {val2} ({cat2}) as {'connected' if state else 'not connected'}"

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        # Check if player has correctly identified all connections
        for person in self.categories["person"]:
            attrs = self.solution[person]

            # Check person -> color
            key1 = ("color", attrs["color"], "person", person)
            key2 = ("person", person, "color", attrs["color"])
            if not self.player_grid.get(key1) and not self.player_grid.get(key2):
                return False

            # Check person -> pet
            key1 = ("person", person, "pet", attrs["pet"])
            key2 = ("pet", attrs["pet"], "person", person)
            if not self.player_grid.get(key1) and not self.player_grid.get(key2):
                return False

            # Check person -> drink
            key1 = ("drink", attrs["drink"], "person", person)
            key2 = ("person", person, "drink", attrs["drink"])
            if not self.player_grid.get(key1) and not self.player_grid.get(key2):
                return False

        return True

    def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        # Find a connection that hasn't been marked
        for person in self.categories["person"]:
            attrs = self.solution[person]

            for cat, val in attrs.items():
                key1 = (cat, val, "person", person)
                key2 = ("person", person, cat, val)

                if not self.player_grid.get(key1) and not self.player_grid.get(key2):
                    hint_data = (person, cat, val)
                    hint_message = f"{person} has the {val} {cat}"
                    return hint_data, hint_message

        return None

    def render_grid(self) -> str:
        """Render the current puzzle state.

        Returns:
            String representation of the clues and current deductions
        """
        lines = []

        lines.append("\n=== LOGIC GRID PUZZLE ===\n")

        # Show clues
        lines.append("CLUES:")
        for i, clue in enumerate(self.clues, 1):
            lines.append(f"  {i}. {clue}")

        lines.append("\nYOUR DEDUCTIONS:")
        if not self.player_grid:
            lines.append("  (none yet)")
        else:
            for (cat1, val1, cat2, val2), state in sorted(self.player_grid.items()):
                if state is True:
                    lines.append(f"  ✓ {val1} ({cat1}) ←→ {val2} ({cat2})")
                elif state is False:
                    lines.append(f"  ✗ {val1} ({cat1}) ←/→ {val2} ({cat2})")

        lines.append("\nCATEGORIES:")
        for cat, values in self.categories.items():
            lines.append(f"  {cat.capitalize()}: {', '.join(values)}")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Logic Grid.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return """LOGIC GRID RULES:
- Use logical deduction to match attributes
- Each person has exactly one color, one pet, and one drink
- No two people share the same attribute value
- Read the clues carefully and mark connections
- Mark connections as True (✓) or False (✗)
- Use elimination and deduction to solve"""

    def get_commands(self) -> str:
        """Get the available commands for Logic Grid.

        Returns:
            Multi-line string describing available commands
        """
        return """LOGIC GRID COMMANDS:
  connect <cat1> <val1> <cat2> <val2>
    - Mark that val1 and val2 are connected (belong to same person)
    - Example: 'connect person Alice color Red'

  exclude <cat1> <val1> <cat2> <val2>
    - Mark that val1 and val2 are NOT connected
    - Example: 'exclude person Bob pet Cat'

  show     - Display clues and deductions
  hint     - Get a hint
  check    - Check if puzzle is solved
  solve    - Show the solution (ends game)
  menu     - Return to game selection
  quit     - Exit the server"""

    def get_stats(self) -> str:
        """Get current game statistics.

        Returns:
            String with game stats
        """
        connections = sum(1 for v in self.player_grid.values() if v is True)
        exclusions = sum(1 for v in self.player_grid.values() if v is False)
        return f"Moves made: {self.moves_made} | Connections: {connections} | Exclusions: {exclusions}"
