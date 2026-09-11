# Harness

Maintains the Harness's own operating model.

This is a support family, not a capability: it owns no Project artifact, which is the boundary the capability contract exists to police. It is therefore shaped lighter than that contract requires.

## Constitution

**[BOUNDARY-01]** The Harness owns **how work is governed**: workflow, composition, routing, lifecycle semantics, contracts, mechanisms, universal Guides, Harness support definitions, deterministic repository mechanics, agent adapters, and Harness Assurance. The Project side owns **contextual project concerns and artifacts**: current intent and project-specific specifications/decisions are Project authority; implementation, tests, repository state, and other evidence are Project state/evidence evaluated against that authority; environment/setup facts belong to the relevant Project concern. Harness skills may operationally own these Project artifacts without turning their project-specific contents into Harness rules.

The Harness may provide universal judgment through Guides. That does not make a Guide a Project specification, and Project evidence does not become authority merely by existing.

**[BOUNDARY-02]** Project authority cannot redefine Harness operation. A Project document may specialize or deliberately depart from a universal Guide only where that Project authority owns the same Project concern; it cannot override Workflow, Lifecycle, Routing, contracts, approval semantics, or another Harness-owned concern. Conversely, the Harness does not invent Project truth merely to make work convenient.

This is a jurisdiction boundary, not a claim that the Harness is opinionless.

## Owns

`.harness/**` except the technology entries under `.harness/knowledge/`, plus the repository-root agent entrypoints and the agent-side skill wrappers to the extent of keeping them thin.

`.harness/skills/harness/change.md` declares that ownership precisely; this definition does not restate it.

## Does not own

- Project specifications, implementation, tests, and environment truth
- Goal and Session lifecycle state
- reusable technology knowledge entries, which Knowledge Capture owns
- whether a Harness design change should be made, which is the owner's and proceeds as a bounded Goal after approval

## Universal Guides

`.harness/guides/definition.md` defines Guides as universal Harness judgment. Project-specific departures remain Project authority and do not silently weaken the Guide itself.

## Skills

- **Harness Change** — `repair` corrects the Harness without changing what it decides; `design` applies an owner-approved change to what it decides.

## Discovery belongs to Sanity

Sanity Harness Check finds internal `.harness/` consistency and structure problems and routes them here. Sanity Repository Check owns repository-level structural checks outside that Harness-internal boundary. Neither Sanity check belongs to this family.

[Harness Limitations](../harness-limitations.md) defines the supported operating boundary. [Harness Assurance](../harness-assurance.md) defines profile-qualified evidence/status reporting and the accepted-risk register for the Harness itself. Neither grades the quality of a Project managed by the Harness.

## Invariants

- Harness and Project authority remain jurisdictionally distinct
- universal Guides remain Harness authority without becoming Project truth
- discovery and editing stay separate: Sanity finds, this family edits
- the Harness never manufactures Project truth
- a change to what the Harness decides reaches this family already approved
