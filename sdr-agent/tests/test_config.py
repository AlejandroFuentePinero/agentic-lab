"""Behavior of `load_settings()`: required keys, defaults, and overrides."""

from __future__ import annotations

import pytest

from src.config import load_settings


_REQUIRED_KEYS = ("SENDGRID_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")
_OPTIONAL_KEYS = ("SDR_FROM_EMAIL", "SDR_TO_EMAIL", "SDR_SALES_MODEL", "SDR_UTILITY_MODEL")


def _set_required(monkeypatch) -> None:
    for key in _REQUIRED_KEYS:
        monkeypatch.setenv(key, f"value-of-{key.lower()}")


def _clear_optional(monkeypatch) -> None:
    for key in _OPTIONAL_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.mark.parametrize("missing", _REQUIRED_KEYS)
def test_missing_required_env_var_raises_with_helpful_message(monkeypatch, missing):
    _set_required(monkeypatch)
    _clear_optional(monkeypatch)
    monkeypatch.delenv(missing, raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        load_settings()

    assert missing in str(exc_info.value), (
        f"Error message should name the missing variable so the user knows what to set, "
        f"got: {exc_info.value!r}"
    )


def test_defaults_applied_when_only_required_vars_are_set(monkeypatch):
    _set_required(monkeypatch)
    _clear_optional(monkeypatch)

    s = load_settings()

    assert s.from_email == "you@example.com"
    assert s.to_email == "you@example.com"
    assert s.sales_persona_model == "claude-sonnet-4-6"
    assert s.utility_model == "gpt-4o-mini"


def test_optional_env_overrides_replace_defaults(monkeypatch):
    _set_required(monkeypatch)
    monkeypatch.setenv("SDR_FROM_EMAIL", "sender@corp.com")
    monkeypatch.setenv("SDR_TO_EMAIL", "lead@prospect.com")
    monkeypatch.setenv("SDR_SALES_MODEL", "claude-opus-4-7")
    monkeypatch.setenv("SDR_UTILITY_MODEL", "gpt-4o")

    s = load_settings()

    assert s.from_email == "sender@corp.com"
    assert s.to_email == "lead@prospect.com"
    assert s.sales_persona_model == "claude-opus-4-7"
    assert s.utility_model == "gpt-4o"


def test_required_credentials_passed_through(monkeypatch):
    _set_required(monkeypatch)
    _clear_optional(monkeypatch)

    s = load_settings()

    assert s.sendgrid_api_key == "value-of-sendgrid_api_key"
    assert s.openai_api_key == "value-of-openai_api_key"
    assert s.anthropic_api_key == "value-of-anthropic_api_key"
