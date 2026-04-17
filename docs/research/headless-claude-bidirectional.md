# Headless Claude Code: Streaming JSON and Bidirectional Communication

Research notes on running Claude Code as a subprocess with two-way communication — the caller sending questions into the session, and Claude asking questions back out.

## What headless mode is

Claude Code running non-interactively. No TUI, no prompt loop. You invoke it with a prompt, it runs, emits output, exits. Built for scripts, CI/CD, git hooks, cron jobs, and SDK integrations.

```bash
claude -p "explain this error" < logs.txt
claude --print "review the diff"
claude -p "..." --output-format stream-json --verbose
```

### Useful flags

- `-p` / `--print` — headless mode
- `--output-format text|json|stream-json` — structured output
- `--input-format text|stream-json` — structured input for multi-turn
- `--max-turns N` — cap agentic loop
- `--allowedTools` / `--disallowedTools` — lock down tool access
- `--permission-mode` — `default`, `bypassPermissions`, etc.
- `--resume <session-id>` / `--continue` — chain invocations into one session
- `--mcp-config` — inject MCP servers for the run
- `--verbose` — required with `stream-json` to get the full event stream

### Output format comparison

| Format | Shape | Use case |
|---|---|---|
| `text` | final answer only | "run and print" |
| `json` | single JSON blob at end | "run and collect" |
| `stream-json` | NDJSON event stream | "observe and intervene" |

## The stream-json event stream

One JSON object per line (NDJSON) as the session progresses. Same stream the TUI consumes internally.

### Event types

- `system` / `init` — session metadata: `session_id`, model, cwd, tools, MCP servers, `plugin_errors` (2.1.111+)
- `assistant` — message from Claude; `content` is an array of blocks (`text`, `thinking`, `tool_use`)
- `user` — `tool_result` blocks after tools run, or user turns the caller sent
- `result` — terminal event: final text, stop reason, token usage, cost, duration, `num_turns`
- `error` — transport or model errors

Each event carries `session_id` and a `message` payload mirroring the Anthropic Messages API shape.

### Gotchas

- Parse line-by-line. Do not `json.load(stdout)`.
- Lines can be long — full message blocks. Don't assume a line fits one read.
- Tool results are events too. Pre-allowing tools means lots of traffic.
- Always pair with `--max-turns` and a tight `--allowedTools` for safe automation.

## Scenarios and examples

### 1. Live UI — stream tokens and tool calls

```python
import json, subprocess, sys

proc = subprocess.Popen(
    ["claude", "-p", "summarize README.md", "--output-format", "stream-json", "--verbose"],
    stdout=subprocess.PIPE, text=True,
)
for line in proc.stdout:
    evt = json.loads(line)
    if evt["type"] == "assistant":
        for block in evt["message"]["content"]:
            if block["type"] == "text":
                sys.stdout.write(block["text"]); sys.stdout.flush()
            elif block["type"] == "tool_use":
                print(f"\n[tool] {block['name']}({block['input']})")
    elif evt["type"] == "result":
        print(f"\n[done] {evt['usage']['output_tokens']} out tokens, ${evt['total_cost_usd']:.4f}")
```

### 2. Orchestration — observe and veto tool calls

```python
import json, subprocess

DENY = {"Bash"}

proc = subprocess.Popen(
    ["claude", "-p", "check git status",
     "--output-format", "stream-json",
     "--input-format", "stream-json",
     "--permission-mode", "default"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
)
for line in proc.stdout:
    evt = json.loads(line)
    if evt["type"] == "assistant":
        for b in evt["message"]["content"]:
            if b["type"] == "tool_use" and b["name"] in DENY:
                print(f"[policy] blocked {b['name']}: {b['input']}")
                # respond with a denied tool_result to unstick the turn
```

