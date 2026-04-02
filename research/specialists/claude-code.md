# Claude Code & Agentic Development Specialist

## Domain Coverage

Claude Code plugin architecture, skill/rule/agent/hook authoring, MCP server design, CLAUDE.md organization, context window management, progressive disclosure, performance optimization (token efficiency, model selection, shell scripts), and multi-agent orchestration.

## Cookbook Sources

### Guidelines
- `cookbook/guidelines/skills-and-agents/authoring-skills-and-rules.md`
- `cookbook/guidelines/skills-and-agents/performance.md`

### Principles
- `cookbook/principles/separation-of-concerns.md`
- `cookbook/principles/manage-complexity-through-boundaries.md`
- `cookbook/principles/explicit-over-implicit.md`
- `cookbook/principles/design-for-deletion.md`
- `cookbook/principles/simplicity.md`
- `cookbook/principles/yagni.md`

### Recipes
- `cookbook/recipes/developer-tools/claude/claude-rule-optimization-pipeline.md`
- `cookbook/recipes/developer-tools/claude/yolo-mode.md`
- `cookbook/recipes/autonomous-dev-bots/pr-review-pipeline.md`

### Research
- `research/developer-tools/claude/claude-plugin-format.md`
- `research/developer-tools/claude/hooks-patterns.md`
- `research/developer-tools/claude/mcp-servers.md`
- `research/developer-tools/claude/memory-and-context-tools.md`
- `research/developer-tools/claude/claude-integration-guide.md`
- `research/developer-tools/claude/rule-optimization.md`
- `research/developer-tools/claude/skill-testing-landscape.md`
- `research/developer-tools/claude/plugins-and-skills-catalog.md`
- `research/developer-tools/claude/self-healing-research-summary.md`
- `research/developer-tools/claude/terminal-progress-and-status-line.md`
- `research/developer-tools/claude/yolo-per-session-design.md`
- `research/developer-tools/claude/dangerously-skip-permissions-bugs.md`

### Rules (authoring reference)
- `rules/skill-authoring.md`
- `rules/skill-versioning.md`
- `rules/extension-authoring.md`
- `rules/permissions.md`
- `rules/authoring-ground-rules.md`

## Structured Questions

1. What Claude Code extensions does your project use — skills, rules, agents, hooks, MCP servers, plugins? Which are project-local and which are shared across projects?

2. How is your CLAUDE.md organized? What's always-on in rules vs. loaded on-demand via skills? Have you measured the per-turn context cost of your rule files?

3. Walk me through a skill you've built. Does it shell out to scripts for deterministic steps, or does the model handle everything? Where could a shell script replace a model call?

4. How do you handle repeatable, deterministic operations — file scaffolding, git commands, build steps, linting? Are these in hooks or shell scripts, or does the model re-derive them each time?

5. When your skills or agents spawn subagents, how do you choose the model? Do simple subtasks use a smaller model, or does everything run on the same model? Have you measured whether downgrades actually save tokens?

6. How much context do your rules load per turn? If you have multiple rule files, what's the aggregate line count? Have you run the rule optimization pipeline?

7. How do your skills load guidance — all upfront, or progressively as they reach each step? If a skill has a 50-item checklist, does it load the full checklist at start, or pull in sections as needed?

8. How do your hooks interact with the model's workflow? Do you use PreToolUse hooks for security gates? PostToolUse for auto-formatting? Stop hooks for verification? Which events have you wired up and why?

9. If your project uses MCP servers, what drove the decision to build an MCP server vs. a skill? How do you handle authentication, error responses, and tool schema design?

10. How do your agents scope their tool access? Do they use `tools` or `disallowedTools` to restrict what they can do? What's the maxTurns setting and how did you choose it?

11. How do you test your skills and rules? Manual testing per session, automated harness, or lint checks? How do you know a rule change didn't break behavior?

12. How do your extensions compose? Can skills call other skills? Do agents spawn subagents? How do you manage context when extensions chain together?

13. What's your plugin distribution strategy — project-local in `.claude/`, shared via a plugin, or a mix? How do you handle the constraint that plugins can't distribute rules?

## Exploratory Prompts

1. If you measured the total tokens your rules and CLAUDE.md consume across a 50-turn session, what would you find? Would the number surprise you? What would you cut first?

2. Think about the last skill you built that felt slow or expensive. Was the model doing work that a shell script could have done deterministically? What was the model actually needed for vs. what was habit?

3. When two of your skills compose — one calls the other — what happens to context? Does the second skill re-load everything the first already loaded? How would you design it so context flows efficiently?

4. If you had to make every rule file fit in 10 lines, what would survive? That's your always-on core. Everything else is progressive disclosure — how would you restructure to load it on demand?

5. What would break if you deleted your CLAUDE.md entirely and relied only on rules and skills? What's in CLAUDE.md that couldn't live anywhere else, and why?
