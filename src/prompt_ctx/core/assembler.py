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

"""Assembler: merge template sections + context providers → final prompt."""

from __future__ import annotations

from typing import Any

from prompt_ctx.context.base import ContextProvider
from prompt_ctx.core.template import PromptTemplate


class Assembler:
    """Assembles a PromptTemplate and dynamic ContextProviders into a final
    prompt string.

    Usage:
        assembler = Assembler(template, providers=[SystemInfoProvider.auto()])
        prompt = assembler.assemble(model="gpt-4o")
    """

    def __init__(
        self,
        template: PromptTemplate,
        providers: list[ContextProvider] | None = None,
    ) -> None:
        self.template = template
        self.providers: list[ContextProvider] = providers or []

    def assemble(self, **ctx: Any) -> str:
        """Produce the final prompt string.

        Keyword arguments become the assembly context used for:
          - conditional section inclusion (Section.conditions)
          - filtering via active_sections()

        Dynamic context from registered providers is appended at the end.
        """
        # 1. Collect active sections (sorted by priority, filtered by ctx)
        active = self.template.active_sections(ctx)

        # 2. Render sections
        parts: list[str] = []
        for section in active:
            rendered = section.render()
            if rendered:
                parts.append(rendered)

        # 3. Append dynamic context from providers
        for provider in self.providers:
            ctx_str = provider.get_context()
            if ctx_str:
                parts.append(ctx_str)

        return "\n\n".join(parts)

    @property
    def section_names(self) -> list[str]:
        """Return ordered list of active section names for inspection."""
        return [s.name for s in self.template.active_sections()]
