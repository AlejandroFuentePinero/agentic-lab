"""Sales-email drafting: three persona agents exposed as tools.

Each persona writes the same kind of artifact (a cold outreach email for ComplAI)
in a different voice. Each agent uses a structured output (`SalesEmailDraft`) and
a deterministic output guardrail that trips on un-filled template placeholders
(e.g. `[INSERT COMPANY]`, `{{name}}`, `XXXX`) — a common failure mode where the
LLM ships a template instead of a finished email.
"""

from __future__ import annotations

import re

from agents import (
    Agent,
    GuardrailFunctionOutput,
    Tool,
    output_guardrail,
)
from agents.extensions.models.litellm_model import LitellmModel
from pydantic import BaseModel, Field

from .config import Settings


class SalesEmailDraft(BaseModel):
    """Structured output returned by each sales-persona agent."""

    body: str = Field(description="The email body, in the persona's voice. Plain text or light markdown.")


_PERSONAS: dict[str, tuple[str, str]] = {
    "professional_sales_agent": (
        "Professional, serious cold sales email",
        "You are a sales agent working for ComplAI, a company that provides a SaaS tool "
        "for ensuring SOC2 compliance and preparing for audits, powered by AI. "
        "You write professional, serious cold emails. Return only the email body — "
        "do not include a subject line, salutation placeholders, or template tokens.",
    ),
    "engaging_sales_agent": (
        "Witty, engaging cold sales email",
        "You are a humorous, engaging sales agent working for ComplAI, a company that provides "
        "a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. "
        "You write witty, engaging cold emails that are likely to get a response. Return only "
        "the email body — do not include a subject line, salutation placeholders, or template tokens.",
    ),
    "busy_sales_agent": (
        "Concise, to-the-point cold sales email",
        "You are a busy sales agent working for ComplAI, a company that provides a SaaS tool "
        "for ensuring SOC2 compliance and preparing for audits, powered by AI. "
        "You write concise, to the point cold emails. Return only the email body — do not "
        "include a subject line, salutation placeholders, or template tokens.",
    ),
}


_PLACEHOLDER_PATTERNS = (
    re.compile(r"\[[A-Z][A-Z0-9 _\-]{2,}\]"),  # [INSERT NAME], [COMPANY_NAME]
    re.compile(r"\{\{[^}]+\}\}"),              # {{name}}, {{company}}
    re.compile(r"X{4,}"),                      # XXXX, XXXXX
)


@output_guardrail
async def guardrail_against_placeholders(ctx, agent, output: SalesEmailDraft) -> GuardrailFunctionOutput:
    matches = [p.pattern for p in _PLACEHOLDER_PATTERNS if p.search(output.body)]
    return GuardrailFunctionOutput(
        output_info={"matched_placeholder_patterns": matches},
        tripwire_triggered=bool(matches),
    )


def build_sales_tools(settings: Settings) -> list[Tool]:
    """Return the three persona agents wrapped as Tools for the Sales Manager."""
    model = LitellmModel(
        model=f"anthropic/{settings.sales_persona_model}",
        api_key=settings.anthropic_api_key,
    )
    return [
        Agent(
            name=name,
            instructions=instructions,
            model=model,
            output_type=SalesEmailDraft,
            output_guardrails=[guardrail_against_placeholders],
        ).as_tool(tool_name=name, tool_description=description)
        for name, (description, instructions) in _PERSONAS.items()
    ]
