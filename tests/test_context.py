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

"""Tests for context providers."""

from prompt_ctx.context import (
    SystemInfoProvider,
    FileContextProvider,
    DynamicContextProvider,
)


class TestSystemInfoProvider:
    def test_renders_all_fields(self):
        p = SystemInfoProvider(
            os_version="darwin 24.3.0",
            shell_path="/bin/zsh",
            workspace="/Users/test/project",
            date_str="2026-07-20",
        )
        out = p.get_context()
        assert "<user_info>" in out
        assert "darwin 24.3.0" in out
        assert "/bin/zsh" in out
        assert "/Users/test/project" in out
        assert "2026-07-20" in out
        assert "</user_info>" in out

    def test_omits_empty_fields(self):
        p = SystemInfoProvider(os_version="linux")
        out = p.get_context()
        assert "Shell:" not in out
        assert "Workspace:" not in out

    def test_extra_fields(self):
        p = SystemInfoProvider(extra={"Custom": "value"})
        out = p.get_context()
        assert "Custom: value" in out

    def test_auto_populates(self):
        p = SystemInfoProvider.auto()
        out = p.get_context()
        assert "OS version:" in out
        # Workspace should match the current dir at call time
        assert "<user_info>" in out


class TestFileContextProvider:
    def test_empty_renders_nothing(self):
        p = FileContextProvider()
        assert p.get_context() == ""

    def test_renders_files_with_disclaimer(self):
        p = FileContextProvider()
        p.add_file("test.py", "print('hello')")
        out = p.get_context()
        assert "<attached_files>" in out
        assert 'path="test.py"' in out
        assert "print('hello')" in out
        assert "</attached_files>" in out
        assert "may or may not be relevant" in out

    def test_disclaimer_disabled(self):
        p = FileContextProvider(disclaimer="")
        p.add_file("a.txt", "data")
        out = p.get_context()
        assert "may or may not" not in out


class TestDynamicContextProvider:
    def test_empty_renders_nothing(self):
        p = DynamicContextProvider()
        assert p.get_context() == ""

    def test_renders_tagged_block(self):
        p = DynamicContextProvider(tag="custom", data={"foo": "bar", "baz": "qux"})
        out = p.get_context()
        assert "<custom>" in out
        assert "foo: bar" in out
        assert "baz: qux" in out
        assert "</custom>" in out
