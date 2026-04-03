/**
 * Unit tests for fixture utilities.
 *
 * Tests fake project creation and cleanup.
 */

import { describe, it, expect, afterEach } from "vitest";
import { existsSync, readFileSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import {
  createFakeProject,
  cleanup,
  REPO_PATHS,
  TEST_CONFIG_PATH,
  personaPath,
} from "../../lib/fixtures.js";

describe("createFakeProject", () => {
  let tempDir: string | undefined;

  afterEach(() => {
    cleanup(tempDir);
  });

  it("creates a temp directory", () => {
    tempDir = createFakeProject("test-project");
    expect(existsSync(tempDir)).toBe(true);
  });

  it("creates directory in system temp", () => {
    tempDir = createFakeProject("test-project");
    expect(tempDir.startsWith(tmpdir())).toBe(true);
  });

  it("includes project name in path", () => {
    tempDir = createFakeProject("my-app");
    expect(tempDir).toContain("interview-test-my-app-");
  });

  it("creates a .git directory", () => {
    tempDir = createFakeProject("test-project");
    expect(existsSync(join(tempDir, ".git"))).toBe(true);
  });

  it("creates a .git/HEAD file", () => {
    tempDir = createFakeProject("test-project");
    const head = readFileSync(join(tempDir, ".git", "HEAD"), "utf-8");
    expect(head).toContain("refs/heads/main");
  });

  it("creates a README.md with project name", () => {
    tempDir = createFakeProject("lumina");
    const readme = readFileSync(join(tempDir, "README.md"), "utf-8");
    expect(readme).toContain("lumina");
  });
});

describe("cleanup", () => {
  it("removes a temp directory", () => {
    const tempDir = createFakeProject("cleanup-test");
    expect(existsSync(tempDir)).toBe(true);
    cleanup(tempDir);
    expect(existsSync(tempDir)).toBe(false);
  });

  it("does nothing for undefined", () => {
    expect(() => cleanup(undefined)).not.toThrow();
  });

  it("does nothing for non-temp paths", () => {
    // Safety check — should not delete paths outside tmpdir
    expect(() => cleanup("/usr/local/bin")).not.toThrow();
    expect(existsSync("/usr/local/bin")).toBe(true);
  });
});

describe("path helpers", () => {
  it("REPO_PATHS.interviewTeam points to the interview team repo", () => {
    expect(existsSync(join(REPO_PATHS.interviewTeam, "agents"))).toBe(true);
  });

  it("TEST_CONFIG_PATH points to the test config", () => {
    expect(existsSync(TEST_CONFIG_PATH)).toBe(true);
  });

  it("personaPath resolves persona files", () => {
    const path = personaPath("sarah-ios-photo-app.md");
    expect(existsSync(path)).toBe(true);
  });

  it("personaPath returns absolute path", () => {
    const path = personaPath("sarah-ios-photo-app.md");
    expect(path.startsWith("/")).toBe(true);
  });
});
