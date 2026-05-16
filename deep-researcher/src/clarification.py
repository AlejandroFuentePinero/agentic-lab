"""Clarification phase: decide whether the query needs to be sharpened before
planning, and carry the user's answers back to the planner.

The clarifier is intentionally conservative. It produces zero questions for
queries that are already specific enough — most queries should pass through
without interaction. Only essential ambiguities (region, timeframe, audience,
scope) that would meaningfully redirect *which* searches to run trigger it.

The orchestrator does not own the human-interaction loop: this module exposes
the clarifier agent and the `Clarification` pair type, and the caller (CLI,
Gradio, anything else) is responsible for collecting answers however its
environment dictates.
"""

from __future__ import annotations

from agents import Agent
from pydantic import BaseModel, Field

from .config import Settings


class Clarification(BaseModel):
    """A question the clarifier raised together with the caller's answer."""

    question: str = Field(description="The clarifying question that was asked.")
    answer: str = Field(description="The caller's answer to that question.")


class ClarificationQuestions(BaseModel):
    """Output of the clarifier agent. Empty list means no clarification needed."""

    questions: list[str] = Field(
        default_factory=list,
        description=(
            "Questions to ask the user. Empty when the query has no essential "
            "ambiguities that would change which searches to run."
        ),
    )


_CLARIFIER_INSTRUCTIONS = """\
You are a research clarifier. Given a user query, decide whether any
essential ambiguities must be resolved BEFORE a planner can generate useful
web searches.

Ask a question ONLY if the answer would materially change which searches to
run. The four categories that qualify:
- **Region / jurisdiction.** "Remote work tax rules" — which country?
- **Timeframe.** "Latest in fusion research" — past year? past decade?
- **Audience / level.** "Best ML book" — for whom? mathematicians? beginners?
- **Scope.** "AI safety" — alignment research? policy? deployment risk?

Do NOT ask about:
- Stylistic preferences (report length, tone, format) — the writer handles those.
- Anything already specific in the query.
- Anything you can guess a reasonable default for.
- Anything the writer or critic can reasonably handle after the fact.

If the query is specific enough as written, return `questions=[]`. This is
the correct answer for the majority of well-formed queries. Be conservative —
asking when you didn't need to wastes the user's time more than missing one
would.

Cap: at most 3 questions, one short sentence each.
"""


def build_clarifier(settings: Settings) -> Agent:
    return Agent(
        name="Clarifier",
        instructions=_CLARIFIER_INSTRUCTIONS,
        model=settings.model,
        output_type=ClarificationQuestions,
    )
