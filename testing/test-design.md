# Test Design — My Agentic Dev Team

## Approach

Automated end-to-end testing using a **simulated user agent** that plays the role of a person being interviewed. The simulated user has a persona file defining who they are, what they're building, and their knowledge/blind spots. The interview system doesn't know it's talking to a simulation.

## What We Test (Flow & Mechanics)

We verify the **system works correctly**, not that it asks good questions. Questions evolve as specialists mature — testing content would create brittle tests.

### 1. Specialist Invocation
- Given a persona building an iOS app, the iOS platform specialist and UI/UX specialist must be invoked
- Given a persona with no accessibility plan, the accessibility specialist must be invoked
- Specialists NOT relevant to the persona should NOT be invoked (e.g., Windows specialist for an iOS-only app)
- Log which specialists were invoked and compare against the persona's expected specialist list

### 2. Transcript Persistence
- Every exchange produces a transcript file in `projects/<project>/transcript/`
- Each transcript file has valid frontmatter: id (UUID), title, type (transcript), created, modified, author, summary, project, session, specialist
- The question and answer in the file match what was asked and answered
- Files are named with valid timestamps: `YYYY-MM-DD-HH-MM-SS-<slug>.md`
- Files sort chronologically

### 3. Analysis Persistence
- Every transcript has a paired analysis file in `projects/<project>/analysis/`
- Analysis frontmatter includes `related` pointing to the transcript's id
- Analysis has all required sections: Key Insights, Implications, Gaps Identified, New Questions, Contradictions, Design Decisions
- Analysis is written AFTER transcript (timestamp is equal or later)

### 4. Checklist Updates
- `projects/<project>/checklist.md` exists after first exchange
- Topics move from Open to Covered as they're discussed
- New topics appear under Discovered when surfaced during exploration
- Checklist is updated after every topic change, not batched

### 5. File Naming & Structure
- All timestamps are valid and to-the-second
- All slugs are kebab-case
- No duplicate filenames
- Transcript and analysis directories contain only .md files

### 6. Config Flow
- With no config: first-run setup is triggered
- With existing config: setup is skipped, greeting is shown

### 7. Resume Behavior
- Run interview, produce some transcripts, stop
- Run again against same project
- Verify: greeting references previous topics, checklist shows prior coverage, new transcripts continue the sequence

### 8. Aggressive Persistence (Interruption Recovery)
- Run interview for N exchanges
- Verify after each exchange: transcript file exists on disk before analyst runs
- Verify after each analysis: analysis file exists on disk before next question
- Simulate interruption (kill process after M exchanges)
- Verify: all M exchanges have transcript files, M or M-1 have analysis files
- Resume: verify system picks up correctly from last persisted state

## What We Do NOT Test

- Quality of questions asked by specialists
- Quality of analysis produced by analysts
- Specific question wording (will change as specialists evolve)
- Which exploratory threads are followed (non-deterministic)
- Token usage or performance (optimize later)

## Test Personas

Each persona is designed to invoke specific specialists:

| Persona | Product | Platforms | Key Specialists Triggered |
|---------|---------|-----------|--------------------------|
| Sarah Chen | iOS photo editor | iOS only | iOS, UI/UX, Accessibility, Data, Architecture, Testing |
| Marcus Webb | Enterprise SaaS PM tool | Windows + Web + Android | All 18 (comprehensive) |
| Priya Sharma | Global marketplace | iOS + Web + Backend | I18n, Security, iOS, Web, Database, Networking, Accessibility |

Marcus is the comprehensive persona that should trigger every specialist.

## Test Infrastructure

### Simulated User Agent
`agents/simulated-user.md` — receives a persona file and a question, returns an in-character answer. Stays within the persona's knowledge, is occasionally vague, never breaks character.

### Test Harness
Adapts the cookbook's test pattern (`claude -p` + Vitest):

1. **Fixture setup**: Create a temp directory with config pointing to a test interview repo
2. **Run**: Invoke the interview skill with the simulated user answering questions
3. **Verify**: Check file outputs (transcripts, analyses, checklist)
4. **Cleanup**: Remove temp directories

### Flow Logging
The interview skill logs specialist invocations and exchange sequences to a structured log file during test mode. The test harness reads this log to verify flow correctness.

**Log format** (`projects/<project>/test-log.jsonl`):
```jsonl
{"event": "specialist_invoked", "specialist": "security", "mode": "structured", "timestamp": "..."}
{"event": "question_asked", "specialist": "security", "question_id": "...", "timestamp": "..."}
{"event": "answer_received", "transcript_file": "...", "timestamp": "..."}
{"event": "analysis_written", "analysis_file": "...", "transcript_id": "...", "timestamp": "..."}
{"event": "checklist_updated", "topic": "...", "action": "covered", "timestamp": "..."}
```

### Test Mode Flag
The skill accepts `--test-mode` which:
- Enables flow logging to `test-log.jsonl`
- Uses the simulated user agent instead of real user interaction
- Accepts `--persona <path>` to specify which persona to use
- Accepts `--max-exchanges <n>` to limit the interview length for bounded tests

### Invocation
```bash
claude -p "/interview --test-mode --persona tests/personas/sarah-ios-photo-app.md --max-exchanges 10" \
  --dangerously-skip-permissions \
  --output-format json
```

## Test Cases

### Smoke Test
- Persona: Sarah (simplest)
- Exchanges: 5
- Verifies: config read, project created, transcript files written, at least one specialist invoked

### Specialist Coverage Test
- Persona: Marcus (comprehensive)
- Exchanges: 20
- Verifies: all expected specialists invoked, no unexpected specialists, correct specialist for each topic

### Persistence Test
- Persona: Sarah
- Exchanges: 10
- Verifies: all transcript+analysis pairs exist, valid frontmatter, correct file naming, chronological ordering

### Resume Test
- Persona: Sarah
- Phase 1: 5 exchanges, stop
- Phase 2: 5 more exchanges
- Verifies: phase 2 greeting references phase 1 topics, checklist carries over, new files continue sequence

### Interruption Test
- Persona: Sarah
- Run 8 exchanges, kill after exchange 5
- Verify: 5 transcript files on disk, 4-5 analysis files on disk
- Resume: picks up from exchange 5 or 6

### First-Run Config Test
- No config file
- Verifies: skill prompts for config, creates config file
- (May need special handling since simulated user needs to answer config questions too)
