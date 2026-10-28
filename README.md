# prompt-ctx

Production system prompts are software. prompt-ctx versions, budgets, and assembles them so your agent doesn’t burn the context window on dead rules.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)

Each rule is a section in a Python file: a name, a priority, and an include rule. Assembly keeps the sections that match the current mode and drops the lowest-priority tail that does not fit the token budget. A prompt change shows up in review like any other diff.

## Before / after

A bloated coding-agent prompt, assembled with `prompt-ctx assemble --budget 2000`. Ten live sections stay. Ten dead rules (retired tone guides, obsolete model workarounds, archived ceremony) are dropped. **3,028 tokens** stay out of the context window. Counts are tiktoken for `gpt-4o`.

```
$ prompt-ctx assemble examples/bloated_system_prompt.py --budget 2000 --report
model:  gpt-4o

BEFORE [################################]    4,860 tokens  20 sections
AFTER  [############....................]    1,832 tokens  budget 2,000 | 10 kept
SAVED  [####################............]    3,028 tokens  10 dropped | 62%

KEPT  (priority order)
priority   tokens  section
--------  -------  -------
       0      142  identity
      10      156  communication
      20      186  tool_discipline
      30      184  making_code_changes
      40      185  verification
      50      150  safety
      60      125  context_relevance
      70      219  git_and_review
      80      245  tests
      90      240  scope

DROPPED  (lowest priority first)
priority   tokens  section
--------  -------  -------
     290      273  stale_vendor_sdk_notes
     280      260  historical_incident_checklist
     270      285  superseded_commit_essay
     260      231  dead_status_broadcast
     250      236  unused_marketing_persona
     240      269  archived_ticket_ceremony
     230      305  obsolete_apply_diff_v1
     220      302  retired_gpt35_workarounds
     210      247  deprecated_emoji_status
     200      620  legacy_tone_guide_2019
```

From a fresh clone:

```bash
git clone https://github.com/zzszmyf/prompt-ctx.git
cd prompt-ctx
uv sync
uv run python examples/budget_demo.py
```

Same report, called as the CLI:

```bash
uv run prompt-ctx assemble examples/bloated_system_prompt.py --budget 2000 --report
```

Lower priority numbers are kept first. The budget drops the tail until the assembled prompt fits.

## Coding mode and chat mode

`examples/claude-code-style/` is one section library with include rules. Shared sections have no condition. Coding-only and chat-only sections set `conditions={"mode": "coding"}` or `{"mode": "chat"}`. A low-priority coding section is there so a tight budget can drop it without touching the live rules.

```bash
uv run python examples/claude-code-style/run.py
```

```
section                  priority  include
-------                  --------  -------
identity                        0  always
communication                  10  always
conversation                   20  mode=chat
editing                        20  mode=coding
no_tools                       30  mode=chat
terminal                       30  mode=coding
chat_brevity                   40  mode=chat
verification                   40  mode=coding
legacy_apply_model            300  mode=coding

MODE coding
  tokens:  318
  kept:    identity, communication, editing, terminal, verification, legacy_apply_model
  dropped: (none)

MODE chat
  tokens:  181
  kept:    identity, communication, conversation, no_tools, chat_brevity
  dropped: (none)

MODE coding  --budget 250
  tokens:  191
  kept:    identity, communication, editing, terminal, verification
  dropped: legacy_apply_model
```

## Priority, budget, and review

- **Priority.** `priority=0` is the rule you are least willing to lose. It is rendered first. Higher numbers are the dead rules, and they are the ones a budget cuts.
- **Budget.** `Assembler.assemble_with_report(..., budget=2000)` and `prompt-ctx assemble --budget 2000` do the same cut. Dynamic context from providers is kept; sections compete for what remains.
- **Git-reviewable sections.** The prompt is a Python module (`template` plus optional `providers`). Changing a rule is a diff a reviewer can read, and `prompt-ctx validate` checks that the module loads.

## Quick start

### Installation

```bash
pip install prompt-ctx
```

Or with uv:

```bash
uv add prompt-ctx
```

The demos above run from a clone (`uv sync`, then `uv run ...`). They need Python 3.13+.

### Basic usage

```python
from prompt_ctx import Section, PromptTemplate, Assembler
from prompt_ctx.context import SystemInfoProvider
from prompt_ctx.adapters import OpenAIChatAdapter
from prompt_ctx.tokenizer import count_tokens

# 1. Compose a template. Lower priority numbers are kept first.
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

# 2. Assemble. A budget drops the lowest-priority tail that does not fit.
#    examples/budget_demo.py is that cut, end to end.
assembler = Assembler(template, providers=[SystemInfoProvider.auto()])
report = assembler.assemble_with_report(model="gpt-4o", budget=2000)
prompt = report.prompt

# 3. Format for OpenAI API
adapter = OpenAIChatAdapter(model="gpt-4o")
messages = adapter.format(prompt)

# 4. The report is the before/after the demo prints.
print(f"{report.tokens_before} -> {report.tokens_after}")
print("dropped:", ", ".join(report.dropped))
print("tokens:", count_tokens(prompt, model="gpt-4o"))
```

Include rules use the same context keywords as `model`:

```python
Section(name="editing", content="...", priority=20, conditions={"mode": "coding"})
assembler.assemble(mode="coding", budget=2000)
```

### CLI

A config file defines `template` and, optionally, `providers`.

```bash
# Full prompt on stdout
prompt-ctx assemble my_prompt.py --model gpt-4o

# Drop the lowest-priority tail, print the comparison
prompt-ctx assemble my_prompt.py --budget 2000 --report

# Write the fitted prompt to a file (add --report to also print the comparison)
prompt-ctx assemble my_prompt.py --budget 2000 -o prompt.txt --count

# Count tokens in a file or stdin
prompt-ctx count system_prompt.txt
echo "Hello world" | prompt-ctx count

# Validate a prompt config
prompt-ctx validate my_prompt.py
```

`assemble` prints the prompt. `--report` prints the before/after comparison in its place.

## Architecture

```
┌──────────────────────────────────────────┐
│  PromptTemplate (ordered Sections)       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Section  │ │ Section  │ │ Section  │ │
│  │ priority │ │ priority │ │ priority │ │
│  │    0     │ │   10     │ │  300     │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└────────────────┬─────────────────────────┘
                 │  assemble(budget=2000)
                 ▼
┌──────────────────────────────────────────┐
│  Assembler                               │
│  keep priority 0, 10, … until the budget │
│  drop the tail (dead rules)              │
│  ContextProviders stay (live context)    │
└────────────────┬─────────────────────────┘
                 │  prompt + kept / dropped
                 ▼
┌──────────────────────────────────────────┐
│  ModelAdapter → OpenAI / Anthropic / ... │
└──────────────────────────────────────────┘
```

## Project structure

```
src/prompt_ctx/
├── __init__.py              # Public API exports
├── core/
│   ├── section.py           # Section — named, tagged prompt block
│   ├── template.py          # PromptTemplate — ordered composition
│   └── assembler.py         # Assembler — budget, kept, dropped
├── context/
│   └── base.py              # SystemInfo, FileContext, Dynamic providers
├── adapters/
│   ├── base.py              # ModelAdapter abstract base
│   └── openai.py            # OpenAIChatAdapter
├── tokenizer.py             # tiktoken wrapper
└── cli.py                   # assemble | count | validate
examples/
├── budget_demo.py           # before/after under --budget 2000
├── bloated_system_prompt.py # section library the demo assembles
├── claude-code-style/       # coding mode vs chat mode
│   ├── sections.py
│   └── run.py
└── cursorzero_demo.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE) for details.
