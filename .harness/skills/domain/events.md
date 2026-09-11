# Domain Events

Models meaningful domain events, their causes, ordering, and effects.

Event storming is the primary method.

## Define

Describe what happens in the domain and how one meaningful change leads to another.

Use when the goal changes or introduces domain flow.

## Inputs

May consume:

- current goal
- Domain language
- brainstorm material
- existing rules
- existing data model

## Outputs

An authoritative domain event flow.

## Owns

May modify the event/flow portions of:

the affected Domain Spec scope(s) selected by Spec Topology

## Method

Use high-level event storming.

For each meaningful event establish:

- what happened
- what caused it
- what state changed
- what may consume or react to the result

Prefer event names that describe the occurrence itself, not merely one resulting effect.

## Flow scrutiny

Walk the flow end to end.

For each step ask:

- what starts this?
- what happened?
- what changed?
- what consumes or enables the result?

A step with no cause is a finding.

A result that nothing uses is a finding.

A missing transition is a finding.

## Modes

No separate modes. Invoking the skill creates or revises the event flow needed by the current goal.

## Approval

No separate lifecycle approval is expected. Harness-proposed domain meaning or event naming requires owner validation before it becomes authoritative.

## Completion

Complete when the relevant flow connects end to end for the current goal.

Do not model unrelated future flows.

## Invariants

- events describe occurrences, not UI actions
- names describe what happened rather than one selected effect
- every modeled step has a cause
- every meaningful result has a place in the flow or is explicitly terminal
- event storming does not become App story mapping
