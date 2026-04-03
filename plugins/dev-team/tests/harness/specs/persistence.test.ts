/**
 * Persistence test — verifies transcript and analysis files
 * are written correctly with valid structure and frontmatter.
 *
 * Verifies:
 * - All transcript files have valid timestamp naming
 * - All transcript files have required frontmatter fields
 * - All analysis files have required frontmatter fields
 * - Analysis files reference their paired transcript
 * - Every answer has a paired analysis
 * - Files sort chronologically
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { runInterview } from "../lib/runner.js";
import {
  createFakeProject,
  cleanup,
  cleanTestOutput,
  testProjectDir,
  personaPath,
  TEST_CONFIG_PATH,
} from "../lib/fixtures.js";
import {
  listFiles,
  hasValidFrontmatter,
  allFilesMatchTimestampPattern,
  parseTestLog,
  allQuestionsAnswered,
  allAnswersAnalyzed,
  TRANSCRIPT_FIELDS,
  ANALYSIS_FIELDS,
} from "../lib/assertions.js";

const PROJECT_NAME = "sarah-lumina";

describe("persistence — file structure and frontmatter", () => {
  let fakeProjectDir: string;
  let outputDir: string;

  beforeEach(async () => {
    cleanTestOutput(PROJECT_NAME);
    fakeProjectDir = createFakeProject(PROJECT_NAME);
    outputDir = testProjectDir(PROJECT_NAME);

    // Run a 10-exchange interview to generate enough files
    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 10,
    });
  });

  afterEach(() => {
    cleanup(fakeProjectDir);
  });

  it("transcript files match timestamp naming pattern", () => {
    expect(
      allFilesMatchTimestampPattern(outputDir, "transcript")
    ).toBe(true);
  });

  it("analysis files match timestamp naming pattern", () => {
    expect(
      allFilesMatchTimestampPattern(outputDir, "analysis")
    ).toBe(true);
  });

  it("all transcript files have required frontmatter", () => {
    const files = listFiles(outputDir, "transcript");
    for (const file of files) {
      expect(
        hasValidFrontmatter(outputDir, `transcript/${file}`, TRANSCRIPT_FIELDS)
      ).toBe(true);
    }
  });

  it("all analysis files have required frontmatter", () => {
    const files = listFiles(outputDir, "analysis");
    for (const file of files) {
      expect(
        hasValidFrontmatter(outputDir, `analysis/${file}`, ANALYSIS_FIELDS)
      ).toBe(true);
    }
  });

  it("transcript files sort chronologically", () => {
    const files = listFiles(outputDir, "transcript");
    const sorted = [...files].sort();
    expect(files).toEqual(sorted);
  });

  it("every question has a matching answer in the log", () => {
    const events = parseTestLog(outputDir, "test-log.jsonl");
    expect(allQuestionsAnswered(events)).toBe(true);
  });

  it("every answer has a matching analysis in the log", () => {
    const events = parseTestLog(outputDir, "test-log.jsonl");
    expect(allAnswersAnalyzed(events)).toBe(true);
  });

  it("transcript and analysis counts match", () => {
    const transcripts = listFiles(outputDir, "transcript");
    const analyses = listFiles(outputDir, "analysis");
    expect(analyses.length).toBe(transcripts.length);
  });
});
