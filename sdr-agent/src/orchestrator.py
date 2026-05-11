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
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from pydantic import BaseModel

from .config import Settings
from .delivery import build_email_manager
from .drafting import build_sales_tools


_SALES_MANAGER_INSTRUCTIONS = prompt_with_handoff_instructions("""
You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales
email and get it sent.

Follow these steps exactly once:
1. Call each of the three sales_agent tools exactly once to produce three drafts.
   Each tool returns a JSON object of the form {"body": "<email text>"}.
2. Pick the single best draft. Do not call the sales_agent tools again.
3. Transfer to the Email Manager (handoff), passing the winning draft's `body`
   string (not the JSON wrapper) as the message to it. The Email Manager will
   format and send the email — that is how this task is completed.

Rules:
- Do not write drafts yourself. Use the sales_agent tools.
- Generate exactly three drafts total. Pick one. Hand it off.
- Finishing means invoking the Email Manager handoff. Do not reply to the user
  with the email text directly.
""")


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
