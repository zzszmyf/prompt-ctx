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

"""Section: a named, tagged, overrideable prompt block."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Section:
    """A single prompt section, optionally wrapped in XML-style tags.

    Inspired by CursorZero's pattern:
      <communication>
      When using markdown...
      </communication>

    Attributes:
        name: Unique identifier for this section.
        content: The body text of the section.
        tag: Optional XML-style tag name. When set, the section is wrapped
             in <tag>...</tag> during assembly.
        priority: Ordering weight (lower = earlier in output).
        enabled: Runtime toggle.
        conditions: Dict of key-value pairs. All must match the assembly
                    context for this section to be included.
                    e.g. {"model": "gpt-4o"} only includes when model=gpt-4o.
    """

    name: str
    content: str
    tag: str | None = None
    priority: int = 100
    enabled: bool = True
    conditions: dict[str, Any] = field(default_factory=dict)

    def matches_conditions(self, ctx: dict[str, Any]) -> bool:
        """Return True if all conditions match the given context."""
        if not self.conditions:
            return True
        return all(
            ctx.get(key) == value for key, value in self.conditions.items()
        )

    def render(self) -> str:
        """Render this section to its string form."""
        if not self.enabled:
            return ""
        text = self.content.strip()
        if not text:
            return ""
        if self.tag:
            return f"<{self.tag}>\n{text}\n</{self.tag}>"
        return text
