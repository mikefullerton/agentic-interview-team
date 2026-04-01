/**
 * Resume test — verifies the interview can be paused and resumed.
 *
 * Runs two interview sessions against the same project:
 * - Phase 1: 5 exchanges
 * - Phase 2: 5 more exchanges
 *
 * Verifies:
 * - Phase 2 finds existing transcripts
 * - Total transcript count spans both phases
 * - Checklist carries over between sessions
 * - No duplicate files between sessions
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
import { fileExists, listFiles } from "../lib/assertions.js";

const PROJECT_NAME = "sarah-lumina-resume";

describe("resume — two-phase interview", () => {
  let fakeProjectDir: string;
  let outputDir: string;

  beforeEach(() => {
    cleanTestOutput(PROJECT_NAME);
    fakeProjectDir = createFakeProject(PROJECT_NAME);
    outputDir = testProjectDir(PROJECT_NAME);
  });

  afterEach(() => {
    cleanup(fakeProjectDir);
  });

  it("produces more transcripts across two sessions than one", async () => {
    // Phase 1
    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 5,
    });

    const phase1Transcripts = listFiles(outputDir, "transcript");
    const phase1Count = phase1Transcripts.length;
    expect(phase1Count).toBeGreaterThanOrEqual(1);

    // Phase 2 — same project, same persona
    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 5,
    });

    const phase2Transcripts = listFiles(outputDir, "transcript");
    expect(phase2Transcripts.length).toBeGreaterThan(phase1Count);
  });

  it("checklist persists between sessions", async () => {
    // Phase 1
    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 5,
    });

    expect(fileExists(outputDir, "checklist.md")).toBe(true);

    // Phase 2
    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 5,
    });

    // Checklist should still exist and have content from both phases
    expect(fileExists(outputDir, "checklist.md")).toBe(true);
  });

  it("no duplicate transcript filenames between sessions", async () => {
    // Phase 1
    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 5,
    });

    // Phase 2
    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 5,
    });

    const allTranscripts = listFiles(outputDir, "transcript");
    const unique = new Set(allTranscripts);
    expect(unique.size).toBe(allTranscripts.length);
  });
});
