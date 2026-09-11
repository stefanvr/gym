# Brainstorm Analyze

Examines supplied material to extract useful evidence, interpretations, contrasts, possibilities, tensions, and questions without turning them into settled design.

## Define

Analyze material in support of understanding an idea or product.

Use when useful understanding is present in artifacts rather than only in the owner's head.

Typical material includes:

- notes
- documents
- screenshots
- sketches
- existing products
- reference products
- code or prototypes
- research material
- previous drafts

The result is structured draft evidence for later Goal, Domain, App, Style, or Tech work.

It does not own the resulting decisions.

## Inputs

Required:

- one or more supplied materials
- the current reason for examining them

Optional:

- current goal
- existing brainstorm material
- known constraints
- existing specifications
- owner commentary about the material

The skill may inspect relationships between multiple materials when comparison is useful.

## Outputs

Analysis may produce:

- observations
- contrasts
- patterns
- constraints
- inferred intent
- opportunities
- candidate ideas
- tensions
- unanswered questions
- candidate goals
- downstream routing

Every finding keeps its evidence status visible.

## Provenance

Use the shared Provenance mechanism; do not define a second evidence taxonomy here.

Analysis commonly produces `Observed`, `Inferred`, `Suggested`, and `Open` findings. If supplied material carries established owner provenance such as `Said` or `Suggested and accepted`, preserve that class rather than collapsing it into the four common analysis outputs.

## Owns

May create brainstorm analysis material only under:

`doc/brainstorm/analysis/<session>.md`

Analysis artifacts remain draft. Brainstorm Interview artifacts remain Interview-owned.

Does not modify authoritative:

- current Goal
- Domain artifacts
- App artifacts
- Style artifacts
- Tech decisions

## Modes

### `run`

Analyze supplied material for the current goal or exploration.

### `compare`

Compare two or more materials where their differences are themselves useful evidence.

Use only when comparison is meaningful to the current exploration.

## Method

### Start from the purpose

Establish why the material is being examined.

Do not perform exhaustive analysis merely because material exists.

The current question determines what deserves attention.

### Observe before interpreting

First identify what the material directly supports.

Then derive interpretations separately.

Do not compress observation and inference into one claim.

### Preserve source boundaries

When several materials are supplied, keep clear which source supports which finding.

Do not accidentally combine separate sources into an apparent consensus.

### Look for differences as well as patterns

Similarity can suggest a pattern.

Difference may reveal:

- design choices
- constraints
- trade-offs
- assumptions
- opportunities
- unresolved preferences

Do not treat frequency as desirability.

### Separate description from preference

A reference demonstrating something does not imply the owner wants it.

A common pattern does not automatically become a recommendation.

A recommendation remains a harness suggestion until accepted.

### Identify tensions

Surface cases where:

- sources conflict
- one desirable property undermines another
- current goals conflict with observed constraints
- stated intent differs from supplied examples

Do not resolve tensions silently.

### Identify absence carefully

Missing information may be useful.

But absence is not evidence that something is intentionally excluded.

Record it as open unless other evidence supports the conclusion.

### Route findings

When analysis reveals something belonging elsewhere:

- candidate outcome → Goal
- domain concept or rule → Domain
- user behavior or interaction → App
- visual/audio characteristic → Style
- technology constraint or open choice → Tech

Routing does not turn the finding into an authoritative decision.

## Scrutiny

Before recording a finding, ask:

1. What evidence supports this?
2. Is it observed, inferred, suggested, or open?
3. Which source supports it?
4. Am I describing the material or judging it?
5. Does this matter to the current goal?
6. Am I inferring owner preference without evidence?
7. Am I resolving a tension that should remain visible?
8. Does this belong to a downstream capability rather than Brainstorm?

## Completion

Analysis is complete when:

- material relevant to the current purpose has been examined
- meaningful observations are captured
- inference is separated from observation
- important tensions and gaps are visible
- unsupported conclusions have not been promoted to facts
- useful downstream findings are routed
- additional analysis would mostly add detail rather than materially change understanding

Completion does not mean every aspect of the source has been described.

## Approval

Analysis normally requires no approval.

When an inference materially affects later work, it should be validated through:

- owner discussion
- the capability that owns the resulting decision
- or direct evidence

Do not convert an inference into owner intent through repetition.

## Invariants

- evidence and interpretation remain distinguishable
- source boundaries remain visible
- frequency does not imply desirability
- references do not imply owner preference
- absence does not automatically imply intent
- conflicts remain visible
- unsupported conclusions remain open
- Brainstorm analysis does not own downstream decisions
- analysis does not extend beyond what is useful to the current exploration
