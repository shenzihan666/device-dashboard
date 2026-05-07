"""Run `tsc --noEmit` for the frontend, cross-platform.

Invoked by the `typecheck-frontend` pre-commit hook. We use the project's own
TypeScript compiler from `node_modules` so contributors don't pay for an extra
pre-commit-managed Node sandbox download, and so the pinned tsc version always
matches what the build uses.

Behavior:
  * Resolves the bundled `tsc` binary at <frontend>/node_modules/.bin/tsc(.cmd).
  * If `node_modules` is absent (fresh clone, hooks installed before
    `npm install`), prints a friendly hint and exits 0 instead of blocking the
    commit. Re-run `npm install` to enable the check.
  * Otherwise runs `tsc --noEmit -p tsconfig.app.json` and forwards the exit
    code so the hook fails fast on type errors.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = REPO_ROOT / "frontend"


def _resolve_tsc() -> Path | None:
    bin_dir = FRONTEND / "node_modules" / ".bin"
    candidates = [bin_dir / "tsc.cmd", bin_dir / "tsc.ps1", bin_dir / "tsc"]
    for c in candidates:
        if c.exists():
            return c
    return None


def main() -> int:
    if not FRONTEND.is_dir():
        print(f"[typecheck-frontend] frontend dir not found at {FRONTEND}; skipping.")
        return 0

    tsc = _resolve_tsc()
    if tsc is None:
        print(
            "[typecheck-frontend] node_modules missing — run `npm install` in "
            "frontend/ to enable type-checking. Skipping.",
        )
        return 0

    cmd = [str(tsc), "--noEmit", "-p", "tsconfig.app.json"]
    if os.name == "nt" and tsc.suffix == "":
        # On Windows the bare-name shim only works through the shell.
        cmd = " ".join(cmd)
        return subprocess.call(cmd, cwd=FRONTEND, shell=True)

    return subprocess.call(cmd, cwd=FRONTEND)


if __name__ == "__main__":
    sys.exit(main())
