# Extensions

Extensions let a project or developer add useful skills without pretending every useful skill belongs in Harness core.

## Scopes

### Project extension

Committed with the project at:

` .harness/extensions/project/<id>/SKILL.md `

Use for a skill that is useful/expected for this project but not universal Harness behavior. The package may contain supporting files beside `SKILL.md`.

### Local extension

Developer-local at:

` .harness/extensions/local/<id>/SKILL.md `

This directory is ignored by Git. Use for personal, newly acquired, or still-being-evaluated skills. "Experimental" is a maturity description, not a separate architectural type.

## Authority boundary

**[EXTENSION-01]** Extensions extend available reasoning/execution capability; they do not extend authority.

An Extension may participate in Discovery, Project reasoning, specification, prototyping, or Build where appropriate. Its output becomes Project truth only through the same existing authority/promotion boundaries as core skills.

Installing an Extension does not grant its scripts or commands automatic execution trust. Inspect and apply normal scrutiny before executing extension-provided code.

## Resolution

Extensions live in an explicit namespace and never silently override core Harness skills.

- `extension:<id>` is valid when the id is unambiguous across installed scopes
- `project-extension:<id>` selects the committed project copy
- `local-extension:<id>` selects the developer-local copy

If both scopes contain the same id, no precedence rule silently chooses one.

The deterministic runtime may list/resolve Extension entrypoints; it never executes them or decides whether their advice should be accepted.

## Promotion

A useful local Extension may be adopted as a project Extension. A generally useful project Extension may later be separately generalized into Harness core. Neither promotion is automatic.
