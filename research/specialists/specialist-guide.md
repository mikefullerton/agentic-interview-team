# Specialist Guide

The canonical reference for what a specialist is, how specialist question sets are structured, and how specialists participate in the three dev-team workflows.

## What Is a Specialist?

A specialist is a domain-expert lens applied across three workflows: interview, recipe review, and code augmentation. Each specialist owns a slice of the cookbook — specific guidelines, principles, compliance checks, and research — and uses that knowledge to ask better questions, catch domain-specific gaps, and add domain concerns to generated code.

Specialists do not work in isolation. They are invoked by the meeting leader (interview), the generate-project skill (recipe review), and the build-project skill (code augmentation). They receive context, do focused work, and return structured output.

## Question Set Format

Every specialist file in `research/specialists/` follows this structure:

### Domain Coverage

One to two sentences defining the specialist's scope. This is the quick filter for "does this specialist care about X?"

### Cookbook Sources

Explicit file paths to the cookbook content this specialist owns. These are the authoritative references the specialist reads during all three workflows. List every relevant directory or file — no implicit discovery.

Categories:
- **Guidelines** — `cookbook/guidelines/<topic>/` directories
- **Principles** — individual `cookbook/principles/<name>.md` files
- **Compliance** — `cookbook/compliance/<category>.md` files
- **Research** — `research/developer-tools/<area>/` files
- **Recipes** — `cookbook/recipes/<area>/` files (for review and augmentation context)
- **Rules** — `rules/<name>.md` files (for authoring-focused specialists)

### Structured Questions

Ten to fifteen methodical questions that cover the specialist's domain systematically. These serve as:
- **Interview mode**: A checklist the specialist-interviewer works through, adapting each question to what's been discussed
- **Recipe review mode**: A checklist of concerns the recipe-reviewer checks against each recipe
- **Code augmentation mode**: A mental model for what the specialist-code-pass agent should look for

Each question should be specific enough to elicit a concrete answer, not vague enough to get a hand-wave. Bad: "How will you handle errors?" Good: "When a network request fails mid-sync, does the operation retry, roll back, or leave partial state? How does the user know what happened?"

### Exploratory Prompts

Three to five "why" and "what-if" questions that push thinking beyond the checklist. These are used in exploratory interview mode to follow threads and surface things the user hasn't considered.

Exploratory prompts should be genuinely curious, not leading. They probe assumptions, test mental models, and surface hidden complexity.

## Three Participation Modes

### 1. Interview (specialist-interviewer agent)

The specialist generates one question at a time for the meeting leader to pass to the user. Two modes:

- **Structured**: Work through the question set methodically, skipping questions already answered, adapting each to the transcript context
- **Exploratory**: Follow threads from previous answers, ask "why" and "what-if" questions, surface implications the user hasn't considered

Output: One question with specialist attribution, context for why it matters, and (in exploratory mode) what thread is being followed.

Key constraint: Questions must be specific to what's been discussed. Generic questions waste the user's time. Reference previous answers. Show the team is listening.

### 2. Recipe Review (recipe-reviewer agent)

The specialist evaluates a generated recipe through their domain lens:

- Check whether the recipe addresses each concern from the structured questions
- Compare requirements against cookbook guidelines and compliance checks
- Identify gaps, suggest specific improvements with rationale
- Flag cross-domain issues when critical

Output: Structured review with compliance gaps, missing sections, actionable suggestions (with cookbook references), and questions that need user input.

Key constraint: Suggestions must be specific and surgical. "Add a MUST requirement for X" not "security needs work." Reference the cookbook source that justifies each suggestion.

### 3. Code Augmentation (specialist-code-pass agent)

The specialist surgically adds domain concerns to generated code:

- Add code (methods, properties, imports, modifiers)
- Wrap existing code (error handling, validation, guards)
- Annotate existing code (accessibility labels, logging, analytics)

Output: Updated source files plus an augmentation report listing changes, recipe requirements addressed, and cookbook guidelines applied.

Key constraints:
- **Additive only** — do not delete code from previous passes
- **Must compile** — code must compile before and after the pass
- **Stay in your lane** — add your domain's concerns, not someone else's (but flag critical cross-domain issues)

## Cross-Domain Responsibilities

Each specialist stays focused on their domain. However, when a specialist notices a critical issue outside their lane, they flag it rather than ignoring it:

- A security specialist reviewing a recipe notices no rate limiting on a login form — flags it
- A UI specialist augmenting code notices user input flowing to a database query unsanitized — flags it
- An accessibility specialist in an interview hears the user describe a custom gesture with no alternative — flags it

The flag goes to the meeting leader (interview), the review output (recipe review), or the augmentation report's "Deferred" section (code augmentation). The specialist does not fix it themselves.

## Adding a New Specialist

1. Create `research/specialists/<domain>.md` following the format above
2. Add the specialist to the roster in `research/cookbook-specialist-mapping.md`
3. Map cookbook sources (guidelines, principles, compliance, research) to the specialist
4. Add a domain-specific section to `agents/specialist-code-pass.md` describing what the specialist adds during code augmentation
5. Test: run the specialist through each workflow mode to verify the questions are specific enough, the cookbook sources are correct, and the code augmentation guidance produces compilable results
