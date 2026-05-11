"""The placeholder output guardrail.

Pure regex behavior — no LLM calls. Most-valuable test: verify it doesn't
false-positive on legitimate cold-email content (sequences of capital letters
inside acronyms like XSS, CSRF) while still catching the real failure modes
(`[INSERT NAME]`, `{{var}}`, `XXXX`).
"""

from __future__ import annotations

import asyncio

import pytest

from src.drafting import SalesEmailDraft, guardrail_against_placeholders


class _StubContext:
    """The guardrail signature requires a context object; it doesn't read from it."""


def _run(body: str):
    coro = guardrail_against_placeholders.run(_StubContext(), None, SalesEmailDraft(body=body))
    return asyncio.run(coro)


@pytest.mark.parametrize(
    "body",
    [
        "Hi Dear CEO,\n\nComplAI is a SOC2 compliance tool powered by AI. Worth a 15-minute chat?",
        "Quick question — how is your team currently handling SOC2 audit prep?",
        "We protect against XSS, CSRF and other OWASP top 10 risks.",  # repeated caps inside acronyms
        "Annual savings vary by org size, but most customers see 30-40% time back on audits.",
        "Reach out if useful.\n\n— A real human, not a template.",
    ],
)
def test_clean_drafts_do_not_trip(body):
    result = _run(body)

    assert result.output.tripwire_triggered is False, (
        f"Guardrail false-positive on legitimate body: {body!r}, "
        f"matched: {result.output.output_info['matched_placeholder_patterns']}"
    )
    assert result.output.output_info["matched_placeholder_patterns"] == []


@pytest.mark.parametrize(
    "body",
    [
        "Hi [INSERT NAME], welcome to ComplAI.",
        "Hi [COMPANY_NAME], we noticed your audit deadline is approaching.",
        "Hi {{name}}, ComplAI handles SOC2 for you.",
        "Save up to $XXXXX per audit cycle.",
        "[CTA HERE] — looking forward to chatting.",
    ],
)
def test_drafts_with_placeholders_trip(body):
    result = _run(body)

    assert result.output.tripwire_triggered is True, (
        f"Guardrail missed an unfilled template token in: {body!r}"
    )
    assert result.output.output_info["matched_placeholder_patterns"], (
        "When the tripwire fires the guardrail must report which pattern caught it, "
        "so callers can debug bad drafts"
    )


def test_multiple_placeholder_kinds_in_one_body_are_all_recorded():
    body = "Hi [INSERT NAME], your account at {{company}} expires in XXXX days."

    result = _run(body)

    assert result.output.tripwire_triggered is True
    assert len(result.output.output_info["matched_placeholder_patterns"]) == 3
