# Build History

Session-by-session log of what was built, decisions made, and what's next.

## Session 1 — 2026-04-01

### Brainstorming Phase (in agentic-cookbook repo)

Started from the question: "I want to create an agent whose purpose is to interview me about the design of a product in order to fully scope out what I am trying to build."

**Key decisions made through discussion (one question at a time):**

1. **Skill, not agent** — the interview is multi-turn and open-ended, needs unlimited interaction. Skills run in main context, agents are bounded subprocesses.

2. **Committee model** — one meeting leader (the skill) orchestrates specialist interviewers and analysts. User only talks to the leader. Specialists pass questions through verbatim with attribution (e.g., "Biff (iOS specialist) asks...").

3. **Two dimensions of specialists** — domain specialists (security, UI, accessibility, etc.) crossed with platform specialists (iOS, Windows, Android, web, database). Power is in the intersection.

4. **Paired specialists** — each specialist interviewer has a paired analyst. Interviewer asks questions, analyst deeply analyzes each answer and surfaces new questions. Analysis must be deep enough to inform the next question, not just a post-mortem.

5. **Transcript analyzer** — a separate agent that reads all transcripts and recommends which specialists to bring in next. The meeting leader tells it when to act (each team member has one job).

6. **Three-repo architecture** — cookbook (upstream knowledge), interview team (the system), user interview repo (personal data, transcripts, growth). Later added a fourth repo for test output.

7. **Output format** — two files per exchange (transcript + analysis), timestamp-to-second naming (YYYY-MM-DD-HH-MM-SS-slug.md), cookbook-derived frontmatter subset (kept: id, title, type, created, modified, author, summary, tags, platforms, related; added: project, session, specialist; dropped: version, status, language, copyright, license, domain, depends-on, references).

8. **Multi-user from day one** — profiles/<username>/, per-user specialist maturation, shared checklist per project.

9. **Structured → explore → structured loop** — cover known questions first, then explore, exploration surfaces new known things, repeat. User controls when to stop.

10. **Living checklist** — tracks what's covered, what's open, what's been discovered but not scoped. Updated after every topic change.

11. **Open-ended sessions** — no forced ending. User asks for summary when ready. Can always come back. Separate planning skill (TBD) reads the transcript.

12. **Dedicated interview repo** — all interview data in one place, not scattered across projects. Cross-pollination between projects. User profile builds over interviews.

13. **Config at ~/.agentic-interviewer/config.json** — interview repo path, cookbook path, interview team repo path, user name, authorized repos. Skill asks on first run.

14. **Repo access opt-in** — interviewer can read authorized project repos. Notices code changes between sessions.

15. **Specialists derived from cookbook** — initial question sets researched from cookbook principles, guidelines, and compliance checks. Agents also get direct cookbook read access for deeper context.

16. **Specialist learning** — per-user maturation first (in user's interview repo), migration to global (in team repo) later with criteria TBD.

17. **Personas for specialist identification** — named personas (Biff, etc.) deferred to later. System designed to support them from the start.

18. **Contextual profile usage** — "Hey Mike, welcome back. I know you have a lot of iOS experience so I'll factor that in." Never dump the full profile — only surface what's relevant.

19. **Meeting leader passes questions verbatim** — doesn't rephrase specialist questions. Attribution preserved.

### Implementation Phase

**Commits (in dev-team repo):**

1. `7693069` — Design spec, research docs, directory structure
2. `35f797d` — 18 specialist definitions with initial question sets (12 domain + 6 platform, ~230 structured questions + ~75 exploratory prompts)
3. `a520261` — Interview skill (SKILL.md) and 3 subagent definitions (transcript-analyzer, specialist-interviewer, specialist-analyst)
4. `278d8f0` — CLAUDE.md, .gitignore, config fix for interview_team_repo
5. `851519a` — README, checklist template, new-project-setup template
6. `ce14dd9` — Always commit and push rule
7. `dd7c86b` — Move CLAUDE.md to .claude/CLAUDE.md
8. `526bfb0` — Wire cookbook access into all agents (all agents get cookbook_repo, interview_team_repo, interview_repo paths)
9. `e3d553b` — Aggressive persistence principle (write immediately, never buffer)
10. `e011ebc` — --config and --test-mode flags for the skill
11. `31e46d9` — Simulated user agent + 3 test personas (Sarah, Marcus, Priya)
12. `e91872e` — Test harness (runner, assertions, fixtures, 4 test specs)

**Commits (in my-agentic-interviews repo):**
1. `d52690e` — Initial setup (profile, directories)
2. `427c63a` — CLAUDE.md, .gitkeep files
3. `2b25c8c` — Always commit and push rule
4. `af14f5d` — Move CLAUDE.md to .claude/CLAUDE.md

**Commits (in dev-team-tests repo):**
1. `830ef3f` — Initial setup (test config, directories)

### What Was Built

- **Skill**: `skills/interview/SKILL.md` — meeting leader with full interview flow, config management, file writing, checklist, test mode, aggressive persistence
- **4 agents**: transcript-analyzer, specialist-interviewer, specialist-analyst, simulated-user (test-only)
- **18 specialist question sets**: 12 domain + 6 platform, each with structured questions and exploratory prompts, mapped to cookbook content
- **3 research docs**: cookbook-specialist-mapping, agent-patterns, conversational-patterns
- **Test harness**: Vitest-based, 4 test specs (smoke, persistence, specialist-coverage, resume), simulated user agent with 3 personas
- **User interview repo**: profile seeded, directories ready
- **Test output repo**: config pointing to test paths
- **Config**: ~/.agentic-interviewer/config.json with all repo paths

### Remaining / Next Steps

1. **First test run** — install vitest deps, run smoke test, iterate on what breaks
2. **Global install story** — how to make /interview available from any project (deferred)
3. **Interruption recovery test** — kill mid-interview, verify persistence
4. **Named specialist personas** — give each specialist a personality (Biff, etc.)
5. **Planning skill** — separate skill that reads transcripts and forms a build plan
6. **Token optimization** — deep analysis on every exchange is expensive, optimize later
7. **Social media cross-pollination** — potential integration with social media bot team
8. **Cloud database** — persistent layers move from local files to cloud

### Discussion Topics Deferred

- Social media platform integration and cross-pollination with social media management bot team
- Cloud database for persistent layers (someday)
- How specialist learning migrates from per-user to global (criteria TBD)
- The separate planning skill that reads transcripts and forms a plan
