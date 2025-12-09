"""Einstein's Puzzle (Zebra Puzzle) game implementation."""

import random
from typing import Any

from ..base.puzzle_game import PuzzleGame


class EinsteinGame(PuzzleGame):
    """Einstein's Puzzle (also known as Zebra Puzzle).

    A classic logic puzzle with 5 houses and 5 attributes each.
    Uses complex deduction with multiple constraint types.
    Perfect for testing AI reasoning capabilities.
    """

    def __init__(self, difficulty: str = "easy"):
        """Initialize a new Einstein's Puzzle game.

        Args:
            difficulty: Game difficulty level (easy/medium/hard)
        """
        super().__init__(difficulty)

        # 5 houses with 5 attributes each
        self.num_houses = 5

        # Attributes
        self.colors = ["Red", "Green", "Blue", "Yellow", "White"]
        self.nationalities = ["British", "Swedish", "Danish", "Norwegian", "German"]
        self.drinks = ["Tea", "Coffee", "Milk", "Beer", "Water"]
        self.smokes = ["Pall Mall", "Dunhill", "Blend", "Blue Master", "Prince"]
        self.pets = ["Dog", "Bird", "Cat", "Horse", "Fish"]

        # Player's assignments: house -> {color, nationality, drink, smoke, pet}
        self.assignments: list[dict[str, str | None]] = [
            {"color": None, "nationality": None, "drink": None, "smoke": None, "pet": None}
            for _ in range(self.num_houses)
        ]

        # Solution
        self.solution: list[dict[str, str]] = []

        # Clues
        self.clues: list[str] = []

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Einstein's Puzzle"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Classic logic deduction - who owns the fish?"

    def generate_puzzle(self) -> None:
        """Generate a new Einstein's Puzzle."""
        # Generate a random valid solution
        solution_attrs = {
            "color": self.colors.copy(),
            "nationality": self.nationalities.copy(),
            "drink": self.drinks.copy(),
            "smoke": self.smokes.copy(),
            "pet": self.pets.copy(),
        }

        # Shuffle each attribute list
        for attr_list in solution_attrs.values():
            random.shuffle(attr_list)

        # Create solution
        self.solution = []
        for i in range(self.num_houses):
            self.solution.append(
                {
                    "color": solution_attrs["color"][i],
                    "nationality": solution_attrs["nationality"][i],
                    "drink": solution_attrs["drink"][i],
                    "smoke": solution_attrs["smoke"][i],
                    "pet": solution_attrs["pet"][i],
                }
            )

        # Generate clues based on solution
        self.clues = self._generate_clues()

        # Initialize player grid
        self.assignments = [
            {"color": None, "nationality": None, "drink": None, "smoke": None, "pet": None}
            for _ in range(self.num_houses)
        ]

        self.moves_made = 0
        self.game_started = True

    def _generate_clues(self) -> list[str]:
        """Generate clues based on the solution."""
        clues = []

        # Find positions of each attribute
        def find_house(attr_type: str, value: str) -> int:
            for i, house in enumerate(self.solution):
                if house[attr_type] == value:
                    return i
            return -1

        # Always include these starter clues
        norwegian_house = find_house("nationality", "Norwegian")
        milk_house = find_house("drink", "Milk")

        clues.append(f"1. The Norwegian lives in house {norwegian_house + 1}")
        clues.append(f"2. Milk is drunk in house {milk_house + 1}")

        # Add attribute-to-attribute clues
        clue_num = 3

        # Same house clues
        for i in range(self.num_houses):
            house = self.solution[i]

            # Color-Nationality
            if random.random() < 0.4:
                clues.append(f"{clue_num}. The {house['nationality']} lives in the {house['color']} house")
                clue_num += 1

            # Nationality-Drink
            if random.random() < 0.4:
                clues.append(f"{clue_num}. The {house['nationality']} drinks {house['drink']}")
                clue_num += 1

            # Smoke-Pet
            if random.random() < 0.4:
                clues.append(f"{clue_num}. The person who smokes {house['smoke']} keeps {house['pet']}s")
                clue_num += 1

        # Neighbor clues
        for i in range(self.num_houses - 1):
            house1 = self.solution[i]
            house2 = self.solution[i + 1]

            if random.random() < 0.3:
                clues.append(f"{clue_num}. The {house1['color']} house is next to the {house2['color']} house")
                clue_num += 1

        # Limit number of clues
        max_clues = {"easy": 12, "medium": 10, "hard": 8}.get(self.difficulty, 12)
        return clues[:max_clues]

    def validate_move(self, house: int, attribute: str, value: str) -> tuple[bool, str]:
        """Assign an attribute to a house.

        Args:
            house: House number (1-indexed, user-facing)
            attribute: Attribute type (color, nationality, drink, smoke, pet)
            value: Attribute value

        Returns:
            Tuple of (success, message)
        """
        # Convert to 0-indexed
        house -= 1

        # Validate house number
        if not (0 <= house < self.num_houses):
            return False, f"Invalid house number. Use 1-{self.num_houses}."

        # Normalize attribute and value
        attribute = attribute.lower()
        value = value.title()  # Use title() to handle multi-word values like "Pall Mall"

        # Validate attribute type
        valid_attrs = {
            "color": self.colors,
            "nationality": self.nationalities,
            "drink": self.drinks,
            "smoke": self.smokes,
            "pet": self.pets,
        }

        if attribute not in valid_attrs:
            return False, f"Invalid attribute. Use: {', '.join(valid_attrs.keys())}"

        # Validate value
        if value not in valid_attrs[attribute]:
            return False, f"Invalid {attribute}. Choose from: {', '.join(valid_attrs[attribute])}"

        # Check if value is already assigned to another house
        for i, other_house in enumerate(self.assignments):
            if i != house and other_house.get(attribute) == value:
                return False, f"{value} is already assigned to house {i + 1}"

        # Check if this house already has a value for this attribute
        if self.assignments[house][attribute] is not None:
            old_value = self.assignments[house][attribute]
            self.assignments[house][attribute] = value
            self.moves_made += 1
            return True, f"Changed house {house + 1}'s {attribute} from {old_value} to {value}"

        # Assign the value
        self.assignments[house][attribute] = value
        self.moves_made += 1
        return True, f"Assigned {value} to house {house + 1}"

    def is_complete(self) -> bool:
        """Check if the puzzle is completely and correctly solved."""
        # All houses must have all attributes assigned
        for house in self.assignments:
            if any(value is None for value in house.values()):
                return False

        # Check if assignments match solution
        for i in range(self.num_houses):
            for attr in ["color", "nationality", "drink", "smoke", "pet"]:
                if self.assignments[i][attr] != self.solution[i][attr]:
                    return False

        return True

    def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None
        """
        # Find first unassigned attribute in solution
        for i in range(self.num_houses):
            for attr in ["color", "nationality", "drink", "smoke", "pet"]:
                if self.assignments[i][attr] != self.solution[i][attr]:
                    value = self.solution[i][attr]
                    hint_data = (i + 1, attr, value)
                    hint_message = f"Try assigning {value} to house {i + 1} as its {attr}"
                    return hint_data, hint_message

        return None

    def render_grid(self) -> str:
        """Render the current puzzle state as ASCII art.

        Returns:
            String representation of the puzzle
        """
        lines = []

        lines.append("Einstein's Puzzle - Who owns the fish?")
        lines.append("")

        # Houses table
        lines.append("House | Color   | Nationality | Drink  | Smoke       | Pet")
        lines.append("------+---------+-------------+--------+-------------+--------")

        for i in range(self.num_houses):
            house = self.assignments[i]
            color = house["color"] or "?"
            nationality = house["nationality"] or "?"
            drink = house["drink"] or "?"
            smoke = house["smoke"] or "?"
            pet = house["pet"] or "?"

            lines.append(f"  {i + 1}   | {color:<7s} | {nationality:<11s} | {drink:<6s} | {smoke:<11s} | {pet:<6s}")

        lines.append("")
        lines.append("Clues:")
        for clue in self.clues:
            lines.append(f"  {clue}")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Einstein's Puzzle.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return """EINSTEIN'S PUZZLE RULES:
- There are 5 houses in a row
- Each house has a unique color, nationality, drink, smoke, and pet
- Use the clues to deduce which attribute belongs in which house
- No attribute can appear in more than one house
- All houses must have all 5 attributes assigned
- Question: WHO OWNS THE FISH?"""

    def get_commands(self) -> str:
        """Get the available commands for Einstein's Puzzle.

        Returns:
            Multi-line string describing available commands
        """
        return """EINSTEIN'S PUZZLE COMMANDS:
  assign <house> <attr> <value>  - Assign attribute (e.g., 'assign 1 color red')
                                   Attributes: color, nationality, drink, smoke, pet
  show                           - Display current assignments
  hint                           - Get a hint
  check                          - Check if solution is correct
  solve                          - Show the solution (ends game)
  menu                           - Return to game selection
  quit                           - Exit the server"""

    def get_stats(self) -> str:
        """Get current game statistics.

        Returns:
            String with game stats
        """
        assigned = sum(1 for house in self.assignments for value in house.values() if value is not None)
        total = self.num_houses * 5

        return f"Moves: {self.moves_made} | Assigned: {assigned}/{total} | Clues: {len(self.clues)}"
