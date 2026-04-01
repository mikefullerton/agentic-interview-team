/**
 * Smoke test — basic interview flow with Sarah persona.
 *
 * Verifies:
 * - Skill runs without errors
 * - Project directory created in test output repo
 * - Transcript files written
 * - At least one specialist invoked
 * - Test log exists and has events
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
  fileExists,
  listFiles,
  parseTestLog,
  specialistsInvoked,
  exchangeCount,
} from "../lib/assertions.js";

const PROJECT_NAME = "sarah-lumina";

describe("smoke test — sarah iOS photo app", () => {
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

  it("completes a 5-exchange interview without errors", async () => {
    const result = await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 5,
    });

    expect(result.exitCode).toBe(0);
  });

  it("creates project directory with transcript and analysis subdirs", async () => {
    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 5,
    });

    expect(fileExists(outputDir, "transcript")).toBe(true);
    expect(fileExists(outputDir, "analysis")).toBe(true);
    expect(fileExists(outputDir, "checklist.md")).toBe(true);
  });

  it("writes transcript files for each exchange", async () => {
    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 5,
    });

    const transcripts = listFiles(outputDir, "transcript");
    expect(transcripts.length).toBeGreaterThanOrEqual(1);
    expect(transcripts.length).toBeLessThanOrEqual(5);
  });

  it("invokes at least one specialist", async () => {
    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 5,
    });

    const events = parseTestLog(outputDir, "test-log.jsonl");
    const specialists = specialistsInvoked(events);
    expect(specialists.length).toBeGreaterThanOrEqual(1);
  });

  it("logs the correct number of exchanges", async () => {
    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 5,
    });

    const events = parseTestLog(outputDir, "test-log.jsonl");
    expect(exchangeCount(events)).toBeLessThanOrEqual(5);
  });
});
