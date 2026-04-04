/**
 * Specialty-team file validation — verifies every file in specialty-teams/
 * has valid frontmatter and required sections.
 */

import { describe, it, expect } from "vitest";
import { readdirSync, readFileSync, statSync, existsSync } from "fs";
import { execFileSync } from "child_process";
import { join, basename } from "path";

const REPO_ROOT = join(__dirname, "../../../..");
const TEAMS_DIR = join(REPO_ROOT, "specialty-teams");
const SPECIALISTS_DIR = join(REPO_ROOT, "specialists");

// Collect all specialty-team files
function getAllTeamFiles(): { category: string; name: string; path: string }[] {
  const files: { category: string; name: string; path: string }[] = [];
  if (!existsSync(TEAMS_DIR)) return files;

  for (const category of readdirSync(TEAMS_DIR)) {
    const categoryPath = join(TEAMS_DIR, category);
    if (!statSync(categoryPath).isDirectory()) continue;

    for (const file of readdirSync(categoryPath)) {
      if (!file.endsWith(".md")) continue;
      files.push({
        category,
        name: basename(file, ".md"),
        path: join(categoryPath, file),
      });
    }
  }
  return files;
}

// Parse frontmatter from a markdown file
function parseFrontmatter(
  content: string
): { fields: Record<string, string>; body: string } | null {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) return null;

  const fields: Record<string, string> = {};
  for (const line of match[1].split("\n")) {
    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue;
    const key = line.slice(0, colonIdx).trim();
    const value = line.slice(colonIdx + 1).trim();
    fields[key] = value;
  }
  return { fields, body: match[2] };
}

const teamFiles = getAllTeamFiles();

describe("specialty-teams directory structure", () => {
  it("has at least one category directory", () => {
    const categories = readdirSync(TEAMS_DIR).filter((f) =>
      statSync(join(TEAMS_DIR, f)).isDirectory()
    );
    expect(categories.length).toBeGreaterThan(0);
  });

  it("every category corresponds to a specialist", () => {
    const categories = readdirSync(TEAMS_DIR).filter((f) =>
      statSync(join(TEAMS_DIR, f)).isDirectory()
    );
    for (const category of categories) {
      const specialistFile = join(SPECIALISTS_DIR, `${category}.md`);
      expect(
        existsSync(specialistFile),
        `Category ${category} has no matching specialist file`
      ).toBe(true);
    }
  });

  it("has the expected number of team files", () => {
    expect(teamFiles.length).toBeGreaterThanOrEqual(200);
  });
});

describe.each(teamFiles)(
  "specialty-teams/%s",
  ({ category, name, path }) => {
    const content = readFileSync(path, "utf-8");
    const parsed = parseFrontmatter(content);

    it("has valid frontmatter", () => {
      expect(parsed, "Missing or malformed frontmatter").not.toBeNull();
    });

    it("has required frontmatter fields", () => {
      expect(parsed!.fields).toHaveProperty("name");
      expect(parsed!.fields).toHaveProperty("description");
      expect(parsed!.fields).toHaveProperty("artifact");
      expect(parsed!.fields).toHaveProperty("version");
    });

    it("name field matches filename", () => {
      expect(parsed!.fields.name).toBe(name);
    });

    it("name is kebab-case", () => {
      expect(name).toMatch(/^[a-z][a-z0-9]*(-[a-z0-9]+)*$/);
    });

    it("artifact is a non-empty path", () => {
      expect(parsed!.fields.artifact.length).toBeGreaterThan(0);
      expect(parsed!.fields.artifact).toMatch(/\.md$/);
    });

    it("version is semver", () => {
      expect(parsed!.fields.version).toMatch(/^\d+\.\d+\.\d+$/);
    });

    it("description is non-empty", () => {
      expect(parsed!.fields.description.length).toBeGreaterThan(0);
    });

    it("has Worker Focus section", () => {
      expect(parsed!.body).toContain("## Worker Focus");
    });

    it("has Verify section", () => {
      expect(parsed!.body).toContain("## Verify");
    });

    it("Worker Focus section is non-empty", () => {
      const match = parsed!.body.match(
        /## Worker Focus\n([\s\S]*?)(?=\n## |\n*$)/
      );
      expect(match, "Worker Focus section not found").not.toBeNull();
      expect(match![1].trim().length).toBeGreaterThan(0);
    });

    it("Verify section is non-empty", () => {
      const match = parsed!.body.match(
        /## Verify\n([\s\S]*?)(?=\n## |\n*$)/
      );
      expect(match, "Verify section not found").not.toBeNull();
      expect(match![1].trim().length).toBeGreaterThan(0);
    });
  }
);

describe("run-specialty-teams.sh", () => {
  const RUN_SCRIPT = join(REPO_ROOT, "scripts", "run-specialty-teams.sh");

  it("outputs valid JSON for a specialist with manifest", () => {
    const result = execFileSync(
      RUN_SCRIPT,
      [join(SPECIALISTS_DIR, "accessibility.md")],
      { encoding: "utf-8" }
    );
    const teams = JSON.parse(result);
    expect(Array.isArray(teams)).toBe(true);
    expect(teams.length).toBe(2);
  });

  it("each team has required fields", () => {
    const result = execFileSync(
      RUN_SCRIPT,
      [join(SPECIALISTS_DIR, "accessibility.md")],
      { encoding: "utf-8" }
    );
    const teams = JSON.parse(result);
    for (const team of teams) {
      expect(team).toHaveProperty("name");
      expect(team).toHaveProperty("artifact");
      expect(team).toHaveProperty("worker_focus");
      expect(team).toHaveProperty("verify");
    }
  });

  it("outputs correct team count for security specialist", () => {
    const result = execFileSync(
      RUN_SCRIPT,
      [join(SPECIALISTS_DIR, "security.md")],
      { encoding: "utf-8" }
    );
    const teams = JSON.parse(result);
    expect(teams.length).toBe(15);
  });

  it("team fields match file content", () => {
    const result = execFileSync(
      RUN_SCRIPT,
      [join(SPECIALISTS_DIR, "security.md")],
      { encoding: "utf-8" }
    );
    const teams = JSON.parse(result);
    const authTeam = teams.find(
      (t: { name: string }) => t.name === "authentication"
    );
    expect(authTeam).toBeDefined();
    expect(authTeam.artifact).toBe("guidelines/security/authentication.md");
    expect(authTeam.worker_focus.length).toBeGreaterThan(0);
    expect(authTeam.verify.length).toBeGreaterThan(0);
  });
});
