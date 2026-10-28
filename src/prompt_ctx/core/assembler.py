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

"""Assembler: merge template sections + context providers → final prompt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from prompt_ctx.context.base import ContextProvider
from prompt_ctx.core.section import Section
from prompt_ctx.core.template import PromptTemplate
from prompt_ctx.tokenizer import count_tokens

_BAR_WIDTH = 32


@dataclass(frozen=True)
class SectionDecision:
    """One active section after a budget pass.

    ``priority`` matches :class:`~prompt_ctx.core.section.Section`: lower
    numbers are kept first. ``tokens`` counts that section on its own.
    """

    name: str
    priority: int
    tokens: int
    kept: bool


@dataclass(frozen=True)
class AssemblyReport:
    """Result of assembling a template, including what the budget dropped.

    ``tokens_before`` is the prompt with every active section.
    ``tokens_after`` is the prompt that was actually produced.
    Dynamic context from providers is kept either way; only sections are cut.
    """

    prompt: str
    decisions: tuple[SectionDecision, ...]
    tokens_before: int
    tokens_after: int
    budget: int | None
    model: str
    provider_tokens: int = 0

    @property
    def kept(self) -> tuple[str, ...]:
        """Section names that landed in the prompt, priority order."""
        return tuple(d.name for d in self.decisions if d.kept)

    @property
    def dropped(self) -> tuple[str, ...]:
        """Active sections omitted to fit the budget, priority order."""
        return tuple(d.name for d in self.decisions if not d.kept)

    @property
    def tokens_saved(self) -> int:
        """Tokens removed versus the unbudgeted prompt."""
        return self.tokens_before - self.tokens_after

    @property
    def within_budget(self) -> bool:
        """True when no budget was set, or the prompt fits."""
        if self.budget is None:
            return True
        return self.tokens_after <= self.budget


class Assembler:
    """Assembles a PromptTemplate and dynamic ContextProviders into a final
    prompt string.

    Usage:
        assembler = Assembler(template, providers=[SystemInfoProvider.auto()])
        prompt = assembler.assemble(model="gpt-4o")
        report = assembler.assemble_with_report(model="gpt-4o", budget=2000)
    """

    def __init__(
        self,
        template: PromptTemplate,
        providers: list[ContextProvider] | None = None,
    ) -> None:
        self.template = template
        self.providers: list[ContextProvider] = providers or []

    def assemble(self, *, budget: int | None = None, **ctx: Any) -> str:
        """Produce the final prompt string.

        Keyword arguments other than ``budget`` become the assembly context
        used for conditional section inclusion (``Section.conditions``).

        When ``budget`` is set, sections stay in priority order (lower number
        = earlier and more important) and the lowest-priority tail is dropped
        until the assembled prompt fits. Providers are dynamic context and
        are not dropped.

        Passing no budget keeps every active section, same as before.
        """
        return self.assemble_with_report(budget=budget, **ctx).prompt

    def assemble_with_report(
        self,
        *,
        budget: int | None = None,
        **ctx: Any,
    ) -> AssemblyReport:
        """Assemble like :meth:`assemble` and report kept, dropped, and tokens."""
        if budget is not None and budget < 0:
            raise ValueError("budget must be >= 0")

        raw_model = ctx.get("model")
        model = str(raw_model) if raw_model else "gpt-4o"

        active = [
            section
            for section in self.template.active_sections(ctx)
            if section.render()
        ]
        provider_parts = [text for text in (p.get_context() for p in self.providers) if text]
        provider_text = "\n\n".join(provider_parts)
        provider_tokens = count_tokens(provider_text, model=model) if provider_text else 0

        def render(sections: list[Section]) -> str:
            parts = [section.render() for section in sections]
            if provider_text:
                parts.append(provider_text)
            return "\n\n".join(parts)

        full = render(active)
        tokens_before = count_tokens(full, model=model)

        kept_sections = list(active)
        if budget is not None:
            while kept_sections and count_tokens(render(kept_sections), model=model) > budget:
                kept_sections.pop()

        prompt = render(kept_sections)
        tokens_after = count_tokens(prompt, model=model)
        kept_names = {section.name for section in kept_sections}
        decisions = tuple(
            SectionDecision(
                name=section.name,
                priority=section.priority,
                tokens=count_tokens(section.render(), model=model),
                kept=section.name in kept_names,
            )
            for section in active
        )
        return AssemblyReport(
            prompt=prompt,
            decisions=decisions,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            budget=budget,
            model=model,
            provider_tokens=provider_tokens,
        )

    @property
    def section_names(self) -> list[str]:
        """Return ordered list of active section names for inspection."""
        return [s.name for s in self.template.active_sections()]


def format_assembly_report(
    report: AssemblyReport,
    *,
    config: str | None = None,
) -> str:
    """Plain-text before/after comparison for a terminal or a README.

    The bars count the assembled prompt. The tables count each section alone,
    so a handful of separator tokens will not add up exactly.
    """
    scale = report.tokens_before
    n_sections = len(report.decisions)
    n_kept = sum(1 for d in report.decisions if d.kept)
    n_dropped = n_sections - n_kept
    saved_pct = round(report.tokens_saved / scale * 100) if scale else 0

    command = "prompt-ctx assemble"
    if config:
        command += f" {config}"
    if report.budget is not None:
        command += f" --budget {report.budget}"
    command += " --report"

    after_detail = f"{n_kept} kept"
    if report.budget is not None:
        after_detail = f"budget {report.budget:,} | {after_detail}"
    saved_detail = f"{n_dropped} dropped | {saved_pct}%"

    lines = [
        f"$ {command}",
        f"model:  {report.model}",
        "",
        _summary("BEFORE", report.tokens_before, scale, f"{n_sections} sections"),
        _summary("AFTER", report.tokens_after, scale, after_detail),
        _summary("SAVED", report.tokens_saved, scale, saved_detail),
    ]
    if report.provider_tokens:
        # Same column as the bars above: label, then "[" + bar + "]".
        lines.append(
            f"{'LIVE':<6} {' ' * (_BAR_WIDTH + 2)}  {report.provider_tokens:>7,} tokens"
            "  dynamic context, kept"
        )
    if report.budget is not None and not report.within_budget:
        lines.append("NOTE    prompt is still over budget; dynamic context is kept in full")

    lines.append("")
    lines.append("KEPT  (priority order)")
    lines.extend(_decision_table([d for d in report.decisions if d.kept]))
    lines.append("")
    lines.append("DROPPED  (lowest priority first)")
    dropped = [d for d in report.decisions if not d.kept]
    dropped.reverse()
    lines.extend(_decision_table(dropped))
    return "\n".join(lines)


def _summary(label: str, tokens: int, scale: int, detail: str) -> str:
    bar = _bar(tokens, scale)
    return f"{label:<6} [{bar}]  {tokens:>7,} tokens  {detail}"


def _bar(value: int, scale: int, width: int = _BAR_WIDTH) -> str:
    if value <= 0 or scale <= 0:
        filled = 0
    else:
        filled = int(round(value * width / scale))
        filled = min(width, max(1, filled))
    return "#" * filled + "." * (width - filled)


def _decision_table(rows: list[SectionDecision]) -> list[str]:
    if not rows:
        return ["  (none)"]
    lines = [
        f"{'priority':>8}  {'tokens':>7}  section",
        f"{'--------':>8}  {'-------':>7}  -------",
    ]
    for row in rows:
        lines.append(f"{row.priority:>8d}  {row.tokens:>7,d}  {row.name}")
    return lines
