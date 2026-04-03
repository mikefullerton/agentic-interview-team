# Claude Code & Agentic Development Specialist

## Role
Claude Code plugin architecture, skill/rule/agent authoring and linting, performance optimization (shell scripts, model selection, progressive disclosure), context window management, and multi-agent orchestration.

## Persona
(coming)

## Cookbook Sources

### Guidelines
- `guidelines/skills-and-agents/authoring-skills-and-rules.md`
- `guidelines/skills-and-agents/performance.md`
- `guidelines/skills-and-agents/skill-checklist.md`
- `guidelines/skills-and-agents/rule-checklist.md`
- `guidelines/skills-and-agents/agent-checklist.md`
- `guidelines/skills-and-agents/skill-structure-reference.md`
- `guidelines/skills-and-agents/rule-structure-reference.md`
- `guidelines/skills-and-agents/agent-structure-reference.md`

### Principles
- `principles/separation-of-concerns.md`
- `principles/manage-complexity-through-boundaries.md`
- `principles/explicit-over-implicit.md`
- `principles/design-for-deletion.md`
- `principles/simplicity.md`
- `principles/yagni.md`
- `principles/support-automation.md`

### Recipes
- `recipes/developer-tools/claude/claude-rule-optimization-pipeline.md`
- `recipes/developer-tools/claude/yolo-mode.md`
- `recipes/autonomous-dev-bots/pr-review-pipeline.md`

### Research
- `appendix/research/developer-tools/claude/claude-plugin-format.md`
- `appendix/research/developer-tools/claude/hooks-patterns.md`
- `appendix/research/developer-tools/claude/mcp-servers.md`
- `appendix/research/developer-tools/claude/memory-and-context-tools.md`
- `appendix/research/developer-tools/claude/claude-integration-guide.md`
- `appendix/research/developer-tools/claude/rule-optimization.md`
- `appendix/research/developer-tools/claude/skill-testing-landscape.md`
- `appendix/research/developer-tools/claude/plugins-and-skills-catalog.md`
- `appendix/research/developer-tools/claude/self-healing-research-summary.md`
- `appendix/research/developer-tools/claude/terminal-progress-and-status-line.md`
- `appendix/research/developer-tools/claude/yolo-per-session-design.md`
- `appendix/research/developer-tools/claude/dangerously-skip-permissions-bugs.md`

## Conventions

**Cookbook project naming**: Cookbook project directories MUST use the suffix `-cookbook-project`. For a source repository named `my-app`, the cookbook project is `my-app-cookbook-project`. This distinguishes cookbook projects from other directories and makes the project type immediately recognizable.

## Specialty Teams

### authoring-skills-and-rules
- **Artifact**: `guidelines/skills-and-agents/authoring-skills-and-rules.md`
- **Worker focus**: Skill design rules — check inventory first, version from day one, session version check, use `$ARGUMENTS` and `${CLAUDE_SKILL_DIR}`, description under 200 chars, atomic permission prompt, error handling; Rule design rules — imperative tone (MUST/MUST NOT), explicit file paths, single concern, MUST NOT section required, enforcement mechanism, deterministic instructions; Agent design — scope tool access, set maxTurns, clear system prompt
- **Verify**: Skill has `version` in frontmatter and prints it on invocation; skill description under 200 chars; rule uses RFC 2119 keywords; rule lists explicit file paths for all references; agent has `maxTurns` set; `/lint-skill`, `/lint-rule`, or `/lint-agent` run after every change

### performance
- **Artifact**: `guidelines/skills-and-agents/performance.md`
- **Worker focus**: Three principles — (1) shell scripts for deterministic work (scaffolding, git, build, lint, file manipulation, metrics); (2) model selection tradeoffs (measure token efficiency and latency before downgrading — ask user when unclear); (3) progressive disclosure — rules/CLAUDE.md are per-turn cost, on-demand reads are per-session, target tier-1 under 200 lines/8KB
- **Verify**: Deterministic steps extracted to shell scripts rather than model reasoning; rule files under 200 lines; CLAUDE.md contains pointers not full procedures; no guideline content front-loaded into every skill step; model downgrade decisions measured, not assumed

