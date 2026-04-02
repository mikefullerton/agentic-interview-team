/**
 * Smoke test — create-project-from-code on a real repo.
 *
 * Verifies:
 * - Skill runs without errors
 * - Architecture map written
 * - Scope report written
 * - At least 1 recipe generated
 * - cookbook-project.json created
 * - Test log has expected events
 *
 * Requires: TEST_TARGET_REPO env var set to a git repo path.
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { runSkill, type RunResult } from "../lib/runner.js";
import {
  getTargetRepo,
  createTestConfig,
  REPO_PATHS,
} from "../lib/fixtures.js";
import {
  fileExists,
  listFiles,
  expectFileWritten,
  expectAgentSpawned,
  expectPhaseCompleted,
} from "../lib/assertions.js";
import { parseLog, testSummary } from "../lib/log-parser.js";
import { existsSync, readdirSync, rmSync } from "fs";
import { join } from "path";

describe("create-project-from-code smoke test", () => {
  let result: RunResult;
  let outputDir: string;
  let configPath: string;
  let targetRepo: string;

  beforeAll(async () => {
    targetRepo = getTargetRepo();
    configPath = createTestConfig();

    // Derive expected output dir from repo name
    const repoName = targetRepo.split("/").pop()!;
    outputDir = join(REPO_PATHS.testOutput, "projects", `${repoName}-cookbook`);

    // Clean previous output
    if (existsSync(outputDir)) {
      rmSync(outputDir, { recursive: true, force: true });
    }

    console.log("[create-project-from-code-smoke] Starting analyze run...");
    console.log(`[create-project-from-code-smoke] target: ${targetRepo}`);
    console.log(`[create-project-from-code-smoke] output: ${outputDir}`);

    result = await runSkill({
      skillName: "create-project-from-code",
      cwd: targetRepo,
      configPath,
      targetPath: targetRepo,
      extraArgs: [`--output ${outputDir}`],
      timeout: 900_000, // 15 minutes
    });

    console.log(`[create-project-from-code-smoke] Completed. exitCode: ${result.exitCode}`);
  }, 960_000);

  it("completes without error", () => {
    expect([0, 143]).toContain(result.exitCode);
  });

  it("writes architecture-map.md", () => {
    expect(
      fileExists(outputDir, "context/research/architecture-map.md")
    ).toBe(true);
  });

  it("writes scope-report.md", () => {
    expect(
      fileExists(outputDir, "context/research/scope-report.md")
    ).toBe(true);
  });

  it("generates at least 1 recipe", () => {
    // Recipes live under app/ in the output dir
    const appDir = join(outputDir, "app");
    if (!existsSync(appDir)) {
      expect.fail("No app/ directory — no recipes generated");
    }
    // Recursively find .md files under app/
    function findMdFiles(dir: string): string[] {
      const results: string[] = [];
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const full = join(dir, entry.name);
        if (entry.isDirectory()) results.push(...findMdFiles(full));
        else if (entry.name.endsWith(".md")) results.push(full);
      }
      return results;
    }
    const recipes = findMdFiles(appDir);
    console.log(`[create-project-from-code-smoke] recipes found: ${recipes.length}`);
    expect(recipes.length).toBeGreaterThanOrEqual(1);
  });

  it("creates cookbook-project.json", () => {
    expect(fileExists(outputDir, "cookbook-project.json")).toBe(true);
  });

  it("writes test log with expected events", () => {
    const events = parseLog(outputDir);
    console.log(`[create-project-from-code-smoke] log events: ${events.length}`);

    expect(events.length).toBeGreaterThanOrEqual(1);
    expect(expectAgentSpawned(events, "codebase-scanner")).toBe(true);
    expect(expectAgentSpawned(events, "scope-matcher")).toBe(true);
    expect(expectAgentSpawned(events, "recipe-writer")).toBe(true);
    expect(expectAgentSpawned(events, "project-assembler")).toBe(true);
  });
});
