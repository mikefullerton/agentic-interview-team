/**
 * Filesystem and interview-specific assertions.
 */

import { existsSync, readFileSync, readdirSync, statSync } from "fs";
import { join } from "path";

// ── Filesystem assertions ───────────────────────────────────────────

export function fileExists(dir: string, relativePath: string): boolean {
  return existsSync(join(dir, relativePath));
}

export function fileContains(
  dir: string,
  relativePath: string,
  substring: string
): boolean {
  const fullPath = join(dir, relativePath);
  if (!existsSync(fullPath)) return false;
  return readFileSync(fullPath, "utf-8").includes(substring);
}

export function fileMatches(
  dir: string,
  relativePath: string,
  pattern: RegExp
): boolean {
  const fullPath = join(dir, relativePath);
  if (!existsSync(fullPath)) return false;
  return pattern.test(readFileSync(fullPath, "utf-8"));
}

export function readFile(dir: string, relativePath: string): string {
  return readFileSync(join(dir, relativePath), "utf-8");
}

export function listFiles(dir: string, relativePath: string): string[] {
  const fullPath = join(dir, relativePath);
  if (!existsSync(fullPath)) return [];
  return readdirSync(fullPath)
    .filter((f) => statSync(join(fullPath, f)).isFile())
    .sort();
}

export function listDirs(dir: string, relativePath: string): string[] {
  const fullPath = join(dir, relativePath);
  if (!existsSync(fullPath)) return [];
  return readdirSync(fullPath)
    .filter((f) => statSync(join(fullPath, f)).isDirectory())
    .sort();
}

// ── Interview-specific assertions ───────────────────────────────────

/** Timestamp filename pattern: YYYY-MM-DD-HH-MM-SS-slug.md */
const TIMESTAMP_FILENAME = /^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-.+\.md$/;

/**
 * Verify all files in a directory match the timestamp naming convention.
 */
export function allFilesMatchTimestampPattern(
  dir: string,
  relativePath: string
): boolean {
  const files = listFiles(dir, relativePath);
  return files.length > 0 && files.every((f) => TIMESTAMP_FILENAME.test(f));
}

/**
 * Verify a file has valid YAML frontmatter with required interview fields.
 */
export function hasValidFrontmatter(
  dir: string,
  relativePath: string,
  requiredFields: string[]
): boolean {
  const content = readFile(dir, relativePath);
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return false;

  const frontmatter = match[1];
  return requiredFields.every((field) =>
    new RegExp(`^${field}:`, "m").test(frontmatter)
  );
}

/**
 * Parse the test log (JSONL) and return events.
 */
export interface TestLogEvent {
  event: string;
  specialist?: string;
  mode?: string;
  question?: string;
  transcript_file?: string;
  analysis_file?: string;
  transcript_id?: string;
  topic?: string;
  action?: string;
  exchanges?: number;
  specialists_invoked?: string[];
  files_written?: number;
  timestamp: string;
}

export function parseTestLog(
  dir: string,
  relativePath: string
): TestLogEvent[] {
  const content = readFile(dir, relativePath);
  return content
    .trim()
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line));
}

/**
 * Extract the list of specialists invoked from the test log.
 */
export function specialistsInvoked(events: TestLogEvent[]): string[] {
  return [
    ...new Set(
      events
        .filter((e) => e.event === "specialist_invoked")
        .map((e) => e.specialist!)
    ),
  ];
}

/**
 * Count exchanges (question_asked events) in the test log.
 */
export function exchangeCount(events: TestLogEvent[]): number {
  return events.filter((e) => e.event === "question_asked").length;
}

/**
 * Verify every question_asked has a matching answer_received.
 */
export function allQuestionsAnswered(events: TestLogEvent[]): boolean {
  const questions = events.filter((e) => e.event === "question_asked").length;
  const answers = events.filter((e) => e.event === "answer_received").length;
  return questions === answers;
}

/**
 * Verify every answer_received has a matching analysis_written.
 */
export function allAnswersAnalyzed(events: TestLogEvent[]): boolean {
  const answers = events.filter((e) => e.event === "answer_received").length;
  const analyses = events.filter((e) => e.event === "analysis_written").length;
  return answers === analyses;
}

/**
 * Required frontmatter fields for transcript files.
 */
export const TRANSCRIPT_FIELDS = [
  "id",
  "title",
  "type",
  "created",
  "modified",
  "author",
  "summary",
  "project",
  "session",
  "specialist",
];

/**
 * Required frontmatter fields for analysis files.
 */
export const ANALYSIS_FIELDS = [
  "id",
  "title",
  "type",
  "created",
  "modified",
  "author",
  "summary",
  "related",
  "project",
  "session",
  "specialist",
];
