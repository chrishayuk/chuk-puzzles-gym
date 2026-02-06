"""Tests for the CHUK-R benchmark scoring system."""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_puzzles_gym.benchmark import (
    ALL_BENCHMARK_GAMES,
    REASONING_FAMILIES,
    build_benchmark_result,
    format_json,
    format_markdown,
    format_text,
    get_family,
    get_family_games,
    score_episode,
    score_game,
)
from chuk_puzzles_gym.benchmark.models import (
    ChukRBenchmarkResult,
    FamilyBenchmarkResult,
    GameBenchmarkResult,
)
from chuk_puzzles_gym.eval import EvaluationReport
from chuk_puzzles_gym.games import AVAILABLE_GAMES
from chuk_puzzles_gym.models import (
    DifficultyLevel,
    EpisodeResult,
    EpisodeStatus,
)
from chuk_puzzles_gym.models.evaluation import ReasoningMetrics

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_episode(
    game: str = "sudoku",
    difficulty: str = "easy",
    seed: int = 42,
    status: EpisodeStatus = EpisodeStatus.SOLVED,
    steps: int = 10,
    invalid: int = 0,
    hints: int = 0,
    time_ms: int = 100,
    optimal_steps: int | None = 10,
    reasoning_metrics: ReasoningMetrics | None = None,
) -> EpisodeResult:
    """Helper to create EpisodeResult for tests."""
    now = datetime.now()
    return EpisodeResult(
        game=game,
        difficulty=DifficultyLevel(difficulty),
        seed=seed,
        started_at=now,
        ended_at=now,
        wall_time_ms=time_ms,
        status=status,
        steps_taken=steps,
        invalid_actions=invalid,
        hints_used=hints,
        optimal_steps=optimal_steps,
        reasoning_metrics=reasoning_metrics,
    )


