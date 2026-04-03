# New Project Setup Template

When creating a new project in the interview repo, create this directory structure:

```
projects/<project-name>/
  transcript/
  analysis/
  checklist.md    (copy from templates/checklist.md, replace {{PROJECT_NAME}} and {{DATE}})
```

The session ID format is: `<project-name>-<YYYYMMDD>-<HHMMSS>`

The transcript and analysis directories are populated during the interview. Each exchange produces:
- `transcript/<YYYY-MM-DD-HH-MM-SS>-<slug>.md`
- `analysis/<YYYY-MM-DD-HH-MM-SS>-<slug>-analysis.md`
