"""Tests for the evaluation harness."""

import sys
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from puzzle_arcade_server.eval import (
    EvaluationReport,
    _apply_hint,
    evaluate_all_games,
    evaluate_game,
    main,
    parse_args,
    run_episode,
)
from puzzle_arcade_server.games import AVAILABLE_GAMES
from puzzle_arcade_server.models import (
    DifficultyLevel,
    EpisodeResult,
    EpisodeStatus,
    SolverConfig,
)


def make_episode(
    game: str = "sudoku",
    difficulty: str = "easy",
    seed: int = 12345,
    status: EpisodeStatus = EpisodeStatus.SOLVED,
    steps: int = 10,
    invalid: int = 0,
    hints: int = 10,
    time_ms: int = 100,
    optimal_steps: int | None = None,
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
    )


class TestEpisodeResult:
    """Tests for EpisodeResult Pydantic model."""

    def test_creation(self):
        """Test creating an EpisodeResult."""
        result = make_episode()
        assert result.game == "sudoku"
        assert result.status == EpisodeStatus.SOLVED
        assert result.success is True

    def test_efficiency_score(self):
        """Test efficiency score calculation."""
        # Optimal solution
        result = make_episode(steps=10, optimal_steps=10)
        assert result.efficiency_score == 1.0

        # Suboptimal solution
        result = make_episode(steps=20, optimal_steps=10)
        assert result.efficiency_score == 0.5

        # No optimal steps known
        result = make_episode(steps=10, optimal_steps=None)
        assert result.efficiency_score == 0.0

    def test_error_rate(self):
        """Test error rate calculation."""
        result = make_episode(steps=10, invalid=0)
        assert result.error_rate == 0.0

        result = make_episode(steps=10, invalid=10)
        assert result.error_rate == 0.5

    def test_to_summary_dict(self):
        """Test converting EpisodeResult to summary dict."""
        result = make_episode()
        d = result.to_summary_dict()
        assert "game" in d
        assert "success" in d
        assert d["game"] == "sudoku"
        assert d["success"] is True

    def test_to_jsonl(self):
        """Test converting to JSONL format."""
        result = make_episode()
        jsonl = result.to_jsonl()
        assert "sudoku" in jsonl
        assert '"success": true' in jsonl


class TestEvaluationReport:
    """Tests for EvaluationReport dataclass."""

    def test_creation(self):
        """Test creating an EvaluationReport."""
        report = EvaluationReport(game="sudoku", difficulty="easy")
        assert report.game == "sudoku"
        assert len(report.episodes) == 0

    def test_properties_empty(self):
        """Test properties with no episodes."""
        report = EvaluationReport(game="sudoku", difficulty="easy")
        assert report.total_episodes == 0
        assert report.solved_count == 0
        assert report.solve_rate == 0.0
        assert report.avg_moves == 0.0
        assert report.avg_invalid_moves == 0.0
        assert report.avg_time_ms == 0.0

    def test_properties_with_episodes(self):
        """Test properties with episodes."""
        report = EvaluationReport(game="sudoku", difficulty="easy")
        report.episodes.append(make_episode(steps=10, invalid=2, time_ms=100))
        assert report.total_episodes == 1
        assert report.solved_count == 1
        assert report.solve_rate == 1.0
        assert report.avg_moves == 10.0
        assert report.avg_invalid_moves == 2.0
        assert report.avg_time_ms == 100.0

    def test_solve_rate_partial(self):
        """Test solve rate with mixed results."""
        report = EvaluationReport(game="sudoku", difficulty="easy")
        report.episodes.append(make_episode(seed=1, status=EpisodeStatus.SOLVED))
        report.episodes.append(make_episode(seed=2, status=EpisodeStatus.FAILED))
        assert report.solve_rate == 0.5

    def test_to_json(self):
        """Test converting report to JSON."""
        report = EvaluationReport(game="sudoku", difficulty="easy")
        json_str = report.to_json()
        assert "sudoku" in json_str

    def test_to_csv(self):
        """Test converting report to CSV."""
        report = EvaluationReport(game="sudoku", difficulty="easy")
        report.episodes.append(make_episode())
        csv_str = report.to_csv()
        assert "sudoku" in csv_str
        assert "solved" in csv_str

    def test_to_markdown(self):
        """Test converting report to markdown."""
        report = EvaluationReport(game="sudoku", difficulty="easy")
        report.episodes.append(make_episode())
        md = report.to_markdown()
        assert "Sudoku" in md or "sudoku" in md
        assert "|" in md  # Table format

    def test_avg_efficiency(self):
        """Test average efficiency calculation."""
        report = EvaluationReport(game="sudoku", difficulty="easy")
        report.episodes.append(make_episode(steps=10, optimal_steps=10))  # 100% efficient
        report.episodes.append(make_episode(steps=20, optimal_steps=10))  # 50% efficient
        assert report.avg_efficiency == 0.75  # Average of 1.0 and 0.5

    def test_solver_config_in_report(self):
        """Test solver config is included in report."""
        solver_config = SolverConfig.solver_free()
        report = EvaluationReport(game="sudoku", difficulty="easy", solver_config=solver_config)
        assert report.solver_config.solver_allowed is False
        json_str = report.to_json()
        assert "solver_allowed" in json_str


