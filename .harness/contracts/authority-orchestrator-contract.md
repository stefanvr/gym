# Authority Orchestrator Contract

Defines the shared contract for a Project authority that coordinates work inside its jurisdiction.

An authority orchestrator is still the same authority-owning capability. It is not a new layer of Project truth and does not replace its narrow skills.

## Purpose

An authority orchestrator accepts work whose concern is clearly inside one Project authority but is too broad or ambiguous to route safely to one narrow skill up front.

**[ORCH-01]** When a Project concern has a clear authority owner but premature narrow-skill classification would risk missing materially related concerns inside that authority, route through the authority orchestrator. The orchestrator may delegate, but accepted Project truth remains owned by the same authority and its authority-editing skills.

It must:

1. establish the relevant part of the current Goal
2. inspect current authority and relevant evidence
3. identify the stable authority scope(s) affected by the requested outcome using the active Project model
4. load only those scopes plus the Project-model dependency closure needed to interpret them
5. choose only the methods and narrow skills useful to resolve those areas
6. keep method output as working material until accepted through an owning authority skill
7. reconcile narrow-skill outputs inside the authority boundary
8. apply Change Impact when authoritative meaning changes, using Project-model reverse dependencies as candidates where available
9. run the authority check before dependent completion where the Goal materially changed that authority
10. route concerns belonging to another authority instead of deciding them incidentally

## Authority boundary

The orchestrator owns no additional artifact beyond the capability's existing ownership declaration.

A child skill may narrow ownership. A method may own non-authoritative working material. Neither broad orchestration nor method use creates a second source of Project truth.

## Method selection

Activated method packs are optional tools, not mandatory phases.

Use a method only when its technique materially improves the current work. An orchestrator must remain able to perform ordinary narrow work without requiring every activated method.

An inactive method pack is not invoked merely because its definition is shipped in the Harness.

## Promotion

A method can elicit, model, analyse, structure, pressure-test, or propose. Its conclusions become Project authority only when the capability's owning skill incorporates them into the authoritative artifact under that skill's normal scrutiny and owner-validation rules.

Do not copy a method artifact wholesale into authority merely to complete the method.

## Cross-authority work

If a concern spans several Project authorities, route through the active cross-authority coordination method when appropriate (Design in the default composition), or route the concerns separately through normal Routing.

Each authority remains responsible for its own resulting truth. Cross-authority coordination never becomes an authority above Domain/App/Style/Tech.

## Completion

Orchestration for an authority is complete when:

- affected concerns inside that authority have been resolved or explicitly left open
- accepted conclusions live in their owning authoritative artifact
- method-only working state is not being treated as authority
- relevant cross-authority impacts have been routed
- required Change Impact has been applied
- the authority's check has been re-established where materially affected

## Invariants

- one Project concern still has one authority owner
- stable Project-model scope identity is not inferred from file location
- orchestration coordinates; it does not duplicate child procedures
- methods never become Project authority by implication
- methods are selected for fit, not executed as a mandatory pipeline
- broad intake does not justify work outside the current Goal
- cross-authority coordination cannot override an authority-owning capability
