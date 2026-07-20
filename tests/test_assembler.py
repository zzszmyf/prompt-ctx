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

"""Tests for Assembler."""

from prompt_ctx import Section, PromptTemplate, Assembler
from prompt_ctx.context import SystemInfoProvider


class TestAssembler:
    def test_assemble_basic(self):
        t = PromptTemplate("test")
        t.add_section(Section(name="role", content="You are helpful.", tag="role"))
        a = Assembler(t)
        prompt = a.assemble()
        assert "<role>\nYou are helpful.\n</role>" in prompt

    def test_assemble_with_context_providers(self):
        t = PromptTemplate("test")
        t.add_section(Section(name="role", content="Hi", tag=None))
        provider = SystemInfoProvider(os_version="linux")
        a = Assembler(t, providers=[provider])
        prompt = a.assemble()
        assert "Hi" in prompt
        assert "<user_info>" in prompt
        assert "linux" in prompt

    def test_conditional_sections_respected(self):
        t = PromptTemplate("test")
        t.add_section(Section(name="always", content="always shown"))
        t.add_section(
            Section(
                name="gpt4_only",
                content="gpt4 content",
                conditions={"model": "gpt-4o"},
            )
        )
        a = Assembler(t)
        prompt_gpt4 = a.assemble(model="gpt-4o")
        prompt_gpt35 = a.assemble(model="gpt-3.5-turbo")
        assert "gpt4 content" in prompt_gpt4
        assert "gpt4 content" not in prompt_gpt35

    def test_section_names(self):
        t = PromptTemplate("test")
        t.add_section(Section(name="a", content="a"))
        t.add_section(Section(name="b", content="b"))
        a = Assembler(t)
        assert a.section_names == ["a", "b"]