def make_reasoning_metrics(
    backtrack_count: int = 0,
    solver_distance_trace: list[int] | None = None,
    error_streak_max: int = 0,
    error_streaks: list[int] | None = None,
    total_actions: int = 10,
    optimal_path_length: int | None = 10,
) -> ReasoningMetrics:
    """Helper to create ReasoningMetrics for tests."""
    return ReasoningMetrics(
        backtrack_count=backtrack_count,
        solver_distance_trace=solver_distance_trace or [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
        error_streak_max=error_streak_max,
        error_streaks=error_streaks or [],
        total_actions=total_actions,
        optimal_path_length=optimal_path_length,
    )


def make_report(
    game: str = "sudoku",
    difficulty: str = "easy",
    episodes: list[EpisodeResult] | None = None,
) -> EvaluationReport:
    """Helper to create EvaluationReport for tests."""
    report = EvaluationReport(game=game, difficulty=difficulty)
    if episodes:
        report.episodes = list(episodes)
    return report


def _make_mock_result() -> ChukRBenchmarkResult:
    """Create a minimal ChukRBenchmarkResult for formatter tests."""
    game = GameBenchmarkResult(
        game="sudoku",
        family="Logic",
        difficulty="easy",
        episodes_evaluated=5,
        episodes_solved=4,
        episode_scores=[90.0, 85.0, 80.0, 75.0, 0.0],
    )
    family = FamilyBenchmarkResult(
        family="Logic",
        games=[game],
        total_games=10,
    )
    return ChukRBenchmarkResult(
        timestamp=datetime(2026, 2, 5, 12, 0, 0),
        difficulty="easy",
        episodes_per_game=5,
        solver_config_desc="hints (budget=100, penalty=0.0)",
        families=[family],
        games=[game],
    )


# ---------------------------------------------------------------------------
# Family mapping tests
# ---------------------------------------------------------------------------


class TestFamilies:
    """Tests for reasoning family definitions."""

    def test_all_available_games_have_family(self):
        """Every game in AVAILABLE_GAMES is mapped to a family."""
        for game_name in AVAILABLE_GAMES:
            assert get_family(game_name) is not None, f"{game_name} has no reasoning family"

    def test_30_games_total(self):
        """Exactly 30 games across all families."""
        assert len(ALL_BENCHMARK_GAMES) == 30

    def test_no_duplicate_games(self):
        """No game appears in multiple families."""
        assert len(ALL_BENCHMARK_GAMES) == len(set(ALL_BENCHMARK_GAMES))

    def test_all_benchmark_games_exist(self):
        """Every game in REASONING_FAMILIES exists in AVAILABLE_GAMES."""
        for game_name in ALL_BENCHMARK_GAMES:
            assert game_name in AVAILABLE_GAMES, f"{game_name} is in REASONING_FAMILIES but not AVAILABLE_GAMES"

    def test_four_families(self):
        """Exactly 4 reasoning families."""
        assert len(REASONING_FAMILIES) == 4
        assert set(REASONING_FAMILIES.keys()) == {
            "Logic",
            "Constraint",
            "Search",
            "Planning",
        }

    def test_get_family(self):
        """get_family returns correct family for known games."""
        assert get_family("sudoku") == "Logic"
        assert get_family("kenken") == "Constraint"
        assert get_family("mastermind") == "Search"
        assert get_family("sokoban") == "Planning"
        assert get_family("nonexistent") is None

    def test_get_family_games(self):
        """get_family_games returns the correct game list."""
        logic_games = get_family_games("Logic")
        assert "sudoku" in logic_games
        assert len(logic_games) == 10

        assert get_family_games("Unknown") == []

    def test_family_sizes(self):
        """Family sizes match the specification."""
        assert len(REASONING_FAMILIES["Logic"]) == 10
        assert len(REASONING_FAMILIES["Constraint"]) == 12
        assert len(REASONING_FAMILIES["Search"]) == 4
        assert len(REASONING_FAMILIES["Planning"]) == 4


# ---------------------------------------------------------------------------
# Per-episode scoring tests
# ---------------------------------------------------------------------------


class TestScoreEpisode:
    """Tests for the per-episode scoring formula."""

    def test_unsolved_scores_zero(self):
        """Unsolved episodes always score 0."""
        ep = make_episode(status=EpisodeStatus.FAILED)
        assert score_episode(ep) == 0.0

    def test_timeout_scores_zero(self):
        """Timed-out episodes score 0."""
        ep = make_episode(status=EpisodeStatus.TIMEOUT)
        assert score_episode(ep) == 0.0

    def test_perfect_episode_scores_100(self):
        """Optimal solve with no errors/hints/backtracks scores 100."""
        ep = make_episode(
            steps=10,
            optimal_steps=10,
            invalid=0,
            hints=0,
        )
        assert score_episode(ep) == 100.0

    def test_perfect_with_reasoning_metrics(self):
        """Perfect solve with perfect reasoning metrics scores 100."""
        rm = make_reasoning_metrics(
            backtrack_count=0,
            total_actions=10,
            optimal_path_length=10,
        )
        ep = make_episode(
            steps=10,
            optimal_steps=10,
            invalid=0,
            hints=0,
            reasoning_metrics=rm,
        )
        assert score_episode(ep) == 100.0

    def test_half_efficiency_reduces_score(self):
        """50% efficiency reduces the score."""
        ep = make_episode(
            steps=20,
            optimal_steps=10,
            invalid=0,
            hints=0,
        )
        score = score_episode(ep)
        # efficiency=0.5, error=1.0, bt=1.0, stead=1.0, hint=1.0
        # = 100 * (0.40*0.5 + 0.15*1 + 0.15*1 + 0.15*1 + 0.15*1) = 80
        assert score == 80.0

    def test_high_error_rate_reduces_score(self):
        """50% error rate penalizes the score."""
        ep = make_episode(
            steps=10,
            optimal_steps=10,
            invalid=10,
            hints=0,
        )
        score = score_episode(ep)
        # error_rate = 10/(10+10) = 0.5, error_component = 0.5
        # = 100 * (0.40*1 + 0.15*0.5 + 0.15*1 + 0.15*1 + 0.15*1)
        # = 100 * (0.40 + 0.075 + 0.15 + 0.15 + 0.15) = 92.5
        assert score == 92.5

    def test_full_hint_dependency_penalizes(self):
        """100% hint dependency penalizes the score."""
        ep = make_episode(
            steps=10,
            optimal_steps=10,
            invalid=0,
            hints=10,
        )
        score = score_episode(ep)
        # hint_dependency = 10/10 = 1.0, hint_component = 0.0
        # = 100 * (0.40*1 + 0.15*1 + 0.15*1 + 0.15*1 + 0.15*0) = 85
        assert score == 85.0

    def test_backtrack_rate_penalizes(self):
        """High backtrack rate reduces score via reasoning metrics."""
        rm = make_reasoning_metrics(
            backtrack_count=5,
            solver_distance_trace=[10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
            total_actions=10,
            optimal_path_length=10,
        )
        ep = make_episode(
            steps=10,
            optimal_steps=10,
            invalid=0,
            hints=0,
            reasoning_metrics=rm,
        )
        score = score_episode(ep)
        # backtrack_rate = 5/10 = 0.5, bt_component = 0.5
        assert score < 100.0

    def test_low_steadiness_penalizes(self):
        """Non-monotonic progress reduces score."""
        # Trace with many non-monotonic steps
        rm = make_reasoning_metrics(
            backtrack_count=0,
            solver_distance_trace=[10, 9, 10, 8, 9, 7, 8, 6, 5, 4, 0],
            total_actions=10,
            optimal_path_length=10,
        )
        ep = make_episode(
            steps=10,
            optimal_steps=10,
            invalid=0,
            hints=0,
            reasoning_metrics=rm,
        )
        score = score_episode(ep)
        assert score < 100.0

    def test_no_optimal_steps_uses_fallback(self):
        """When optimal_steps is None, fallback efficiency is used."""
        ep = make_episode(
            steps=5,
            optimal_steps=None,
            invalid=0,
            hints=0,
        )
        score = score_episode(ep)
        # Fallback: max(0, 1 - (5-1)/100) = 0.96
        # = 100 * (0.40*0.96 + 0.15*1 + 0.15*1 + 0.15*1 + 0.15*1) = 98.4
        assert score > 90.0

    def test_no_reasoning_metrics_defaults_perfect(self):
        """Missing reasoning_metrics assumes no backtracks, perfect steadiness."""
        ep = make_episode(
            steps=10,
            optimal_steps=10,
            invalid=0,
            hints=0,
        )
        assert ep.reasoning_metrics is None
        assert score_episode(ep) == 100.0

    def test_score_bounded_0_100(self):
        """Score is always in [0, 100]."""
        for steps in [1, 10, 100]:
            for invalid in [0, 5, 50]:
                for hints in [0, 5, 50]:
                    ep = make_episode(
                        steps=max(1, steps),
                        optimal_steps=10,
                        invalid=invalid,
                        hints=hints,
                    )
                    s = score_episode(ep)
                    assert 0.0 <= s <= 100.0, (
                        f"Score {s} out of bounds for steps={steps}, invalid={invalid}, hints={hints}"
                    )

    def test_score_is_rounded(self):
        """Scores are rounded to 2 decimal places."""
        ep = make_episode(steps=13, optimal_steps=10, invalid=3, hints=2)
        score = score_episode(ep)
        assert score == round(score, 2)


# ---------------------------------------------------------------------------
# Per-game scoring tests
# ---------------------------------------------------------------------------


class TestScoreGame:
    """Tests for per-game scoring."""

    def test_empty_report_scores_zero(self):
        """Game with no episodes scores 0."""
        report = make_report()
        result = score_game(report)
        assert result.score == 0.0
        assert result.episodes_evaluated == 0

    def test_all_perfect_scores_100(self):
        """All perfectly solved episodes produce score 100."""
        episodes = [make_episode(seed=i, steps=10, optimal_steps=10, invalid=0, hints=0) for i in range(5)]
        report = make_report(episodes=episodes)
        result = score_game(report)
        assert result.score == 100.0
        assert result.episodes_evaluated == 5
        assert result.episodes_solved == 5

    def test_mixed_solved_unsolved(self):
        """Mix of solved and unsolved episodes."""
        episodes = [
            make_episode(seed=0, steps=10, optimal_steps=10, invalid=0, hints=0),
            make_episode(seed=1, status=EpisodeStatus.FAILED, steps=5, optimal_steps=10),
        ]
        report = make_report(episodes=episodes)
        result = score_game(report)
        # Episode 0 = 100, Episode 1 = 0, mean = 50
        assert result.score == 50.0
        assert result.solve_rate == 0.5

    def test_family_assignment_logic(self):
        """Sudoku is assigned to Logic family."""
        report = make_report(game="sudoku")
        result = score_game(report)
        assert result.family == "Logic"

    def test_family_assignment_constraint(self):
        """KenKen is assigned to Constraint family."""
        report = make_report(game="kenken")
        result = score_game(report)
        assert result.family == "Constraint"

    def test_family_assignment_search(self):
        """Mastermind is assigned to Search family."""
        report = make_report(game="mastermind")
        result = score_game(report)
        assert result.family == "Search"

    def test_family_assignment_planning(self):
        """Sokoban is assigned to Planning family."""
        report = make_report(game="sokoban")
        result = score_game(report)
        assert result.family == "Planning"

    def test_score_std(self):
        """Standard deviation is computed correctly."""
        episodes = [
            make_episode(seed=0, steps=10, optimal_steps=10, invalid=0, hints=0),
            make_episode(seed=1, status=EpisodeStatus.FAILED, steps=5, optimal_steps=10),
        ]
        report = make_report(episodes=episodes)
        result = score_game(report)
        assert result.score_std == 50.0  # std of [100, 0]


# ---------------------------------------------------------------------------
# Build benchmark result tests
# ---------------------------------------------------------------------------


class TestBuildBenchmarkResult:
    """Tests for build_benchmark_result."""

    def test_empty_reports(self):
        """No reports yields CHUK-R of 0."""
        result = build_benchmark_result({}, "easy", 5)
        assert result.chuk_r == 0.0
        assert result.coverage == 0.0
        assert result.total_episodes == 0

    def test_always_four_families(self):
        """Result always has 4 family entries."""
        result = build_benchmark_result({}, "easy", 5)
        assert len(result.families) == 4

    def test_single_game(self):
        """Single game contributes to one family only."""
        episodes = [make_episode(seed=i, steps=10, optimal_steps=10, invalid=0, hints=0) for i in range(3)]
        report = make_report(game="sudoku", episodes=episodes)
        result = build_benchmark_result({"sudoku": report}, "easy", 3)

        assert result.chuk_r == 100.0  # Only Logic family, score 100
        assert result.families_evaluated == 1
        assert result.coverage > 0

    def test_multi_family(self):
        """Games from different families produce a multi-family result."""
        ep_perfect = [make_episode(seed=0, steps=10, optimal_steps=10, invalid=0, hints=0)]
        reports = {
            "sudoku": make_report(game="sudoku", episodes=ep_perfect),
            "kenken": make_report(game="kenken", episodes=ep_perfect),
            "mastermind": make_report(game="mastermind", episodes=ep_perfect),
            "sokoban": make_report(game="sokoban", episodes=ep_perfect),
        }
        result = build_benchmark_result(reports, "easy", 1)
        assert result.families_evaluated == 4
        assert result.chuk_r == 100.0

    def test_metadata(self):
        """Metadata fields are set correctly."""
        result = build_benchmark_result({}, "medium", 10, solver_config_desc="test")
        assert result.difficulty == "medium"
        assert result.episodes_per_game == 10
        assert result.solver_config_desc == "test"

    def test_unevaluated_games_have_zero_episodes(self):
        """Games not in reports show up with 0 episodes in family results."""
        result = build_benchmark_result({}, "easy", 5)
        for fam in result.families:
            for g in fam.games:
                assert g.episodes_evaluated == 0


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestModels:
    """Tests for benchmark Pydantic models."""

    def test_game_result_frozen(self):
        """GameBenchmarkResult is frozen (immutable)."""
        result = GameBenchmarkResult(
            game="sudoku",
            family="Logic",
            difficulty="easy",
            episodes_evaluated=1,
            episodes_solved=1,
            episode_scores=[100.0],
        )
        try:
            result.game = "kenken"  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except Exception:
            pass

    def test_family_result_coverage(self):
        """FamilyBenchmarkResult computes coverage correctly."""
        game = GameBenchmarkResult(
            game="sudoku",
            family="Logic",
            difficulty="easy",
            episodes_evaluated=5,
            episodes_solved=5,
            episode_scores=[100.0] * 5,
        )
        fam = FamilyBenchmarkResult(
            family="Logic",
            games=[game],
            total_games=10,
        )
        assert fam.coverage == 0.1  # 1/10
        assert fam.evaluated_count == 1

    def test_chuk_r_computed(self):
        """ChukRBenchmarkResult.chuk_r is the mean of family scores."""
        game_a = GameBenchmarkResult(
            game="sudoku",
            family="Logic",
            difficulty="easy",
            episodes_evaluated=1,
            episodes_solved=1,
            episode_scores=[80.0],
        )
        game_b = GameBenchmarkResult(
            game="mastermind",
            family="Search",
            difficulty="easy",
            episodes_evaluated=1,
            episodes_solved=1,
            episode_scores=[60.0],
        )
        fam_a = FamilyBenchmarkResult(
            family="Logic",
            games=[game_a],
            total_games=10,
        )
        fam_b = FamilyBenchmarkResult(
            family="Search",
            games=[game_b],
            total_games=4,
        )
        fam_c = FamilyBenchmarkResult(
            family="Constraint",
            games=[],
            total_games=12,
        )
        fam_d = FamilyBenchmarkResult(
            family="Planning",
            games=[],
            total_games=4,
        )
        result = ChukRBenchmarkResult(
            timestamp=datetime.now(),
            difficulty="easy",
            episodes_per_game=1,
            solver_config_desc="test",
            families=[fam_a, fam_b, fam_c, fam_d],
            games=[game_a, game_b],
        )
        # Only Logic (80) and Search (60) have evaluated games
        assert result.chuk_r == 70.0
        assert result.families_evaluated == 2


# ---------------------------------------------------------------------------
# Report formatter tests
# ---------------------------------------------------------------------------


class TestReport:
    """Tests for output formatting."""

    def test_format_text_includes_chuk_r(self):
        """Text output includes CHUK-R header and score."""
        result = _make_mock_result()
        text = format_text(result)
        assert "CHUK REASONING SCORE" in text
        assert "CHUK-R" in text
        assert "sudoku" in text

    def test_format_text_includes_family(self):
        """Text output includes family name."""
        result = _make_mock_result()
        text = format_text(result)
        assert "Logic" in text

    def test_format_json_is_valid(self):
        """JSON output is valid and contains expected keys."""
        result = _make_mock_result()
        j = format_json(result)
        parsed = json.loads(j)
        assert "chuk_r" in parsed
        assert "families" in parsed
        assert "games" in parsed
        assert "Logic" in parsed["families"]
        assert "sudoku" in parsed["games"]

    def test_format_json_values(self):
        """JSON output has correct score values."""
        result = _make_mock_result()
        parsed = json.loads(format_json(result))
        # Game score = mean([90, 85, 80, 75, 0]) = 66.0
        assert parsed["games"]["sudoku"]["score"] == 66.0
        assert parsed["games"]["sudoku"]["solved"] == 4
        assert parsed["games"]["sudoku"]["episodes"] == 5

    def test_format_markdown_has_tables(self):
        """Markdown output has markdown table syntax."""
        result = _make_mock_result()
        md = format_markdown(result)
        assert "|" in md
        assert "# CHUK Reasoning Score" in md
        assert "## Family Scores" in md
        assert "## Per-Game Scores" in md

    def test_format_markdown_includes_game(self):
        """Markdown includes game-level data."""
        result = _make_mock_result()
        md = format_markdown(result)
        assert "sudoku" in md
        assert "Logic" in md


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------


class TestBenchmarkIntegration:
    """Integration tests for the full benchmark pipeline."""

    async def test_end_to_end_single_game(self):
        """Full pipeline: evaluate -> score -> format."""
        from chuk_puzzles_gym.eval import evaluate_game

        report = await evaluate_game("sudoku", difficulty="easy", episodes=2)
        result = build_benchmark_result(
            {"sudoku": report},
            difficulty="easy",
            episodes_per_game=2,
        )
        assert 0.0 <= result.chuk_r <= 100.0
        assert result.families_evaluated >= 1

        text = format_text(result)
        assert "CHUK-R" in text

        j = json.loads(format_json(result))
        assert "chuk_r" in j
