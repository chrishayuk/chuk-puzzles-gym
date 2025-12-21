"""Mastermind puzzle game implementation."""

from typing import Any

from ...models import DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import MastermindConfig


class MastermindGame(PuzzleGame):
    """Mastermind code-breaking puzzle game.

    Guess the secret code using logical deduction from feedback.
    Each guess gives you black pegs (correct color + position)
    and white pegs (correct color, wrong position).
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        """Initialize a new Mastermind game.

        Args:
            difficulty: Game difficulty level (easy/medium/hard)
        """
        super().__init__(difficulty, seed, **kwargs)

        # Use pydantic config based on difficulty
        self.config = MastermindConfig.from_difficulty(self.difficulty)
        self.code_length = self.config.code_length
        self.num_colors = self.config.num_colors
        self.max_guesses = self.config.max_guesses

        # Color representation (1-8 for easy display)
        self.colors = list(range(1, self.num_colors + 1))
        self.color_names = {
            1: "Red",
            2: "Blue",
            3: "Green",
            4: "Yellow",
            5: "Orange",
            6: "Purple",
            7: "Cyan",
            8: "Magenta",
        }

        # Game state
        self.secret_code: list[int] = []
        self.guesses: list[list[int]] = []
        self.feedback: list[tuple[int, int]] = []  # (black_pegs, white_pegs)

    @property
    def name(self) -> str:
        """The display name of this puzzle type."""
        return "Mastermind"

    @property
    def description(self) -> str:
        """A one-line description of this puzzle type."""
        return "Code-breaking with logical deduction and feedback"

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this puzzle."""
        return ["feedback", "elimination", "logical_inference", "pattern_matching", "iterative_refinement"]

    @property
    def business_analogies(self) -> list[str]:
        """Business problems this puzzle models."""
        return ["hypothesis_testing", "feedback_loops", "iterative_optimization", "parameter_tuning"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        """Complexity profile of this puzzle."""
        return {"reasoning_type": "hybrid", "search_space": "exponential", "constraint_density": "sparse"}

    @property
    def optimal_steps(self) -> int | None:
        """Optimal guesses for Mastermind with hints = 1 (hint reveals code)."""
        # With hints, the code is revealed directly, so optimal is 1
        return 1

    @property
    def difficulty_profile(self) -> "DifficultyProfile":
        """Difficulty characteristics for Mastermind."""
        from ...models import DifficultyLevel

        logic_depth = {
            DifficultyLevel.EASY.value: 2,
            DifficultyLevel.MEDIUM.value: 4,
            DifficultyLevel.HARD.value: 5,
        }.get(self.difficulty.value, 3)
        branching = self.num_colors**self.code_length  # Huge search space
        return DifficultyProfile(
            logic_depth=logic_depth,
            branching_factor=min(10.0, branching / 100),  # Normalized
            state_observability=0.3,  # Hidden code
            constraint_density=0.2,
        )

    async def generate_puzzle(self) -> None:
        """Generate a new Mastermind puzzle."""
        # Generate random secret code
        self.secret_code = [self._rng.choice(self.colors) for _ in range(self.code_length)]

        # Reset game state
        self.guesses = []
        self.feedback = []
        self.moves_made = 0
        self.game_started = True

    def _calculate_feedback(self, guess: list[int]) -> tuple[int, int]:
        """Calculate feedback for a guess.

        Args:
            guess: The guessed code

        Returns:
            Tuple of (black_pegs, white_pegs)
            - black_pegs: correct color in correct position
            - white_pegs: correct color in wrong position
        """
        black_pegs = 0
        white_pegs = 0

        # Create copies to track which positions have been matched
        secret_remaining = list(self.secret_code)
        guess_remaining = list(guess)

        # First pass: count black pegs (exact matches)
        for i in range(self.code_length):
            if guess[i] == self.secret_code[i]:
                black_pegs += 1
                secret_remaining[i] = -1  # Mark as used
                guess_remaining[i] = -1  # Mark as used

        # Second pass: count white pegs (color matches in wrong position)
        for i in range(self.code_length):
            if guess_remaining[i] != -1:  # Not already matched
                if guess_remaining[i] in secret_remaining:
                    white_pegs += 1
                    # Remove the first occurrence from secret_remaining
                    idx = secret_remaining.index(guess_remaining[i])
                    secret_remaining[idx] = -1

        return black_pegs, white_pegs

    async def validate_move(self, *guess: int) -> MoveResult:
        """Make a guess.

        Args:
            *guess: Variable number of color values (should match code_length)

        Returns:
            MoveResult with success status and message
        """
        # Check if game is over
        if len(self.guesses) >= self.max_guesses:
            return MoveResult(
                success=False, message=f"No guesses remaining! The code was: {' '.join(map(str, self.secret_code))}"
            )

        # Validate guess length
        if len(guess) != self.code_length:
            return MoveResult(success=False, message=f"Guess must be exactly {self.code_length} colors.")

        # Validate all colors are in range
        for color in guess:
            if color not in self.colors:
                return MoveResult(success=False, message=f"Invalid color {color}. Use colors 1-{self.num_colors}.")

        # Convert tuple to list
        guess_list = list(guess)

        # Calculate feedback
        black_pegs, white_pegs = self._calculate_feedback(guess_list)

        # Store guess and feedback
        self.guesses.append(guess_list)
        self.feedback.append((black_pegs, white_pegs))
        self.moves_made += 1

        # Check if won
        if black_pegs == self.code_length:
            return MoveResult(
                success=True,
                message=f"Congratulations! You cracked the code in {len(self.guesses)} guesses!",
                state_changed=True,
                game_over=True,
            )

        # Check if out of guesses
        if len(self.guesses) >= self.max_guesses:
            code_str = " ".join(map(str, self.secret_code))
            return MoveResult(
                success=True, message=f"Game over! The code was: {code_str}", state_changed=True, game_over=True
            )

        return MoveResult(success=True, message=f"Feedback: {black_pegs} black, {white_pegs} white", state_changed=True)

    def is_complete(self) -> bool:
        """Check if the puzzle is complete (code cracked)."""
        if not self.feedback:
            return False
        black_pegs, _white_pegs = self.feedback[-1]
        return black_pegs == self.code_length

    async def get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move.

        For evaluation purposes, provides the complete secret code as a guess.

        Returns:
            Tuple of (hint_data, hint_message) or None if no hints available
        """
        if self.is_complete():
            return None

        # Provide the complete secret code as hint for evaluation
        # The validate_move function expects the full code as arguments
        hint_data = tuple(self.secret_code)
        code_str = " ".join(str(c) for c in self.secret_code)
        hint_message = f"The secret code is: {code_str}"
        return hint_data, hint_message

    def render_grid(self) -> str:
        """Render the current game state as ASCII art.

        Returns:
            String representation of the game state
        """
        lines = []

        # Header
        lines.append(f"Mastermind - Crack the {self.code_length}-color code!")
        lines.append(f"Colors available: 1-{self.num_colors}")
        lines.append(f"Guesses remaining: {self.max_guesses - len(self.guesses)}")
        lines.append("")

        # Color legend
        lines.append("Color Legend:")
        legend_parts = []
        for color in range(1, self.num_colors + 1):
            legend_parts.append(f"{color}={self.color_names[color][:3]}")
        lines.append("  " + ", ".join(legend_parts))
        lines.append("")

        # Guess history
        if self.guesses:
            lines.append("Guess History:")
            lines.append("  #  | Code        | Black | White")
            lines.append("  " + "-" * 38)

            for i, (guess, (black, white)) in enumerate(zip(self.guesses, self.feedback, strict=True), 1):
                guess_str = " ".join(str(c) for c in guess)
                lines.append(f"  {i:2d} | {guess_str:11s} |   {black}   |   {white}")
        else:
            lines.append("No guesses yet. Make your first guess!")

        return "\n".join(lines)

    def get_rules(self) -> str:
        """Get the rules description for Mastermind.

        Returns:
            Multi-line string describing the puzzle rules
        """
        return f"""MASTERMIND RULES:
- Guess the secret {self.code_length}-color code
- Each position uses colors 1-{self.num_colors}
- Colors can repeat in the code
- After each guess, you get feedback:
  * Black peg = correct color in correct position
  * White peg = correct color in wrong position
- You have {self.max_guesses} guesses to crack the code
- Use logic to eliminate possibilities!"""

    def get_commands(self) -> str:
        """Get the available commands for Mastermind.

        Returns:
            Multi-line string describing available commands
        """
        example = " ".join(["1"] * self.code_length)
        return f"""MASTERMIND COMMANDS:
  guess <c1> <c2> ... <c{self.code_length}>  - Make a guess (e.g., 'guess {example}')
  show                   - Display current game state
  hint                   - Get a hint for the code
  solve                  - Reveal the solution (ends game)
  menu                   - Return to game selection
  quit                   - Exit the server"""

    def get_stats(self) -> str:
        """Get current game statistics.

        Returns:
            String with game stats
        """
        return f"Guesses made: {len(self.guesses)}/{self.max_guesses} | Code length: {self.code_length} | Colors: 1-{self.num_colors} | Seed: {self.seed}"
