# Event Storming

Domain discovery/modelling method for understanding meaningful domain behavior before authoritative Domain conclusions are written.

## Purpose

Use event-centred exploration to expose what happens in the domain, why it happens, who or what initiates it, policies and decisions between events, relevant state boundaries, read needs, and unresolved hotspots.

This method is broader than the authoritative Domain Events skill. It helps discover candidate Domain meaning; Domain Language, Events, Rules, and Data remain the authority-editing skills.

## Inputs

May consume:

- current Goal
- current Domain authority
- owner/expert input
- existing Domain terminology, rules, events, and data
- implementation/evidence when it reveals current behavior or uncertainty
- Interview Me output

## Working outputs

Prefer a transient modelling surface during exploration.

When durable workshop state is useful, Event Storming may create non-authoritative working material under:

`doc/working/event-storming/`

Useful elements may include:

- domain events
- commands or initiating intents
- actors/roles/systems
- policies/reactions
- candidate aggregates or consistency boundaries
- read-model/information needs
- external systems
- hotspots/questions

These labels are modelling aids, not mandatory permanent Domain document sections.

## Authority interaction

Event Storming owns no Domain specification state.

Accepted conclusions route to the Domain orchestrator, which promotes them through Domain Language, Domain Events, Domain Rules, and/or Domain Data as appropriate.

Workshop notation must not be copied wholesale into Domain authority merely because the workshop completed.

## Invocation

Use when domain behavior is consequential, poorly understood, spans several rules/events, or would benefit from seeing causal flow before individual Domain skills edit authority.

For a narrow, already-understood event change, invoke Domain Events directly instead.

## Method

1. establish the Goal slice being explored
2. place meaningful past-tense domain events in causal order
3. identify what initiates each event and what decision/rule permits it
4. identify actors or external systems where their participation matters
5. expose policies/reactions that connect one event to later behavior
6. note state/consistency boundaries only when they clarify rules; do not force aggregate design prematurely
7. identify information/read needs separately from command-side behavior where useful
8. mark hotspots, contradictions, missing causes, and unresolved terminology explicitly
9. finish by routing accepted conclusions to the appropriate Domain authority skills

## Completion

Complete when the relevant behavior can be explained end to end well enough for Domain authority work, major hotspots are explicit, and each accepted modelling conclusion has a clear owning Domain skill.

## Invariants

- events describe domain occurrences rather than UI actions
- modelling aids do not become architecture decisions by default
- unresolved hotspots remain visible
- Event Storming does not own Domain truth
- App flow and Style decisions are routed rather than absorbed into the Domain model
- only the current Goal slice is explored unless explicitly broadened
