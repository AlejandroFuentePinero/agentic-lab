"""Shared pytest fixtures.

Two responsibilities:

1. Provide a `settings` fixture with stub credentials so wiring tests can build
   the agent graph without touching real env vars or making network calls.
2. Neutralise `load_dotenv` inside `src.config` for every test. Otherwise the
   real `.env` at the repo root would override `monkeypatch.setenv` calls
   (because `load_dotenv(override=True)` clobbers existing env), making the
   "missing env var" tests pass for the wrong reason.
"""

from __future__ import annotations

import pytest

from src.config import Settings


@pytest.fixture(autouse=True)
def _disable_dotenv(monkeypatch):
    monkeypatch.setattr("src.config.load_dotenv", lambda *args, **kwargs: None)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        sendgrid_api_key="test-sendgrid-key",
        openai_api_key="test-openai-key",
        anthropic_api_key="test-anthropic-key",
        from_email="from@example.com",
        to_email="to@example.com",
    )
