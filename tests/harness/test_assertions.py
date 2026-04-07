"""
Unit tests for assertion utilities.

Tests the harness functions that parse and validate interview output.
No Claude invocation needed — runs in milliseconds.

Converted from tests/harness/specs/unit/assertions.test.ts.
"""

import re
from pathlib import Path

import pytest

from assertions import (
    ANALYSIS_FIELDS,
    TRANSCRIPT_FIELDS,
    all_answers_analyzed,
    all_files_match_timestamp_pattern,
    all_questions_answered,
    exchange_count,
    file_contains,
    file_exists,
    file_matches,
    has_valid_frontmatter,
    list_files,
    parse_test_log,
    specialists_invoked,
)

SAMPLE_DIR = str(Path(__file__).parent / "fixtures" / "sample-data")


# ── file_exists ──────────────────────────────────────────────────────

class TestFileExists:
    def test_returns_true_for_existing_files(self):
        assert file_exists(SAMPLE_DIR, "valid-transcript.md") is True

    def test_returns_false_for_missing_files(self):
        assert file_exists(SAMPLE_DIR, "nonexistent.md") is False


# ── file_contains ────────────────────────────────────────────────────

class TestFileContains:
    def test_finds_a_string_in_a_file(self):
        assert file_contains(SAMPLE_DIR, "valid-transcript.md", "Lumina") is True

    def test_returns_false_when_string_not_found(self):
        assert file_contains(SAMPLE_DIR, "valid-transcript.md", "XYZNOTHERE") is False

    def test_returns_false_for_missing_files(self):
        assert file_contains(SAMPLE_DIR, "nonexistent.md", "anything") is False


# ── file_matches ─────────────────────────────────────────────────────

class TestFileMatches:
    def test_matches_a_regex_pattern(self):
        assert file_matches(SAMPLE_DIR, "valid-transcript.md", re.compile(r"type:\s*transcript")) is True

    def test_returns_false_when_pattern_doesnt_match(self):
        assert file_matches(SAMPLE_DIR, "valid-transcript.md", re.compile(r"type:\s*analysis")) is False

    def test_returns_false_for_missing_files(self):
        assert file_matches(SAMPLE_DIR, "nonexistent.md", re.compile(r"anything")) is False


# ── list_files ───────────────────────────────────────────────────────

class TestListFiles:
    def test_lists_files_in_a_directory(self):
        files = list_files(SAMPLE_DIR, ".")
        assert "valid-transcript.md" in files
        assert "valid-analysis.md" in files
        assert "test-log.jsonl" in files

    def test_returns_sorted_filenames(self):
        files = list_files(SAMPLE_DIR, ".")
        assert files == sorted(files)

    def test_returns_empty_array_for_missing_directory(self):
        assert list_files(SAMPLE_DIR, "nonexistent-dir") == []


# ── all_files_match_timestamp_pattern ────────────────────────────────

class TestAllFilesMatchTimestampPattern:
    def test_returns_false_when_files_dont_match_timestamp_pattern(self):
        # sample-data has files like valid-transcript.md, not timestamp-named
        assert all_files_match_timestamp_pattern(SAMPLE_DIR, ".") is False


# ── has_valid_frontmatter ─────────────────────────────────────────────

class TestHasValidFrontmatter:
    def test_validates_a_transcript_with_all_required_fields(self):
        assert has_valid_frontmatter(SAMPLE_DIR, "valid-transcript.md", TRANSCRIPT_FIELDS) is True

    def test_validates_an_analysis_with_all_required_fields(self):
        assert has_valid_frontmatter(SAMPLE_DIR, "valid-analysis.md", ANALYSIS_FIELDS) is True

    def test_fails_when_required_fields_are_missing(self):
        assert has_valid_frontmatter(SAMPLE_DIR, "missing-fields-transcript.md", TRANSCRIPT_FIELDS) is False

    def test_passes_with_a_subset_of_fields(self):
        assert has_valid_frontmatter(SAMPLE_DIR, "missing-fields-transcript.md", ["id", "title", "type"]) is True


# ── parse_test_log ────────────────────────────────────────────────────

class TestParseTestLog:
    def test_parses_all_events_from_jsonl(self):
        events = parse_test_log(SAMPLE_DIR, "test-log.jsonl")
        assert len(events) == 14

    def test_parses_event_types_correctly(self):
        events = parse_test_log(SAMPLE_DIR, "test-log.jsonl")
        types = [e["event"] for e in events]
        assert "specialist_invoked" in types
        assert "question_asked" in types
        assert "answer_received" in types
        assert "analysis_written" in types
        assert "checklist_updated" in types
        assert "test_complete" in types

    def test_preserves_specialist_field(self):
        events = parse_test_log(SAMPLE_DIR, "test-log.jsonl")
        first_invoke = next(e for e in events if e["event"] == "specialist_invoked")
        assert first_invoke["specialist"] == "ui-ux-design"

    def test_preserves_timestamp_field(self):
        events = parse_test_log(SAMPLE_DIR, "test-log.jsonl")
        assert events[0]["timestamp"] == "2026-04-01T19:30:00"


# ── specialists_invoked ───────────────────────────────────────────────

class TestSpecialistsInvoked:
    def test_returns_unique_specialists(self):
        events = parse_test_log(SAMPLE_DIR, "test-log.jsonl")
        result = specialists_invoked(events)
        assert result == ["ui-ux-design", "platform-ios-apple", "security"]

    def test_deduplicates_specialists_invoked_multiple_times(self):
        events = [
            {"event": "specialist_invoked", "specialist": "security", "timestamp": "t1"},
            {"event": "specialist_invoked", "specialist": "security", "timestamp": "t2"},
            {"event": "specialist_invoked", "specialist": "ui-ux-design", "timestamp": "t3"},
        ]
        assert specialists_invoked(events) == ["security", "ui-ux-design"]

    def test_returns_empty_list_when_no_specialists_invoked(self):
        assert specialists_invoked([]) == []


# ── exchange_count ────────────────────────────────────────────────────

class TestExchangeCount:
    def test_counts_question_asked_events(self):
        events = parse_test_log(SAMPLE_DIR, "test-log.jsonl")
        assert exchange_count(events) == 3

    def test_returns_0_for_empty_events(self):
        assert exchange_count([]) == 0


# ── all_questions_answered ────────────────────────────────────────────

class TestAllQuestionsAnswered:
    def test_returns_true_when_questions_and_answers_match(self):
        events = parse_test_log(SAMPLE_DIR, "test-log.jsonl")
        assert all_questions_answered(events) is True

    def test_returns_false_when_answer_is_missing(self):
        events = [
            {"event": "question_asked", "specialist": "security", "timestamp": "t1"},
            {"event": "question_asked", "specialist": "ui-ux-design", "timestamp": "t2"},
            {"event": "answer_received", "transcript_file": "f1.md", "timestamp": "t3"},
        ]
        assert all_questions_answered(events) is False


# ── all_answers_analyzed ──────────────────────────────────────────────

class TestAllAnswersAnalyzed:
    def test_returns_true_when_answers_and_analyses_match(self):
        events = parse_test_log(SAMPLE_DIR, "test-log.jsonl")
        assert all_answers_analyzed(events) is True

    def test_returns_false_when_analysis_is_missing(self):
        events = [
            {"event": "answer_received", "transcript_file": "f1.md", "timestamp": "t1"},
            {"event": "answer_received", "transcript_file": "f2.md", "timestamp": "t2"},
            {"event": "analysis_written", "analysis_file": "a1.md", "timestamp": "t3"},
        ]
        assert all_answers_analyzed(events) is False
