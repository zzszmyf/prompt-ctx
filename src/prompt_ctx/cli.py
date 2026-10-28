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

"""CLI for prompt-ctx: assemble, count, and validate prompts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prompt-ctx",
        description=(
            "Version, budget, and assemble production system prompts"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ---- assemble ----
    assemble = sub.add_parser("assemble", help="Assemble a prompt from a Python config")
    assemble.add_argument(
        "config",
        type=Path,
        help="Path to a Python file that defines 'template' and optionally 'providers'",
    )
    assemble.add_argument(
        "--model", default="gpt-4o", help="Model name for conditional sections (default: gpt-4o)"
    )
    assemble.add_argument(
        "--output", "-o", type=Path, default=None, help="Write prompt to file instead of stdout"
    )
    assemble.add_argument(
        "--budget",
        type=int,
        default=None,
        help=(
            "Maximum tokens for the assembled prompt. "
            "Lowest-priority sections are dropped until it fits."
        ),
    )
    assemble.add_argument(
        "--report",
        action="store_true",
        help="Print kept and dropped sections and how many tokens were saved",
    )
    assemble.add_argument(
        "--count", action="store_true", help="Also print token count"
    )

    # ---- count ----
    count = sub.add_parser("count", help="Count tokens in a text file or stdin")
    count.add_argument(
        "file", type=Path, nargs="?", default=None, help="File to count (stdin if omitted)"
    )
    count.add_argument(
        "--model", default="gpt-4o", help="Model for tokenization (default: gpt-4o)"
    )

    # ---- validate ----
    validate = sub.add_parser("validate", help="Validate a prompt config file")
    validate.add_argument(
        "config", type=Path, help="Path to a Python config file"
    )

    return parser


_CONFIG_LOADS = 0


def _load_config(config_path: Path) -> dict:
    """Load 'template' (and optionally 'providers') from a Python config file."""
    import importlib.util
    import sys

    global _CONFIG_LOADS
    _CONFIG_LOADS += 1
    # Unique name so two configs can be loaded in one process.
    module_name = f"prompt_ctx_config_{_CONFIG_LOADS}"
    spec = importlib.util.spec_from_file_location(module_name, config_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load config: {config_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(module_name, None)
        raise

    if not hasattr(mod, "template"):
        raise ValueError(f"Config file {config_path} must define 'template'")

    providers = getattr(mod, "providers", [])
    return {"template": mod.template, "providers": providers}


# ---- commands -----------------------------------------------------------


def _cmd_assemble(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    template = config["template"]
    providers = config["providers"]

    from prompt_ctx.core.assembler import Assembler, format_assembly_report

    assembler = Assembler(template, providers=providers)
    try:
        report = assembler.assemble_with_report(budget=args.budget, model=args.model)
    except ValueError as exc:
        print(f"assemble failed: {exc}", file=sys.stderr)
        return 1

    if args.output:
        args.output.write_text(report.prompt)
        print(f"Written to {args.output}")
    elif not args.report:
        print(report.prompt)

    if args.report:
        print(format_assembly_report(report, config=str(args.config)))
    elif args.count:
        print(f"\n--- Token count ({args.model}): {report.tokens_after} ---")

    return 0


def _cmd_count(args: argparse.Namespace) -> int:
    if args.file:
        text = args.file.read_text()
    else:
        text = sys.stdin.read()

    from prompt_ctx.tokenizer import count_tokens

    n = count_tokens(text, model=args.model)
    print(f"Tokens ({args.model}): {n}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        config = _load_config(args.config)
        template = config["template"]
        providers = config["providers"]
        print(f"✓ Config loaded: {args.config}")
        print(f"  Template: {template.name!r} with {len(template)} sections")
        print(f"  Sections: {[s.name for s in template.sections]}")
        print(f"  Providers: {len(providers)}")
        print("✓ Validation passed")
        return 0
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return 1


# ---- entry point --------------------------------------------------------


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    handlers = {
        "assemble": _cmd_assemble,
        "count": _cmd_count,
        "validate": _cmd_validate,
    }
    handler = handlers.get(args.command)
    if handler:
        sys.exit(handler(args))
