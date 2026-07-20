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

"""PromptTemplate: ordered composition of Sections."""

from __future__ import annotations

from typing import Any

from prompt_ctx.core.section import Section


class PromptTemplate:
    """An ordered, named collection of Sections.

    Usage:
        template = PromptTemplate(name="my-assistant")
        template.add_section(Section(name="role", content="You are...", priority=0))
        template.add_section(Section(name="rules", content="Always...", priority=10))
    """

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._sections: dict[str, Section] = {}

    # ---- mutation ---------------------------------------------------

    def add_section(self, section: Section) -> None:
        """Add or replace a section by name."""
        self._sections[section.name] = section

    def remove_section(self, name: str) -> None:
        """Remove a section by name (no-op if missing)."""
        self._sections.pop(name, None)

    def enable(self, name: str) -> None:
        """Enable a section."""
        if name in self._sections:
            self._sections[name].enabled = True

    def disable(self, name: str) -> None:
        """Disable a section (it will be skipped during assembly)."""
        if name in self._sections:
            self._sections[name].enabled = False

    # ---- query ------------------------------------------------------

    def get(self, name: str) -> Section | None:
        """Get a section by name, or None."""
        return self._sections.get(name)

    @property
    def sections(self) -> list[Section]:
        """Return all sections sorted by priority (ascending)."""
        return sorted(self._sections.values(), key=lambda s: s.priority)

    def active_sections(self, ctx: dict[str, Any] | None = None) -> list[Section]:
        """Return enabled sections that match the given context."""
        ctx = ctx or {}
        return [
            s
            for s in self.sections
            if s.enabled and s.matches_conditions(ctx)
        ]

    def __len__(self) -> int:
        return len(self._sections)

    def __repr__(self) -> str:
        return f"<PromptTemplate name={self.name!r} sections={len(self)}>"
