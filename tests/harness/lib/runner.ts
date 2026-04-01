/**
 * Interview skill runner — invokes the interview skill via `claude -p` (CLI).
 *
 * Reads SKILL.md directly and sends it as the prompt with arguments
 * substituted, since the fake test project doesn't have the skill installed.
 *
 * Uses the CLI instead of the Agent SDK so test runs go through
 * the Claude Max subscription, not API billing.
 */

import { execFile } from "child_process";
import { readFileSync, appendFileSync, mkdirSync, existsSync } from "fs";
import { resolve, join, dirname } from "path";

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
function repoRoot(): string {
  // tests/harness/lib/runner.ts → ../../.. gets to repo root
  return resolve(import.meta.dirname, "../../..");
}

/**
 * Write a timestamped log line to the test harness log.
 */
function log(logFile: string, msg: string): void {
  const ts = new Date().toISOString();
  const line = `[${ts}] ${msg}\n`;
  appendFileSync(logFile, line);
}

/**
 * Run the interview skill in test mode.
 *
 * Reads SKILL.md and sends it as the prompt with $ARGUMENTS and
 * $CLAUDE_SKILL_DIR substituted. This avoids needing the skill
 * installed in the fake project.
 */
export async function runInterview(
  opts: InterviewRunOptions
): Promise<RunResult> {
  const timeout = opts.timeout ?? DEFAULT_TIMEOUT;
  const personaAbsolute = resolve(opts.personaPath);
  const configAbsolute = resolve(opts.configPath);
  const root = repoRoot();

  // Set up harness log
  const logDir = join(root, "tests/harness/.logs");
  if (!existsSync(logDir)) mkdirSync(logDir, { recursive: true });
  const logFile = join(logDir, `run-${Date.now()}.log`);

  log(logFile, "=== Interview Test Run ===");
  log(logFile, `cwd: ${opts.cwd}`);
  log(logFile, `config: ${configAbsolute}`);
  log(logFile, `persona: ${personaAbsolute}`);
  log(logFile, `maxExchanges: ${opts.maxExchanges}`);
  log(logFile, `repoRoot: ${root}`);

  // Read SKILL.md and strip YAML frontmatter (starts with --- which claude CLI
  // interprets as a CLI flag)
  const skillPath = join(root, "skills/interview/SKILL.md");
  log(logFile, `Reading skill from: ${skillPath}`);
  let skillContent = readFileSync(skillPath, "utf-8");

  // Strip frontmatter — everything between first --- and second ---
  const fmMatch = skillContent.match(/^---\n[\s\S]*?\n---\n/);
  if (fmMatch) {
    log(logFile, `Stripping frontmatter (${fmMatch[0].length} chars)`);
    skillContent = skillContent.slice(fmMatch[0].length);
  }

  // Build the arguments string
  const argsString = [
    "--test-mode",
    `--config ${configAbsolute}`,
    `--persona ${personaAbsolute}`,
    `--max-exchanges ${opts.maxExchanges}`,
  ].join(" ");

  log(logFile, `Arguments: ${argsString}`);

  // Substitute variables in the skill content
  const skillDir = join(root, "skills/interview");
  let prompt = skillContent
    .replace(/\$ARGUMENTS/g, argsString)
    .replace(/\$\{ARGUMENTS\}/g, argsString)
    .replace(/\$CLAUDE_SKILL_DIR/g, skillDir)
    .replace(/\$\{CLAUDE_SKILL_DIR\}/g, skillDir);

  // Append explicit execution instruction
  prompt += `\n\n---\n\n## EXECUTE NOW\n\nYou are running in test mode. Execute the skill above immediately with these arguments: ${argsString}\n\nThe interview team repo is at: ${root}\nThe skill directory is at: ${skillDir}\n\nIMPORTANT: You MUST:\n1. Read the config file at ${configAbsolute}\n2. Create the project directory structure in the interview_repo from config\n3. Run the interview loop using the simulated user agent\n4. Write transcript files, analysis files, and checklist\n5. Write test-log.jsonl with structured events\n6. Stop after ${opts.maxExchanges} exchanges\n\nStart by reading the config file NOW.\n`;

  log(logFile, `Prompt length: ${prompt.length} chars`);

  const args = [
    "-p", prompt,
    "--output-format", "json",
    "--dangerously-skip-permissions",
    "--max-turns", "50",
  ];

  log(logFile, `Launching claude with args: ${args.filter(a => a !== prompt).join(" ")}`);
  log(logFile, "Waiting for claude to complete...");

  return new Promise((resolvePromise) => {
    const proc = execFile(
      "claude",
      args,
      {
        cwd: opts.cwd,
        timeout,
        maxBuffer: 1024 * 1024 * 10, // 10MB
        env: {
          ...process.env,
          // Ensure Claude can find the skill directory
          CLAUDE_SKILL_DIR: skillDir,
        },
      },
      (error, stdout, stderr) => {
        log(logFile, `claude exited. error: ${error?.message ?? "none"}, code: ${error?.code ?? "0"}`);
        log(logFile, `stdout length: ${stdout?.length ?? 0}`);
        log(logFile, `stderr length: ${stderr?.length ?? 0}`);

        if (stderr) {
          log(logFile, `STDERR:\n${stderr.slice(0, 2000)}`);
        }
        if (stdout) {
          log(logFile, `STDOUT (first 2000 chars):\n${stdout.slice(0, 2000)}`);
        }

        if (error && !stdout) {
          log(logFile, `FAILED: ${error.message}`);
          resolvePromise({
            output: stderr || error.message,
            exitCode: typeof error.code === "number" ? error.code : 1,
            raw: stdout || "",
          });
          return;
        }

        try {
          const parsed = JSON.parse(stdout);
          log(logFile, `Parsed JSON output. result length: ${parsed.result?.length ?? 0}`);
          log(logFile, `Full result:\n${parsed.result?.slice(0, 5000) ?? "(no result)"}`);
          resolvePromise({
            output: parsed.result ?? "",
            exitCode: 0,
            raw: stdout,
          });
        } catch {
          log(logFile, `Could not parse JSON. Raw output used.`);
          resolvePromise({
            output: stdout || stderr || "",
            exitCode: typeof error?.code === "number" ? error.code : 0,
            raw: stdout,
          });
        }
      }
    );
  });
}
