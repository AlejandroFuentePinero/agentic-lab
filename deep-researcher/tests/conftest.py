"""Shared pytest fixtures.

Two responsibilities:

1. Provide a `settings` fixture with a stub `OPENAI_API_KEY` so wiring tests can
   build the agent graph without touching real env vars or making network calls.
2. Neutralise `load_dotenv` inside `src.config` for every test. Otherwise the
   real `.env` at the repo root would override `monkeypatch.setenv` / `delenv`
   calls (because `load_dotenv(override=True)` clobbers existing env), making
   the "missing env var" tests pass for the wrong reason.
"""

from __future__ import annotations

import pytest

from src.config import Settings


@pytest.fixture(autouse=True)
def _disable_dotenv(monkeypatch):
    monkeypatch.setattr("src.config.load_dotenv", lambda *args, **kwargs: None)


@pytest.fixture
def settings() -> Settings:
    return Settings(openai_api_key="test-openai-key")
