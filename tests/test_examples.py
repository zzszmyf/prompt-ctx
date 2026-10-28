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

"""The runnable examples keep their budget and mode stories."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from prompt_ctx import Assembler

ROOT = Path(__file__).resolve().parents[1]
BUDGET = 2000


def _load_template(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.template


def test_readme_leads_with_positioning_and_real_counts():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    template = _load_template(ROOT / "examples" / "bloated_system_prompt.py")
    report = Assembler(template).assemble_with_report(budget=BUDGET, model="gpt-4o")
    assert readme.startswith("# prompt-ctx\n\nProduction system prompts are software.")
    assert "doesn’t burn the context window on dead rules." in readme.split("## ", 1)[0]
    assert f"{report.tokens_before:,}" in readme
    assert f"{report.tokens_after:,}" in readme
    assert f"{report.tokens_saved:,}" in readme
    assert "examples/claude-code-style/" in readme
    assert "examples/budget_demo.py" in readme


def test_bloated_prompt_drops_dead_rules_under_budget():
    template = _load_template(ROOT / "examples" / "bloated_system_prompt.py")
    report = Assembler(template).assemble_with_report(budget=BUDGET, model="gpt-4o")

    assert report.tokens_before > BUDGET
    assert report.tokens_after <= BUDGET
    assert report.tokens_after >= 1500
    assert report.within_budget
    assert report.tokens_saved == report.tokens_before - report.tokens_after
    assert report.dropped
    assert "identity" in report.kept
    assert "legacy_tone_guide_2019" in report.dropped
    assert "stale_vendor_sdk_notes" in report.dropped

    kept_priority = [d.priority for d in report.decisions if d.kept]
    dropped_priority = [d.priority for d in report.decisions if not d.kept]
    assert max(kept_priority) < min(dropped_priority)


def test_budget_demo_script():
    completed = subprocess.run(
        [sys.executable, str(ROOT / "examples" / "budget_demo.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    out = completed.stdout
    assert "--budget 2000" in out
    assert "BEFORE" in out and "AFTER" in out and "SAVED" in out
    assert "legacy_tone_guide_2019" in out
    assert "identity" in out


def test_claude_code_style_modes():
    script = ROOT / "examples" / "claude-code-style" / "run.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    out = completed.stdout
    assert "mode=coding" in out
    assert "mode=chat" in out
    assert "legacy_apply_model" in out
    assert "editing" in out
    assert "conversation" in out
