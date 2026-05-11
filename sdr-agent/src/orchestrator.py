"""Top-level Sales Manager: orchestrates drafting, picks a winner, hands off to delivery.

Also defines the input guardrail (lab 3): trips when the user's prompt names a
specific person, on the assumption that personalised outreach should go through
a different (verified) flow.
"""

from __future__ import annotations

from agents import (
    Agent,
    GuardrailFunctionOutput,
    Runner,
    input_guardrail,
)
from pydantic import BaseModel

from .config import Settings
from .delivery import build_email_manager
from .drafting import build_sales_tools


_SALES_MANAGER_INSTRUCTIONS = """
You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales
email using the sales_agent tools.

Follow these steps carefully:
1. Generate Drafts: Use all three sales_agent tools to generate three different email
   drafts. Each tool returns a JSON object of the form {"body": "<email text>"}.
   Do not proceed until all three drafts are ready.

2. Evaluate and Select: Review the drafts and choose the single best email using your
   judgment of which one is most effective. You can use the tools multiple times if
   you're not satisfied with the results from the first try.

3. Handoff for Sending: Pass ONLY the winning email's body string (not the JSON
   wrapper) to the 'Email Manager' agent. The Email Manager will take care of
   formatting and sending.

Crucial Rules:
- You must use the sales agent tools to generate the drafts — do not write them yourself.
- You must hand off exactly ONE email to the Email Manager — never more than one.
"""


class _NameCheckOutput(BaseModel):
    is_name_in_message: bool
    name: str


def build_sales_manager(settings: Settings) -> Agent:
    return Agent(
        name="Sales Manager",
        instructions=_SALES_MANAGER_INSTRUCTIONS,
        tools=build_sales_tools(settings),
        handoffs=[build_email_manager(settings)],
        model=settings.utility_model,
        input_guardrails=[_build_name_guardrail(settings)],
    )


def _build_name_guardrail(settings: Settings):
    name_check_agent = Agent(
        name="Name check",
        instructions="Check if the user is including someone's personal name in what they want you to do.",
        output_type=_NameCheckOutput,
        model=settings.utility_model,
    )

    @input_guardrail
    async def guardrail_against_name(ctx, agent, message):
        result = await Runner.run(name_check_agent, message, context=ctx.context)
        return GuardrailFunctionOutput(
            output_info={"found_name": result.final_output},
            tripwire_triggered=result.final_output.is_name_in_message,
        )

    return guardrail_against_name
