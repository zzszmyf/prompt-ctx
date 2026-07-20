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

"""Dynamic context providers that inject data at assembly time."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class ContextProvider(ABC):
    """Abstract base for objects that supply dynamic context at assembly time.

    Each provider returns a string (plain text or XML-tagged block) that
    is appended to the assembled prompt.
    """

    @abstractmethod
    def get_context(self) -> str:  # pragma: no cover
        ...


# ---- built-in providers ------------------------------------------------


@dataclass
class SystemInfoProvider(ContextProvider):
    """Injects <user_info> block with OS, shell, workspace, and date.

    Mirrors CursorZero's pattern:
        <user_info>
        OS version: darwin 24.3.0
        Workspace: /Users/...
        Shell: /bin/zsh
        </user_info>
    """

    os_version: str = ""
    shell_path: str = ""
    workspace: str = ""
    date_str: str = ""
    extra: dict[str, str] = field(default_factory=dict)

    def get_context(self) -> str:
        lines: list[str] = ["<user_info>"]
        if self.os_version:
            lines.append(f"OS version: {self.os_version}")
        if self.shell_path:
            lines.append(f"Shell: {self.shell_path}")
        if self.workspace:
            lines.append(f"Workspace: {self.workspace}")
        if self.date_str:
            lines.append(f"Date: {self.date_str}")
        for key, val in self.extra.items():
            lines.append(f"{key}: {val}")
        lines.append("</user_info>")
        return "\n".join(lines)

    @classmethod
    def auto(cls) -> "SystemInfoProvider":
        """Create a provider populated from the current runtime environment."""
        import datetime
        import os
        import platform

        return cls(
            os_version=f"{platform.system()} {platform.release()}",
            shell_path=os.environ.get("SHELL", ""),
            workspace=os.getcwd(),
            date_str=datetime.date.today().isoformat(),
        )


@dataclass
class FileContextProvider(ContextProvider):
    """Injects attached file contents with a relevance disclaimer.

    Mirrors CursorZero's pattern:
        <attached_files>
        <file_contents path=...>
        ...
        </file_contents>
        </attached_files>
        This information may or may not be relevant...
    """

    files: dict[str, str] = field(default_factory=dict)
    disclaimer: str = (
        "This information may or may not be relevant to the coding task; "
        "it is up to you to decide."
    )

    def add_file(self, path: str, content: str) -> None:
        """Register a file to be injected."""
        self.files[path] = content

    def get_context(self) -> str:
        if not self.files:
            return ""
        parts: list[str] = ["<attached_files>"]
        for path, content in self.files.items():
            parts.append(f'<file_contents path="{path}">')
            parts.append(content)
            parts.append("</file_contents>")
        parts.append("</attached_files>")
        if self.disclaimer:
            parts.append(self.disclaimer)
        return "\n".join(parts)


@dataclass
class DynamicContextProvider(ContextProvider):
    """Ad-hoc key-value context injected as an XML block.

    Usage:
        DynamicContextProvider(tag="custom", data={"key": "value"})
        → <custom>\nkey: value\n</custom>
    """

    tag: str = "dynamic_context"
    data: dict[str, str] = field(default_factory=dict)

    def get_context(self) -> str:
        if not self.data:
            return ""
        lines = [f"<{self.tag}>"]
        for key, val in self.data.items():
            lines.append(f"{key}: {val}")
        lines.append(f"</{self.tag}>")
        return "\n".join(lines)
