# App Interaction

Defines how users perform App steps and how the application responds structurally.

## Authority target

Follow the [Project Authority Target Contract](../../contracts/project-authority-target-contract.md). Under `spec`, edit/check the affected stable Spec scope(s). Under `repository-native`, edit/check the corresponding section of the current transient Goal Spec and relevant named native constraints. Any scope-ID, Spec Topology, reverse-dependency, or scoped identifier requirement below is `spec`-only unless the repository already uses an equivalent native identifier deliberately.


## Define

For each relevant Story Map step, define:

- how the user initiates it
- what interaction occurs
- what application state or surface response follows
- where feedback is triggered when behavior requires it

Interaction owns **when and why** user-facing feedback occurs.

It does not own what that feedback looks or sounds like, nor how it is technically implemented.

## Inputs

May consume:

- App Story Map
- Domain rules and events
- current goal
- existing App specification
- Brainstorm material
- owner intent

## Outputs

Authoritative interaction behavior for relevant user steps.

## Owns

May modify interaction portions of:

the active App authority target

## Method

For each relevant step establish:

1. what starts the interaction
2. what input or action the user supplies
3. what the application does in response
4. what state changes from the user's perspective
5. what becomes possible next
6. whether visual, audio, or animated feedback is triggered

## Interaction boundary

App may state:

- an error receives visible feedback
- completion triggers a sound
- opening something transitions into another mode
- an action must work without a mouse

App does not decide:

- the color of the error
- which sound plays
- animation easing
- rendering framework
- audio API

## Modes

No separate modes. Invoking the skill creates or revises the interaction portion required by the current goal; creation versus revision does not change the operation.

## Approval

No separate lifecycle approval is expected. When the interaction contains a meaningful unresolved product choice, validate that choice with the owner before recording it; otherwise accumulate toward Goal completion and landing approval.

## Completion

Complete when every relevant Story Map step has enough interaction definition that implementation does not need to invent user behavior.

## Invariants

- every specified interaction serves an existing step
- interaction does not invent Domain rules
- interaction defines feedback triggers, not Style
- interaction defines behavior, not implementation technology
- input assumptions are explicit where they affect user capability
