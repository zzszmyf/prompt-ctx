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

"""Demonstrate prompt-ctx by replicating the CursorZero system prompt structure.

This mirrors the production prompt we analyzed:
  <communication>  — markdown rules
  <search_and_reading> — decision bias ("Bias towards not asking")
  <making_code_changes> — diff format + apply-model awareness
  <user_info> — dynamic OS/shell/workspace injection (via provider)
  <additional_data> — file attachments with relevance disclaimer

Run:
    uv run python examples/cursorzero_demo.py
"""

from prompt_ctx import Section, PromptTemplate, Assembler
from prompt_ctx.adapters import OpenAIChatAdapter
from prompt_ctx.context import SystemInfoProvider, FileContextProvider
from prompt_ctx.tokenizer import count_tokens

# ---- 1. Build the template ------------------------------------------------

template = PromptTemplate(name="cursorzero-style")

# Priority 0: Core identity
template.add_section(
    Section(
        name="identity",
        tag=None,  # no wrapper tag — raw text at the top
        content=(
            "You are an AI coding assistant, powered by "
            "tensorzero::function_name::cursorzero. "
            "You operate in Cursor.\n\n"
            "You are pair programming with a USER to solve their coding task. "
            "Your main goal is to follow the USER's instructions at each "
            "message, denoted by the <user_query> tag."
        ),
        priority=0,
    )
)

# Priority 10: Communication rules
template.add_section(
    Section(
        name="communication",
        tag="communication",
        content=(
            "When using markdown in assistant messages, use backticks to "
            "format file, directory, function, and class names. "
            "Use ( and ) for inline math, [ and ] for block math."
        ),
        priority=10,
    )
)

# Priority 20: Search and reading behavior (with decision bias)
template.add_section(
    Section(
        name="search_and_reading",
        tag="search_and_reading",
        content=(
            "If you are unsure about the answer to the USER's request or how "
            "to satiate their request, you should gather more information. "
            "This can be done by asking the USER for more information.\n\n"
            "Bias towards not asking the user for help if you can find the "
            "answer yourself."
        ),
        priority=20,
    )
)

# Priority 30: Code changes format (with apply-model awareness)
template.add_section(
    Section(
        name="making_code_changes",
        tag="making_code_changes",
        content=(
            "The user is likely just asking questions and not looking for "
            "edits. Only suggest edits if you are certain that the user is "
            "looking for edits.\n"
            "When the user is asking for edits to their code, please output "
            "a simplified version of the code block that highlights the "
            "changes necessary and adds comments to indicate where unchanged "
            "code has been skipped.\n\n"
            "The user can see the entire file, so they prefer to only read "
            "the updates to the code. Often this will mean that the "
            "start/end of the file will be skipped, but that's okay! "
            "Rewrite the entire file only if specifically requested.\n\n"
            "These edit codeblocks are also read by a less intelligent "
            "language model, colloquially called the apply model, to update "
            "the file. To help specify the edit to the apply model, you will "
            "be very careful when generating the codeblock to not introduce "
            "ambiguity. You will specify all unchanged regions (code and "
            "comments) of the file with '// ... existing code ...' comment "
            "markers."
        ),
        priority=30,
    )
)

# Priority 40: Citation format (machine-parseable)
template.add_section(
    Section(
        name="citation_format",
        tag=None,
        content=(
            "You MUST use the following format when citing code regions:\n"
            "```12:15:app/components/Todo.tsx\n"
            "// ... existing code ...\n"
            "```\n"
            "This is the ONLY acceptable format for code citations."
        ),
        priority=40,
    )
)

# Priority 50: Relevance disclaimer for attached context
template.add_section(
    Section(
        name="context_disclaimer",
        tag=None,
        content=(
            "Each time the USER sends a message, we may automatically attach "
            "some information about their current state, such as files open, "
            "cursor position, edit history...\n"
            "This information may or may not be relevant to the coding task; "
            "it is up to you to decide."
        ),
        priority=50,
    )
)

# ---- 2. Create context providers -----------------------------------------

sys_info = SystemInfoProvider.auto()

file_ctx = FileContextProvider()
file_ctx.add_file(
    "nginx/nginx.conf",
    (
        "events {}\n\n"
        "http {\n"
        "  server {\n"
        "    listen 80;\n"
        "    location / {\n"
        "      proxy_pass http://gateway:3000;\n"
        "    }\n"
        "  }\n"
        "}"
    ),
)

# ---- 3. Assemble ---------------------------------------------------------

assembler = Assembler(template, providers=[sys_info, file_ctx])
prompt = assembler.assemble(model="gpt-4o")

# ---- 4. Format for OpenAI / count tokens ---------------------------------

adapter = OpenAIChatAdapter(model="gpt-4o")
messages = adapter.format(prompt)
tokens = count_tokens(prompt, model="gpt-4o")

# ---- 5. Output -----------------------------------------------------------

print("=" * 70)
print("ASSEMBLED SYSTEM PROMPT")
print("=" * 70)
print(prompt)
print()
print("=" * 70)
print("OPENAI MESSAGES FORMAT")
print("=" * 70)
print(messages)
print()
print(f"Token count (gpt-4o): {tokens}")
print(f"Active sections: {assembler.section_names}")
