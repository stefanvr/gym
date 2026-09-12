# ChatGPT / OpenAI Coding-Agent Adapter

OpenAI coding agents execute the agent-independent harness; this adapter does not own project policy.

## Load

Read `.harness/workflow/WORKFLOW.md` and follow its shared session-start/loading policy.

OpenAI-specific instructions belong here only when workspace/tool/permission mechanics differ. Shared workflow/lifecycle/product policy does not.
## Extensions

Extensions are never loaded merely because they exist. When the owner or Routing selects one, resolve it with `python .harness/runtime/harness.py extension resolve --id <id>` (add `--scope project|local` if the id exists in both scopes), then read the returned `SKILL.md` and any package material it explicitly requires. Treat it as additional capability under `.harness/extensions/definition.md`, never as authority or an implicit override of a core skill.

