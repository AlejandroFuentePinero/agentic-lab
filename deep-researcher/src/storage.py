"""Persist final reports to disk as self-contained markdown files."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


_SLUG_MAX_LEN = 60


def slugify(query: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")
    if len(slug) <= _SLUG_MAX_LEN:
        return slug
    truncated = slug[:_SLUG_MAX_LEN]
    # If we cut mid-word, drop the trailing partial word so the slug ends on a
    # whole token. Falls back to the hard truncation if the limit landed on the
    # very first word.
    last_hyphen = truncated.rfind("-")
    if last_hyphen > 0:
        truncated = truncated[:last_hyphen]
    return truncated.rstrip("-")


def save_report(
    *,
    query: str,
    short_summary: str,
    markdown_report: str,
    follow_up_questions: list[str],
    sources: list[str],
    reports_dir: Path,
    now: datetime | None = None,
) -> Path:
    when = now or datetime.now(timezone.utc)
    stamp = when.strftime("%Y-%m-%dT%H%M%SZ")
    filename = f"{stamp}--{slugify(query)}.md"
    path = reports_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _render(query, short_summary, markdown_report, follow_up_questions, sources, when)
    )
    return path


def _render(
    query: str,
    short_summary: str,
    markdown_report: str,
    follow_up_questions: list[str],
    sources: list[str],
    when: datetime,
) -> str:
    follow_ups = "\n".join(f"- {q}" for q in follow_up_questions) or "_(none)_"
    references = "\n".join(f"- <{u}>" for u in sources) or "_(none)_"
    return (
        f"# {query}\n\n"
        f"**Generated:** {when.strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n"
        f"## Summary\n\n{short_summary}\n\n"
        f"---\n\n"
        f"{markdown_report}\n\n"
        f"---\n\n"
        f"## References\n\n{references}\n\n"
        f"---\n\n"
        f"## Follow-up questions\n\n{follow_ups}\n"
    )
