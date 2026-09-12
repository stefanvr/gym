# Gemini Adapter

Gemini executes the agent-independent harness; it does not own project policy.

## Load

Read `.harness/workflow/WORKFLOW.md` and follow its shared session-start/loading policy.

Gemini-specific instructions belong here only when instruction loading, tools, or permissions require different execution mechanics. Shared workflow/lifecycle/product policy does not.
## Extensions

Extensions are never loaded merely because they exist. When the owner or Routing selects one, resolve it with `python .harness/runtime/harness.py extension resolve --id <id>` (add `--scope project|local` if the id exists in both scopes), then read the returned `SKILL.md` and any package material it explicitly requires. Treat it as additional capability under `.harness/extensions/definition.md`, never as authority or an implicit override of a core skill.

