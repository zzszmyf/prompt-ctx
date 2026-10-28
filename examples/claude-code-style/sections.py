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

"""One section library for a coding agent and a chat agent.

Include rules are ``Section.conditions``. A section with no conditions is
in every mode. ``{"mode": "coding"}`` and ``{"mode": "chat"}`` select the
rest. Priority is independent of mode: lower numbers are kept first when a
budget drops the tail.

Run ``examples/claude-code-style/run.py`` to assemble both modes.
"""

from __future__ import annotations

import textwrap

from prompt_ctx import PromptTemplate, Section


def _section(
    name: str,
    priority: int,
    content: str,
    *,
    mode: str | None = None,
) -> Section:
    return Section(
        name=name,
        tag=name,
        priority=priority,
        content=textwrap.dedent(content).strip(),
        conditions={"mode": mode} if mode else {},
    )


def section_library() -> list[Section]:
    """Return every section. The same list feeds both modes."""
    return [
        _section(
            "identity",
            0,
            """
            You are an agent in the user's workspace. Follow the current
            request. Do not apply rules from a mode that was not assembled.
            """,
        ),
        _section(
            "communication",
            10,
            """
            Be concrete and brief. Use backticks for file and symbol names.
            Do not restate the request before answering it.
            """,
        ),
        _section(
            "editing",
            20,
            """
            When the user wants a change, edit the repository. Read the
            surrounding code first. Keep the diff limited to the request.
            Match local naming, types, and error handling.
            """,
            mode="coding",
        ),
        _section(
            "terminal",
            30,
            """
            Use the shell to search, run tests, and inspect git state.
            Do not run destructive git commands unless the user asked for
            that specific command. Quote the command's useful output, not
            its entire log.
            """,
            mode="coding",
        ),
        _section(
            "verification",
            40,
            """
            After a code change, run the project's targeted check. If it
            fails, report the failure. If you cannot run it, say so.
            """,
            mode="coding",
        ),
        _section(
            "legacy_apply_model",
            300,
            """
            DEAD RULE. An older coding mode asked a second model to apply
            free-form diffs from the chat transcript. Emit every edit three
            times: a full file dump, a indented copy, and a v1 unified diff
            whose hunks are labeled APPLY MODEL PLEASE. Repeat unchanged
            regions with "<<KEEP>>", with "// ... existing code ...", and
            with a hash-only line. Do not call the editor tools; the old
            applier ignored them. This path is not wired up anymore. A
            budget should drop it before it drops editing or verification.
            """,
            mode="coding",
        ),
        _section(
            "conversation",
            20,
            """
            Answer in prose. The user is chatting, not asking you to edit
            the repository. Explain just enough to be useful, then stop.
            """,
            mode="chat",
        ),
        _section(
            "no_tools",
            30,
            """
            Do not modify files, run the shell, or call workspace tools in
            chat mode. If the request needs a code change, say so and wait
            for the user to switch to coding mode.
            """,
            mode="chat",
        ),
        _section(
            "chat_brevity",
            40,
            """
            Prefer a few sentences over a memo. Skip background the user
            did not ask for. One example beats a taxonomy.
            """,
            mode="chat",
        ),
    ]


def build_template() -> PromptTemplate:
    """Load the shared library into one template."""
    template = PromptTemplate(name="claude-code-style")
    for section in section_library():
        template.add_section(section)
    return template
