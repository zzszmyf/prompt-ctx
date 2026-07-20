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

"""Token counting via tiktoken."""

from __future__ import annotations

import tiktoken


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Return the number of tokens in *text* for the given model.

    Args:
        text: The prompt string to count.
        model: OpenAI model name (default: gpt-4o).

    Returns:
        Token count as an integer.
    """
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback for unknown model names
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def fits_in_context(text: str, model: str = "gpt-4o", max_tokens: int = 128_000) -> bool:
    """Check whether *text* fits within *max_tokens* for *model*."""
    return count_tokens(text, model) <= max_tokens
