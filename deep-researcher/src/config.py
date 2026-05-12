"""Runtime settings. Only the OpenAI key is read from env — everything else
is a Python default, kept out of the shared `.env`."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Anchor the default reports directory to the agent root so reports always land
# in deep-researcher/reports/ regardless of where the CLI is invoked from.
_AGENT_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_REPORTS_DIR = _AGENT_DIR / "reports"


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    model: str = "gpt-4o-mini"
    # The critic uses a stronger model than the rest of the pipeline. Its job
    # is to catch fabricated citations and unsupported claims in the writer's
    # draft — a scrutiny task where gpt-4o-mini was empirically too lenient.
    critic_model: str = "gpt-4o"
    num_searches: int = 5
    reports_dir: Path = _DEFAULT_REPORTS_DIR


def load_settings() -> Settings:
    load_dotenv(override=True)
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Missing required environment variable: OPENAI_API_KEY")
    return Settings(openai_api_key=key)
