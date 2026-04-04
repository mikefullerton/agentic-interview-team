---
name: nullable-reference-types
description: Enable `<Nullable>enable</Nullable>` in all projects; treat warnings as design signals — `string` means non-null, `strin...
artifact: guidelines/language/csharp/nullable-reference-types.md
version: 1.0.0
---

## Worker Focus
Enable `<Nullable>enable</Nullable>` in all projects; treat warnings as design signals — `string` means non-null, `string?` means nullable; avoid null-forgiving operator (`!`) — prefer `?? throw` or guard clauses; use `required` properties and constructor parameters for non-null initialization; use `[NotNull]`, `[MaybeNull]`, `[NotNullWhen]` for contracts compiler cannot infer

## Verify
`<Nullable>enable</Nullable>` in all `.csproj` files; no null-forgiving operator (`!`) usage; non-null properties use `required`; `ArgumentNullException.ThrowIfNull` used at entry points; zero nullable warnings
