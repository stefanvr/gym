# Knowledge Capture

Records a reusable technology-specific learning discovered during real work.

## Define

Record a reusable technology-specific operational learning discovered through real work without turning it into a project choice or general principle.

## Started
A surprising or non-obvious finding from:

- Build Proof
- Setup
- Build
- Sanity
- deployment/integration work

## Classification

Ask:

1. Is this reusable across projects using the same technology?
   - yes → Knowledge
2. Is it only true of this project?
   - route to Tech/Setup/specification
3. Is it machine-specific?
   - route to Setup or optional environment-specific notes
4. Is it broadly true regardless of technology?
   - route the experience to Dream; Dream may propose a change to the appropriate Guide

## Method

Record:

- observed failure/behavior
- why it is deceptive or important
- safe pattern
- verification
- context boundary
- concise example where useful

Do not turn one incident into a universal rule without evidence.

## Inputs

Required:

- an observed, reproducible or well-evidenced technology-specific finding
- the technology/context it applies to

Optional: proof/setup/build evidence and an existing knowledge entry to refine.

## Outputs

A concise reusable knowledge entry describing the finding, deceptive failure mode, safe pattern, verification, and context boundary.

## Owns

Only the matching entry in the configured knowledge store. In this repository that is `.harness/knowledge/<technology>.md`; when an external knowledge-base repository is configured, ownership moves there. It never owns project Tech choices or Setup state.

## Modes

### `capture`

Create or refine one reusable technology learning. Generalization to a Guide or routing to Setup/Tech is classification, not another mode.

## Approval

No lifecycle approval. If writing to a shared external knowledge base has its own review policy, follow that repository’s policy.

## Invariants

- nothing here chooses the technology
- observations remain context-bounded
- project-specific facts route to project authority
- broader principles route through Dream as proposals rather than being promoted directly
- do not record secrets or personal machine details

## Completion

Complete when future work using the same technology can avoid rediscovering the same trap.
