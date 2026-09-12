# Project Authority Target Contract

Defines how model-neutral Project reasoning writes accepted conclusions under the active Project model.

**[TARGET-01]** Domain, App, Style, and Tech reasoning is shared across Project models. The selected Project model decides where accepted conclusions become Project authority.

## Target resolution

Before an authority-editing skill changes Project truth, resolve the active target:

- under `spec`, accepted conclusions are written to the affected stable Spec scope(s) selected through Spec Topology and follow the Spec model's **Authority recording discipline** (`SPEC-WRITE-01`)
- under `repository-native`, accepted conclusions are written to the relevant section(s) of the current branch's transient Goal Spec at `doc/goals/<branch>.spec.md`

Repository-native reasoning may also read existing native documentation, ADRs, schemas, tests, code, design-system material, and conventions as evidence or pre-existing native authority. Existing files are not automatically promoted to Harness authority merely because they exist.

## Repository-native Goal Spec

The Goal Spec is the accepted executable interpretation of one Goal. It may contain only the sections the Goal needs, normally from:

- outcome and boundaries
- relevant existing repository shape/constraints
- work/change description
- Domain
- App
- Style
- Tech
- acceptance/proof
- documentation disposition

It is implementation-ready when implementation can begin without silently making a consequential product, domain, style, or technology decision.

The Goal Spec is local transient state. It is not committed as Project documentation and is removed after successful landing or explicit abandonment.

## Native authority

When a repository already treats a native artifact as normative, such as an ADR, API schema, architecture document, design-system contract, or product documentation, the Goal Spec must name and respect that constraint. If the Goal intentionally changes that native authority, updating it is part of implementation, not optional post-work documentation.

## Scope-only mechanics

Stable scope IDs, Spec Topology dependency closure, reverse dependents, and scoped `R-n`/`A-n` citation rules are `spec`-model mechanics. Under `repository-native`, use explicit Goal-Spec sections and repository-native references instead. Do not manufacture Spec scope IDs merely to exercise a shared reasoning skill.

## Completion

Targeted reasoning is complete when accepted conclusions are present in the active Project authority target, unresolved consequential choices are explicit or blocking, and implementation no longer needs to invent intended behavior. Under `spec`, completion also requires that durable conclusions have been compressed out of the working reasoning rather than copied into stable authority as a transcript.

## Invariants

- one active Project model decides authority placement
- reasoning procedure and authority persistence are separate concerns
- implementation never becomes the hidden specification phase
- repository evidence does not become desired-state authority by accident
- repository-native Goal Specs remain Goal-bounded and transient
- model-specific mechanics are not imposed on the other model
