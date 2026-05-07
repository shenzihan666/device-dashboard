"""Run pytest for the connection-dashboard backend, cross-platform.

Invoked by the `pytest-backend` pre-push hook. Resolves pytest in this order:

  1. <project>/.venv (Windows: Scripts/, POSIX: bin/)
  2. Whatever `python -m pytest` resolves on PATH

If neither is available, prints a setup hint and exits non-zero so the push is
blocked (tests are not optional pre-push). Use `git push --no-verify` if you
absolutely must bypass — see the project README.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT = REPO_ROOT / "connection-dashboard"
VENV = PROJECT / ".venv"


def _venv_pytest() -> Path | None:
    if os.name == "nt":
        candidate = VENV / "Scripts" / "pytest.exe"
    else:
        candidate = VENV / "bin" / "pytest"
    return candidate if candidate.exists() else None


def main() -> int:
    if not PROJECT.is_dir():
        print(f"[pytest-backend] project not found at {PROJECT}; nothing to test.")
        return 0

    pytest_bin = _venv_pytest()
    if pytest_bin is not None:
        cmd: list[str] = [str(pytest_bin)]
    elif shutil.which("pytest"):
        cmd = ["pytest"]
    else:
        print(
            "[pytest-backend] pytest not found. Install dev deps:\n"
            "    cd connection-dashboard\n"
            "    pip install -e .[dev]\n"
            "  or activate the project venv before pushing.",
            file=sys.stderr,
        )
        return 1

    cmd += ["-q", "tests"]
    return subprocess.call(cmd, cwd=PROJECT)


if __name__ == "__main__":
    sys.exit(main())
