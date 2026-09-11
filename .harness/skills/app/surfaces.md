# App Surfaces

Defines the structural places where user interaction occurs.

## Define

Establish which user-facing surfaces exist and which interactions live on them.

A surface may be:

- screen
- page
- panel
- dialog
- overlay
- persistent chrome
- application mode
- another structurally distinct interaction area

The skill defines structure, not visual styling.

## Inputs

May consume:

- App Story Map
- App Interaction
- current goal
- existing App specification
- platform constraints from Tech

## Outputs

An authoritative structural surface model.

May define:

- which surfaces exist
- which modes exist
- where steps occur
- persistent vs temporary surfaces
- presence of structural chrome
- meaningful size/form-factor modes
- transitions between surfaces

## Owns

May modify structural surface portions of:

the affected App Spec scope(s) selected by Spec Topology

## Method

Start from interaction.

For each step ask:

- where does this happen?
- does the required surface already exist?
- does this require a distinct mode?
- what persists while the user moves through the activity?
- what structural chrome must always or conditionally exist?
- does a meaningful form-factor difference require another structural mode?

Create only surfaces required by current user behavior.

## Structural vs visual

Surfaces may specify:

- header exists
- footer is persistent
- menu contains an entry
- small and large modes differ structurally
- profile action appears in persistent chrome

Surfaces do not specify:

- exact spacing
- color
- typography
- visual balance
- logo aesthetics
- animation character

Those belong to Style.

## Interaction loop

Interaction and Surfaces deliberately revise one another.

## Modes

No separate modes. Invoking the skill creates or revises the structural surfaces required by current interactions.

## Approval

No separate lifecycle approval is expected. Validate a meaningful unresolved product-structure choice with the owner before recording it; do not manufacture a checkpoint for routine structural completion.

## Completion

Complete when:

- every relevant interaction has a surface
- every created surface serves current user behavior
- structural modes needed by the current goal are explicit
- implementation does not need to invent screen/surface structure

## Invariants

- no orphan surface
- no interaction without a surface
- structural layout belongs here
- visual composition belongs to Style
- surfaces are introduced only when required by current behavior
