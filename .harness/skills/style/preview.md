# Style Preview

Builds developer-facing demonstrations of the authoritative Style specification.

## Authority target

Follow the [Project Authority Target Contract](../../contracts/project-authority-target-contract.md). Under `spec`, edit/check the affected stable Spec scope(s). Under `repository-native`, edit/check the corresponding section of the current transient Goal Spec and relevant named native constraints. Any scope-ID, Spec Topology, reverse-dependency, or scoped identifier requirement below is `spec`-only unless the repository already uses an equivalent native identifier deliberately.


## Define

Make Style decisions directly inspectable without requiring the production application to reach every relevant state.

Style Preview demonstrates what the relevant Style Spec scope(s) selected by Spec Topology decide. It does not decide Style.

## Inputs

Required:

- the relevant Style Spec scope(s) selected by Spec Topology

As applicable:

- centralized visual values
- centralized audio values
- implementation components needed to render or play them
- project-specific developer-affordance conventions or Tech constraints
- an existing developer preview/index surface

## Outputs

Developer-facing preview artifacts that demonstrate relevant Style decisions, plus discoverable links/index entries when the project uses a developer preview index.

Exact paths are project-specific and are established from the project's existing structure or current goal; the harness defines no universal preview path.

## Owns

Only the Style preview artifacts and index entries created for the current project at the project-specific paths established during the work.

It does not own product UI, the Style specification, or a universal `dev/` directory convention.

## Modes

### `visual`

Build or update a visual Style preview.

Demonstrate relevant values such as palette, typography, reusable visual values, and representative states.

Prefer systematic/tabulated presentation over recreating product screens unnecessarily.

### `audio`

Build or update an audio Style preview.

Demonstrate each specified sound, relevant variations, and deliberate silence where Style defines it.

### `index`

When the project has or needs a developer preview index, ensure the Style previews are reachable from it.

Do not invent an index solely because this mode exists.

### `check`

Own the demonstrability check for Style Preview. Compare the Style specification with the project's actual/documented preview coverage.

Find:

- specified decisions/values that cannot be inspected where demonstration is expected
- stale or missing demonstrations
- preview values that diverge from the product implementation source of truth
- preview-local copies that have become independent sources of Style values

Do not re-check whether the product implementation itself has one source of truth; Style Check owns that question.

## Method

### Demonstrate, do not reinterpret

Read Style decisions from their authoritative implementation sources where practical.

Do not maintain separate copies of palette values, typography values, sound definitions, or other centralized Style constants.

### Prefer isolated demonstration

Demonstrate Style independently of production flows where isolation makes inspection easier.

### Show the boundary

Preview enough context to understand the Style decision without quietly becoming an alternate application implementation.

## Completion

Preview work is complete when:

- relevant Style decisions can be directly inspected
- previews consume the intended sources of truth
- no demonstrated value has drifted into an independent copy
- previews are discoverable through the project's established developer-affordance route where one exists
- any Style decision that cannot yet be demonstrated is explicitly identified

## Approval

Preview itself normally requires no separate approval. It provides the inspection surface used when Style work requires user validation.

## Invariants

- Preview demonstrates; Style decides
- Preview is developer-facing tooling, not product UI
- Preview does not duplicate authoritative Style values
- Preview does not invent new Style decisions
- exact preview paths are project-specific, not harness policy
- visual and audio previews may remain separate
- deliberate silence is demonstrable where relevant
