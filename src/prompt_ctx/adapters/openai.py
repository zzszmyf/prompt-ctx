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

"""OpenAI Chat Completions adapter."""

from __future__ import annotations

from prompt_ctx.adapters.base import ModelAdapter


class OpenAIChatAdapter(ModelAdapter):
    """Formats an assembled system prompt into OpenAI messages format.

    Usage:
        adapter = OpenAIChatAdapter(model="gpt-4o")
        messages = adapter.format(prompt_string)
        # → [{"role": "system", "content": prompt_string}]
    """

    def __init__(self, model: str = "gpt-4o") -> None:
        self.model = model

    def format(self, system_prompt: str) -> list[dict[str, str]]:
        """Return a messages list suitable for openai.chat.completions.create."""
        return [{"role": "system", "content": system_prompt}]
