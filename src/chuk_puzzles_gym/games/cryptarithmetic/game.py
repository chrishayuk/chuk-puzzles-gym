"""Cryptarithmetic puzzle game implementation."""

import string
from itertools import permutations
from typing import Any

from ...models import DifficultyLevel, DifficultyProfile, MoveResult
from .._base import PuzzleGame
from .config import CryptarithmeticConfig


class CryptarithmeticGame(PuzzleGame):
    """Cryptarithmetic puzzle - map letters to digits to satisfy an addition equation.

    Rules:
    - Each letter represents a unique digit (0-9)
    - The equation must be a valid addition (e.g., SEND + MORE = MONEY)
    - No number may have a leading zero
    - Each digit is used by at most one letter
    """

    def __init__(self, difficulty: str = "easy", seed: int | None = None, **kwargs):
        super().__init__(difficulty, seed, **kwargs)
        self.config = CryptarithmeticConfig.from_difficulty(self.difficulty)
        self.operands: list[str] = []
        self.result_word: str = ""
        self.equation: str = ""
        self.letters: list[str] = []
        self.leading_letters: set[str] = set()
        self.letter_mapping: dict[str, int] = {}  # Solution
        self.player_mapping: dict[str, int | None] = {}  # Player's assignments
        self.initial_mapping: dict[str, int] = {}  # Pre-assigned

    @property
    def name(self) -> str:
        return "Cryptarithmetic"

    @property
    def description(self) -> str:
        return "Map letters to digits to make the addition equation work"

    @property
    def constraint_types(self) -> list[str]:
        return ["arithmetic", "all_different", "carry_propagation", "bijective_mapping"]

    @property
    def business_analogies(self) -> list[str]:
        return ["code_breaking", "financial_reconciliation", "auditing", "data_mapping"]

    @property
    def complexity_profile(self) -> dict[str, str]:
        return {
            "reasoning_type": "deductive",
            "search_space": "large",
            "constraint_density": "dense",
        }

    @property
    def complexity_metrics(self) -> dict[str, int | float]:
        unassigned = sum(1 for v in self.player_mapping.values() if v is None)
        return {
            "variable_count": len(self.letters),
            "constraint_count": len(self.letters) + len(self.leading_letters) + 1,
            "domain_size": 10,
            "branching_factor": 10 - len(self.letters) / 2.0,
            "empty_cells": unassigned,
        }

    @property
    def difficulty_profile(self) -> DifficultyProfile:
        profiles = {
            DifficultyLevel.EASY: DifficultyProfile(
                logic_depth=3, branching_factor=4.0, state_observability=1.0, constraint_density=0.7
            ),
            DifficultyLevel.MEDIUM: DifficultyProfile(
                logic_depth=5, branching_factor=6.0, state_observability=1.0, constraint_density=0.6
            ),
            DifficultyLevel.HARD: DifficultyProfile(
                logic_depth=7, branching_factor=8.0, state_observability=1.0, constraint_density=0.5
            ),
        }
        return profiles[self.difficulty]

    @property
    def optimal_steps(self) -> int | None:
        return len(self.letters) - len(self.initial_mapping)

    def _word_to_number(self, word: str, mapping: dict[str, int]) -> int | None:
        """Convert a word to a number using the letter-digit mapping."""
        digits = []
        for ch in word:
            if ch not in mapping or mapping[ch] is None:
                return None
            digits.append(str(mapping[ch]))
        return int("".join(digits))

    def _verify_unique_solution(
        self, letters: list[str], leading: set[str], operands: list[str], result_word: str
    ) -> dict[str, int] | None:
        """Brute-force verify the puzzle has a unique solution.

        Returns the solution mapping if unique, None otherwise.
        """
        n = len(letters)
        if n > 10:
            return None

        solutions = []
        for perm in permutations(range(10), n):
            mapping = dict(zip(letters, perm, strict=True))
            # Check leading zeros
            if any(mapping[ch] == 0 for ch in leading):
                continue
            # Check equation
            operand_values = []
            for word in operands:
                val = 0
                for ch in word:
                    val = val * 10 + mapping[ch]
                operand_values.append(val)

            result_val = 0
            for ch in result_word:
                result_val = result_val * 10 + mapping[ch]

            if sum(operand_values) == result_val:
                solutions.append(mapping.copy())
                if len(solutions) > 1:
                    return None  # Not unique

        return solutions[0] if len(solutions) == 1 else None

    async def generate_puzzle(self) -> None:
        """Generate a cryptarithmetic puzzle."""
        max_len = self.config.max_word_length
        max_attempts = 200

        for _ in range(max_attempts):
            # Generate random numbers
            min_val = 10 ** (max_len - 1)
            max_val = 10**max_len - 1

            num1 = self._rng.randint(min_val, max_val)
            num2 = self._rng.randint(min_val, max_val)
            total = num1 + num2

            # Collect all digits used
            all_digits_str = str(num1) + str(num2) + str(total)
            unique_digits = sorted({int(d) for d in all_digits_str})

            if len(unique_digits) < 4 or len(unique_digits) > 10:
                continue

            # Create letter mapping: digit -> letter
            available_letters = list(string.ascii_uppercase)
            self._rng.shuffle(available_letters)
            digit_to_letter = {}
            for i, digit in enumerate(unique_digits):
                digit_to_letter[digit] = available_letters[i]

            # Convert numbers to words
            word1 = "".join(digit_to_letter[int(d)] for d in str(num1))
            word2 = "".join(digit_to_letter[int(d)] for d in str(num2))
            result = "".join(digit_to_letter[int(d)] for d in str(total))

            # Build letter mapping (letter -> digit)
            letter_mapping = {v: k for k, v in digit_to_letter.items()}
            letters = sorted(letter_mapping.keys())
            leading = {word1[0], word2[0], result[0]}

            # Verify uniqueness
            solution = self._verify_unique_solution(letters, leading, [word1, word2], result)
            if solution is None:
                continue

            # Found a valid puzzle
            self.operands = [word1, word2]
            self.result_word = result
            self.equation = f"{word1} + {word2} = {result}"
            self.letters = letters
            self.leading_letters = leading
            self.letter_mapping = solution

            # Initialize player mapping
            self.player_mapping = dict.fromkeys(letters)

            # Pre-assign some letters based on difficulty
            pre_count = min(self.config.pre_assigned, len(letters))
            pre_letters = letters[:]
            self._rng.shuffle(pre_letters)
            self.initial_mapping = {}
            for ch in pre_letters[:pre_count]:
                self.initial_mapping[ch] = solution[ch]
                self.player_mapping[ch] = solution[ch]

            self.game_started = True
            return

        # Fallback: hardcoded puzzle
        self._generate_fallback()

    def _generate_fallback(self) -> None:
        """Generate a simple fallback puzzle."""
        # AB + CD = EF where 12 + 34 = 46 -> not unique
        # Use: TO + GO = OUT (89 + 78 = 167) ... not quite.
        # Simple: 21 + 34 = 55 is not all-different.
        # Use manually verified: IF + IT = AT -> not valid
        # Simplest: use small known puzzles
        self.operands = ["AB", "CD"]
        self.result_word = "EFG"
        # 98 + 76 = 174 -> A=9,B=8,C=7,D=6,E=1,F=7 -> F and C both 7, not unique letters
        # Try: 57 + 48 = 105 -> A=5,B=7,C=4,D=8,E=1,F=0,G=5 -> A and G both 5
        # Just use a known-good puzzle: 34 + 56 = 90 -> nope, only 5 unique
        # Go with: AB + CB = DEA: 23 + 43 = 66 -> nope
        # Simpler fallback strategy: just pick numbers and accept
        self.operands = ["AB", "BA"]
        self.result_word = "CDC"
        # 12 + 21 = 33 -> nope (D=C)
        # 13 + 31 = 44 -> nope
        # 27 + 72 = 99 -> nope
        # 19 + 91 = 110 -> A=1,B=9,C=1 -> conflict
        # Just hardcode SEND+MORE=MONEY equivalent at small scale
        # Use: 23 + 45 = 68 -> A=2,B=3,C=4,D=5,E=6,F=8 -> all unique, 6 letters
        self.operands = ["AB", "CD"]
        self.result_word = "EF"
        self.letter_mapping = {"A": 2, "B": 3, "C": 4, "D": 5, "E": 6, "F": 8}
        # Verify: 23 + 45 = 68 ✓
        self.equation = "AB + CD = EF"
        self.letters = sorted(self.letter_mapping.keys())
        self.leading_letters = {"A", "C", "E"}
        self.player_mapping = dict.fromkeys(self.letters)
        self.initial_mapping = {}
        self.game_started = True

    async def validate_move(self, letter: str, digit: int) -> MoveResult:
        """Validate assigning a digit to a letter.

        Args:
            letter: Uppercase letter
            digit: 0-9 to assign, -1 to unassign
        """
        letter = letter.upper()

        if letter not in self.letters:
            self.record_move((letter,), False)
            return MoveResult(
                success=False,
                message=f"Letter '{letter}' is not in this puzzle. Available: {', '.join(self.letters)}",
            )

        if letter in self.initial_mapping:
            self.record_move((letter,), False)
            return MoveResult(success=False, message=f"Letter '{letter}' is pre-assigned and cannot be changed.")

        # Unassign
        if digit == -1:
            if self.player_mapping[letter] is None:
                self.record_move((letter,), False)
                return MoveResult(success=False, message=f"Letter '{letter}' is not assigned.")
            self.player_mapping[letter] = None
            self.record_move((letter,), True)
            return MoveResult(success=True, message=f"Unassigned letter '{letter}'.", state_changed=True)

        if not (0 <= digit <= 9):
            self.record_move((letter,), False)
            return MoveResult(success=False, message="Digit must be between 0 and 9.")

        # Check leading zero constraint
        if digit == 0 and letter in self.leading_letters:
            self.record_move((letter,), False)
            return MoveResult(
                success=False,
                message=f"Letter '{letter}' starts a word and cannot be 0 (no leading zeros).",
            )

        # Check if digit is already used by another letter
        for other_letter, other_digit in self.player_mapping.items():
            if other_digit == digit and other_letter != letter:
                self.record_move((letter,), False)
                return MoveResult(
                    success=False,
                    message=f"Digit {digit} is already assigned to letter '{other_letter}'.",
                )

        self.player_mapping[letter] = digit
        self.record_move((letter,), True)
        return MoveResult(success=True, message=f"Assigned {letter} = {digit}.", state_changed=True)

    def is_complete(self) -> bool:
        """Check if all letters are assigned and the equation holds."""
        # Check all assigned
        if any(v is None for v in self.player_mapping.values()):
            return False

        # Check equation
        operand_values = []
        for word in self.operands:
            val = self._word_to_number(word, self.player_mapping)
            if val is None:
                return False
            operand_values.append(val)

        result_val = self._word_to_number(self.result_word, self.player_mapping)
        if result_val is None:
            return False

        return sum(operand_values) == result_val

    async def get_hint(self) -> tuple[Any, str] | None:
        """Suggest a letter-digit assignment."""
        if not self.can_use_hint():
            return None
        for letter in self.letters:
            if self.player_mapping[letter] is None:
                digit = self.letter_mapping[letter]
                return (
                    (letter, digit),
                    f"Try assigning {letter} = {digit}.",
                )
        return None

    def render_grid(self) -> str:
        """Render the equation and current assignments."""
        lines = []
        lines.append(f"Equation: {self.equation}")
        lines.append("")

        # Show the equation with current assignments
        def render_word(word: str) -> str:
            chars = []
            for ch in word:
                val = self.player_mapping.get(ch)
                if val is not None:
                    chars.append(str(val))
                else:
                    chars.append(ch)
            return "".join(chars)

        rendered_operands = [render_word(w) for w in self.operands]
        rendered_result = render_word(self.result_word)
        lines.append(f"  {' + '.join(rendered_operands)} = {rendered_result}")
        lines.append("")

        # Letter assignments table
        lines.append("Assignments:")
        for letter in self.letters:
            val = self.player_mapping[letter]
            prefix = "*" if letter in self.initial_mapping else " "
            leading = " (leading)" if letter in self.leading_letters else ""
            if val is not None:
                lines.append(f"  {prefix}{letter} = {val}{leading}")
            else:
                lines.append(f"   {letter} = ?{leading}")

        # Available digits
        used_digits = {v for v in self.player_mapping.values() if v is not None}
        available = [str(d) for d in range(10) if d not in used_digits]
        lines.append(f"\nAvailable digits: {', '.join(available)}")

        assigned = sum(1 for v in self.player_mapping.values() if v is not None)
        lines.append(f"Assigned: {assigned}/{len(self.letters)}")

        return "\n".join(lines)

    def get_stats(self) -> str:
        """Get current game statistics."""
        assigned = sum(1 for v in self.player_mapping.values() if v is not None)
        return f"Moves: {self.moves_made} | Assigned: {assigned}/{len(self.letters)} | Seed: {self.seed}"

    def get_rules(self) -> str:
        return (
            "CRYPTARITHMETIC\n"
            "Each letter represents a unique digit (0-9).\n"
            "Find the digit for each letter so the addition equation is correct.\n"
            "No number may have a leading zero.\n"
            "Each digit is used by at most one letter."
        )

    def get_commands(self) -> str:
        return (
            "Commands:\n"
            "  assign <letter> <digit>  - Assign a digit to a letter\n"
            "  unassign <letter>        - Remove assignment\n"
            "  hint                     - Get a hint\n"
            "  check                    - Check if solved\n"
            "  show                     - Show current state\n"
            "  menu                     - Return to menu"
        )
