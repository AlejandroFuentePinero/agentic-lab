"""Agent-graph shape: what the gathering and reporting builders expose.

These tests don't introspect *how* the agents were built (model class, prompt
strings) — only the contract they expose to the orchestrator: structured
output types, tool counts, names. They survive prompt edits; they fail when
wiring genuinely breaks.
"""

from __future__ import annotations

from src.clarification import (
    Clarification,
    ClarificationQuestions,
    build_clarifier,
)
from src.reporting import (
    CritiqueResult,
    ReportData,
    build_critic,
    build_writer,
)
from src.research import WebSearchItem, WebSearchPlan, build_planner, build_search_agent


def test_clarifier_returns_structured_clarificationquestions(settings):
    clarifier = build_clarifier(settings)

    assert clarifier.name == "Clarifier"
    assert clarifier.output_type is ClarificationQuestions


def test_clarificationquestions_defaults_to_empty_list():
    # Empty list is the *expected* output for already-specific queries.
    # The default_factory keeps that path cheap for the LLM.
    cq = ClarificationQuestions()
    assert cq.questions == []


def test_clarification_pairs_question_with_answer():
    c = Clarification(question="Which country?", answer="Spain")

    assert c.question == "Which country?"
    assert c.answer == "Spain"


def test_planner_returns_structured_websearchplan(settings):
    planner = build_planner(settings)

    assert planner.name == "Planner"
    assert planner.output_type is WebSearchPlan


def test_websearchplan_model_has_searches_list_of_websearchitem():
    plan = WebSearchPlan(
        searches=[
            WebSearchItem(reason="r1", query="q1"),
            WebSearchItem(reason="r2", query="q2"),
        ]
    )

    assert len(plan.searches) == 2
    assert plan.searches[0].query == "q1"
    assert plan.searches[1].reason == "r2"


def test_search_agent_has_websearch_tool_and_requires_tool_use(settings):
    agent = build_search_agent(settings)

    assert agent.name == "Search Agent"
    # Without `tool_choice="required"` the model can decide to skip the search
    # and answer from training-data memory, defeating the point of this agent.
    assert agent.model_settings.tool_choice == "required"
    # Exactly one tool: WebSearchTool. If more tools appear, this should be a
    # deliberate update with a clear reason — extra tools change the contract.
    assert len(agent.tools) == 1


def test_writer_returns_structured_reportdata(settings):
    writer = build_writer(settings)

    assert writer.name == "Writer"
    assert writer.output_type is ReportData


def test_reportdata_carries_summary_report_followups_and_sources():
    r = ReportData(
        short_summary="s",
        markdown_report="# Title\nbody",
        follow_up_questions=["q1", "q2"],
        sources=["https://example.com/a", "https://example.com/b"],
    )

    assert r.short_summary == "s"
    assert r.markdown_report.startswith("# Title")
    assert r.follow_up_questions == ["q1", "q2"]
    # Sources are required so the writer can't silently omit citations.
    assert r.sources == ["https://example.com/a", "https://example.com/b"]


def test_critic_returns_structured_critiqueresult(settings):
    critic = build_critic(settings)

    assert critic.name == "Critic"
    assert critic.output_type is CritiqueResult


def test_critiqueresult_supports_strict_pass_fail_with_issues():
    passing = CritiqueResult(passes=True, issues=[])
    failing = CritiqueResult(passes=False, issues=["claim X has no source", "structure unclear"])

    assert passing.passes is True
    assert failing.passes is False
    assert len(failing.issues) == 2