class TestRunEpisode:
    """Tests for run_episode function."""

    async def test_run_episode_sudoku(self):
        """Test running an episode for Sudoku."""
        game_class = AVAILABLE_GAMES["sudoku"]
        result = await run_episode(
            game_class=game_class,  # type: ignore[type-abstract]
            difficulty="easy",
            seed=12345,
            use_hints=True,
            max_moves=100,
        )
        assert result.game == "Sudoku"
        assert result.status in [EpisodeStatus.SOLVED, EpisodeStatus.FAILED, EpisodeStatus.TIMEOUT]

    async def test_run_episode_binary(self):
        """Test running an episode for Binary puzzle."""
        game_class = AVAILABLE_GAMES["binary"]
        result = await run_episode(
            game_class=game_class,  # type: ignore[type-abstract]
            difficulty="easy",
            seed=42,
            use_hints=True,
            max_moves=100,
        )
        assert result.game == "Binary Puzzle"

    async def test_run_episode_mastermind(self):
        """Test running an episode for Mastermind."""
        game_class = AVAILABLE_GAMES["mastermind"]
        result = await run_episode(
            game_class=game_class,  # type: ignore[type-abstract]
            difficulty="easy",
            seed=42,
            use_hints=True,
            max_moves=100,
        )
        assert result.game == "Mastermind"

    async def test_run_episode_einstein(self):
        """Test running an episode for Einstein puzzle."""
        game_class = AVAILABLE_GAMES["einstein"]
        result = await run_episode(
            game_class=game_class,  # type: ignore[type-abstract]
            difficulty="easy",
            seed=42,
            use_hints=True,
            max_moves=100,
        )
        assert "Einstein" in result.game

    async def test_run_episode_logic(self):
        """Test running an episode for Logic Grid puzzle."""
        game_class = AVAILABLE_GAMES["logic"]
        result = await run_episode(
            game_class=game_class,  # type: ignore[type-abstract]
            difficulty="easy",
            seed=42,
            use_hints=True,
            max_moves=100,
        )
        assert result.game == "Logic Grid"

    async def test_run_episode_with_solver_config(self):
        """Test running an episode with solver configuration."""
        game_class = AVAILABLE_GAMES["sudoku"]
        solver_config = SolverConfig(hint_budget=5, hint_penalty=0.1)
        result = await run_episode(
            game_class=game_class,  # type: ignore[type-abstract]
            difficulty="easy",
            seed=12345,
            solver_config=solver_config,
            use_hints=True,
            max_moves=100,
        )
        assert result.solver_config.hint_budget == 5
        assert result.solver_config.hint_penalty == 0.1

    async def test_run_episode_solver_free(self):
        """Test running an episode in solver-free mode."""
        game_class = AVAILABLE_GAMES["sudoku"]
        solver_config = SolverConfig.solver_free()
        result = await run_episode(
            game_class=game_class,  # type: ignore[type-abstract]
            difficulty="easy",
            seed=12345,
            solver_config=solver_config,
            use_hints=True,
            max_moves=100,
        )
        # Should fail immediately since hints are disabled
        assert result.status == EpisodeStatus.FAILED
        assert result.hints_used == 0


