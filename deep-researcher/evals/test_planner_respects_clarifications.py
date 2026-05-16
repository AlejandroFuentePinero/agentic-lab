"""Eval: does the planner actually treat clarifications as hard constraints?

This runs the real planner against the OpenAI API — it is NOT part of the
unit-test suite (which is intentionally network-free). Run it manually when
you change the planner's instructions or the clarifications prompt block:

    cd deep-researcher
    uv run python -m evals.test_planner_respects_clarifications

Why this exists: the planner can silently ignore a clarification by emitting
generic-sounding search terms, and the rest of the pipeline will not flag it
(the searches will succeed, the writer will write *something*, the critic
only grades citations and structure). Without an eval pinning the contract
between clarifications and search terms, regressions to the planner prompt
go unnoticed until a user notices their region/timeframe filter was dropped.

Each scenario picks a query that is ambiguous on a single axis (region,
timeframe, scope) and an answer that should appear *as a keyword* in every
search the planner emits. The threshold is "majority of searches mention
the constraint" — not "all" — because the planner is also instructed to
diversify the searches, and one general-context search per plan is fine.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from agents import Runner

from src.clarification import Clarification
from src.config import load_settings
from src.research import WebSearchPlan, build_planner


@dataclass(frozen=True)
class Scenario:
    name: str
    query: str
    clarifications: list[Clarification]
    # Each accepted_keywords entry is a set of synonyms; a search counts as
    # respecting the constraint if it mentions ANY synonym in the set.
    accepted_keywords: list[set[str]]


SCENARIOS: list[Scenario] = [
    Scenario(
        name="region: Spain",
        query="What are the rules on remote work taxation?",
        clarifications=[Clarification(question="Which country?", answer="Spain")],
        accepted_keywords=[{"spain", "spanish", "españa"}],
    ),
    Scenario(
        name="timeframe: 2025 only",
        query="What is new in fusion research?",
        clarifications=[
            Clarification(question="What timeframe?", answer="Calendar year 2025")
        ],
        accepted_keywords=[{"2025"}],
    ),
    Scenario(
        name="scope: alignment, not policy",
        query="Tell me about AI safety.",
        clarifications=[
            Clarification(
                question="Which area of AI safety?",
                answer="Technical alignment research, not policy or governance",
            )
        ],
        accepted_keywords=[{"alignment"}],
    ),
]


async def _plan(query: str, clarifications: list[Clarification]) -> WebSearchPlan:
    settings = load_settings()
    planner = build_planner(settings)
    block = "\n".join(f"- Q: {c.question}\n  A: {c.answer}" for c in clarifications)
    prompt = (
        f"Query: {query}\n\n"
        f"Clarifications (HARD CONSTRAINTS on every search):\n{block}"
    )
    result = await Runner.run(planner, prompt)
    return result.final_output_as(WebSearchPlan)


def _count_matches(plan: WebSearchPlan, keyword_set: set[str]) -> int:
    return sum(
        1
        for s in plan.searches
        if any(k in s.query.lower() for k in keyword_set)
    )


async def _run_scenario(scenario: Scenario) -> tuple[bool, str]:
    plan = await _plan(scenario.query, scenario.clarifications)
    n = len(plan.searches)
    required = (n // 2) + 1  # strict majority

    failures: list[str] = []
    for keyword_set in scenario.accepted_keywords:
        matches = _count_matches(plan, keyword_set)
        if matches < required:
            failures.append(
                f"Expected ≥{required}/{n} searches to mention any of "
                f"{sorted(keyword_set)}; got {matches}."
            )

    listed = "\n".join(f"    {i + 1}. {s.query}" for i, s in enumerate(plan.searches))
    detail = f"Searches produced:\n{listed}"
    if failures:
        return False, "  " + "\n  ".join(failures) + "\n  " + detail
    return True, "  " + detail


async def main() -> int:
    print("Running planner clarification evals against the live OpenAI API…\n")
    all_passed = True
    for scenario in SCENARIOS:
        print(f"[{scenario.name}]")
        passed, detail = await _run_scenario(scenario)
        print(detail)
        print(f"  → {'PASS' if passed else 'FAIL'}\n")
        all_passed = all_passed and passed
    print("All scenarios passed." if all_passed else "Some scenarios failed.")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
