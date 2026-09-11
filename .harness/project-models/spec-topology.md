# Spec Topology

Defines how the Spec Project model locates, identifies, loads, and relates authoritative specification scopes.

Topology is Project-model structure, not a product authority. Domain, App, Style, and Tech continue to own Project truth.

## Manifest

Spec topology is explicit at `doc/spec/topology.json` with schema version `1`:

```json
{
  "schema_version": 1,
  "project_model": "spec",
  "scopes": [
    {
      "id": "domain.identity",
      "authority": "domain",
      "path": "doc/spec/domain/identity.md",
      "depends_on": []
    },
    {
      "id": "domain.billing",
      "authority": "domain",
      "path": "doc/spec/domain/billing.md",
      "depends_on": ["domain.identity"]
    },
    {
      "id": "app.customer",
      "authority": "app",
      "path": "doc/spec/app/customer.md",
      "depends_on": ["domain.billing"]
    }
  ]
}
```

The runtime reports topology as `unconfigured` when the manifest is absent. It does not synthesize scopes from file names.

## Stable scope identity

**[TOPOLOGY-01]** In the Spec Project model, authoritative Project truth is addressed by a stable scope ID independent of physical path. A file may move without changing its scope ID or canonical citations. Changing a scope ID changes authority structure; it is not merely a file move.

Scope IDs use the owning authority as prefix:

```text
domain.<scope>
app.<scope>
style.<scope>
tech.<scope>
```

The remaining segments are lowercase kebab-case components separated by dots. Each scope ID and path is unique within the topology.

## Scope records

Each scope declares:

- `id` — stable authority identity
- `authority` — `domain`, `app`, `style`, or `tech`, matching the ID prefix
- `path` — project-relative Markdown file outside `.harness/`
- `depends_on` — stable IDs whose authority is needed to understand this scope

Dependency edges describe authority dependency, not execution order. The dependent scope owns its outgoing edge.

## Scoped loading

For a selected scope set, load:

1. the selected scopes
2. all transitive dependencies

Do not load unrelated scopes merely because they share a directory or authority family.

`python .harness/runtime/harness.py spec affected --scope <id>` computes this load set mechanically.

## Change Impact

A changed scope may affect scopes that depend on it. For changed scopes, compute transitive reverse dependents as the impact set.

The graph-check set is:

```text
(selected + transitive dependencies)
∪
(selected + transitive reverse dependents)
```

This is a candidate boundary for Change Impact and cross-scope checking. It does not mean every reverse dependent must change.

## Cycles

Cycles are allowed when the authority genuinely has mutual dependency; they do not alter ownership. A strongly connected group loads together, and Sanity should question whether the partition remains useful when cycles become broad or accidental.

## Checks

An authority check has two scales:

1. **local scope check** — inspect selected scope(s) under the owning capability's rules
2. **affected graph check** — inspect relevant dependency/reverse-dependent boundaries for contradictions, stale references, duplicated ownership, or unpropagated change

Sanity Specification Check combines those scales. A full-project sanity run may intentionally select every scope.

## Canonical citations

Where a capability uses stable local identifiers, scope ID provides the namespace:

- `domain.billing:R-017`
- `tech.architecture:A-004`

Identifier uniqueness is required within the owning scope. Cross-scope references use the canonical scoped form.

## Project-model boundary

Spec topology is an implementation detail of the `spec` Project model. Kernel lifecycle mechanics do not assume these scope IDs or paths; they require only that the active Project model can locate relevant authority, expose ownership, and support Change Impact.

## Invariants

- stable scope identity is independent of physical path
- scope prefix matches owning authority
- topology metadata does not become a fifth Project authority
- dependency edges are explicit
- scoped loading follows selected scopes plus transitive dependencies
- Change Impact candidates include reverse dependents
- methods remain non-authoritative regardless of which scope they assist
