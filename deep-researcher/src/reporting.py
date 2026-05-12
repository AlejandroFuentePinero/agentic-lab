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
            "invent URLs. Every inline `[Source: <url>]` citation in the body "
            "must appear in this list."
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

If a previous draft is included, treat this as a revision pass: address every
listed issue, preserve content the issues don't object to, and produce a
cleaner version of the same report. Do not rewrite from scratch.

If no previous draft is included, this is the first pass: outline the report,
then produce the full markdown. Aim for 1000+ words and clear structure
(introduction, body sections, conclusion).

CITATIONS — strict rules:
- Every substantive claim (a specific finding, statistic, attribution, study,
  or position) must be followed by an inline citation in the form
  `[Source: <url>]`, where `<url>` is one of the URLs from the `Sources:`
  blocks in the search summaries you were given.
- Never invent or guess a URL. Never cite a URL that did not appear in the
  search summaries. If a claim has no supporting URL in the summaries, either
  remove the claim or rephrase it as a general statement without a citation.
- Populate the `sources` field with the deduplicated list of every URL you
  cite in the body. Every URL in `sources` must appear in the search
  summaries; every inline citation in the body must appear in `sources`.

Always return four fields: a 2–3 sentence summary, the full markdown report
(with inline citations as specified), 3–5 follow-up questions worth
researching next, and the `sources` list.
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
   - Every URL in `sources` must appear in at least one `Sources:` block from
     the search summaries. Any URL that doesn't is fabricated — fail the draft
     and name it in `issues`.
   - Every inline `[Source: <url>]` citation in the markdown body must appear
     in the `sources` list. Any citation that doesn't is unsupported — fail
     the draft and name it.
   - Every substantive claim (a specific finding, statistic, attribution,
     study, or named position) must be followed by an inline citation. Vague
     introductory framing doesn't need one; specific factual claims do. If
     substantive claims appear without citations, fail the draft.
   - Be especially suspicious of any citation that pairs a major institution
     ("Anthropic", "The Atlantic", a named university) with a year but has no
     matching URL — that's the classic hallucination shape.

2. **Query coverage.** The report addresses every part of the original query.
   No drift into adjacent topics; no missing sub-questions.

3. **Structural coherence.** Introduction → body → conclusion, with no orphan
   sections, dangling references, or contradictions between sections.

Return `passes=True` if and only if all three criteria are met, with
`issues=[]`. Otherwise return `passes=False` and a list of specific,
actionable issues for the writer to fix. For citation failures, name the
exact URL or claim and say what's wrong with it (e.g. "URL https://… in
sources does not appear in any search summary" or "claim X has no inline
[Source: …] citation"). Do not nitpick style or word choice.
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
