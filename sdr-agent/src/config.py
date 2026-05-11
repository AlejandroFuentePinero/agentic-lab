"""Runtime settings: env vars + model choices in one place."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    sendgrid_api_key: str
    openai_api_key: str
    anthropic_api_key: str
    from_email: str
    to_email: str
    sales_persona_model: str = "claude-sonnet-4-6"
    utility_model: str = "gpt-4o-mini"


def load_settings() -> Settings:
    load_dotenv(override=True)
    return Settings(
        sendgrid_api_key=_required("SENDGRID_API_KEY"),
        openai_api_key=_required("OPENAI_API_KEY"),
        anthropic_api_key=_required("ANTHROPIC_API_KEY"),
        from_email=os.environ.get("SDR_FROM_EMAIL", "alejandrofuentepinero@gmail.com"),
        to_email=os.environ.get("SDR_TO_EMAIL", "alejandrofuentepinero@gmail.com"),
        sales_persona_model=os.environ.get("SDR_SALES_MODEL", "claude-sonnet-4-6"),
        utility_model=os.environ.get("SDR_UTILITY_MODEL", "gpt-4o-mini"),
    )


def _required(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value
