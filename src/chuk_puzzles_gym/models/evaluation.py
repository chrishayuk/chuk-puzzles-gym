"""Evaluation and scoring models for the Puzzle Arcade server.

These models support the standardised evaluation schema for benchmarking
agent performance across puzzles.

Re-exports core types from chuk-gym-core for convenience.
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

# Import core types from chuk-gym-core
from chuk_gym_core import (
    SolverConfig,
)
from pydantic import BaseModel, ConfigDict, Field, computed_field

from .enums import DifficultyLevel, EpisodeStatus


class MoveRecord(BaseModel):
    """Record of a single move in an episode for step-level analysis."""

    model_config = ConfigDict(frozen=True)

    step: int = Field(ge=0, description="Step number in episode (0-indexed)")
    action: str = Field(description="Action taken (e.g., 'place 1 5 7')")
    success: bool = Field(description="Whether the move was valid")
    advances_solution: bool = Field(
        default=True,
        description="Whether this move advances toward solution (not a backtrack)",
    )
    hint_used: bool = Field(default=False, description="Whether this move came from a hint")
    timestamp_ms: int = Field(default=0, description="Milliseconds since episode start")


class ReasoningMetrics(BaseModel):
    """Reasoning depth metrics for evaluating quality of agent reasoning.

    Goes beyond binary success/failure to measure *how* an agent reasons:
    - Backtrack detection: did the agent revise previous placements?
    - Progress tracking: how steadily did the agent make progress?
    - Error patterns: were errors isolated or clustered in streaks?
    - Reasoning overhead: how much wasted work relative to optimal?
    """

    model_config = ConfigDict(frozen=True)

    # Raw tracking data
    backtrack_count: int = Field(
        default=0,
        ge=0,
        description="Times agent placed a value at a previously filled position",
    )
    solver_distance_trace: list[int] = Field(
        default_factory=list,
        description="Remaining positions to fill after each valid move",
    )
    error_streak_max: int = Field(
        default=0,
        ge=0,
        description="Longest consecutive run of invalid moves",
    )
    error_streaks: list[int] = Field(
        default_factory=list,
        description="Lengths of each consecutive error streak",
    )
    total_actions: int = Field(
        default=0,
        ge=0,
        description="Total actions taken (valid + invalid)",
    )
    optimal_path_length: int | None = Field(
        default=None,
        ge=1,
        description="Minimum steps to solve (from solver)",
    )

    @computed_field
    @property
    def reasoning_overhead(self) -> float:
        """Ratio of total actions to optimal path length.

        1.0 = perfect (no wasted actions). Higher = more wasted reasoning.
        Returns 0.0 if optimal path length is unknown.
        """
        if self.optimal_path_length is None or self.optimal_path_length == 0:
            return 0.0
        if self.total_actions == 0:
            return 0.0
        return self.total_actions / self.optimal_path_length

    @computed_field
    @property
    def backtrack_rate(self) -> float:
        """Fraction of valid moves that were backtracks (revisions).

        0.0 = no backtracks, 1.0 = every move was a revision.
        """
        valid_moves = len(self.solver_distance_trace)
        if valid_moves == 0:
            return 0.0
        return self.backtrack_count / valid_moves

    @computed_field
    @property
    def progress_velocity(self) -> float:
        """Average progress per valid move (cells solved per step).

        Measures how much closer to the solution each move gets.
        1.0 = every move reduces remaining by exactly 1. Lower = backtracks/plateaus.
        Returns 0.0 if insufficient data.
        """
        trace = self.solver_distance_trace
        if len(trace) < 2:
            return 0.0
        total_progress = trace[0] - trace[-1]
        steps = len(trace) - 1
        if steps == 0:
            return 0.0
        return total_progress / steps

    @computed_field
    @property
    def progress_steadiness(self) -> float:
        """Measure of how monotonically progress decreased (0.0 to 1.0).

        1.0 = perfectly monotonic progress (every move reduced remaining count).
        0.0 = no monotonic progress at all.
        """
        trace = self.solver_distance_trace
        if len(trace) < 2:
            return 1.0
        monotonic_steps = sum(1 for i in range(1, len(trace)) if trace[i] < trace[i - 1])
        return monotonic_steps / (len(trace) - 1)

    @computed_field
    @property
    def avg_error_streak(self) -> float:
        """Average length of consecutive error streaks.

        Returns 0.0 if no error streaks occurred.
        """
        if not self.error_streaks:
            return 0.0
        return sum(self.error_streaks) / len(self.error_streaks)

    def to_dict(self) -> dict[str, Any]:
        """Convert to flat dictionary for reporting."""
        return {
            "backtrack_count": self.backtrack_count,
            "backtrack_rate": round(self.backtrack_rate, 3),
            "reasoning_overhead": round(self.reasoning_overhead, 3),
            "progress_velocity": round(self.progress_velocity, 3),
            "progress_steadiness": round(self.progress_steadiness, 3),
            "error_streak_max": self.error_streak_max,
            "avg_error_streak": round(self.avg_error_streak, 3),
            "total_actions": self.total_actions,
            "optimal_path_length": self.optimal_path_length,
        }


class EpisodeResult(BaseModel):
    """Complete result of a single puzzle episode with normalized metrics.

    This is the core output format that turns Puzzle Arcade into:
    - A benchmark (comparable scores)
    - An RL environment (reward signals)
    - A regression test suite for agents
    """

    model_config = ConfigDict(frozen=True)

    # Identity
    game: str = Field(description="Game identifier (e.g., 'sudoku')")
    difficulty: DifficultyLevel = Field(description="Difficulty level")
    seed: int = Field(description="Reproducible puzzle seed")

    # Timing
    started_at: datetime = Field(description="Episode start timestamp")
    ended_at: datetime = Field(description="Episode end timestamp")
    wall_time_ms: int = Field(ge=0, description="Total wall clock time in milliseconds")

    # Outcome
    status: EpisodeStatus = Field(description="Final episode status")

    # Raw metrics
    steps_taken: int = Field(ge=0, description="Total valid moves made")
    invalid_actions: int = Field(ge=0, description="Rejected/invalid moves")
    hints_used: int = Field(ge=0, description="Solver hints consumed")
    retries: int = Field(
        default=0,
        ge=0,
        description="Attempts on same cell (backtracking indicator)",
    )

    # Ground truth reference (if available)
    optimal_steps: int | None = Field(
        default=None,
        ge=1,
        description="Minimum steps to solve (from solver)",
    )

    # Solver configuration used
    solver_config: SolverConfig = Field(
        default_factory=SolverConfig,
        description="Solver/hint configuration for this episode",
    )

    # Optional step-level trace
    move_history: list[MoveRecord] = Field(
        default_factory=list,
        description="Complete move history for detailed analysis",
    )

    # Reasoning depth metrics
    reasoning_metrics: ReasoningMetrics | None = Field(
        default=None,
        description="Detailed reasoning depth metrics (backtracks, progress, error patterns)",
    )

    # Computed normalized metrics
    @computed_field
    @property
    def success(self) -> bool:
        """Whether the puzzle was solved."""
        return self.status == EpisodeStatus.SOLVED

    @computed_field
    @property
    def efficiency_score(self) -> float:
        """Ratio of optimal steps to actual steps (1.0 = optimal).

        Returns 0.0 if puzzle not solved or optimal_steps unknown.
        """
        if not self.success or self.optimal_steps is None or self.steps_taken == 0:
            return 0.0
        return min(1.0, self.optimal_steps / self.steps_taken)

    @computed_field
    @property
    def error_rate(self) -> float:
        """Ratio of invalid actions to total actions."""
        total = self.steps_taken + self.invalid_actions
        if total == 0:
            return 0.0
        return self.invalid_actions / total

    @computed_field
    @property
    def error_recovery_rate(self) -> float:
        """Ratio of successful corrections after errors.

        Approximated as: if we had errors but still solved, we recovered.
        More accurate tracking requires move_history analysis.
        """
        if self.invalid_actions == 0:
            return 1.0  # No errors to recover from
        if not self.success:
            return 0.0  # Failed to recover
        # Approximation: solved despite errors
        return 1.0 - self.error_rate

    @computed_field
    @property
    def hint_dependency(self) -> float:
        """Ratio of moves that came from hints (tool dependency)."""
        if self.steps_taken == 0:
            return 0.0
        return min(1.0, self.hints_used / self.steps_taken)

    @computed_field
    @property
    def adjusted_score(self) -> float:
        """Final score accounting for efficiency and hint penalties.

        Score = efficiency_score * (1 - hint_penalty * hint_dependency)
        """
        base_score = self.efficiency_score
        penalty = self.solver_config.hint_penalty * self.hint_dependency
        return max(0.0, base_score * (1 - penalty))

    def to_summary_dict(self) -> dict[str, Any]:
        """One-line episode summary for logging/streaming."""
        d: dict[str, Any] = {
            "game": self.game,
            "seed": self.seed,
            "difficulty": self.difficulty.value,
            "success": self.success,
            "steps": self.steps_taken,
            "invalid": self.invalid_actions,
            "hints": self.hints_used,
            "efficiency": round(self.efficiency_score, 3),
            "time_ms": self.wall_time_ms,
        }
        if self.reasoning_metrics is not None:
            d["reasoning"] = self.reasoning_metrics.to_dict()
        return d

    def to_jsonl(self) -> str:
        """Single-line JSON for streaming output."""
        import json

        return json.dumps(self.to_summary_dict())


class EvaluationSummary(BaseModel):
    """Aggregated summary of multiple episodes for a game/difficulty."""

    model_config = ConfigDict(frozen=True)

    game: str
    difficulty: DifficultyLevel
    total_episodes: int = Field(ge=0)
    solved_count: int = Field(ge=0)
    episodes: list[EpisodeResult] = Field(default_factory=list)

    @computed_field
    @property
    def solve_rate(self) -> float:
        """Fraction of episodes solved."""
        if self.total_episodes == 0:
            return 0.0
        return self.solved_count / self.total_episodes

    @computed_field
    @property
    def avg_steps(self) -> float:
        """Average steps taken across all episodes."""
        if not self.episodes:
            return 0.0
        return sum(e.steps_taken for e in self.episodes) / len(self.episodes)

    @computed_field
    @property
    def avg_efficiency(self) -> float:
        """Average efficiency score across solved episodes."""
        solved = [e for e in self.episodes if e.success]
        if not solved:
            return 0.0
        return sum(e.efficiency_score for e in solved) / len(solved)

    @computed_field
    @property
    def avg_time_ms(self) -> float:
        """Average wall time across all episodes."""
        if not self.episodes:
            return 0.0
        return sum(e.wall_time_ms for e in self.episodes) / len(self.episodes)

    @computed_field
    @property
    def avg_backtrack_rate(self) -> float:
        """Average backtrack rate across episodes with reasoning metrics."""
        with_metrics = [e for e in self.episodes if e.reasoning_metrics is not None]
        if not with_metrics:
            return 0.0
        return sum(e.reasoning_metrics.backtrack_rate for e in with_metrics) / len(with_metrics)  # type: ignore[union-attr]

    @computed_field
    @property
    def avg_reasoning_overhead(self) -> float:
        """Average reasoning overhead across episodes with reasoning metrics."""
        with_metrics = [
            e for e in self.episodes if e.reasoning_metrics is not None and e.reasoning_metrics.reasoning_overhead > 0
        ]
        if not with_metrics:
            return 0.0
        return sum(e.reasoning_metrics.reasoning_overhead for e in with_metrics) / len(with_metrics)  # type: ignore[union-attr]

    @computed_field
    @property
    def avg_progress_steadiness(self) -> float:
        """Average progress steadiness across episodes with reasoning metrics."""
        with_metrics = [e for e in self.episodes if e.reasoning_metrics is not None]
        if not with_metrics:
            return 0.0
        return sum(e.reasoning_metrics.progress_steadiness for e in with_metrics) / len(with_metrics)  # type: ignore[union-attr]


class TraceEvent(BaseModel):
    """A single event in an episode trace for JSONL logging."""

    model_config = ConfigDict(frozen=True)

    type: str = Field(description="Event type: episode_start, observation, action, hint, episode_end")
    episode_id: str = Field(description="Unique episode identifier")
    timestamp_ms: int = Field(description="Milliseconds since episode start")
    data: dict[str, Any] = Field(default_factory=dict, description="Event-specific data")

    def to_jsonl(self) -> str:
        """Convert to single-line JSON for streaming."""
        return json.dumps({"type": self.type, "id": self.episode_id, "ts": self.timestamp_ms, **self.data})


class EpisodeTracer:
    """Traces complete episodes in JSONL format for offline analysis.

    Usage:
        tracer = EpisodeTracer(output_path="traces.jsonl")

        # Start episode
        tracer.start_episode(game="sudoku", seed=42, difficulty="medium")

        # Log observations
        tracer.log_observation(grid=[[...]], valid_actions=[...])

        # Log actions
        tracer.log_action(action="place 1 5 7", success=True)

        # Log hints
        tracer.log_hint(hint="Try row 3, column 4")

        # End episode
        tracer.end_episode(status="solved", moves=45, efficiency=0.92)

    Output format (JSONL):
        {"type":"episode_start","id":"ep_abc123","ts":0,"game":"sudoku","seed":42,"difficulty":"medium"}
        {"type":"observation","id":"ep_abc123","ts":100,"grid":[...],"valid_actions":[...]}
        {"type":"action","id":"ep_abc123","ts":150,"action":"place 1 5 7","success":true}
        {"type":"episode_end","id":"ep_abc123","ts":12400,"status":"solved","moves":45,"efficiency":0.92}
    """

    def __init__(self, output: str | Path | TextIO | None = None):
        """Initialize the tracer.

        Args:
            output: Output destination - file path, Path object, file handle, or None for memory-only
        """
        self._output: TextIO | None = None
        self._owns_file = False
        self._events: list[TraceEvent] = []

        if output is not None:
            if isinstance(output, str | Path):
                self._output = open(output, "a", encoding="utf-8")
                self._owns_file = True
            else:
                self._output = output

        self._episode_id: str | None = None
        self._start_time_ns: int = 0
        self._game: str = ""
        self._seed: int = 0
        self._difficulty: str = ""

    def __enter__(self) -> "EpisodeTracer":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """Close the output file if we own it."""
        if self._owns_file and self._output:
            self._output.close()
            self._output = None

    def _elapsed_ms(self) -> int:
        """Get milliseconds since episode start."""
        if self._start_time_ns == 0:
            return 0
        return int((time.time_ns() - self._start_time_ns) / 1_000_000)

    def _emit(self, event: TraceEvent) -> None:
        """Emit an event to output and memory."""
        self._events.append(event)
        if self._output:
            self._output.write(event.to_jsonl() + "\n")
            self._output.flush()

    def start_episode(
        self,
        game: str,
        seed: int,
        difficulty: str,
        solver_config: SolverConfig | None = None,
        **extra: Any,
    ) -> str:
        """Start tracing a new episode.

        Args:
            game: Game identifier
            seed: Puzzle seed
            difficulty: Difficulty level
            solver_config: Solver configuration
            **extra: Additional metadata to include

        Returns:
            Episode ID for reference
        """
        self._episode_id = f"ep_{uuid.uuid4().hex[:12]}"
        self._start_time_ns = time.time_ns()
        self._game = game
        self._seed = seed
        self._difficulty = difficulty
        self._events = []

        data: dict[str, Any] = {
            "game": game,
            "seed": seed,
            "difficulty": difficulty,
        }
        if solver_config:
            data["solver_config"] = {
                "solver_allowed": solver_config.solver_allowed,
                "hint_budget": solver_config.hint_budget,
                "hint_penalty": solver_config.hint_penalty,
            }
        data.update(extra)

        event = TraceEvent(type="episode_start", episode_id=self._episode_id, timestamp_ms=0, data=data)
        self._emit(event)

        return self._episode_id

    def log_observation(self, grid: Any = None, valid_actions: list[str] | None = None, **extra: Any) -> None:
        """Log a state observation.

        Args:
            grid: Current grid state
            valid_actions: List of valid actions
            **extra: Additional observation data
        """
        if not self._episode_id:
            return

        data: dict[str, Any] = {}
        if grid is not None:
            data["grid"] = grid
        if valid_actions is not None:
            data["valid_actions"] = valid_actions
        data.update(extra)

        event = TraceEvent(type="observation", episode_id=self._episode_id, timestamp_ms=self._elapsed_ms(), data=data)
        self._emit(event)

    def log_action(self, action: str, success: bool, **extra: Any) -> None:
        """Log an action taken.

        Args:
            action: Action string (e.g., 'place 1 5 7')
            success: Whether the action was valid
            **extra: Additional action data (e.g., result message)
        """
        if not self._episode_id:
            return

        data: dict[str, Any] = {"action": action, "success": success}
        data.update(extra)

        event = TraceEvent(type="action", episode_id=self._episode_id, timestamp_ms=self._elapsed_ms(), data=data)
        self._emit(event)

    def log_hint(self, hint: str, hints_remaining: int | None = None, **extra: Any) -> None:
        """Log a hint request.

        Args:
            hint: Hint content
            hints_remaining: Remaining hint budget
            **extra: Additional hint data
        """
        if not self._episode_id:
            return

        data: dict[str, Any] = {"hint": hint}
        if hints_remaining is not None:
            data["hints_remaining"] = hints_remaining
        data.update(extra)

        event = TraceEvent(type="hint", episode_id=self._episode_id, timestamp_ms=self._elapsed_ms(), data=data)
        self._emit(event)

    def log_reasoning(self, thought: str, **extra: Any) -> None:
        """Log agent reasoning/thought.

        Args:
            thought: Reasoning content
            **extra: Additional data
        """
        if not self._episode_id:
            return

        data: dict[str, Any] = {"thought": thought}
        data.update(extra)

        event = TraceEvent(type="reasoning", episode_id=self._episode_id, timestamp_ms=self._elapsed_ms(), data=data)
        self._emit(event)

    def end_episode(
        self,
        status: str | EpisodeStatus,
        moves: int = 0,
        invalid_moves: int = 0,
        hints_used: int = 0,
        optimal_steps: int | None = None,
        **extra: Any,
    ) -> None:
        """End the current episode.

        Args:
            status: Final status (solved, failed, timeout, abandoned)
            moves: Total valid moves made
            invalid_moves: Total invalid attempts
            hints_used: Total hints consumed
            optimal_steps: Minimum steps (if known)
            **extra: Additional final data
        """
        if not self._episode_id:
            return

        if isinstance(status, EpisodeStatus):
            status = status.value

        elapsed = self._elapsed_ms()
        efficiency = 0.0
        if status == "solved" and optimal_steps and moves > 0:
            efficiency = min(1.0, optimal_steps / moves)

        data: dict[str, Any] = {
            "status": status,
            "moves": moves,
            "invalid_moves": invalid_moves,
            "hints_used": hints_used,
            "wall_time_ms": elapsed,
        }
        if optimal_steps is not None:
            data["optimal_steps"] = optimal_steps
            data["efficiency"] = round(efficiency, 3)
        data.update(extra)

        event = TraceEvent(type="episode_end", episode_id=self._episode_id, timestamp_ms=elapsed, data=data)
        self._emit(event)

        # Reset state
        self._episode_id = None
        self._start_time_ns = 0

    @property
    def events(self) -> list[TraceEvent]:
        """Get all events for current/last episode."""
        return self._events.copy()

    @property
    def current_episode_id(self) -> str | None:
        """Get current episode ID, or None if not in episode."""
        return self._episode_id
