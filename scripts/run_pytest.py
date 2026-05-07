"""Run pytest for the backend, cross-platform.

Invoked by the `pytest-backend` pre-push hook. Uses `python -m pytest` instead
of the `pytest` console script so a broken `pytest.exe` shim on Windows does not
block pushes when pytest is installed in the venv.

Resolution order:

  1. <repo>/.venv `python.exe` (`-m pytest`) if pytest imports
  2. `sys.executable` (`-m pytest`) if pytest imports
  3. `pytest` on PATH

If pytest cannot be run, prints a setup hint and exits non-zero. Use
`git push --no-verify` sparingly — see the project README.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENV = REPO_ROOT / ".venv"
TESTS_DIR = REPO_ROOT / "tests"


def _venv_python() -> Path | None:
    if os.name == "nt":
        candidate = VENV / "Scripts" / "python.exe"
    else:
        candidate = VENV / "bin" / "python"
    return candidate if candidate.exists() else None


def _has_pytest(py: Path) -> bool:
    return (
        subprocess.run(
            [str(py), "-c", "import pytest"],
            cwd=REPO_ROOT,
            capture_output=True,
        ).returncode
        == 0
    )


def main() -> int:
    if not TESTS_DIR.is_dir():
        print(f"[pytest-backend] tests dir not found at {TESTS_DIR}; nothing to test.")
        return 0

    vp = _venv_python()
    if vp is not None and _has_pytest(vp):
        return subprocess.call([str(vp), "-m", "pytest", "-q", "tests"], cwd=REPO_ROOT)

    interp = Path(sys.executable)
    if _has_pytest(interp):
        return subprocess.call([str(interp), "-m", "pytest", "-q", "tests"], cwd=REPO_ROOT)

    pytest_bin = shutil.which("pytest")
    if pytest_bin:
        return subprocess.call([pytest_bin, "-q", "tests"], cwd=REPO_ROOT)

    print(
        "[pytest-backend] pytest not found. Install dev deps:\n"
        "    pip install -e .[dev]\n"
        "  or activate the project venv before pushing.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
