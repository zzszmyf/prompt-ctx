# prompt-ctx

**Structured prompt context management toolkit for production-grade LLM system prompts.**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)

`prompt-ctx` brings software engineering rigor to prompt engineering. Compose modular, version-controllable system prompts with dynamic context injection, token budget awareness, and multi-model adapter support.

## Why?

Production system prompts (like CursorZero's) are complex software artifacts — they mix static rules, dynamic context, output format constraints, and model-specific instructions. Yet most teams manage them as monolithic strings in Google Docs. `prompt-ctx` treats prompts as **composable, testable, versionable code**.

## Features

- **XML-style section partitioning** — named, tagged, prioritized prompt blocks (`<communication>`, `<user_info>`, etc.)
- **Dynamic context injection** — runtime providers for system info, file contents, and arbitrary data
- **Conditional inclusion** — same template adapts to different models or modes at assembly time
- **Token counting** — built-in `tiktoken` integration for budget-aware assembly
- **Model adapters** — format prompts for OpenAI Chat Completions (extensible to Anthropic, etc.)
- **CLI + Library** — use as a Python library or via `prompt-ctx` CLI commands
- **Version-controlled prompts** — prompt configs are Python files → git diff, PR review, CI validation

## Quick Start

### Installation

```bash
pip install prompt-ctx
```

Or with uv:

```bash
uv add prompt-ctx
```

### Basic Usage

```python
from prompt_ctx import Section, PromptTemplate, Assembler
from prompt_ctx.context import SystemInfoProvider
from prompt_ctx.adapters import OpenAIChatAdapter
from prompt_ctx.tokenizer import count_tokens

# 1. Compose a template
template = PromptTemplate(name="my-assistant")

template.add_section(Section(
    name="role",
    content="You are a helpful coding assistant.",
    tag=None,
    priority=0,
))

template.add_section(Section(
    name="rules",
    content="Always respond in markdown. Be concise.",
    tag="communication",
    priority=10,
))

# 2. Assemble with dynamic context
assembler = Assembler(template, providers=[SystemInfoProvider.auto()])
prompt = assembler.assemble(model="gpt-4o")

# 3. Format for OpenAI API
adapter = OpenAIChatAdapter(model="gpt-4o")
messages = adapter.format(prompt)

# 4. Check token budget
tokens = count_tokens(prompt, model="gpt-4o")
print(f"Tokens: {tokens}")
```

### CLI

```bash
# Assemble a prompt from a Python config
prompt-ctx assemble my_prompt.py --model gpt-4o

# Count tokens in a file or stdin
prompt-ctx count system_prompt.txt
echo "Hello world" | prompt-ctx count

# Validate a prompt config
prompt-ctx validate my_prompt.py
```

## Architecture

```
┌──────────────────────────────────────────┐
│  PromptTemplate (ordered Sections)       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Section  │ │ Section  │ │ Section  │ │
│  │ priority │ │ priority │ │ priority │ │
│  │    0     │ │   10     │ │   20     │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└────────────────┬─────────────────────────┘
                 │  assemble(ctx)
                 ▼
┌──────────────────────────────────────────┐
│  Assembler                               │
│  ┌────────────────────────────────────┐  │
│  │ Active sections (filtered, sorted) │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │ ContextProviders (dynamic data)    │  │
│  │ - SystemInfoProvider               │  │
│  │ - FileContextProvider              │  │
│  │ - DynamicContextProvider           │  │
│  └────────────────────────────────────┘  │
└────────────────┬─────────────────────────┘
                 │  final prompt string
                 ▼
┌──────────────────────────────────────────┐
│  ModelAdapter → OpenAI / Anthropic / ... │
└──────────────────────────────────────────┘
```

## Project Structure

```
src/prompt_ctx/
├── __init__.py              # Public API exports
├── core/
│   ├── section.py           # Section — named, tagged prompt block
│   ├── template.py          # PromptTemplate — ordered composition
│   └── assembler.py         # Assembler — merge sections + context
├── context/
│   └── base.py              # SystemInfo, FileContext, Dynamic providers
├── adapters/
│   ├── base.py              # ModelAdapter abstract base
│   └── openai.py            # OpenAIChatAdapter
├── tokenizer.py             # tiktoken wrapper
└── cli.py                   # assemble | count | validate
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE) for details.
