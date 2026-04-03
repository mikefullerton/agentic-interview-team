/**
 * Unified test-log.jsonl parser.
 *
 * Parses the unified log schema (skill + phase + event + timestamp)
 * and the legacy interview format (event + timestamp, no skill/phase).
 */

import { readFileSync, existsSync } from "fs";
import { join } from "path";

/** Base fields present on every unified log event. */
export interface BaseLogEvent {
  skill: string;
  phase: string;
  event: string;
  timestamp: string;
  [key: string]: unknown;
}

/** Legacy interview log event (no skill/phase fields). */
export interface LegacyLogEvent {
  event: string;
  timestamp: string;
  [key: string]: unknown;
}

export type LogEvent = BaseLogEvent;

/**
 * Parse a test-log.jsonl file. Handles both unified and legacy formats.
 * Legacy events (missing skill/phase) are normalized with
 * skill="interview" and phase="unknown".
 */
export function parseLog(dir: string, relativePath = "test-log.jsonl"): LogEvent[] {
  const fullPath = join(dir, relativePath);
  if (!existsSync(fullPath)) return [];

  const content = readFileSync(fullPath, "utf-8");
  return content
    .trim()
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => {
      const parsed = JSON.parse(line);
      // Normalize legacy format
      if (!parsed.skill) {
        parsed.skill = "interview";
      }
      if (!parsed.phase) {
        parsed.phase = "unknown";
      }
      return parsed as LogEvent;
    });
}

/** Filter events by skill name. */
export function filterBySkill(events: LogEvent[], skill: string): LogEvent[] {
  return events.filter((e) => e.skill === skill);
}

/** Filter events by phase name. */
export function filterByPhase(events: LogEvent[], phase: string): LogEvent[] {
  return events.filter((e) => e.phase === phase);
}

/** Filter events by event type. */
export function filterByEvent(events: LogEvent[], event: string): LogEvent[] {
  return events.filter((e) => e.event === event);
}

/** Get all unique agent names that were spawned. */
export function agentsSpawned(events: LogEvent[]): string[] {
  return [
    ...new Set(
      filterByEvent(events, "agent_spawned").map((e) => e.agent as string)
    ),
  ];
}

/** Get all unique specialists that had passes. */
export function specialistsPassed(events: LogEvent[]): string[] {
  return [
    ...new Set(
      filterByEvent(events, "specialist_pass_complete").map(
        (e) => e.specialist as string
      )
    ),
  ];
}

/** Get all file_written events. */
export function filesWritten(events: LogEvent[]): LogEvent[] {
  return filterByEvent(events, "file_written");
}

/** Get all phases that completed. */
export function phasesCompleted(events: LogEvent[]): string[] {
  return filterByEvent(events, "phase_completed").map((e) => e.phase);
}

/** Get the test_complete summary event, if present. */
export function testSummary(events: LogEvent[]): LogEvent | undefined {
  return filterByEvent(events, "test_complete")[0];
}
