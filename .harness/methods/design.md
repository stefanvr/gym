# Design

Cross-authority coordination method for product/system design work that cannot be responsibly classified into one Project authority before exploration.

## Purpose

Turn a broad design request into coordinated authority work without inventing a new Design authority.

Design identifies which Project authorities are materially affected, delegates each concern to its owner, keeps cross-authority constraints visible, and reconciles the resulting shape against the current Goal.

## Inputs

May consume:

- current Goal
- current Project authority from several capability families
- owner intent
- evidence from the repository or existing product
- outputs from Interview Me, Event Storming, Story Mapping, or other active methods

## Working outputs

Usually an in-context coordination plan plus routed authority work.

When a durable coordination artifact is useful, Design may create non-authoritative working material under:

`doc/working/design/`

It may record:

- affected authorities
- open questions
- cross-authority constraints
- delegated decisions
- reconciliation notes

## Authority interaction

Design owns no Project truth.

For either supported Project model, reasoning remains authority-neutral until promoted. Under `spec`:

- world concepts/rules/events/data → Domain
- user activities/interactions/surfaces → App
- perceptual character/reference → Style
- project-specific technology/architecture → Tech

Each authority orchestrator remains responsible for its accepted conclusions and checks.

## Invocation

Use for a broad design request that materially spans several authorities or whose correct authority decomposition is itself part of the problem.

Do not route every ordinary Project change through Design. When the concern already has a clear authority owner, enter that authority orchestrator directly.

## Method

1. restate the bounded design outcome in current-Goal terms
2. identify which authority questions are genuinely material
3. use Interview Me or other active discovery methods only where uncertainty warrants them
4. delegate each concern to its authority orchestrator
5. preserve explicit constraints and dependencies crossing authority boundaries
6. reconcile returned conclusions for contradictions or gaps without overruling their owners
7. trigger Change Impact where authoritative changes affect dependent conclusions
8. ensure relevant authority checks and cross-spec checks are re-established before completion

## Completion

Complete when every material design concern has an owner, accepted conclusions live in those owners' authoritative state, cross-authority contradictions are resolved or explicit, and no Design working artifact is being treated as Project truth.

## Invariants

- Design coordinates but owns no Project truth
- Design never becomes an authority above Domain/App/Style/Tech
- already-clear concerns route directly rather than adding ceremony
- method output remains working state
- cross-authority constraints stay visible until reconciled
- design scope remains bounded by the current Goal
