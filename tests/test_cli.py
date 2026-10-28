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

"""Tests for the prompt-ctx CLI."""

from __future__ import annotations

import pytest

from prompt_ctx.cli import _build_parser, main


CONFIG = """
from prompt_ctx import PromptTemplate, Section

template = PromptTemplate("cli")
template.add_section(Section(name="core", content="KEEP_CORE " * 20, priority=0))
template.add_section(Section(name="dead", content="DROP_DEAD " * 80, priority=200))
"""


def test_parser_accepts_budget_and_report(tmp_path):
    parser = _build_parser()
    args = parser.parse_args(
        ["assemble", str(tmp_path / "p.py"), "--budget", "2000", "--report", "--model", "gpt-4o"]
    )
    assert args.command == "assemble"
    assert args.budget == 2000
    assert args.report is True
    assert args.model == "gpt-4o"


def test_assemble_report_shows_drop_list(tmp_path, capsys, monkeypatch):
    cfg = tmp_path / "prompt.py"
    cfg.write_text(CONFIG)
    monkeypatch.setattr(
        "sys.argv",
        ["prompt-ctx", "assemble", str(cfg), "--budget", "80", "--report"],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "BEFORE" in out
    assert "AFTER" in out
    assert "SAVED" in out
    kept, _, dropped = out.partition("DROPPED")
    assert "core" in kept
    assert "dead" not in kept
    assert "dead" in dropped
    assert "KEEP_CORE" not in out
    assert "DROP_DEAD" not in out


def test_assemble_without_report_prints_prompt(tmp_path, capsys, monkeypatch):
    cfg = tmp_path / "prompt.py"
    cfg.write_text(CONFIG)
    monkeypatch.setattr(
        "sys.argv",
        ["prompt-ctx", "assemble", str(cfg), "--budget", "100000"],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "KEEP_CORE" in out
    assert "DROP_DEAD" in out
    assert "DROPPED" not in out


def test_negative_budget_fails(tmp_path, capsys, monkeypatch):
    cfg = tmp_path / "prompt.py"
    cfg.write_text(CONFIG)
    monkeypatch.setattr(
        "sys.argv",
        ["prompt-ctx", "assemble", str(cfg), "--budget", "-5"],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "budget" in err
