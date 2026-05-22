"""
Dynamic discovery of the displayplacer binary.
Works with Homebrew (Apple Silicon & Intel), uv, pyenv, and manual installs.
"""

import shutil
import subprocess

_FALLBACK_PATHS = [
    "/opt/homebrew/bin/displayplacer",  # Apple Silicon Homebrew
    "/usr/local/bin/displayplacer",     # Intel Homebrew
]

_cached_path: str | None = None
_discovery_done: bool = False


def find_displayplacer() -> str | None:
    """Return the first usable displayplacer path, or None if not found.

    Result is cached after the first successful call.
    """
    global _cached_path, _discovery_done
    if _discovery_done:
        return _cached_path

    # Prefer PATH lookup — works with uv, pyenv, nix, and non-standard installs
    found = shutil.which("displayplacer")
    if found:
        _cached_path = found
        _discovery_done = True
        return _cached_path

    # Fall back to known Homebrew paths
    for path in _FALLBACK_PATHS:
        try:
            result = subprocess.run([path, "--version"], capture_output=True, timeout=5)
            if result.returncode == 0:
                _cached_path = path
                _discovery_done = True
                return _cached_path
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue

    _discovery_done = True
    return None


def require_displayplacer() -> str:
    """Return the displayplacer path, raising RuntimeError if not found."""
    path = find_displayplacer()
    if path is None:
        raise RuntimeError(
            "displayplacer not found. Install it with:\n"
            "  brew install jakehilborn/jakehilborn/displayplacer"
        )
    return path


def invalidate_cache() -> None:
    """Clear the cached path (useful after installation)."""
    global _cached_path, _discovery_done
    _cached_path = None
    _discovery_done = False
