"""Reporting phase: write a long-form markdown report, then critique it.

The Writer handles both first-pass synthesis and revision (when the orchestrator
re-runs it with the previous draft and a list of critic issues attached). The
Critic enforces a fixed three-criterion rubric and returns a strict pass/fail.
"""

from __future__ import annotations

from agents import Agent
from pydantic import BaseModel, Field

from .config import Settings


class ReportData(BaseModel):
    short_summary: str = Field(description="A 2–3 sentence summary of the findings.")
    markdown_report: str = Field(description="The full report in markdown.")
    follow_up_questions: list[str] = Field(
        description="Topics worth researching further as a follow-up."
    )
    sources: list[str] = Field(
        description=(
            "The deduplicated list of URLs that back the report's claims. "
            "Every URL must come from the provided search summaries — do not "
            "invent URLs. Every inline markdown-link citation in the body "
            "must point at a URL in this list."
        )
    )


class CritiqueResult(BaseModel):
    passes: bool = Field(
        description="True if the report satisfies all three rubric criteria."
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Specific problems for the writer to fix. Empty when passes=True.",
    )


_WRITER_INSTRUCTIONS = """\
You are a senior researcher writing a cohesive long-form report.

You will receive:
- The original user query.
- A list of summarised search results, each ending with a `Sources:` block of
  URLs that the search agent used to produce the summary.
- Optionally: a previous draft of the report and a list of issues raised by a
  critic.

If a previous draft is included, treat this as a revision pass (see REVISION
RULES below). Otherwise, this is the first pass: outline the report, then
produce the full markdown. Aim for 1000+ words and clear structure
(introduction, body sections, conclusion).

CITATIONS — what counts as a citation:
- A citation is a standard markdown link in the body: `[text](<url>)`. The
  link text can be anything you find useful (e.g. the source domain, the
  publication name, the word "Source"). The URL is what matters.
- Every substantive claim (a specific finding, statistic, attribution, study,
  or named position) must be followed by such a markdown link.
- Every cited URL must be one of the URLs from the `Sources:` blocks in the
  search summaries you were given. Never invent or guess a URL.
- Populate the `sources` field with the deduplicated list of every URL you
  cite in the body. Every URL in `sources` must appear in the search
  summaries; every URL cited in the body must appear in `sources`.

REVISION RULES (only apply when a previous draft is given):
- Address each listed issue specifically. Do NOT change content the issues
  don't object to. Surgical edits, not a rewrite.
- Preserve every inline markdown-link citation from the previous draft that
  no issue objects to. Stripping citations to "clean up" the body is a
  failure mode, not a fix.
- When an issue says a claim is unsupported or a URL is fabricated, prefer in
  this order: (1) find a different URL in the search summaries that does
  support the claim and use it; (2) soften the claim so it doesn't need a
  specific citation; (3) only as a last resort, delete the claim. Default to
  grounding, not deleting.

REPORT BODY STRUCTURE — strict rules:
- The `markdown_report` field is the report BODY ONLY: introduction, body
  sections, conclusion. Use `##` for major sections and `###` for subsections.
- Do NOT include your own `## Summary`, `## References`, `## Sources`, or
  `## Follow-up questions` sections in the body. Those are rendered separately
  by the system from the `short_summary`, `sources`, and `follow_up_questions`
  fields. Duplicating them produces a malformed saved file.

Always return four fields: a 2–3 sentence summary, the full markdown report
(with inline markdown-link citations as specified, body only), 3–5 follow-up
questions worth researching next, and the `sources` list.
"""


_CRITIC_INSTRUCTIONS = """\
You are a strict reviewer of research reports. Your priority is detecting
fabricated or unsupported citations — LLMs are prone to inventing plausible-
sounding sources, and your job is to catch that.

You will receive the original query, the summarised search results that were
given to the writer (each ending with a `Sources:` block of URLs), and the
writer's draft (markdown body + the `sources` list of URLs). Apply exactly
these three criteria, in order:

1. **Citation grounding (strict, URL-based).**
   - The `sources` list must be non-empty.
   - A citation in the body is any standard markdown link `[text](<url>)`.
     The link text is not significant — verify by URL only.
   - Every URL in `sources` must appear in at least one `Sources:` block from
     the search summaries. Any URL that doesn't is fabricated — fail the draft
     and name it in `issues`.
   - Every URL cited in the body (i.e. inside any `[text](<url>)` link) must
     appear in the `sources` list. Any cited URL not in `sources` is
     unsupported — fail the draft and name it.
   - Every substantive claim (a specific finding, statistic, attribution,
     study, or named position) must be followed by a markdown-link citation.
     Vague introductory framing doesn't need one; specific factual claims do.
     If substantive claims appear without citations, fail the draft.
   - Be especially suspicious of any claim that pairs a major institution
     ("Anthropic", "The Atlantic", a named university) with a year but has no
     supporting markdown link — that's the classic hallucination shape.

2. **Query coverage.** The report addresses every part of the original query.
   No drift into adjacent topics; no missing sub-questions.

3. **Structural coherence.** Introduction → body → conclusion, with no orphan
   sections, dangling references, or contradictions between sections.

Return `passes=True` if and only if all three criteria are met, with
`issues=[]`. Otherwise return `passes=False` and a list of specific,
actionable issues for the writer to fix. For citation failures, name the
exact URL or claim and say what's wrong with it (e.g. "URL https://… in
sources does not appear in any search summary" or "claim about X has no
supporting markdown-link citation"). Do not nitpick style or word choice.
"""


def build_writer(settings: Settings) -> Agent:
    return Agent(
        name="Writer",
        instructions=_WRITER_INSTRUCTIONS,
        model=settings.model,
        output_type=ReportData,
    )


def build_critic(settings: Settings) -> Agent:
    return Agent(
        name="Critic",
        instructions=_CRITIC_INSTRUCTIONS,
        model=settings.critic_model,
        output_type=CritiqueResult,
    )
