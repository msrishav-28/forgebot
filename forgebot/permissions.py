"""Permission scopes. Enforced, not suggested.

A bot's manifest declares what it may do; the engine checks EVERY action
against this list before handing tools to the agent or applying output.
"""

from __future__ import annotations

# Every scope the engine knows how to grant.
KNOWN_SCOPES = {
    "read:repo",        # read files, git log/diff/blame
    "read:runs_dir",    # read watch-directory files
    "write:comments",   # post issue/PR comments (via gh cli)
    "write:pr",         # open pull requests (via gh cli)
    "write:files",      # modify working-tree files
}

READ_SCOPES = {"read:repo", "read:runs_dir"}
WRITE_SCOPES = {"write:comments", "write:pr", "write:files"}


class PermissionDenied(RuntimeError):
    pass


def validate(scopes: list[str]) -> list[str]:
    unknown = [s for s in scopes if s not in KNOWN_SCOPES]
    if unknown:
        raise PermissionError(f"Unknown permission scopes: {unknown}")
    return scopes


def allowed(scopes: list[str], scope: str) -> bool:
    return scope in set(scopes)


def require(scopes: list[str], scope: str, bot_name: str = "bot") -> None:
    """Raise unless the bot is allowed `scope`. Engine calls this before every action."""
    if not allowed(scopes, scope):
        raise PermissionDenied(
            f"[{bot_name}] permission denied: '{scope}' not in manifest {scopes}"
        )
