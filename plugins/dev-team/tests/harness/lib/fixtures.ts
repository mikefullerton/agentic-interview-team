/**
 * Fixture management for interview tests.
 *
 * Creates temp directories for fake projects (the cwd for tests)
 * and cleans up test output in the test repo between runs.
 */

import {
  cpSync,
  mkdtempSync,
  rmSync,
  existsSync,
  mkdirSync,
  writeFileSync,
} from "fs";
import { join, resolve } from "path";
import { tmpdir } from "os";

const FIXTURES_DIR = join(import.meta.dirname, "../../fixtures");

/**
 * Paths to the repos used by the test harness.
 */
export const REPO_PATHS = {
  interviewTeam: resolve(import.meta.dirname, "../../.."),
  testOutput: resolve(import.meta.dirname, "../../../../dev-team-tests"),
  cookbook: resolve(import.meta.dirname, "../../../../agentic-cookbook"),
};

/**
 * Path to the test config file in the test output repo.
 */
export const TEST_CONFIG_PATH = join(
  REPO_PATHS.testOutput,
  "config/test-config.json"
);

/**
 * Path to a persona file (relative to interview team repo).
 */
export function personaPath(name: string): string {
  return join(REPO_PATHS.interviewTeam, "tests/personas", name);
}

/**
 * Create a temporary fake project directory to serve as cwd.
 * Initializes a bare .git so the skill can infer a project name.
 */
export function createFakeProject(projectName: string): string {
  const dest = mkdtempSync(
    join(tmpdir(), `interview-test-${projectName}-`)
  );

  // Create a minimal git repo so the skill can infer the project
  const gitDir = join(dest, ".git");
  mkdirSync(gitDir);
  writeFileSync(
    join(gitDir, "config"),
    `[core]\n\trepositoryformatversion = 0\n`
  );
  writeFileSync(join(gitDir, "HEAD"), "ref: refs/heads/main\n");

  // Write a marker file so the skill knows the project name
  writeFileSync(
    join(dest, "README.md"),
    `# ${projectName}\n\nTest project for interview system testing.\n`
  );

  return dest;
}

/**
 * Clean up a temp directory.
 */
export function cleanup(dir: string | undefined): void {
  if (dir && dir.startsWith(tmpdir())) {
    rmSync(dir, { recursive: true, force: true });
  }
}

/**
 * Clean test output for a specific project in the test repo.
 */
export function cleanTestOutput(projectName: string): void {
  const projectDir = join(REPO_PATHS.testOutput, "projects", projectName);
  if (existsSync(projectDir)) {
    rmSync(projectDir, { recursive: true, force: true });
  }
}

/**
 * Get the path to a project's output in the test repo.
 */
export function testProjectDir(projectName: string): string {
  return join(REPO_PATHS.testOutput, "projects", projectName);
}

/**
 * Get the target repo path for analyze tests.
 * Reads from TEST_TARGET_REPO env var, or falls back to a default.
 */
export function getTargetRepo(): string {
  const envPath = process.env.TEST_TARGET_REPO;
  if (envPath) return resolve(envPath);
  throw new Error(
    "TEST_TARGET_REPO env var must be set to a git repo path for analyze tests"
  );
}

/**
 * Get the target cookbook project path for generate/build tests.
 * Reads from TEST_TARGET_PROJECT env var, or falls back to a default.
 */
export function getTargetProject(): string {
  const envPath = process.env.TEST_TARGET_PROJECT;
  if (envPath) return resolve(envPath);
  throw new Error(
    "TEST_TARGET_PROJECT env var must be set to a cookbook project path for generate/build tests"
  );
}

/**
 * Create a test config file with the given overrides.
 * Returns the path to the created config file.
 */
export function createTestConfig(overrides: Record<string, string> = {}): string {
  const configDir = join(REPO_PATHS.testOutput, "config");
  if (!existsSync(configDir)) mkdirSync(configDir, { recursive: true });

  const configPath = join(configDir, `test-config-${Date.now()}.json`);
  const config = {
    interview_repo: REPO_PATHS.testOutput,
    cookbook_repo: REPO_PATHS.cookbook,
    interview_team_repo: REPO_PATHS.interviewTeam,
    user_name: "test-user",
    ...overrides,
  };

  writeFileSync(configPath, JSON.stringify(config, null, 2));
  return configPath;
}
