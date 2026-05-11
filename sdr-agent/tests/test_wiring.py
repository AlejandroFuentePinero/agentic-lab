"""Agent-graph shape: the externally visible structure of the manager + email manager.

These tests don't introspect *how* the agents were built (which model class,
which prompt strings) — only the contract they expose to the rest of the system:
which tools are present, which agents are reachable via handoff, how many
guardrails are attached. They survive prompt edits and provider swaps; they fail
when the wiring genuinely breaks.
"""

from __future__ import annotations

from src import build_sales_manager
from src.delivery import build_email_manager


def test_sales_manager_exposes_three_personas_as_tools(settings):
    mgr = build_sales_manager(settings)

    assert mgr.name == "Sales Manager"
    assert sorted(t.name for t in mgr.tools) == [
        "busy_sales_agent",
        "engaging_sales_agent",
        "professional_sales_agent",
    ]


def test_sales_manager_hands_off_to_the_email_manager(settings):
    mgr = build_sales_manager(settings)

    assert [h.name for h in mgr.handoffs] == ["Email Manager"]


def test_sales_manager_has_an_input_guardrail(settings):
    mgr = build_sales_manager(settings)

    assert len(mgr.input_guardrails) == 1, (
        "The Sales Manager should have exactly the name-check input guardrail; "
        "if you add more, update this test deliberately"
    )


def test_email_manager_owns_subject_html_and_send_tools(settings):
    em = build_email_manager(settings)

    assert em.name == "Email Manager"
    assert sorted(t.name for t in em.tools) == [
        "html_converter",
        "send_html_email",
        "subject_writer",
    ]


def test_email_manager_advertises_a_handoff_description(settings):
    em = build_email_manager(settings)

    assert em.handoff_description, (
        "Without a handoff_description, the Sales Manager has no signal for "
        "*when* to hand off — the LLM has to guess"
    )
