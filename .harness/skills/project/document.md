# Project Document

Optionally persists useful non-authoritative Project knowledge from a Goal or Discovery after any required authoritative updates are handled.

## Define

Choose whether useful information from a Goal or explicitly published Discovery should become durable documentation, and if so persist it in one deliberate mode.

## Inputs

Required:

- a completed/near-complete Goal **or** an explicitly published Discovery finding
- active Project model
- relevant Project authority/context

As needed:

- existing repository documentation style and structure
- current Goal Spec in repository-native mode when the source is a Goal
- candidate Harness Spec topology/content

## Outputs

One of:

- no documentation change
- native repository documentation updated in its existing style
- candidate/shadow Harness Spec material enriched from the source

## Owns

Only optional documentation work. Required changes to an existing native authoritative document are implementation work and are not deferred here.

## Modes

### `native`

Add or update useful explanatory documentation using existing repository conventions and avoiding a parallel Harness-specific documentation system.

### `spec-project`

Project durable knowledge into Harness-style Spec material. While `repository-native` remains active, this material is non-authoritative candidate/shadow Spec until an explicit Project-model migration validates and activates it.

### `none`

Record no additional durable documentation when the implementation and required authority already communicate the result adequately.

## Completion

Complete when the chosen disposition is executed consistently and no optional document is being mistaken for a second authority source.

## Approval

Routine explanatory documentation needs no separate approval. Changing Project-model authority or promoting candidate Spec into active authority requires an explicit Harness/project-model migration decision.

## Invariants

- required native authority maintenance is never classified as optional
- native mode follows existing repository style
- spec projection does not silently activate `spec`
- no duplicate authority is created
- documentation remains bounded to useful knowledge from the source
- Discovery publication is explicit; Project Document never turns transient exploration into durable state on its own
