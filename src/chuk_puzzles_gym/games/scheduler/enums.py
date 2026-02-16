"""Scheduler game enums."""

from enum import StrEnum


class SchedulerAction(StrEnum):
    """Actions for Scheduler game."""

    ASSIGN = "assign"
    UNASSIGN = "unassign"
