/**
 * Interview skill runner — invokes the interview skill via `claude -p` (CLI).
 *
 * Uses the CLI instead of the Agent SDK so test runs go through
 * the Claude Max subscription, not API billing.
 */

import { execFile } from "child_process";
import { resolve } from "path";

export interface RunResult {
  output: string;
  exitCode: number;
  raw: string;
}

export interface InterviewRunOptions {
  /** Working directory — the fake project the interview runs "in" */
  cwd: string;
  /** Path to the test config file */
  configPath: string;
  /** Path to the persona file */
  personaPath: string;
  /** Maximum number of question-answer exchanges */
  maxExchanges: number;
  /** Timeout in ms (default: 10 minutes) */
  timeout?: number;
}

const DEFAULT_TIMEOUT = 600_000; // 10 minutes

/**
 * Resolve a path relative to the interview team repo root.
 */
function repoPath(relativePath: string): string {
  // tests/harness/lib/runner.ts → ../../.. gets to repo root
  return resolve(import.meta.dirname, "../../..", relativePath);
}

/**
 * Run the interview skill in test mode.
 *
 * Invokes `/interview --test-mode` with the simulated user agent,
 * a persona file, and a bounded exchange count. Output (transcripts,
 * analyses, test log) goes to the test output repo configured in
 * the test config.
 *
 * Runs through Claude Max subscription — no API billing.
 */
export async function runInterview(
  opts: InterviewRunOptions
): Promise<RunResult> {
  const timeout = opts.timeout ?? DEFAULT_TIMEOUT;
  const personaAbsolute = resolve(opts.personaPath);
  const configAbsolute = resolve(opts.configPath);

  const prompt = [
    "/interview --test-mode",
    `--config ${configAbsolute}`,
    `--persona ${personaAbsolute}`,
    `--max-exchanges ${opts.maxExchanges}`,
  ].join(" ");

  const args = [
    "-p", prompt,
    "--output-format", "json",
    "--dangerously-skip-permissions",
  ];

  return new Promise((resolve) => {
    execFile(
      "claude",
      args,
      {
        cwd: opts.cwd,
        timeout,
        maxBuffer: 1024 * 1024 * 10, // 10MB — interviews produce a lot of output
      },
      (error, stdout, stderr) => {
        if (error && !stdout) {
          resolve({
            output: stderr || error.message,
            exitCode: error.code ?? 1,
            raw: stdout || "",
          });
          return;
        }

        try {
          const parsed = JSON.parse(stdout);
          resolve({
            output: parsed.result ?? "",
            exitCode: 0,
            raw: stdout,
          });
        } catch {
          resolve({
            output: stdout || stderr || "",
            exitCode: error?.code ?? 0,
            raw: stdout,
          });
        }
      }
    );
  });
}
