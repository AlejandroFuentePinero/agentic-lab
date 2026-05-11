"""CLI entry point: `python -m sdr "<prompt>"`."""

from __future__ import annotations

import argparse
import asyncio

from agents import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    Runner,
    trace,
)

from .config import load_settings
from .orchestrator import build_sales_manager


_DEFAULT_PROMPT = "Send out a cold sales email addressed to Dear CEO"


async def _run(prompt: str) -> int:
    settings = load_settings()
    sales_manager = build_sales_manager(settings)
    try:
        with trace("Automated SDR"):
            # 3 personas + 1 pick + 1 handoff + 3 email-mgr tools = ~8 turns happy path;
            # 20 leaves headroom for the model to retry a tool call without aborting.
            result = await Runner.run(sales_manager, prompt, max_turns=20)
    except InputGuardrailTripwireTriggered as exc:
        print(f"Input guardrail tripped: refusing to send. Details: {exc}")
        return 2
    except OutputGuardrailTripwireTriggered as exc:
        print(f"Output guardrail tripped: a draft was rejected. Details: {exc}")
        return 3

    # The handoff to Email Manager is the only path that actually sends mail.
    # If the manager replied directly instead of invoking it, no send happened.
    final_agent = result.last_agent.name if result.last_agent else "<unknown>"
    if final_agent != "Email Manager":
        print(
            f"No email sent. The Sales Manager finished without handing off to "
            f"the Email Manager (last agent: {final_agent!r}). Check the trace "
            f"to see where the chain stopped."
        )
        return 4
    print(f"Done. Email sent to {settings.to_email} (check inbox/spam).")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="sdr", description="ComplAI SDR demo")
    parser.add_argument(
        "prompt",
        nargs="?",
        default=_DEFAULT_PROMPT,
        help="Instruction for the Sales Manager (default: a generic CEO outreach).",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args.prompt)))


if __name__ == "__main__":
    main()
