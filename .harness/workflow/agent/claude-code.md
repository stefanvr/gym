# Claude Code Adapter

Claude Code executes the agent-independent harness; it does not own project policy.

## Load

Read `.harness/workflow/WORKFLOW.md` and follow its shared session-start/loading policy.

Explicit callable skills under `.claude/skills/` are steering shortcuts to the same authoritative `.harness` skills.

Claude-specific instructions belong here only when Claude Code's instruction loading, tools, or permissions require different execution mechanics. Shared workflow/lifecycle/product policy does not.
