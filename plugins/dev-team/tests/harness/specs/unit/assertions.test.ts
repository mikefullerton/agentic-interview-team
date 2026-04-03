/**
 * Unit tests for assertion utilities.
 *
 * Tests the harness functions that parse and validate interview output.
 * No Claude invocation needed — runs in milliseconds.
 */

import { describe, it, expect } from "vitest";
import { join } from "path";
import {
  fileExists,
  fileContains,
  fileMatches,
  readFile,
  listFiles,
  allFilesMatchTimestampPattern,
  hasValidFrontmatter,
  parseTestLog,
  specialistsInvoked,
  exchangeCount,
  allQuestionsAnswered,
  allAnswersAnalyzed,
  TRANSCRIPT_FIELDS,
  ANALYSIS_FIELDS,
} from "../../lib/assertions.js";

const SAMPLE_DIR = join(import.meta.dirname, "../../fixtures/sample-data");

// ── fileExists ──────────────────────────────────────────────────────

describe("fileExists", () => {
  it("returns true for existing files", () => {
    expect(fileExists(SAMPLE_DIR, "valid-transcript.md")).toBe(true);
  });

  it("returns false for missing files", () => {
    expect(fileExists(SAMPLE_DIR, "nonexistent.md")).toBe(false);
  });
});

// ── fileContains ────────────────────────────────────────────────────

describe("fileContains", () => {
  it("finds a string in a file", () => {
    expect(fileContains(SAMPLE_DIR, "valid-transcript.md", "Lumina")).toBe(true);
  });

  it("returns false when string not found", () => {
    expect(fileContains(SAMPLE_DIR, "valid-transcript.md", "XYZNOTHERE")).toBe(false);
  });

  it("returns false for missing files", () => {
    expect(fileContains(SAMPLE_DIR, "nonexistent.md", "anything")).toBe(false);
  });
});

// ── fileMatches ─────────────────────────────────────────────────────

describe("fileMatches", () => {
  it("matches a regex pattern", () => {
    expect(fileMatches(SAMPLE_DIR, "valid-transcript.md", /type:\s*transcript/)).toBe(true);
  });

  it("returns false when pattern doesn't match", () => {
    expect(fileMatches(SAMPLE_DIR, "valid-transcript.md", /type:\s*analysis/)).toBe(false);
  });

  it("returns false for missing files", () => {
    expect(fileMatches(SAMPLE_DIR, "nonexistent.md", /anything/)).toBe(false);
  });
});

// ── listFiles ───────────────────────────────────────────────────────

describe("listFiles", () => {
  it("lists files in a directory", () => {
    const files = listFiles(SAMPLE_DIR, ".");
    expect(files).toContain("valid-transcript.md");
    expect(files).toContain("valid-analysis.md");
    expect(files).toContain("test-log.jsonl");
  });

  it("returns sorted filenames", () => {
    const files = listFiles(SAMPLE_DIR, ".");
    const sorted = [...files].sort();
    expect(files).toEqual(sorted);
  });

  it("returns empty array for missing directory", () => {
    expect(listFiles(SAMPLE_DIR, "nonexistent-dir")).toEqual([]);
  });
});

// ── allFilesMatchTimestampPattern ───────────────────────────────────

describe("allFilesMatchTimestampPattern", () => {
  it("returns false when files don't match timestamp pattern", () => {
    // sample-data has files like valid-transcript.md, not timestamp-named
    expect(allFilesMatchTimestampPattern(SAMPLE_DIR, ".")).toBe(false);
  });
});

// ── hasValidFrontmatter ─────────────────────────────────────────────

describe("hasValidFrontmatter", () => {
  it("validates a transcript with all required fields", () => {
    expect(
      hasValidFrontmatter(SAMPLE_DIR, "valid-transcript.md", TRANSCRIPT_FIELDS)
    ).toBe(true);
  });

  it("validates an analysis with all required fields", () => {
    expect(
      hasValidFrontmatter(SAMPLE_DIR, "valid-analysis.md", ANALYSIS_FIELDS)
    ).toBe(true);
  });

  it("fails when required fields are missing", () => {
    expect(
      hasValidFrontmatter(SAMPLE_DIR, "missing-fields-transcript.md", TRANSCRIPT_FIELDS)
    ).toBe(false);
  });

  it("passes with a subset of fields", () => {
    expect(
      hasValidFrontmatter(SAMPLE_DIR, "missing-fields-transcript.md", ["id", "title", "type"])
    ).toBe(true);
  });
});

