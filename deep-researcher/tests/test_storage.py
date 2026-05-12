"""Behavior of `storage.py`: slug generation, filename format, and file writing.

Pure-Python module — no agents, no network. Anything that breaks here would
silently corrupt the reports archive, so it's worth testing thoroughly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.storage import save_report, slugify


def test_slug_lowercases_and_hyphenates_basic_query():
    assert slugify("Effects of microplastics on marine life") == (
        "effects-of-microplastics-on-marine-life"
    )


def test_slug_truncates_long_queries_at_word_boundary():
    long_query = (
        "What are the long-term economic, social, and environmental implications of "
        "transitioning to renewable energy sources across developing nations"
    )

    slug = slugify(long_query)

    assert len(slug) <= 60, f"slug too long: {len(slug)} chars"
    assert not slug.endswith("-"), "slug should not end with a hyphen after truncation"
    assert slug.startswith("what-are-the"), "should keep the start of the query"


def test_slug_handles_unicode_and_punctuation_safely():
    # Anything not ASCII alphanumeric collapses to a single hyphen — keeps
    # filenames filesystem-safe on every OS without losing readability.
    assert slugify("Café résumés: what's new?") == "caf-r-sum-s-what-s-new"
    assert slugify("AI/ML & you — 2026!") == "ai-ml-you-2026"
    assert slugify("🚀 launch day") == "launch-day"


def test_save_writes_file_named_with_timestamp_and_slug(tmp_path):
    frozen = datetime(2026, 5, 12, 14, 30, 52, tzinfo=timezone.utc)

    path = save_report(
        query="Effects of microplastics",
        short_summary="s",
        markdown_report="body",
        follow_up_questions=["q1"],
        sources=["https://example.com/a"],
        reports_dir=tmp_path,
        now=frozen,
    )

    assert path.name == "2026-05-12T143052Z--effects-of-microplastics.md"
    assert path.parent == tmp_path


def test_save_creates_reports_dir_if_missing(tmp_path):
    nested = tmp_path / "does" / "not" / "exist" / "yet"

    path = save_report(
        query="q",
        short_summary="s",
        markdown_report="body",
        follow_up_questions=[],
        sources=[],
        reports_dir=nested,
    )

    assert path.exists()
    assert nested.is_dir()


def test_save_writes_query_summary_body_followups_and_sources_into_file(tmp_path):
    path = save_report(
        query="What is dark matter?",
        short_summary="Dark matter is the invisible mass that holds galaxies together.",
        markdown_report="## Body\nFull report goes here.",
        follow_up_questions=["What is dark energy?", "How is it detected?"],
        sources=["https://nasa.gov/dark-matter", "https://cern.ch/dark-matter"],
        reports_dir=tmp_path,
    )

    contents = path.read_text()
    assert "What is dark matter?" in contents, "query should appear in the file"
    assert "Dark matter is the invisible mass" in contents, "short_summary must be saved"
    assert "Full report goes here." in contents, "markdown_report must be saved"
    assert "What is dark energy?" in contents, "follow-up questions must be saved"
    assert "How is it detected?" in contents
    # References section must be rendered so the reader can verify citations.
    assert "## References" in contents
    assert "https://nasa.gov/dark-matter" in contents
    assert "https://cern.ch/dark-matter" in contents
