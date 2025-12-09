"""Puzzle Arcade Server - Multi-game puzzle server for telnet connections."""

__version__ = "0.1.0"


# Lazy import to avoid loading chuk_protocol_server during tests
def __getattr__(name):
    if name == "ArcadeHandler":
        from .server import ArcadeHandler

        return ArcadeHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ArcadeHandler", "__version__"]
