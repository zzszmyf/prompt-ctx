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

"""Tests for the Section class."""

import pytest
from prompt_ctx import Section


class TestSectionBasic:
    def test_render_with_tag(self):
        s = Section(name="comm", content="Be concise.", tag="communication")
        rendered = s.render()
        assert rendered == "<communication>\nBe concise.\n</communication>"

    def test_render_without_tag(self):
        s = Section(name="identity", content="You are an AI.", tag=None)
        assert s.render() == "You are an AI."

    def test_render_disabled(self):
        s = Section(name="x", content="hidden", enabled=False)
        assert s.render() == ""

    def test_render_empty_content(self):
        s = Section(name="x", content="  ", tag="tag")
        assert s.render() == ""

    def test_render_multiline_content(self):
        s = Section(name="rules", content="Line 1\nLine 2", tag="rules")
        rendered = s.render()
        assert rendered == "<rules>\nLine 1\nLine 2\n</rules>"


class TestSectionConditions:
    def test_no_conditions_always_matches(self):
        s = Section(name="x", content="hi")
        assert s.matches_conditions({})
        assert s.matches_conditions({"model": "gpt-4o"})

    def test_single_condition_match(self):
        s = Section(name="x", content="hi", conditions={"model": "gpt-4o"})
        assert s.matches_conditions({"model": "gpt-4o"})

    def test_single_condition_mismatch(self):
        s = Section(name="x", content="hi", conditions={"model": "gpt-4o"})
        assert not s.matches_conditions({"model": "gpt-3.5"})

    def test_missing_key_in_context(self):
        s = Section(name="x", content="hi", conditions={"model": "gpt-4o"})
        assert not s.matches_conditions({})

    def test_multiple_conditions_all_match(self):
        s = Section(name="x", content="hi", conditions={"model": "gpt-4o", "lang": "en"})
        assert s.matches_conditions({"model": "gpt-4o", "lang": "en", "extra": True})

    def test_multiple_conditions_partial_match(self):
        s = Section(name="x", content="hi", conditions={"model": "gpt-4o", "lang": "en"})
        assert not s.matches_conditions({"model": "gpt-4o", "lang": "fr"})
