# Method Pack Contract

Defines first-class optional methods used by authority-owning orchestrators.

A method pack is a reusable way of discovering, eliciting, modelling, structuring, or coordinating work. It is deliberately separate from Project authority.

## Activation

Method packs are selected through `.harness/composition/active.json`.

- zero or more supported method packs may be active
- only active packs are first-class named methods for current work
- shipping a method definition does not activate it
- deactivating a method changes available technique, not existing Project truth
- Project and Collaboration model selection remain independent of method activation

## Required definition

Every method definition explicitly answers:

- Purpose
- Inputs
- Working outputs
- Authority interaction
- Invocation
- Method
- Completion
- Invariants

A method may additionally define durable working-state ownership when useful. Such state must be clearly non-authoritative.

## Working outputs

Method outputs are evidence or working material. They may include interview notes, workshop maps, candidate structures, questions, hotspots, alternatives, or coordination plans.

**[METHOD-01]** A method output never becomes Project authority merely because the method completed or because its artifact exists. Accepted meaning must be promoted through the Project authority that owns that concern.

A method should avoid durable output when transient working state is sufficient. If durable working output is useful, its path must not overlap an authoritative Project artifact.

## Authority interaction

Methods do not own Domain, App, Style, Tech, Goal, lifecycle, or Harness policy.

A method may:

- surface candidates for several authorities
- ask for owner clarification
- pass structured findings to an authority orchestrator or narrow authority skill
- identify uncertainty or contradiction
- recommend which authority should decide next

A method must not:

- silently promote a candidate into a specification
- redefine another authority's invariant
- treat workshop notation as permanent authority by default
- create a new approval boundary merely because a technique has stages

## Invocation

Authority orchestrators select methods based on fit. A broad concern may enter an orchestrator first and be decomposed there rather than requiring Routing to predict every narrow skill before the concern is understood.

A directly requested active method may be invoked when the request is itself method-shaped, but resulting Project conclusions still route to their owner.

## Composition independence

Method packs may declare which Project models or authorities they integrate with. The method contract itself remains kernel-level: method output is non-authoritative regardless of Project model.

A Project model is not required to imitate the Spec model merely to use a method pack.

## Invariants

- method activation is explicit composition
- inactive methods are not silently invoked as named Harness procedures
- method outputs remain non-authoritative until promoted by an owner
- method working artifacts never overlap authoritative artifact ownership
- method completion does not imply Goal completion
- methods may coordinate several authorities but never outrank them
