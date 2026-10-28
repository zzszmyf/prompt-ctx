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

"""prompt-ctx: version, budget, and assemble production system prompts.

Production system prompts are software. prompt-ctx versions, budgets, and
assembles them so your agent doesn’t burn the context window on dead rules.

Usage:
    from prompt_ctx import Section, PromptTemplate, Assembler
    from prompt_ctx.context import SystemInfoProvider
"""

from prompt_ctx.core.section import Section
from prompt_ctx.core.template import PromptTemplate
from prompt_ctx.core.assembler import Assembler, AssemblyReport

__all__ = ["Section", "PromptTemplate", "Assembler", "AssemblyReport"]


def main() -> None:
    """CLI entry point (delegates to prompt_ctx.cli.main)."""
    from prompt_ctx.cli import main as _cli_main

    _cli_main()
