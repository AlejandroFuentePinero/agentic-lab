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
            await Runner.run(sales_manager, prompt)
    except InputGuardrailTripwireTriggered as exc:
        print(f"Input guardrail tripped: refusing to send. Details: {exc}")
        return 2
    except OutputGuardrailTripwireTriggered as exc:
        print(f"Output guardrail tripped: a draft was rejected. Details: {exc}")
        return 3
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
