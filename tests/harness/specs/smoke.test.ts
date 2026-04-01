/**
 * Smoke test — basic interview flow with Sarah persona.
 *
 * Verifies:
 * - Skill runs without errors
 * - Project directory created in test output repo
 * - Transcript files written
 * - At least one specialist invoked
 * - Test log exists and has events
 *
 * NOTE: The skill infers the project name from the product being built
 * (e.g., "lumina"), not from the persona name. We discover the project
 * directory dynamically after the first run.
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { runInterview, type RunResult } from "../lib/runner.js";
import {
  createFakeProject,
  cleanup,
  cleanTestOutput,
  personaPath,
  TEST_CONFIG_PATH,
  REPO_PATHS,
} from "../lib/fixtures.js";
import {
  fileExists,
  listFiles,
  parseTestLog,
  specialistsInvoked,
  exchangeCount,
} from "../lib/assertions.js";
import { readdirSync, existsSync } from "fs";
import { join } from "path";

// Use 3 exchanges — each takes ~2-3 minutes with agent spawning
const MAX_EXCHANGES = 3;

describe("smoke test — sarah iOS photo app", () => {
  let fakeProjectDir: string;
  let outputDir: string;
  let result: RunResult;

  // Run the interview once for all tests (it's expensive)
  beforeAll(async () => {
    // Clean any previous test output
    const projectsDir = join(REPO_PATHS.testOutput, "projects");
    if (existsSync(projectsDir)) {
      const entries = readdirSync(projectsDir);
      for (const entry of entries) {
        if (entry !== ".gitkeep") {
          cleanTestOutput(entry);
        }
      }
    }

    fakeProjectDir = createFakeProject("sarah-lumina");

    console.log("[smoke] Starting interview run...");
    console.log(`[smoke] cwd: ${fakeProjectDir}`);
    console.log(`[smoke] config: ${TEST_CONFIG_PATH}`);
    console.log(`[smoke] persona: ${personaPath("sarah-ios-photo-app.md")}`);
    console.log(`[smoke] maxExchanges: ${MAX_EXCHANGES}`);

    result = await runInterview({
      cwd: fakeProjectDir,
      configPath: TEST_CONFIG_PATH,
      personaPath: personaPath("sarah-ios-photo-app.md"),
      maxExchanges: MAX_EXCHANGES,
      timeout: 600_000, // 10 minutes
    });

    console.log(`[smoke] Interview completed. exitCode: ${result.exitCode}`);
    console.log(`[smoke] Output length: ${result.output.length}`);

    // Discover the project directory — the skill names it from the product,
    // not the persona (e.g., "lumina" from the Lumina photo app)
    if (existsSync(projectsDir)) {
      const entries = readdirSync(projectsDir).filter(e => e !== ".gitkeep");
      console.log(`[smoke] Project directories found: ${entries.join(", ") || "(none)"}`);
      if (entries.length > 0) {
        outputDir = join(projectsDir, entries[0]);
        console.log(`[smoke] Using output dir: ${outputDir}`);
      }
    }

    if (!outputDir) {
      console.log("[smoke] WARNING: No project directory was created!");
      outputDir = join(projectsDir, "sarah-lumina"); // fallback for error messages
    }
  }, 660_000); // beforeAll timeout slightly longer than interview timeout

  afterAll(() => {
    cleanup(fakeProjectDir);
  });

  it("completes the interview without errors", () => {
    console.log(`[smoke:exit-code] exitCode=${result.exitCode}`);
    if (result.exitCode !== 0) {
      console.log(`[smoke:exit-code] output: ${result.output.slice(0, 500)}`);
    }
    expect(result.exitCode).toBe(0);
  });

  it("creates project directory with transcript and analysis subdirs", () => {
    console.log(`[smoke:dirs] outputDir=${outputDir}`);
    console.log(`[smoke:dirs] exists=${existsSync(outputDir)}`);
    if (existsSync(outputDir)) {
      const contents = readdirSync(outputDir);
      console.log(`[smoke:dirs] contents: ${contents.join(", ")}`);
    }

    expect(fileExists(outputDir, "transcript")).toBe(true);
    expect(fileExists(outputDir, "analysis")).toBe(true);
    expect(fileExists(outputDir, "checklist.md")).toBe(true);
  });

  it("writes transcript files for each exchange", () => {
    const transcripts = listFiles(outputDir, "transcript");
    console.log(`[smoke:transcripts] count=${transcripts.length}, files=${transcripts.join(", ")}`);
    expect(transcripts.length).toBeGreaterThanOrEqual(1);
    expect(transcripts.length).toBeLessThanOrEqual(MAX_EXCHANGES);
  });

  it("invokes at least one specialist", () => {
    const logPath = join(outputDir, "test-log.jsonl");
    console.log(`[smoke:specialist] logPath=${logPath}, exists=${existsSync(logPath)}`);

    const events = parseTestLog(outputDir, "test-log.jsonl");
    const specialists = specialistsInvoked(events);
    console.log(`[smoke:specialist] events=${events.length}, specialists=${specialists.join(", ")}`);
    expect(specialists.length).toBeGreaterThanOrEqual(1);
  });

  it("logs exchanges in the test log", () => {
    const events = parseTestLog(outputDir, "test-log.jsonl");
    const count = exchangeCount(events);
    console.log(`[smoke:exchanges] count=${count}, max=${MAX_EXCHANGES}`);
    expect(count).toBeGreaterThanOrEqual(1);
    expect(count).toBeLessThanOrEqual(MAX_EXCHANGES);
  });
});
