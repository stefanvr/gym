# Build Proof

Produces the smallest executable and operational evidence needed to resolve uncertainty behind a technical decision.

## Define

A proof establishes whether a technical seam, toolchain, integration, or required operating path actually works sufficiently for the decision that depends on it.

It does not implement product functionality.

## Requested by

Typically:

`Tech Decide`

Tech owns the decision.

Build Proof owns the executable/operational evidence.

## Before proof

Use Knowledge Lookup for the named technology where relevant.

## Inputs

Required:

- uncertainty being tested
- seams/behaviors to exercise
- environment assumptions that could invalidate the result
- success/failure evidence

## Method

1. Name the seams and operational assumptions.
2. Exercise the smallest real path that resolves the uncertainty.
3. Exclude product behavior not required by the proof.
4. Verify the artifact/result rather than only command success.
5. Route findings.

## Finding routes

- decision evidence → Tech
- development setup fact → Setup Dev
- runtime/deployment fact → Setup App
- reusable technology-specific finding → Knowledge
- project-specific architecture consequence → Tech
- machine-specific anomaly → Setup or optional environment-specific note

## Product-decision test

For any product rule in the proof, ask:

> If this rule were removed, would any intended seam or operational assumption stop being proven?

If no, remove it.

## Goal boundary

A goal such as `choose X` ends when X has been selected and sufficiently proven.

Do not continue into product implementation without an explicit goal transition.

## Outputs

Executable/operational evidence sufficient for the decision owner, plus routed findings for Tech, Setup, or Knowledge. Proof-specific code/scripts may be temporary or retained when they remain useful evidence.

## Owns

Only proof-specific executable artifacts and transient evidence needed to exercise the named uncertainty. It does not own the Tech decision, product specifications, Setup instructions, or Knowledge entries created from its findings. It may record transient findings/notes in Build's shared `doc/scratchpad/`; closure of that directory is owned by Build Check `close`.

## Modes

### `prove`

Exercise the smallest real technical and operational path that resolves the bounded uncertainty. A proof does not have an implementation mode; crossing into product functionality routes to a new goal.

## Approval

Build Proof itself requires no approval. The decision informed by the proof follows the approval policy of its owner, typically Tech Decide.

## Completion

Complete when:

- every named seam/assumption has been genuinely exercised
- relevant uncertainty has evidence
- operational findings are routed
- no unnecessary product rules exist
- the result is sufficient for the decision owner

## Invariants

- proof is evidence, not product development
- operational reality is part of the proof when it can invalidate the choice
- Tech owns the decision
- Setup owns operational instructions
- Knowledge owns reusable technology learnings
