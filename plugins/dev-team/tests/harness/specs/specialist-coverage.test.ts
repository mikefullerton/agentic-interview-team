/**
 * Specialist coverage test — verifies the right specialists
 * are invoked for a given persona.
 *
 * Uses Marcus (comprehensive persona) to verify all specialists
 * can be triggered, and Sarah (focused persona) to verify
 * irrelevant specialists are NOT triggered.
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
import { parseTestLog, specialistsInvoked } from "../lib/assertions.js";

describe("specialist coverage — sarah (focused)", () => {
  const PROJECT_NAME = "sarah-lumina-coverage";
  let fakeProjectDir: string;
  let outputDir: string;

  beforeEach(async () => {
    cleanTestOutput(PROJECT_NAME);
    fakeProjectDir = createFakeProject(PROJECT_NAME);
    outputDir = testProjectDir(PROJECT_NAME);

    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: 15,
    });
  });

  afterEach(() => {
    cleanup(fakeProjectDir);
  });

  it("invokes iOS platform specialist for an iOS app", () => {
    const events = parseTestLog(outputDir, "test-log.jsonl");
    const specialists = specialistsInvoked(events);
    expect(specialists).toContain("platform-ios-apple");
  });

  it("invokes UI/UX specialist for a visual app", () => {
    const events = parseTestLog(outputDir, "test-log.jsonl");
    const specialists = specialistsInvoked(events);
    expect(specialists).toContain("ui-ux-design");
  });

  it("does NOT invoke Windows specialist for an iOS-only app", () => {
    const events = parseTestLog(outputDir, "test-log.jsonl");
    const specialists = specialistsInvoked(events);
    expect(specialists).not.toContain("platform-windows");
  });

  it("does NOT invoke Android specialist for an iOS-only app", () => {
    const events = parseTestLog(outputDir, "test-log.jsonl");
    const specialists = specialistsInvoked(events);
    expect(specialists).not.toContain("platform-android");
  });
});

describe("specialist coverage — marcus (comprehensive)", () => {
  const PROJECT_NAME = "marcus-forge-coverage";
  let fakeProjectDir: string;
  let outputDir: string;

  beforeEach(async () => {
    cleanTestOutput(PROJECT_NAME);
    fakeProjectDir = createFakeProject(PROJECT_NAME);
    outputDir = testProjectDir(PROJECT_NAME);

    await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("marcus-enterprise-saas.md"),
      maxExchanges: 20,
      timeout: 900_000, // 15 minutes for comprehensive test
    });
  });

  afterEach(() => {
    cleanup(fakeProjectDir);
  });

  it("invokes specialists from multiple domains", () => {
    const events = parseTestLog(outputDir, "test-log.jsonl");
    const specialists = specialistsInvoked(events);
    // Marcus should trigger at least 5 different specialists in 20 exchanges
    expect(specialists.length).toBeGreaterThanOrEqual(5);
  });

  it("invokes at least one platform specialist", () => {
    const events = parseTestLog(outputDir, "test-log.jsonl");
    const specialists = specialistsInvoked(events);
    const platformSpecialists = specialists.filter((s) =>
      s.startsWith("platform-")
    );
    expect(platformSpecialists.length).toBeGreaterThanOrEqual(1);
  });

  it("invokes security specialist for an enterprise app", () => {
    const events = parseTestLog(outputDir, "test-log.jsonl");
    const specialists = specialistsInvoked(events);
    expect(specialists).toContain("security");
  });
});
