# Specialty-Team Extraction Plan

Extract specialty-teams from embedded specialist markdown sections into independent files in a shared pool, with specialist manifests referencing them.

## Target Structure

```
specialty-teams/
  security/
    authentication.md
    authorization.md
    token-handling.md
    ...
  reliability/
    error-handling.md
    ...
  ui-ux-design/
    ...
specialists/
  security.md          # role + ## Manifest section listing paths
  reliability.md
  ...
```

## Specialty-Team File Format

```yaml
---
name: authentication
description: OAuth 2.0/OIDC with PKCE for public clients, SSO, multi-client strategies
artifact: guidelines/security/authentication.md
version: 1.0.0
---

## Worker Focus
OAuth 2.0/OIDC with PKCE for public clients, system browser for native apps, no implicit flow, SSO and multi-client strategies

## Verify
No implicit flow; PKCE code_challenge present; system browser on native (no embedded WebView); no client_secret in public clients
```

## Specialist Manifest Format

The `## Specialty Teams` section in each specialist file is replaced with a `## Manifest` section listing paths to specialty-team files:

```markdown
## Manifest
- specialty-teams/security/authentication.md
- specialty-teams/security/authorization.md
- specialty-teams/security/token-handling.md
```

## Scope

- 19 specialists
- 229 specialty-teams
- 4 fields per team: name, artifact, worker_focus, verify (plus new: description, version)

## Consumers To Update

| Consumer | Type | What Changes |
|----------|------|-------------|
| `scripts/run-specialty-teams.sh` | Shell script | Rewrite: read individual files instead of parsing embedded markdown |
| `agents/specialty-team-worker.md` | Agent | May need path updates in instructions |
| `agents/specialty-team-verifier.md` | Agent | May need path updates in instructions |
| `agents/specialist-code-pass.md` | Agent | References specialty-teams as checklist |
| `agents/specialist-interviewer.md` | Agent | References specialty-teams as checklist |
| `agents/recipe-reviewer.md` | Agent | References specialty-teams as checklist |
| `docs/specialist-spec.md` | Spec | Describes old embedded format |
| `docs/specialist-guide.md` | Guide | Describes old embedded format |
| `.claude/skills/lint-specialist/` | Skill | Validates old embedded format |
| `.claude/skills/create-specialist/` | Skill | Scaffolds old embedded format |
| `skills/dev-team/workflows/generate.md` | Workflow | References run-specialty-teams.sh |

## Steps

Commit after each step.

### Phase 1: Create Pool

1. Create the new pool of specialty-teams as individual files. Don't touch existing specialists.

### Phase 2: Verify Pool

2. Verification pass — do all specialty-teams exist in both places (embedded and file)? Is the content the same or improved?
3. Fix issues found.
4. Goto 2 until no issues found.

### Phase 3: Test Pool

5. Write unit tests for new specialty-team files (frontmatter validity, required fields, artifact paths exist, etc.).
6. Run tests.
7. Fix issues found.
8. Goto 6 until done.

### Phase 4: Wire Up and Remove Old

9. Wire specialists up to their new manifests (add `## Manifest` section).
10. Remove old embedded `## Specialty Teams` sections from specialists.

### Phase 5: Update Consumers

11. Rewrite `run-specialty-teams.sh` to read from individual specialty-team files via specialist manifest.
12. Update consumer agents, workflows, docs, and skills for the new structure.

### Phase 6: Verify and Test Everything

13. Verify integrity of all references (manifest paths resolve, artifact paths exist, no broken refs).
14. Update and adjust all existing tests for the new organization.
15. Run tests.
16. Fix issues found.
17. Goto 15 until done.
