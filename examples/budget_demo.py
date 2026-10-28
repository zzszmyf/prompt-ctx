# Copyright 2026 The prompt-ctx Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Show a bloated system prompt assembled under a token budget.

Production system prompts are software. prompt-ctx versions, budgets, and
assembles them so your agent doesn’t burn the context window on dead rules.

Install (from a fresh clone of this repository):

    uv sync

Run, from the clone root:

    uv run python examples/budget_demo.py

That command runs:

    prompt-ctx assemble examples/bloated_system_prompt.py --budget 2000 --report

The report prints the bloated token count, the assembled token count, and
which low-priority sections were dropped.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    config = Path(__file__).resolve().parent / "bloated_system_prompt.py"
    if not config.is_file():
        print(f"missing prompt config: {config}", file=sys.stderr)
        return 1

    try:
        shown = config.relative_to(Path.cwd())
    except ValueError:
        shown = config

    cmd = [
        sys.executable,
        "-m",
        "prompt_ctx",
        "assemble",
        str(shown),
        "--budget",
        "2000",
        "--report",
    ]
    completed = subprocess.run(cmd)
    if completed.returncode != 0:
        print(
            "\nIf prompt-ctx is not installed, run `uv sync` from the clone root "
            "and then `uv run python examples/budget_demo.py`.",
            file=sys.stderr,
        )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
