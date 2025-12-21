"""Logic Grid puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import LogicGridConfig
from .constants import CATEGORIES, COLORS, DRINKS, PEOPLE, PETS
from .models import LogicGridCategories, PersonAttributes


class LogicGridGame(PuzzleGame):
    """Logic Grid puzzle game (like Einstein's Riddle or Zebra Puzzle).

    Use logical deduction to determine which attributes belong together.
    Each person/house has exactly one of each attribute type.
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Logic Grid game.

        Args:
            difficulty: Game difficulty level (easy=3x3, medium=4x4, hard=5x5)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Use pydantic config based on difficulty
        self.config = LogicGridConfig.from_difficulty(self.difficulty)
        self.num_people = self.config.num_people

        # Categories using Pydantic model with constants
        self.categories = LogicGridCategories(
            person=PEOPLE[: self.num_people],
            color=COLORS[: self.num_people],
            pet=PETS[: self.num_people],
            drink=DRINKS[: self.num_people],
        )

        # Solution: dict mapping person -> PersonAttributes
        self.solution: dict[str, PersonAttributes] = {}

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

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return [
            "all_different_per_attribute",
            "cross_attribute_links",
            "transitive_closure",
            "bi-directional_inference",
        ]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["multi_factor_matching", "relationship_mapping", "entity_resolution", "attribute_correlation"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "deductive", "search_space": "medium", "constraint_density": "moderate"}

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps = attribute assignments (people x attributes)."""
        return self.num_people * 3  # 3 attributes per person

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Logic Grid."""
        from ...models import DifficultyLevel

        logic_depth = {
            DifficultyLevel.EASY.value: 3,
            DifficultyLevel.MEDIUM.value: 5,
            DifficultyLevel.HARD.value: 7,
        }.get(self.difficulty.value, 4)
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=float(self.num_people),
            state_observability=1.0,
            constraint_density=0.6,
        )

    def _generate_solution(self) -> None:
        """Generate a random valid solution."""
        people = self.categories.person

        # Randomly assign each attribute to each person
        colors = self.categories.color[:]
        pets = self.categories.pet[:]
        drinks = self.categories.drink[:]

        self._rng.shuffle(colors)
        self._rng.shuffle(pets)
        self._rng.shuffle(drinks)

        self.solution = {}
        for i, person in enumerate(people):
            self.solution[person] = PersonAttributes(
                color=colors[i],
                pet=pets[i],
                drink=drinks[i],
            )

    def _generate_clues(self) -> None:
        """Generate clues from the solution."""
        self.clues = []
        people = self.categories.person

        # Generate direct association clues
        num_direct = self.num_people - 1
        for i in range(num_direct):
            person = people[i]
            attrs = self.solution[person]

            # Choose two attributes to reveal
            cat1, cat2 = self._rng.sample(["color", "pet", "drink"], 2)
            val1 = getattr(attrs, cat1)
            val2 = getattr(attrs, cat2)
            clue = f"{person} has the {val1} {cat1} and drinks {val2}"
            self.clues.append(clue)

        # Generate relative/constraint clues
        for _ in range(self.num_people):
            p1, p2 = self._rng.sample(people, 2)
            cat = self._rng.choice(["color", "pet", "drink"])

            val = getattr(self.solution[p2], cat)
            clue = f"{p1} does not have the {val} {cat}"
            self.clues.append(clue)

    async def generate_puzzle(self) -> None:
        """Generate a new Logic Grid puzzle."""
        self._generate_solution()
        self._generate_clues()

        # Initialize player grid (all unknown)
        self.player_grid = {}

        self.moves_made = 0
        self.game_started = True

    async def validate_move(self, cat1: str, val1: str, cat2: str, val2: str, state: bool) -> MoveResult:
        """Mark a connection in the logic grid.

        Args:
            cat1: First category
            val1: First value
            cat2: Second category
            val2: Second value
            state: True = connected, False = not connected

        Returns:
            MoveResult with success status and message
        """
        # Normalize categories
        cat1 = cat1.lower()
        cat2 = cat2.lower()

        # Validate categories
        valid_categories = ["person", "color", "pet", "drink"]
        if cat1 not in valid_categories or cat2 not in valid_categories:
            return MoveResult(success=False, message=f"Invalid category. Use: {', '.join(valid_categories)}")

        if cat1 == cat2:
            return MoveResult(success=False, message="Cannot connect values from the same category")

        # Validate values
        cat1_values = getattr(self.categories, cat1)
        cat2_values = getattr(self.categories, cat2)

        if val1 not in cat1_values:
            return MoveResult(success=False, message=f"Invalid {cat1}. Choose from: {', '.join(cat1_values)}")

        if val2 not in cat2_values:
            return MoveResult(success=False, message=f"Invalid {cat2}. Choose from: {', '.join(cat2_values)}")

        # Store the connection (normalize order)
        key = (cat1, val1, cat2, val2) if cat1 < cat2 else (cat2, val2, cat1, val1)
        self.player_grid[key] = state
        self.moves_made += 1

        return MoveResult(
            success=True,
            message=f"Marked {val1} ({cat1}) and {val2} ({cat2}) as {'connected' if state else 'not connected'}",
            state_changed=True,
        )

    def is_complete(self) -> bool:
        """Check if the puzzle is complete and correct."""
        # Check if player has correctly identified all connections
        for person in self.categories.person:
            attrs = self.solution[person]

            # Check person -> color
            key1 = ("color", attrs.color, "person", person)
            key2 = ("person", person, "color", attrs.color)
            if not self.player_grid.get(key1) and not self.player_grid.get(key2):
                return False

            # Check person -> pet
            key1 = ("person", person, "pet", attrs.pet)
            key2 = ("pet", attrs.pet, "person", person)
            if not self.player_grid.get(key1) and not self.player_grid.get(key2):
                return False

            # Check person -> drink
            key1 = ("drink", attrs.drink, "person", person)
            key2 = ("person", person, "drink", attrs.drink)
            if not self.player_grid.get(key1) and not self.player_grid.get(key2):
                return False

        return True

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        Returns:
            Tuple of (hint_data, hint_message) or None if puzzle is complete
        """
        # Find a connection that hasn't been marked
        for person in self.categories.person:
            attrs = self.solution[person]

            # Check all categories except person
            for cat in [c for c in CATEGORIES if c != "person"]:
                val = getattr(attrs, cat)
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
        for cat in CATEGORIES:
            values = getattr(self.categories, cat)
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
        return (
            f"Moves made: {self.moves_made} | Connections: {connections} | Exclusions: {exclusions} | Seed: {self.seed}"
        )
