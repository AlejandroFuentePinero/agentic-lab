"""Behavior of `load_settings()`: required keys and defaults."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config import Settings, load_settings


def test_missing_openai_key_raises_with_helpful_message(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        load_settings()

    assert "OPENAI_API_KEY" in str(exc_info.value), (
        "Error message should name the missing variable so the user knows what to set"
    )


def test_defaults_applied_when_only_api_key_is_set(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    s = load_settings()

    assert s.openai_api_key == "test-key"
    assert s.model == "gpt-4o-mini"
    assert s.critic_model == "gpt-4o"
    assert s.num_searches == 5
    # reports_dir is anchored to the agent directory so reports always land in
    # deep-researcher/reports/ regardless of cwd
    assert s.reports_dir.is_absolute()
    assert s.reports_dir.name == "reports"
    assert s.reports_dir.parent.name == "deep-researcher"


def test_settings_is_constructible_directly_for_tests():
    s = Settings(openai_api_key="x", model="gpt-4o", num_searches=3, reports_dir=Path("/tmp/r"))

    assert s.model == "gpt-4o"
    assert s.num_searches == 3
    assert s.reports_dir == Path("/tmp/r")