### skill-checklist
- **Artifact**: `guidelines/skills-and-agents/skill-checklist.md`
- **Worker focus**: Structure checks (frontmatter present, name kebab-case ≤64 chars, description present, main file named `SKILL.md`, ≤500 lines); content quality (single responsibility, actionable steps, `${CLAUDE_SKILL_DIR}` for file refs, no conflicting instructions); best practices (verification method provided, `disable-model-invocation` for side-effect skills, no kitchen-sink anti-pattern, description under ~200 chars)
- **Verify**: S01/S03/S04/S13 checks pass (FAIL-severity); B06 (no kitchen-sink) passes; C06 (`${CLAUDE_SKILL_DIR}`) passes; skill passes `/lint-skill` with no FAILs

### rule-checklist
- **Artifact**: `guidelines/skills-and-agents/rule-checklist.md`
- **Worker focus**: Content quality (single responsibility, actionable/specific, no conflicting instructions); rule-specific (imperative tone throughout, numbered steps if procedural, no vague directives, explicit file refs, MUST NOT section present, deterministic, lowercase kebab-case filename); optimization (under 200 lines/8KB, no duplication across rules, `globs` frontmatter for scoped rules)
- **Verify**: R04 (no vague directives) passes; R05 (explicit file refs) passes; R06 (no contradictions) passes; R11 (MUST NOT section) present; O01 (under 200 lines) met; file passes `/lint-rule` with no FAILs

### agent-checklist
- **Artifact**: `guidelines/skills-and-agents/agent-checklist.md`
- **Worker focus**: Structure checks (frontmatter present with name+description, kebab-case filename); content quality (single responsibility, error handling covered, no conflicting instructions); agent-specific (tool access restricted via `tools`/`disallowedTools`, `maxTurns` set for bounded tasks, `permissionMode` appropriate — `plan` for read-only, `bypassPermissions` for automated)
- **Verify**: A01 (name+description present) passes; A02 (tool access restricted) reviewed; A05 (`permissionMode`) appropriate for task; A06 (`maxTurns`) set; agent passes `/lint-agent` with no FAILs

