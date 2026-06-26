"""Make a violated architecture contract a pytest failure, not just a CI step.

Runs the import-linter contracts; if any fails, this test fails with the full
output so the offending edge is obvious.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_lint_imports_passes() -> None:
    environment = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        ["uv", "run", "lint-imports"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    assert result.returncode == 0, (
        f"lint-imports failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
