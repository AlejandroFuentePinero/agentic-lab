"""Orchestrates plan → search → write → critique → (revise) → save.

The flow is an async generator that yields human-readable status strings as it
progresses, so both CLI inspection and the Gradio UI can consume the same
contract. The critic + one-revision loop is the only non-trivial piece of
control flow; everything else is sequential composition.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from agents import Runner, gen_trace_id, trace

from .config import Settings
from .reporting import CritiqueResult, ReportData, build_critic, build_writer
from .research import WebSearchItem, WebSearchPlan, build_planner, build_search_agent
from .storage import save_report


class ResearchManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._planner = build_planner(settings)
        self._search_agent = build_search_agent(settings)
        self._writer = build_writer(settings)
        self._critic = build_critic(settings)

    async def run(self, query: str) -> AsyncIterator[str]:
        trace_id = gen_trace_id()
        with trace("Deep research", trace_id=trace_id):
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

            yield "Planning searches…"
            plan = await self._plan(query)
            yield f"Planned {len(plan.searches)} searches. Searching…"

            results = await self._search(plan)
            yield f"Got {len(results)} search summaries. Writing draft report…"

            report = await self._write(query, results)
            yield "Draft ready. Critiquing…"

            critique = await self._critique(query, results, report)
            if critique.passes:
                yield "Critic approved on the first pass."
            else:
                yield (
                    f"Critic flagged {len(critique.issues)} issue(s). "
                    f"Revising once more…"
                )
                report = await self._revise(query, results, report, critique.issues)
                yield "Revision complete. Re-reviewing the revised draft…"

                final_critique = await self._critique(query, results, report)
                if final_critique.passes:
                    yield "Revised draft passed review. Saving."
                else:
                    yield (
                        f"Revised draft still has {len(final_critique.issues)} "
                        f"issue(s). Doing one more revision pass (no further "
                        f"review after this — see remaining issues below):"
                    )
                    for issue in final_critique.issues:
                        yield f"  - {issue}"
                    # Second revision is the final draft: writer runs at most
                    # three times, critic at most twice. The hard cap on cost.
                    report = await self._revise(
                        query, results, report, final_critique.issues
                    )
                    yield "Final revision complete. Saving."

            path = save_report(
                query=query,
                short_summary=report.short_summary,
                markdown_report=report.markdown_report,
                follow_up_questions=report.follow_up_questions,
                sources=report.sources,
                reports_dir=self.settings.reports_dir,
            )
            yield f"Saved to {path}"
            yield report.markdown_report

    async def _plan(self, query: str) -> WebSearchPlan:
        result = await Runner.run(self._planner, f"Query: {query}")
        return result.final_output_as(WebSearchPlan)

    async def _search(self, plan: WebSearchPlan) -> list[str]:
        tasks = [asyncio.create_task(self._search_one(item)) for item in plan.searches]
        results: list[str] = []
        for task in asyncio.as_completed(tasks):
            outcome = await task
            if outcome is not None:
                results.append(outcome)
        return results

    async def _search_one(self, item: WebSearchItem) -> str | None:
        prompt = f"Search term: {item.query}\nReason: {item.reason}"
        try:
            result = await Runner.run(self._search_agent, prompt)
            return str(result.final_output)
        except Exception:
            # Soft-fail individual searches so one bad result doesn't sink the
            # whole run — the writer will just see fewer summaries.
            return None

    async def _write(self, query: str, search_results: list[str]) -> ReportData:
        prompt = (
            f"Original query: {query}\n"
            f"Summarised search results: {search_results}"
        )
        result = await Runner.run(self._writer, prompt)
        return result.final_output_as(ReportData)

    async def _critique(
        self, query: str, search_results: list[str], draft: ReportData
    ) -> CritiqueResult:
        prompt = (
            f"Original query: {query}\n\n"
            f"Summarised search results: {search_results}\n\n"
            f"Draft report:\n---\n{draft.markdown_report}\n---"
        )
        result = await Runner.run(self._critic, prompt)
        return result.final_output_as(CritiqueResult)

    async def _revise(
        self,
        query: str,
        search_results: list[str],
        previous: ReportData,
        issues: list[str],
    ) -> ReportData:
        issues_block = "\n".join(f"- {i}" for i in issues)
        previous_sources = "\n".join(f"- {u}" for u in previous.sources) or "(none)"
        prompt = (
            f"Original query: {query}\n"
            f"Summarised search results: {search_results}\n\n"
            f"Previous draft:\n---\n{previous.markdown_report}\n---\n\n"
            f"Previous sources:\n{previous_sources}\n\n"
            f"Critic issues to address:\n{issues_block}\n\n"
            f"Produce a revised report addressing every listed issue. "
            f"Preserve content the issues don't object to. The same citation "
            f"rules apply: every URL cited in the body (inside any markdown "
            f"link `[text](<url>)`) must appear in `sources`, and every URL "
            f"in `sources` must come from the search summaries."
        )
        result = await Runner.run(self._writer, prompt)
        return result.final_output_as(ReportData)