class TestEvaluateGame:
    """Tests for evaluate_game function."""

    async def test_evaluate_game_basic(self):
        """Test basic game evaluation."""
        report = await evaluate_game(
            game_name="sudoku",
            difficulty="easy",
            episodes=2,
            use_hints=True,
        )
        assert report.game == "sudoku"
        assert len(report.episodes) == 2

    async def test_evaluate_game_with_seeds(self):
        """Test evaluation with specific seeds."""
        report = await evaluate_game(
            game_name="sudoku",
            difficulty="easy",
            seeds=[12345, 67890],
            use_hints=True,
        )
        assert len(report.episodes) == 2
        assert report.episodes[0].seed == 12345
        assert report.episodes[1].seed == 67890

    async def test_evaluate_game_verbose(self):
        """Test evaluation with verbose output."""
        report = await evaluate_game(
            game_name="binary",
            difficulty="easy",
            episodes=1,
            use_hints=True,
            verbose=True,
        )
        assert len(report.episodes) == 1

    async def test_evaluate_game_invalid_name(self):
        """Test evaluation with invalid game name."""
        try:
            await evaluate_game(game_name="nonexistent", difficulty="easy", episodes=1)
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Unknown game" in str(e)


class TestApplyHint:
    """Tests for _apply_hint function."""

    async def test_apply_hint_sudoku(self):
        """Test applying hint for Sudoku."""
        game = AVAILABLE_GAMES["sudoku"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert result.success

    async def test_apply_hint_binary(self):
        """Test applying hint for Binary puzzle."""
        game = AVAILABLE_GAMES["binary"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert result.success

    async def test_apply_hint_hitori(self):
        """Test applying hint for Hitori."""
        game = AVAILABLE_GAMES["hitori"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_star_battle(self):
        """Test applying hint for Star Battle."""
        game = AVAILABLE_GAMES["star_battle"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_tents(self):
        """Test applying hint for Tents."""
        game = AVAILABLE_GAMES["tents"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_minesweeper(self):
        """Test applying hint for Minesweeper."""
        game = AVAILABLE_GAMES["minesweeper"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_bridges(self):
        """Test applying hint for Bridges."""
        game = AVAILABLE_GAMES["bridges"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_shikaku(self):
        """Test applying hint for Shikaku."""
        game = AVAILABLE_GAMES["shikaku"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_slitherlink(self):
        """Test applying hint for Slitherlink."""
        game = AVAILABLE_GAMES["slither"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_sokoban(self):
        """Test applying hint for Sokoban."""
        game = AVAILABLE_GAMES["sokoban"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_knapsack(self):
        """Test applying hint for Knapsack."""
        game = AVAILABLE_GAMES["knapsack"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_scheduler(self):
        """Test applying hint for Scheduler."""
        game = AVAILABLE_GAMES["scheduler"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_nurikabe(self):
        """Test applying hint for Nurikabe."""
        game = AVAILABLE_GAMES["nurikabe"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_lights_out(self):
        """Test applying hint for Lights Out."""
        game = AVAILABLE_GAMES["lights"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_generic_fallback(self):
        """Test applying hint with generic fallback."""
        game = AVAILABLE_GAMES["sudoku"]("easy", seed=42)
        await game.generate_puzzle()

        # Apply hint with a tuple
        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_single_value_fallback(self):
        """Test applying hint with single value fallback."""
        game = AVAILABLE_GAMES["mastermind"]("easy", seed=42)
        await game.generate_puzzle()

        # Apply hint with mastermind's format
        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_kakuro(self):
        """Test applying hint for Kakuro."""
        game = AVAILABLE_GAMES["kakuro"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_nonogram(self):
        """Test applying hint for Nonogram."""
        game = AVAILABLE_GAMES["nonogram"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_hidato(self):
        """Test applying hint for Hidato."""
        game = AVAILABLE_GAMES["hidato"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_fillomino(self):
        """Test applying hint for Fillomino."""
        game = AVAILABLE_GAMES["fillomino"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_futoshiki(self):
        """Test applying hint for Futoshiki."""
        game = AVAILABLE_GAMES["futoshiki"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)

    async def test_apply_hint_killer_sudoku(self):
        """Test applying hint for Killer Sudoku."""
        game = AVAILABLE_GAMES["killer"]("easy", seed=42)
        await game.generate_puzzle()

        hint = await game.get_hint()
        if hint:
            result = await _apply_hint(game, hint[0])
            assert isinstance(result.success, bool)


class TestPrintSummary:
    """Tests for EvaluationReport.print_summary method."""

    def test_print_summary(self):
        """Test print_summary output."""
        report = EvaluationReport(game="sudoku", difficulty="easy")
        report.episodes.append(make_episode(steps=10, invalid=2, time_ms=100))

        # Capture stdout
        captured = StringIO()
        with patch("sys.stdout", captured):
            report.print_summary()

        output = captured.getvalue()
        assert "Sudoku" in output
        assert "Easy" in output
        assert "1/1" in output
        assert "100" in output

    def test_print_summary_no_episodes(self):
        """Test print_summary with no episodes."""
        report = EvaluationReport(game="kenken", difficulty="medium")

        captured = StringIO()
        with patch("sys.stdout", captured):
            report.print_summary()

        output = captured.getvalue()
        assert "Kenken" in output
        assert "0/0" in output

    def test_print_summary_mixed_results(self):
        """Test print_summary with mixed solved/failed."""
        report = EvaluationReport(game="binary", difficulty="hard")
        report.episodes.append(
            make_episode(
                game="binary", difficulty="hard", seed=1, status=EpisodeStatus.SOLVED, steps=20, invalid=1, time_ms=200
            )
        )
        report.episodes.append(
            make_episode(
                game="binary", difficulty="hard", seed=2, status=EpisodeStatus.FAILED, steps=15, invalid=5, time_ms=150
            )
        )

        captured = StringIO()
        with patch("sys.stdout", captured):
            report.print_summary()

        output = captured.getvalue()
        assert "1/2" in output
        assert "50" in output


class TestEvaluateAllGames:
    """Tests for evaluate_all_games function."""

    async def test_evaluate_all_games_basic(self):
        """Test evaluating all games."""
        reports = await evaluate_all_games(
            difficulty="easy",
            episodes=1,
            use_hints=True,
            verbose=False,
        )

        # Should have reports for all available games
        assert len(reports) > 0
        for game_name, report in reports.items():
            assert report.game == game_name
            assert len(report.episodes) == 1

    async def test_evaluate_all_games_verbose(self):
        """Test evaluating all games with verbose output."""
        captured = StringIO()
        with patch("sys.stdout", captured):
            reports = await evaluate_all_games(
                difficulty="easy",
                episodes=1,
                use_hints=True,
                verbose=True,
            )

        assert len(reports) > 0
        output = captured.getvalue()
        # Verbose should print game names
        assert "Evaluating" in output


class TestRunEpisodeEdgeCases:
    """Tests for run_episode edge cases."""

    async def test_run_episode_without_hints(self):
        """Test running an episode without using hints."""
        game_class = AVAILABLE_GAMES["sudoku"]
        result = await run_episode(
            game_class=game_class,  # type: ignore[type-abstract]
            difficulty="easy",
            seed=12345,
            use_hints=False,
            max_moves=100,
        )
        # Without hints, can't solve
        assert result.status == EpisodeStatus.FAILED
        assert result.steps_taken == 0

    async def test_run_episode_max_moves_limit(self):
        """Test that max_moves limit is respected."""
        game_class = AVAILABLE_GAMES["sudoku"]
        result = await run_episode(
            game_class=game_class,  # type: ignore[type-abstract]
            difficulty="easy",
            seed=12345,
            use_hints=True,
            max_moves=1,  # Very low limit
        )
        # Should stop after 1 move
        assert result.steps_taken <= 1

    async def test_run_episode_with_invalid_moves(self):
        """Test run_episode handles invalid moves."""
        game_class = AVAILABLE_GAMES["sudoku"]
        result = await run_episode(
            game_class=game_class,  # type: ignore[type-abstract]
            difficulty="easy",
            seed=42,
            use_hints=True,
            max_moves=100,
        )
        # Should complete normally
        assert result.status in ["solved", "failed", "timeout"]


class TestParseArgs:
    """Tests for parse_args function."""

    def test_parse_args_game_only(self):
        """Test parsing with just game name."""
        with patch("sys.argv", ["eval", "sudoku"]):
            args = parse_args()
        assert args.game == "sudoku"
        assert args.difficulty == "easy"
        assert args.episodes == 10

    def test_parse_args_with_difficulty(self):
        """Test parsing with difficulty."""
        with patch("sys.argv", ["eval", "kenken", "-d", "hard"]):
            args = parse_args()
        assert args.game == "kenken"
        assert args.difficulty == "hard"

    def test_parse_args_with_episodes(self):
        """Test parsing with episodes count."""
        with patch("sys.argv", ["eval", "binary", "-n", "5"]):
            args = parse_args()
        assert args.game == "binary"
        assert args.episodes == 5

    def test_parse_args_with_seeds(self):
        """Test parsing with seeds."""
        with patch("sys.argv", ["eval", "sudoku", "--seeds", "1,2,3"]):
            args = parse_args()
        assert args.seeds == "1,2,3"

    def test_parse_args_with_output_format(self):
        """Test parsing with output format."""
        with patch("sys.argv", ["eval", "sudoku", "-o", "json"]):
            args = parse_args()
        assert args.output == "json"

    def test_parse_args_all_flag(self):
        """Test parsing with --all flag."""
        with patch("sys.argv", ["eval", "--all"]):
            args = parse_args()
        assert args.all is True

    def test_parse_args_verbose(self):
        """Test parsing with verbose flag."""
        with patch("sys.argv", ["eval", "sudoku", "-v"]):
            args = parse_args()
        assert args.verbose is True

    def test_parse_args_list_games(self):
        """Test parsing with --list-games flag."""
        with patch("sys.argv", ["eval", "--list-games"]):
            args = parse_args()
        assert args.list_games is True

    def test_parse_args_max_moves(self):
        """Test parsing with --max-moves."""
        with patch("sys.argv", ["eval", "sudoku", "--max-moves", "500"]):
            args = parse_args()
        assert args.max_moves == 500


class TestMainFunction:
    """Tests for main CLI function."""

    def test_main_list_games(self):
        """Test main with --list-games."""
        captured = StringIO()
        with patch("sys.argv", ["eval", "--list-games"]):
            with patch("sys.stdout", captured):
                main()

        output = captured.getvalue()
        assert "Available games" in output
        assert "sudoku" in output

    def test_main_no_game_no_all(self):
        """Test main with no game and no --all flag."""
        import pytest

        with patch("sys.argv", ["eval"]):
            with pytest.raises(SystemExit) as exc_info:
                with patch("sys.stdout", StringIO()):
                    main()
            assert exc_info.value.code == 1

    def test_main_single_game_text(self):
        """Test main with single game and text output."""
        captured = StringIO()
        with patch("sys.argv", ["eval", "sudoku", "-n", "1"]):
            with patch("sys.stdout", captured):
                main()

        output = captured.getvalue()
        assert "Sudoku" in output

    def test_main_single_game_json(self):
        """Test main with single game and JSON output."""
        captured = StringIO()
        with patch("sys.argv", ["eval", "binary", "-n", "1", "-o", "json"]):
            with patch("sys.stdout", captured):
                main()

        output = captured.getvalue()
        assert "binary" in output
        assert "{" in output

    def test_main_single_game_csv(self):
        """Test main with single game and CSV output."""
        captured = StringIO()
        with patch("sys.argv", ["eval", "binary", "-n", "1", "-o", "csv"]):
            with patch("sys.stdout", captured):
                main()

        output = captured.getvalue()
        assert "game,difficulty" in output

    def test_main_single_game_markdown(self):
        """Test main with single game and markdown output."""
        captured = StringIO()
        with patch("sys.argv", ["eval", "binary", "-n", "1", "-o", "markdown"]):
            with patch("sys.stdout", captured):
                main()

        output = captured.getvalue()
        assert "#" in output
        assert "|" in output

    def test_main_single_game_with_seeds(self):
        """Test main with single game and specific seeds."""
        captured = StringIO()
        with patch("sys.argv", ["eval", "sudoku", "--seeds", "42,43"]):
            with patch("sys.stdout", captured):
                main()

        output = captured.getvalue()
        assert "Sudoku" in output

    def test_main_all_games_text(self):
        """Test main with --all flag and text output."""
        captured = StringIO()
        with patch("sys.argv", ["eval", "--all", "-n", "1"]):
            with patch("sys.stdout", captured):
                main()

        output = captured.getvalue()
        assert "PUZZLE ARCADE EVALUATION SUMMARY" in output

    def test_main_all_games_json(self):
        """Test main with --all flag and JSON output."""
        captured = StringIO()
        with patch("sys.argv", ["eval", "--all", "-n", "1", "-o", "json"]):
            with patch("sys.stdout", captured):
                main()

        output = captured.getvalue()
        assert "{" in output

    def test_main_all_games_csv(self):
        """Test main with --all flag and CSV output."""
        captured = StringIO()
        with patch("sys.argv", ["eval", "--all", "-n", "1", "-o", "csv"]):
            with patch("sys.stdout", captured):
                main()

        output = captured.getvalue()
        assert "game,difficulty" in output

    def test_main_all_games_markdown(self):
        """Test main with --all flag and markdown output."""
        captured = StringIO()
        with patch("sys.argv", ["eval", "--all", "-n", "1", "-o", "markdown"]):
            with patch("sys.stdout", captured):
                main()

        output = captured.getvalue()
        assert "#" in output

    def test_main_all_games_verbose(self):
        """Test main with --all flag and verbose."""
        captured = StringIO()
        with patch("sys.argv", ["eval", "--all", "-n", "1", "-v"]):
            with patch("sys.stdout", captured):
                main()

        output = captured.getvalue()
        assert "Evaluating" in output


class TestEpisodeTracer:
    """Tests for episode trace logging."""

    def test_tracer_memory_only(self):
        """Test tracer with memory-only output."""
        from puzzle_arcade_server.models import EpisodeTracer

        tracer = EpisodeTracer()

        episode_id = tracer.start_episode(game="sudoku", seed=42, difficulty="easy")
        assert episode_id.startswith("ep_")
        assert tracer.current_episode_id == episode_id

        tracer.log_observation(grid=[[1, 2], [3, 4]], valid_actions=["place 1 1 5"])
        tracer.log_action(action="place 1 1 5", success=True)
        tracer.log_hint(hint="Try row 2", hints_remaining=9)
        tracer.log_reasoning(thought="Row 2 needs a 5")
        tracer.end_episode(status="solved", moves=10, invalid_moves=2, hints_used=1, optimal_steps=8)

        events = tracer.events
        assert len(events) == 6
        assert events[0].type == "episode_start"
        assert events[1].type == "observation"
        assert events[2].type == "action"
        assert events[3].type == "hint"
        assert events[4].type == "reasoning"
        assert events[5].type == "episode_end"

        # Check episode_end data
        end_event = events[5]
        assert end_event.data["status"] == "solved"
        assert end_event.data["moves"] == 10
        assert end_event.data["efficiency"] == 0.8  # 8/10

    def test_tracer_file_output(self, tmp_path):
        """Test tracer with file output."""
        from puzzle_arcade_server.models import EpisodeTracer

        trace_file = tmp_path / "traces.jsonl"

        with EpisodeTracer(output=trace_file) as tracer:
            tracer.start_episode(game="kenken", seed=123, difficulty="medium")
            tracer.log_action(action="place 1 1 3", success=True)
            tracer.end_episode(status="solved", moves=5)

        # Check file was written
        assert trace_file.exists()
        lines = trace_file.read_text().strip().split("\n")
        assert len(lines) == 3

        # Parse and verify
        import json

        start_event = json.loads(lines[0])
        assert start_event["type"] == "episode_start"
        assert start_event["game"] == "kenken"
        assert start_event["seed"] == 123

        end_event = json.loads(lines[2])
        assert end_event["type"] == "episode_end"
        assert end_event["status"] == "solved"

    def test_tracer_with_solver_config(self):
        """Test tracer records solver config."""
        from puzzle_arcade_server.models import EpisodeTracer, SolverConfig

        tracer = EpisodeTracer()
        config = SolverConfig(solver_allowed=True, hint_budget=5, hint_penalty=0.1)

        tracer.start_episode(game="sudoku", seed=1, difficulty="hard", solver_config=config)
        tracer.end_episode(status="solved", moves=50)

        start_event = tracer.events[0]
        assert "solver_config" in start_event.data
        assert start_event.data["solver_config"]["hint_budget"] == 5
        assert start_event.data["solver_config"]["hint_penalty"] == 0.1

    def test_tracer_to_jsonl_format(self):
        """Test JSONL output format."""
        from puzzle_arcade_server.models import EpisodeTracer

        tracer = EpisodeTracer()
        tracer.start_episode(game="bridges", seed=99, difficulty="easy")

        event = tracer.events[0]
        jsonl = event.to_jsonl()

        import json

        parsed = json.loads(jsonl)
        assert parsed["type"] == "episode_start"
        assert parsed["id"].startswith("ep_")
        assert parsed["ts"] == 0
        assert parsed["game"] == "bridges"

    def test_tracer_no_events_before_start(self):
        """Test that events before start are ignored."""
        from puzzle_arcade_server.models import EpisodeTracer

        tracer = EpisodeTracer()

        # These should be no-ops
        tracer.log_action(action="place 1 1 1", success=True)
        tracer.log_observation(grid=[[]])
        tracer.end_episode(status="failed", moves=0)

        assert len(tracer.events) == 0

    def test_tracer_episode_status_enum(self):
        """Test tracer accepts EpisodeStatus enum."""
        from puzzle_arcade_server.models import EpisodeStatus, EpisodeTracer

        tracer = EpisodeTracer()
        tracer.start_episode(game="sudoku", seed=1, difficulty="easy")
        tracer.end_episode(status=EpisodeStatus.TIMEOUT, moves=10)

        end_event = tracer.events[1]
        assert end_event.data["status"] == "timeout"


class TestEvaluationSummary:
    """Tests for EvaluationSummary Pydantic model."""

    def test_creation(self):
        """Test creating an EvaluationSummary."""
        from puzzle_arcade_server.models.evaluation import EvaluationSummary

        summary = EvaluationSummary(
            game="sudoku",
            difficulty=DifficultyLevel.EASY,
            total_episodes=0,
            solved_count=0,
        )
        assert summary.game == "sudoku"
        assert summary.total_episodes == 0

    def test_solve_rate_empty(self):
        """Test solve rate with no episodes."""
        from puzzle_arcade_server.models.evaluation import EvaluationSummary

        summary = EvaluationSummary(
            game="sudoku",
            difficulty=DifficultyLevel.EASY,
            total_episodes=0,
            solved_count=0,
        )
        assert summary.solve_rate == 0.0

    def test_solve_rate_with_episodes(self):
        """Test solve rate with episodes."""
        from puzzle_arcade_server.models.evaluation import EvaluationSummary

        summary = EvaluationSummary(
            game="sudoku",
            difficulty=DifficultyLevel.EASY,
            total_episodes=10,
            solved_count=7,
        )
        assert summary.solve_rate == 0.7

    def test_avg_steps_empty(self):
        """Test avg steps with no episodes."""
        from puzzle_arcade_server.models.evaluation import EvaluationSummary

        summary = EvaluationSummary(
            game="sudoku",
            difficulty=DifficultyLevel.EASY,
            total_episodes=0,
            solved_count=0,
            episodes=[],
        )
        assert summary.avg_steps == 0.0

    def test_avg_steps_with_episodes(self):
        """Test avg steps with episodes."""
        from puzzle_arcade_server.models.evaluation import EvaluationSummary

        summary = EvaluationSummary(
            game="sudoku",
            difficulty=DifficultyLevel.EASY,
            total_episodes=2,
            solved_count=2,
            episodes=[
                make_episode(steps=10, optimal_steps=10),
                make_episode(steps=20, optimal_steps=10),
            ],
        )
        assert summary.avg_steps == 15.0

    def test_avg_efficiency_empty(self):
        """Test avg efficiency with no episodes."""
        from puzzle_arcade_server.models.evaluation import EvaluationSummary

        summary = EvaluationSummary(
            game="sudoku",
            difficulty=DifficultyLevel.EASY,
            total_episodes=0,
            solved_count=0,
            episodes=[],
        )
        assert summary.avg_efficiency == 0.0

    def test_avg_efficiency_with_solved(self):
        """Test avg efficiency with solved episodes."""
        from puzzle_arcade_server.models.evaluation import EvaluationSummary

        summary = EvaluationSummary(
            game="sudoku",
            difficulty=DifficultyLevel.EASY,
            total_episodes=2,
            solved_count=2,
            episodes=[
                make_episode(steps=10, optimal_steps=10),  # efficiency 1.0
                make_episode(steps=20, optimal_steps=10),  # efficiency 0.5
            ],
        )
        assert summary.avg_efficiency == 0.75

    def test_avg_time_ms_empty(self):
        """Test avg time with no episodes."""
        from puzzle_arcade_server.models.evaluation import EvaluationSummary

        summary = EvaluationSummary(
            game="sudoku",
            difficulty=DifficultyLevel.EASY,
            total_episodes=0,
            solved_count=0,
            episodes=[],
        )
        assert summary.avg_time_ms == 0.0

    def test_avg_time_ms_with_episodes(self):
        """Test avg time with episodes."""
        from puzzle_arcade_server.models.evaluation import EvaluationSummary

        summary = EvaluationSummary(
            game="sudoku",
            difficulty=DifficultyLevel.EASY,
            total_episodes=2,
            solved_count=2,
            episodes=[
                make_episode(time_ms=100),
                make_episode(time_ms=200),
            ],
        )
        assert summary.avg_time_ms == 150.0


class TestEpisodeResultEdgeCases:
    """Edge case tests for EpisodeResult."""

    def test_error_recovery_rate_no_errors(self):
        """Test error recovery rate with no errors."""
        result = make_episode(steps=10, invalid=0, status=EpisodeStatus.SOLVED)
        assert result.error_recovery_rate == 1.0

    def test_error_recovery_rate_failed(self):
        """Test error recovery rate when failed."""
        result = make_episode(steps=10, invalid=5, status=EpisodeStatus.FAILED)
        assert result.error_recovery_rate == 0.0

    def test_error_recovery_rate_recovered(self):
        """Test error recovery rate when recovered from errors."""
        result = make_episode(steps=10, invalid=5, status=EpisodeStatus.SOLVED)
        # error_rate = 5/15 = 0.333..., so error_recovery_rate = 1 - 0.333.. = 0.666..
        assert 0.6 < result.error_recovery_rate < 0.7

    def test_hint_dependency_no_steps(self):
        """Test hint dependency with no steps."""
        result = make_episode(steps=0, hints=5)
        assert result.hint_dependency == 0.0

    def test_hint_dependency_with_hints(self):
        """Test hint dependency with hints."""
        result = make_episode(steps=10, hints=5)
        assert result.hint_dependency == 0.5

    def test_adjusted_score(self):
        """Test adjusted score calculation."""
        # With no hints, adjusted should equal efficiency
        result = make_episode(steps=10, hints=0, optimal_steps=10)
        assert result.adjusted_score == 1.0

        # With hints, there should be a penalty
        result = make_episode(steps=10, hints=10, optimal_steps=10)
        # efficiency = 1.0, hint_dependency = 1.0, default hint_penalty = 0.0
        assert result.adjusted_score == 1.0  # No penalty when hint_penalty is 0

    def test_error_rate_zero_total(self):
        """Test error rate with zero total actions."""
        result = make_episode(steps=0, invalid=0)
        assert result.error_rate == 0.0
