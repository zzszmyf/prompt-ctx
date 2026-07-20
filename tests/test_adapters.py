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

"""Tests for tokenizer and adapters."""

import pytest
from prompt_ctx.tokenizer import count_tokens, fits_in_context
from prompt_ctx.adapters import OpenAIChatAdapter


class TestTokenizer:
    def test_count_tokens_returns_int(self):
        n = count_tokens("Hello, world!", model="gpt-4o")
        assert isinstance(n, int)
        assert n > 0

    def test_count_tokens_empty_string(self):
        n = count_tokens("", model="gpt-4o")
        assert n == 0

    def test_count_tokens_longer_text_more_tokens(self):
        short = count_tokens("hi", model="gpt-4o")
        long = count_tokens("hi " * 100, model="gpt-4o")
        assert long > short

    def test_count_tokens_unknown_model_fallback(self):
        n = count_tokens("hello", model="nonexistent-model-v42")
        assert isinstance(n, int)
        assert n > 0

    def test_fits_in_context(self):
        assert fits_in_context("short", model="gpt-4o", max_tokens=128_000)
        assert not fits_in_context("word " * 200_000, model="gpt-4o", max_tokens=100)


class TestOpenAIChatAdapter:
    def test_format_returns_messages(self):
        adapter = OpenAIChatAdapter(model="gpt-4o")
        messages = adapter.format("You are a helpful assistant.")
        assert len(messages) == 1
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant."

    def test_model_stored(self):
        adapter = OpenAIChatAdapter(model="gpt-4o-mini")
        assert adapter.model == "gpt-4o-mini"
