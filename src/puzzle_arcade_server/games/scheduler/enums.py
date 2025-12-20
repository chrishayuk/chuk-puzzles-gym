"""Scheduler game enums."""

from enum import Enum


class SchedulerAction(str, Enum):
    """Actions for Scheduler game."""

    ASSIGN = "assign"
    UNASSIGN = "unassign"
