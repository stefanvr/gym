# Claude Code Adapter

Claude Code executes the agent-independent harness; it does not own project policy.

## Load

Read `.harness/workflow/WORKFLOW.md` and follow its shared session-start/loading policy.

Explicit callable skills under `.claude/skills/` are steering shortcuts to the same authoritative `.harness` skills.

Claude-specific instructions belong here only when Claude Code's instruction loading, tools, or permissions require different execution mechanics. Shared workflow/lifecycle/product policy does not.

## Extensions

Extensions are never loaded merely because they exist. When the owner or Routing selects one, resolve it with `python .harness/runtime/harness.py extension resolve --id <id>` (add `--scope project|local` if the id exists in both scopes), then read the returned `SKILL.md` and any package material it explicitly requires. Treat it as additional capability under `.harness/extensions/definition.md`, never as authority or an implicit override of a core skill.

## Compact repetitive verification output

Project-local `.claude/settings.json` registers a `PreToolUse` Bash hook for `npm test`, `npm run test:e2e`, and `.harness/runtime/harness.py check`. For simple invocations, `.claude/hooks/compact-bash-output.py` preserves the command's exit status while replacing successful stdout with a one-line PASS summary and limiting failures to a compact diagnostic excerpt. Compound or dynamic shell commands are deliberately not rewritten.

Use the compact result as the normal verification result. Re-run a target command without compaction only when full raw output is specifically needed to diagnose a failure.
