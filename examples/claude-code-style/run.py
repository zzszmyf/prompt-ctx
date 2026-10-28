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

"""Assemble the same section library in coding mode and chat mode.

Install (from a fresh clone):

    uv sync

Run, from the clone root:

    uv run python examples/claude-code-style/run.py

Include rules live on each section as ``conditions``. Priority decides what
a budget keeps. Coding mode carries an extra low-priority dead rule so the
second pass can show it dropped under a tight budget.
"""

from __future__ import annotations

import sys

from prompt_ctx import Assembler

from sections import build_template, section_library

# Fits the live coding sections and drops legacy_apply_model.
CODING_BUDGET = 250


def _include_label(conditions: dict) -> str:
    if not conditions:
        return "always"
    return ", ".join(f"{key}={value}" for key, value in conditions.items())


def _print_mode(title: str, report) -> None:
    names = ", ".join(report.kept) if report.kept else "(none)"
    dropped = ", ".join(report.dropped) if report.dropped else "(none)"
    print(title)
    print(f"  tokens:  {report.tokens_after}")
    print(f"  kept:    {names}")
    print(f"  dropped: {dropped}")
    print()


def main() -> int:
    library = section_library()
    template = build_template()
    assembler = Assembler(template)

    print("claude-code-style")
    print("one section library, two modes")
    print()
    print(f"{'section':<24} {'priority':>8}  include")
    print(f"{'-------':<24} {'--------':>8}  -------")
    for section in sorted(library, key=lambda item: (item.priority, item.name)):
        label = _include_label(section.conditions)
        print(f"{section.name:<24} {section.priority:>8}  {label}")
    print()

    coding = assembler.assemble_with_report(mode="coding")
    chat = assembler.assemble_with_report(mode="chat")
    coding_budget = assembler.assemble_with_report(mode="coding", budget=CODING_BUDGET)

    _print_mode("MODE coding", coding)
    _print_mode("MODE chat", chat)
    _print_mode(f"MODE coding  --budget {CODING_BUDGET}", coding_budget)

    coding_names = set(coding.kept)
    chat_names = set(chat.kept)
    if coding_names == chat_names:
        print("coding and chat loaded the same sections", file=sys.stderr)
        return 1
    if "editing" not in coding_names or "terminal" not in coding_names:
        print("coding mode is missing its tool sections", file=sys.stderr)
        return 1
    if "conversation" not in chat_names or "no_tools" not in chat_names:
        print("chat mode is missing its chat sections", file=sys.stderr)
        return 1
    if "editing" in chat_names or "conversation" in coding_names:
        print("mode conditions did not filter the library", file=sys.stderr)
        return 1
    if "legacy_apply_model" not in coding_budget.dropped:
        print("budget did not drop legacy_apply_model", file=sys.stderr)
        return 1
    if "editing" not in coding_budget.kept or "verification" not in coding_budget.kept:
        print("budget dropped a live coding section", file=sys.stderr)
        return 1
    if not coding_budget.within_budget:
        print("coding budget was exceeded", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
