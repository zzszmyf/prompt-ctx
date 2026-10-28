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

import pytest

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


class TestBudget:
    def _template(self) -> PromptTemplate:
        t = PromptTemplate("budget")
        t.add_section(Section(name="core", content="core rule " * 30, priority=0))
        t.add_section(Section(name="mid", content="mid rule " * 30, priority=10))
        t.add_section(Section(name="dead", content="dead rule " * 30, priority=90))
        return t

    def test_no_budget_matches_full_prompt(self):
        t = self._template()
        a = Assembler(t)
        assert a.assemble() == a.assemble(budget=None)
        report = a.assemble_with_report()
        assert report.prompt == a.assemble()
        assert report.dropped == ()
        assert report.tokens_saved == 0
        assert report.within_budget
        assert report.budget is None

    def test_large_budget_keeps_every_section(self):
        a = Assembler(self._template())
        assert a.assemble(budget=10**9) == a.assemble()

    def test_drops_lowest_priority_first(self):
        from prompt_ctx.tokenizer import count_tokens

        t = self._template()
        prefix = PromptTemplate("prefix")
        prefix.add_section(t.get("core"))
        prefix.add_section(t.get("mid"))
        two_tokens = count_tokens(Assembler(prefix).assemble(), model="gpt-4o")

        report = Assembler(t).assemble_with_report(budget=two_tokens)
        assert report.kept == ("core", "mid")
        assert report.dropped == ("dead",)
        assert report.tokens_after <= two_tokens
        assert report.tokens_before > two_tokens
        assert report.tokens_saved == report.tokens_before - report.tokens_after
        assert report.within_budget
        assert "dead rule" not in report.prompt
        assert report.prompt.index("core rule") < report.prompt.index("mid rule")

        tighter = Assembler(t).assemble_with_report(budget=two_tokens - 1)
        assert tighter.kept == ("core",)
        assert "mid" in tighter.dropped and "dead" in tighter.dropped

    def test_conditions_are_not_listed_as_dropped(self):
        t = self._template()
        t.add_section(
            Section(
                name="chat_only",
                content="chat only rule " * 20,
                priority=5,
                conditions={"mode": "chat"},
            )
        )
        report = Assembler(t).assemble_with_report(budget=10**9, mode="coding")
        assert "chat_only" not in report.kept
        assert "chat_only" not in report.dropped
        assert "chat only rule" not in report.prompt

    def test_disabled_section_is_not_a_budget_decision(self):
        t = self._template()
        t.add_section(Section(name="off", content="hidden rule", priority=1, enabled=False))
        report = Assembler(t).assemble_with_report(budget=10**9)
        assert "off" not in report.kept
        assert "off" not in report.dropped

    def test_negative_budget_raises(self):
        with pytest.raises(ValueError):
            Assembler(self._template()).assemble(budget=-1)

    def test_providers_are_kept_when_sections_drop(self):
        from prompt_ctx.context import DynamicContextProvider

        provider = DynamicContextProvider(tag="ctx", data={"note": "live context"})
        report = Assembler(self._template(), providers=[provider]).assemble_with_report(budget=5)
        assert report.kept == ()
        assert report.provider_tokens > 0
        assert "<ctx>" in report.prompt
        assert report.within_budget is False

    def test_report_text_names_dropped_section(self):
        from prompt_ctx.core.assembler import format_assembly_report
        from prompt_ctx.tokenizer import count_tokens

        t = self._template()
        core_tokens = count_tokens(t.get("core").render(), model="gpt-4o")
        report = Assembler(t).assemble_with_report(budget=core_tokens, model="gpt-4o")
        text = format_assembly_report(report, config="examples/prompt.py")
        assert "BEFORE" in text and "AFTER" in text and "SAVED" in text
        assert "DROPPED" in text
        assert "dead" in text
        assert "core" in text
        assert "--budget" in text
        assert "examples/prompt.py" in text