### skill-structure-reference
- **Artifact**: `guidelines/skills-and-agents/skill-structure-reference.md`
- **Worker focus**: Directory layout (`.claude/skills/<name>/SKILL.md` + optional references/scripts/examples/); frontmatter fields (name, description, argument-hint, disable-model-invocation, user-invocable, allowed-tools, model, effort, context, hooks, paths, shell); string substitutions (`$ARGUMENTS`, `$0`-`$N`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_SKILL_DIR}`); invocation control matrix
- **Verify**: Skill directory follows `.claude/skills/<name>/SKILL.md` layout; only recognized frontmatter fields present; `${CLAUDE_SKILL_DIR}` used for supporting file references; `argument-hint` present when `$ARGUMENTS` used

### rule-structure-reference
- **Artifact**: `guidelines/skills-and-agents/rule-structure-reference.md`
- **Worker focus**: Rules are plain `.md` files (no required frontmatter schema), lowercase kebab-case filename, per-turn cost model (rules in `.claude/rules/` injected every turn); quality criteria — imperative tone, deterministic, explicit file refs, no vague directives; optimization — under 200 lines/8KB, inline small content, reference large, `globs` frontmatter for scoped rules
- **Verify**: Rule filename is lowercase kebab-case; no uppercase stem unless identity file; per-turn cost reviewed (size ×turns = budget impact); large reference material moved to on-demand reads

### agent-structure-reference
- **Artifact**: `guidelines/skills-and-agents/agent-structure-reference.md`
- **Worker focus**: Agents are `.md` files in `.claude/agents/` with YAML frontmatter; body is the system prompt; frontmatter fields (name, description, tools, disallowedTools, model, permissionMode, maxTurns, skills, mcpServers, hooks, memory, background, effort, isolation); tool access via allowlist (`tools`) or denylist (`disallowedTools`), mutually exclusive
- **Verify**: Agent file in `.claude/agents/`; only recognized frontmatter fields; `tools` and `disallowedTools` not both set; `permissionMode` matches use case; system prompt is focused and unambiguous

### separation-of-concerns
- **Artifact**: `principles/separation-of-concerns.md`
- **Worker focus**: Each skill, rule, and agent should have one reason to change; if describing what a skill/rule does requires "and," consider splitting; applies at every scale — a skill that does planning AND execution AND reporting is three skills
- **Verify**: Each skill/rule/agent has a single stated purpose; skill description does not contain "and" joining unrelated concerns; workflow steps are separated into distinct agents rather than one agent doing everything

### manage-complexity-through-boundaries
- **Artifact**: `principles/manage-complexity-through-boundaries.md`
- **Worker focus**: Well-defined interfaces between subsystems — skills expose clear input/output contracts; agents receive narrow, specific instructions; use adapters to translate between external systems and internal interfaces; don't let external technology details bleed across boundaries
- **Verify**: Skill inputs and outputs are clearly documented; agents receive only the context needed for their task (not the full session history); external tool calls wrapped behind a consistent interface rather than scattered inline

### explicit-over-implicit
- **Artifact**: `principles/explicit-over-implicit.md`
- **Worker focus**: Make dependencies visible — skills that need files should read them explicitly, not rely on ambient context; name things for what they do; prefer clear parameter passing over ambient state; no hidden behavior or magic invocation paths
- **Verify**: All file dependencies listed explicitly in skill steps; no skills relying on undocumented ambient state; agent instructions say what to do, not how to "figure it out"; context injected explicitly rather than assumed to be present

### design-for-deletion
- **Artifact**: `principles/design-for-deletion.md`
- **Worker focus**: Build skills and rules that are easy to remove without affecting others; treat lines of instructions as lines spent — delete rules that no longer apply; do not abstract prematurely across skills; when in doubt, duplicate rather than couple two skills together
- **Verify**: Each skill and rule can be deleted without breaking other skills; no cross-skill coupling via shared state; no premature abstraction layers across unrelated skills; dead rules (no longer triggered) removed rather than kept "just in case"

### simplicity
- **Artifact**: `principles/simplicity.md`
- **Worker focus**: Simple means no interleaving of concerns — not just "familiar"; optimizing for easy (convenient) leads to complexity that kills velocity; before adding abstraction to a skill or workflow, ask "am I braiding two concerns together?"; complexity in instructions compounds — resist at introduction time
- **Verify**: Skill/rule complexity reviewed before adding new abstraction; each new layer has a clear, single justification; skills do not mix orchestration and domain logic; no convenience helpers that obscure what is actually happening

### yagni
- **Artifact**: `principles/yagni.md`
- **Worker focus**: Build skills and agents for today's known requirements; speculative generality in prompts (adding "in case we need it" context, future-proofing flags, unused parameters) adds maintenance cost with no current value; adding capabilities when the need materializes is almost always cheaper than maintaining premature abstractions
- **Verify**: No unused parameters or frontmatter fields; no "in case we need it" context blocks in skill bodies; no speculative multi-platform handling not required by current targets; skills address actual current workflows, not hypothetical future ones

### support-automation
- **Artifact**: `principles/support-automation.md`
- **Worker focus**: Skills and agents should expose capabilities through scriptable interfaces — not just interactive use; design operations as discrete, composable commands that can be invoked programmatically; provide non-interactive entry points (shell scripts, CLI flags, batch modes) so workflows can drive the extension without human intervention
- **Verify**: Key operations callable non-interactively (no required interactive prompts for automation paths); shell scripts wrap deterministic operations for direct invocation; skills can be chained without requiring human confirmation at each step; outputs are machine-parseable (not just human-readable)

## Exploratory Prompts

1. If you measured the total tokens your rules and CLAUDE.md consume across a 50-turn session, what would you find? Would the number surprise you? What would you cut first?

2. Think about the last skill you built that felt slow or expensive. Was the model doing work that a shell script could have done deterministically? What was the model actually needed for vs. what was habit?

3. When two of your skills compose — one calls the other — what happens to context? Does the second skill re-load everything the first already loaded? How would you design it so context flows efficiently?

4. If you had to make every rule file fit in 10 lines, what would survive? That's your always-on core. Everything else is progressive disclosure — how would you restructure to load it on demand?

5. What would break if you deleted your CLAUDE.md entirely and relied only on rules and skills? What's in CLAUDE.md that couldn't live anywhere else, and why?