// ── parseTestLog ────────────────────────────────────────────────────

describe("parseTestLog", () => {
  it("parses all events from JSONL", () => {
    const events = parseTestLog(SAMPLE_DIR, "test-log.jsonl");
    expect(events.length).toBe(14);
  });

  it("parses event types correctly", () => {
    const events = parseTestLog(SAMPLE_DIR, "test-log.jsonl");
    const types = events.map((e) => e.event);
    expect(types).toContain("specialist_invoked");
    expect(types).toContain("question_asked");
    expect(types).toContain("answer_received");
    expect(types).toContain("analysis_written");
    expect(types).toContain("checklist_updated");
    expect(types).toContain("test_complete");
  });

  it("preserves specialist field", () => {
    const events = parseTestLog(SAMPLE_DIR, "test-log.jsonl");
    const firstInvoke = events.find((e) => e.event === "specialist_invoked");
    expect(firstInvoke?.specialist).toBe("ui-ux-design");
  });

  it("preserves timestamp field", () => {
    const events = parseTestLog(SAMPLE_DIR, "test-log.jsonl");
    expect(events[0].timestamp).toBe("2026-04-01T19:30:00");
  });
});

// ── specialistsInvoked ──────────────────────────────────────────────

describe("specialistsInvoked", () => {
  it("returns unique specialists", () => {
    const events = parseTestLog(SAMPLE_DIR, "test-log.jsonl");
    const specialists = specialistsInvoked(events);
    expect(specialists).toEqual(["ui-ux-design", "platform-ios-apple", "security"]);
  });

  it("deduplicates specialists invoked multiple times", () => {
    const events = [
      { event: "specialist_invoked", specialist: "security", timestamp: "t1" },
      { event: "specialist_invoked", specialist: "security", timestamp: "t2" },
      { event: "specialist_invoked", specialist: "ui-ux-design", timestamp: "t3" },
    ];
    expect(specialistsInvoked(events)).toEqual(["security", "ui-ux-design"]);
  });

  it("returns empty array when no specialists invoked", () => {
    expect(specialistsInvoked([])).toEqual([]);
  });
});

// ── exchangeCount ───────────────────────────────────────────────────

describe("exchangeCount", () => {
  it("counts question_asked events", () => {
    const events = parseTestLog(SAMPLE_DIR, "test-log.jsonl");
    expect(exchangeCount(events)).toBe(3);
  });

  it("returns 0 for empty events", () => {
    expect(exchangeCount([])).toBe(0);
  });
});

// ── allQuestionsAnswered ────────────────────────────────────────────

describe("allQuestionsAnswered", () => {
  it("returns true when questions and answers match", () => {
    const events = parseTestLog(SAMPLE_DIR, "test-log.jsonl");
    expect(allQuestionsAnswered(events)).toBe(true);
  });

  it("returns false when answer is missing", () => {
    const events = [
      { event: "question_asked", specialist: "security", timestamp: "t1" },
      { event: "question_asked", specialist: "ui-ux-design", timestamp: "t2" },
      { event: "answer_received", transcript_file: "f1.md", timestamp: "t3" },
    ];
    expect(allQuestionsAnswered(events)).toBe(false);
  });
});

// ── allAnswersAnalyzed ──────────────────────────────────────────────

describe("allAnswersAnalyzed", () => {
  it("returns true when answers and analyses match", () => {
    const events = parseTestLog(SAMPLE_DIR, "test-log.jsonl");
    expect(allAnswersAnalyzed(events)).toBe(true);
  });

  it("returns false when analysis is missing", () => {
    const events = [
      { event: "answer_received", transcript_file: "f1.md", timestamp: "t1" },
      { event: "answer_received", transcript_file: "f2.md", timestamp: "t2" },
      { event: "analysis_written", analysis_file: "a1.md", timestamp: "t3" },
    ];
    expect(allAnswersAnalyzed(events)).toBe(false);
  });
});
