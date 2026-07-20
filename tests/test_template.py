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

"""Tests for PromptTemplate."""

import pytest
from prompt_ctx import Section, PromptTemplate


class TestPromptTemplate:
    def test_add_and_get_section(self):
        t = PromptTemplate("test")
        s = Section(name="hello", content="world")
        t.add_section(s)
        assert t.get("hello") is s
        assert len(t) == 1

    def test_add_replaces_by_name(self):
        t = PromptTemplate("test")
        t.add_section(Section(name="a", content="v1"))
        t.add_section(Section(name="a", content="v2"))
        assert len(t) == 1
        assert t.get("a").content == "v2"

    def test_remove_section(self):
        t = PromptTemplate("test")
        t.add_section(Section(name="a", content="x"))
        t.remove_section("a")
        assert t.get("a") is None
        assert len(t) == 0

    def test_remove_missing_is_noop(self):
        t = PromptTemplate("test")
        t.remove_section("nope")  # no exception

    def test_enable_disable(self):
        t = PromptTemplate("test")
        s = Section(name="a", content="x", enabled=True)
        t.add_section(s)
        t.disable("a")
        assert not s.enabled
        t.enable("a")
        assert s.enabled

    def test_sections_sorted_by_priority(self):
        t = PromptTemplate("test")
        t.add_section(Section(name="c", content="c", priority=30))
        t.add_section(Section(name="a", content="a", priority=10))
        t.add_section(Section(name="b", content="b", priority=20))
        names = [s.name for s in t.sections]
        assert names == ["a", "b", "c"]

    def test_active_sections_filters_disabled(self):
        t = PromptTemplate("test")
        t.add_section(Section(name="a", content="a", enabled=True))
        t.add_section(Section(name="b", content="b", enabled=False))
        active = t.active_sections()
        assert len(active) == 1
        assert active[0].name == "a"

    def test_active_sections_filters_by_conditions(self):
        t = PromptTemplate("test")
        t.add_section(Section(name="a", content="a", conditions={"model": "gpt-4o"}))
        t.add_section(Section(name="b", content="b"))
        active = t.active_sections({"model": "gpt-3.5"})
        names = [s.name for s in active]
        assert "a" not in names
        assert "b" in names