For hard policy enforcement, use `PreToolUse` hooks (they run inside Claude's loop). This pattern is for light intervention from outside.

### 3. Observability — feed events to a tracing sink

```python
import json, os, subprocess, time

env = {**os.environ,
       "TRACEPARENT": "00-" + os.urandom(16).hex() + "-" + os.urandom(8).hex() + "-01"}
proc = subprocess.Popen(
    ["claude", "-p", "analyze logs/*.log", "--output-format", "stream-json", "--verbose"],
    stdout=subprocess.PIPE, text=True, env=env,
)
with open("trace.ndjson", "w") as f:
    for line in proc.stdout:
        evt = json.loads(line)
        f.write(json.dumps({"ts": time.time(),
                            "traceparent": env["TRACEPARENT"],
                            **evt}) + "\n")
```

Ship `trace.ndjson` to Honeycomb / Loki / Datadog. Every tool call, every token count, correlated by traceparent. `TRACEPARENT` / `TRACESTATE` env vars are picked up as of 2.1.110.

### 4. Resumable pipelines — capture session_id, continue later

```python
import json, subprocess

def run_and_capture_session(prompt: str, resume: str | None = None) -> tuple[str, str]:
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose"]
    if resume:
        cmd += ["--resume", resume]
    sid, final = None, ""
    for line in subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True).stdout:
        evt = json.loads(line)
        if evt["type"] == "system" and evt.get("subtype") == "init":
            sid = evt["session_id"]
        elif evt["type"] == "result":
            final = evt["result"]
    return sid, final

sid, _ = run_and_capture_session("Start reviewing PR #42")
# later, in a different shell, job, or day:
_, answer = run_and_capture_session("Summarize the issues you found", resume=sid)
```

### 5. Debugging plugins/MCP — surface loader failures

```python
import json, subprocess, sys

proc = subprocess.Popen(
    ["claude", "-p", "/doctor", "--output-format", "stream-json", "--verbose"],
    stdout=subprocess.PIPE, text=True,
)
for line in proc.stdout:
    evt = json.loads(line)
    if evt["type"] == "system" and evt.get("subtype") == "init":
        errs = evt.get("plugin_errors") or []
        if errs:
            for e in errs:
                print(f"  - {e.get('plugin')}: {e.get('message')}")
            sys.exit(1)
        print("MCP servers:", [s["name"] for s in evt.get("mcp_servers", [])])
        break
```

## Bidirectional communication

Both directions are first-class. The pattern is a bidirectional NDJSON pipe: stdin for caller → Claude, stdout for Claude → caller. The subprocess acts as a coroutine.

### Caller → Claude: multi-turn input

Keep stdin open, write one user turn per line:

```python
def send_user(proc, text: str) -> None:
    msg = {"type": "user",
           "message": {"role": "user",
                       "content": [{"type": "text", "text": text}]}}
    proc.stdin.write(json.dumps(msg) + "\n"); proc.stdin.flush()

send_user(proc, "What files are in src/?")
# ... read events until assistant turn completes ...
send_user(proc, "Now tell me which one is the entry point.")
```

Each call adds a turn to the same conversation.

### Claude → caller: three mechanisms

**(a) `AskUserQuestion` built-in tool.** Claude emits a `tool_use` block named `AskUserQuestion`. Caller surfaces the question somehow (CLI, Slack, web form) and replies with a matching `tool_result` user turn.

**(b) Permission prompts.** Any tool Claude tries that isn't pre-allowed surfaces as a permission request event. Good for "should I run this destructive command?"

**(c) Custom MCP tool.** Most flexible. Define `ask_human`, `ask_expert`, `ask_sre_oncall`, etc. Claude calls it like any other tool. Your MCP server blocks until it has an answer. Routes questions to specific people or channels.

### Full bidirectional loop

```python
import json, subprocess, threading, queue

proc = subprocess.Popen(
    ["claude", "-p",
     "--input-format", "stream-json",
     "--output-format", "stream-json",
     "--verbose",
     "--max-turns", "30"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
)

events: queue.Queue = queue.Queue()
threading.Thread(
    target=lambda: [events.put(json.loads(l)) for l in proc.stdout],
    daemon=True,
).start()

def send(obj: dict) -> None:
    proc.stdin.write(json.dumps(obj) + "\n"); proc.stdin.flush()

def user_turn(text: str) -> None:
    send({"type": "user",
          "message": {"role": "user",
                      "content": [{"type": "text", "text": text}]}})

def tool_result(tool_use_id: str, content: str) -> None:
    send({"type": "user",
          "message": {"role": "user",
                      "content": [{"type": "tool_result",
                                   "tool_use_id": tool_use_id,
                                   "content": content}]}})

user_turn("Help me name a new service. Ask clarifying questions first.")

while True:
    evt = events.get()
    t = evt.get("type")

    if t == "assistant":
        for b in evt["message"]["content"]:
            if b["type"] == "text":
                print("claude:", b["text"])
            elif b["type"] == "tool_use" and b["name"] == "AskUserQuestion":
                q = b["input"].get("question", "")
                answer = input(f"\n? {q}\n> ")
                tool_result(b["id"], answer)

    elif t == "result":
        break
```

Claude asks questions via `AskUserQuestion`, the caller answers at the prompt, Claude continues. The caller can inject new `user_turn()` messages at any time.

## System architecture for production use

Four layers:

1. **Transport** — stream-json pipe. One subprocess per conversation. Track `session_id` from the `init` event for later `--resume`.

2. **Session manager** — maps incoming questions (HTTP, Slack, webhook, queue) to the right subprocess's stdin. A `dict[session_id, Process]` keyed by whatever "conversation" means in the domain.

3. **Human-in-the-loop router** — an MCP server exposing `ask_product_owner`, `ask_sre_oncall`, `request_approval`, etc. Each tool:
   - Publishes the question to Slack / email / ticket / UI
   - Blocks on a `Future` or equivalent
   - Returns when a human submits an answer

   Cleaner than `AskUserQuestion` because Claude can target *who* to ask, and the return value is structured.

4. **Policy and safety** — `--permission-mode default`, a tight `--allowedTools` list, `--max-turns`, plus `PreToolUse` hooks for hard policy. Permission requests become another form of Claude → caller question.

### Two lifecycle patterns

**Short-lived, synchronous** — CLI or chat bot. Subprocess stays alive. `AskUserQuestion` handles in-the-moment clarification.

**Long-lived, asynchronous** — workflow or ticketing. Custom MCP `ask_human` tool stores the question in a queue, the session exits or pauses, a separate worker resumes the session via `--resume <sid>` when a human answers. Survives restarts. Suits workflows where humans answer on their own timeline.

### Persistence

`--resume <session-id>` rehydrates a conversation. Subprocesses don't have to stay resident. Park a session, wait hours for a human answer, resume. This is the foundation for async workflows ("Claude drafts a migration, asks DBA for sign-off, resumes next day when DBA replies").

### SDK

For anything past prototype, use the Claude Agent SDK (`@anthropic-ai/claude-agent-sdk`, `claude-agent-sdk` for Python) instead of rolling subprocess plumbing. It wraps the pipe layer and exposes higher-level primitives.

## Version notes

- **2.1.108** — prompt caching TTL controls, recap feature, skill-invokable slash commands
- **2.1.110** — `TRACEPARENT` / `TRACESTATE` pickup, push notification tool for Remote Control, `--resume` / `--continue` resurrect scheduled tasks
- **2.1.111** — `plugin_errors` on init events for stream-json headless, PowerShell tool on Windows (rolling out), `/ultrareview` parallel multi-agent cloud review

## Relevance to this project

For dev-team, the HITL router pattern (layer 3) is the likely fit. A specialist that needs a product decision, a sign-off, or a judgment call can invoke a domain-specific MCP tool rather than guessing. Combined with resumable sessions, this enables long-running multi-agent workflows where human checkpoints are first-class rather than improvised.
