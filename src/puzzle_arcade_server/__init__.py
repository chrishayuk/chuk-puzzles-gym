"""Puzzle Arcade Server - Multi-game puzzle server for telnet connections."""

__version__ = "0.1.0"


# Lazy import to avoid loading chuk_protocol_server during tests
def __getattr__(name):
    if name == "ArcadeHandler":
        from .server import ArcadeHandler

        return ArcadeHandler
    if name == "PuzzleEnv":
        from .gym_env import PuzzleEnv

        return PuzzleEnv
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ArcadeHandler", "PuzzleEnv", "__version__"]
