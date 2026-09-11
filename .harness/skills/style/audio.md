# Style Audio

Defines what the user should hear and the values that establish that audio character.

## Define

Specify the auditory character required by the current goal.

This may include:

- sound identity
- timbre
- pitch relationships
- rhythm
- envelope
- duration
- loudness relationships
- silence
- layering
- transition character

Style Audio owns **what is heard**.

Domain/App own the event or interaction that causes feedback.

Tech owns how the sound is generated or played.

## Inputs

May consume:

- audio Style reference
- App feedback triggers
- Domain events where relevant
- current goal
- Brainstorm findings
- existing Style specification

## Outputs

Authoritative audio rules, values, exceptions, deliberate silence, and open decisions where genuinely unresolved.

## Owns

May modify audio portions of:

the affected Style Spec scope(s) selected by Spec Topology

## Method

For each auditory decision establish:

### Trigger reference

Identify the already-owned event or interaction that calls for audio feedback.

### Rule

State whether sound occurs, does not occur, differs by perceptual state, layers, or deliberately reuses another sound.

### Value

Define the auditory characteristics that make the sound what it is.

Do not choose APIs, libraries, synthesis engines, or file formats unless they are themselves a Tech decision.

## Modes

No separate modes. Invoking the skill creates or revises only the auditory decisions required by the current goal.

## Approval

No separate lifecycle approval is expected. Owner validation is required for genuinely new perceptual character decisions; routine translation of an accepted reference into craft values does not create a release checkpoint.

## Completion

Complete when:

- every relevant sound decision is specified
- deliberate silence is explicit where meaningful
- concrete audio values needed by implementation are defined
- values have one intended implementation source of truth
- Preview can demonstrate them, or the gap is explicitly named

## Invariants

- audio Style describes perception, not production
- trigger ownership remains in Domain/App
- silence can be an intentional Style rule
- audio reference need not match visual reference
- no speculative sound system beyond the current goal
