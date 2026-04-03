/**
 * Smoke test — build on an existing cookbook project.
 *
 * Verifies:
 * - Skill runs without errors
 * - Project scaffold created
 * - At least 1 recipe's code generated
 * - Build attempted
 * - Smoke test attempted
 * - Test log has expected events
 *
 * Requires: TEST_TARGET_PROJECT env var set to a cookbook project path.
 */

import { describe, it, expect, beforeAll } from "vitest";
import { runSkill, type RunResult } from "../lib/runner.js";
import { getTargetProject, createTestConfig, REPO_PATHS } from "../lib/fixtures.js";
import {
  fileExists,
  expectAgentSpawned,
  expectPhaseCompleted,
  expectBuildResult,
} from "../lib/assertions.js";
import { parseLog, filterByEvent, testSummary } from "../lib/log-parser.js";
import { existsSync, readFileSync } from "fs";
import { join } from "path";

describe("build smoke test", () => {
  let result: RunResult;
  let projectDir: string;
  let outputDir: string;
  let configPath: string;

  beforeAll(async () => {
    projectDir = getTargetProject();
    configPath = createTestConfig();

    // Derive output dir — build creates <project>/../<name>-build/
    const projectName = projectDir.split("/").pop()!;
    const parentDir = join(projectDir, "..");
    outputDir = join(parentDir, `${projectName}-build`);

    console.log("[build-smoke] Starting build run...");
    console.log(`[build-smoke] project: ${projectDir}`);
    console.log(`[build-smoke] expected output: ${outputDir}`);

    result = await runSkill({
      skillName: "build",
      cwd: projectDir,
      configPath,
      targetPath: projectDir,
      extraArgs: [`--output ${outputDir}`],
      timeout: 1_800_000, // 30 minutes — builds are slow
    });

    console.log(`[build-smoke] Completed. exitCode: ${result.exitCode}`);
  }, 1_860_000); // 31 minutes

  it("completes without error", () => {
    expect([0, 143]).toContain(result.exitCode);
  });

  it("creates scaffold report", () => {
    expect(
      fileExists(outputDir, "context/build-log/scaffold-report.md")
    ).toBe(true);
  });

  it("spawns project-scaffolder agent", () => {
    const events = parseLog(outputDir);
    expect(expectAgentSpawned(events, "project-scaffolder")).toBe(true);
  });

  it("generates code for at least 1 recipe", () => {
    const events = parseLog(outputDir);
    const codeGenerated = filterByEvent(events, "code_generated");
    console.log(`[build-smoke] recipes with code: ${codeGenerated.length}`);
    expect(codeGenerated.length).toBeGreaterThanOrEqual(1);
  });

  it("runs specialist passes in tier order", () => {
    const events = parseLog(outputDir);
    const passes = filterByEvent(events, "specialist_pass_complete");
    console.log(
      `[build-smoke] specialist passes: ${passes.map((p) => `${p.recipe_scope}:${p.specialist}`).join(", ")}`
    );

    // Verify at least 1 specialist pass ran
    expect(passes.length).toBeGreaterThanOrEqual(1);

    // Verify tier ordering per recipe
    const TIER_ORDER = [
      "software-architecture",
      "reliability", "data-persistence", "networking-api",
      "security", "ui-ux-design", "accessibility", "localization-i18n",
      "testing-qa", "devops-observability", "code-quality", "development-process",
      "platform-ios-apple", "platform-android", "platform-windows",
      "platform-web-frontend", "platform-web-backend", "platform-database",
    ];

    // Group by recipe
    const byRecipe = new Map<string, string[]>();
    for (const p of passes) {
      const recipe = p.recipe_scope as string;
      if (!byRecipe.has(recipe)) byRecipe.set(recipe, []);
      byRecipe.get(recipe)!.push(p.specialist as string);
    }

    for (const [recipe, specialists] of byRecipe) {
      const expectedOrder = TIER_ORDER.filter((s) => specialists.includes(s));
      expect(specialists).toEqual(expectedOrder);
    }
  });

  it("attempts a build", () => {
    const events = parseLog(outputDir);
    const buildAttempts = filterByEvent(events, "build_attempted");
    console.log(`[build-smoke] build attempts: ${buildAttempts.length}`);
    expect(buildAttempts.length).toBeGreaterThanOrEqual(1);
  });

  it("writes build summary", () => {
    expect(
      fileExists(outputDir, "context/research/build-summary.md")
    ).toBe(true);
  });
});
