# Conversational Interview Patterns

Patterns extracted from existing cookbook skills and workflows that inform how the interview system conducts conversations.

## Phase-Based Conversation (from code-planning.md)

The cookbook's planning workflow uses 5 explicit phases with entry/exit criteria:

| Phase | Purpose | Exit Criteria |
|-------|---------|---------------|
| 1. Understand | Restate the request, confirm scope | User confirms understanding |
| 2. Explore | Search existing context | Clear picture of what exists |
| 3. Checklist | Evaluate applicability of guidelines | All decisions recorded |
| 4. Clarify | Batch remaining questions | No remaining ambiguity |
| 5. Produce | Structured output | User approves |

**Applied to interviews:** The structured → explore → structured loop maps to phases 2-4 repeating, with phase 1 at session start and phase 5 when the user asks for a summary.

## Propose-Then-Refine (from plan-cookbook-recipe)

Pattern: Don't ask open-ended questions when you can propose and iterate.

```
Interviewer: "For the settings window, I'd expect you'd want sections for 
Appearance, Accounts, Notifications, and Privacy. Does that match your 
thinking, or would you organize it differently?"

NOT: "What sections does your settings window have?"
```

The first approach gives the user something to react to. The second puts all the creative burden on them.

**When to use:** After enough context is established to make reasonable proposals. Don't propose in the early big-picture phase — that's genuinely open-ended.

## Section-by-Section Progression (from plan-cookbook-recipe)

Walk through topics one at a time:
1. Identify the section
2. Brief focused discussion
3. Propose draft content
4. Refine with user
5. Move to next section

**Applied to interviews:** Each specialist covers one topic area. Within that area, go control-by-control, feature-by-feature. Don't jump around.

## Checklist Modes (from guideline-checklist.md)

Not all questions have equal weight:

| Mode | Meaning | Example |
|------|---------|---------|
| **Always** | Ask every time, no opt-out | "What platforms are you targeting?" |
| **Opt-in** | Assume relevant, user can skip | "Let's talk about accessibility — unless you want to skip this for now?" |
| **Opt-out** | Assume not relevant, user can add | "We won't cover A/B testing unless you want to" |
| **Ask** | No assumption, must ask | "Are you planning to support offline mode?" |

**Applied to interviews:** The transcript analyzer categorizes each specialist's questions into these modes based on what's been learned so far.

## Consolidated Question Presentation (from guideline-checklist.md)

When presenting checklist-style questions, batch them:

```
"Here's what I'd like to cover for the main window:
- Layout and navigation structure (always)
- Color scheme and theming (always)
- Accessibility (opt-in — I'll cover this unless you say skip)
- Localization (ask — are you planning multi-language support?)

Anything you want to add or skip?"
```

NOT: asking each one individually.

**Applied to interviews:** At the start of each topic area, the meeting leader previews what the relevant specialist will cover. User can adjust scope before diving in.

## Design Decision Flagging (from plan-cookbook-recipe)

Whenever a choice is made (explicitly or implicitly), flag it:

```
"**Design Decision:** You mentioned both a sidebar and a tab bar for 
navigation. I'm going with sidebar since you described a document-based 
app and that's the standard pattern on macOS. Does that work?"
```

**Applied to interviews:** The specialist analyst watches for implicit decisions in answers and flags them for explicit confirmation.

## Error Recovery (from ai-chat-control recipe)

When an answer is incomplete or confusing:

1. **Rephrase with examples:** "Let me ask that differently — for example, when you say 'persistent,' do you mean saved to disk between sessions, or just kept in memory while the app is open?"
2. **Offer concrete options:** "There are three common approaches to this: A, B, or C. Which is closest to what you're thinking?"
3. **Note and move on:** "Okay, let's come back to that. Moving on to..."
4. **Circle back:** Return to skipped questions later with more context

## One Question at a Time

During open-ended exploration, ask ONE question per turn. Wait for the answer. Follow the thread.

During structured checklist coverage, batching is okay because the user is confirming/adjusting a known list, not generating new ideas.

## Sources

- `skills/plan-cookbook-recipe/SKILL.md`
- `workflows/code-planning.md`
- `workflows/guideline-checklist.md`
- `recipes/ui/components/ai-chat-control.md`
