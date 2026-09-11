# Software Design

Defines universal standing preferences for how implementation is structured, tested, and kept inspectable.

This Guide follows [Guides](definition.md): its rules should remain useful across substantially different projects. Project-specific architecture belongs in Tech. Where Tech explicitly owns a same-concern departure, that Project decision governs the Project without changing this Guide; where Tech is silent, this Guide governs implementation-design judgment and specializes General Guidelines.

## Belonging test

A rule belongs here when it would remain useful on another project.

If it names:

- a technology
- a project-specific store
- a domain concept
- a project-specific architecture

it belongs in Tech instead.

## Rule shape

Strong design rules must expose their boundary.

Prefer rules that state:

- the desired property
- the normal technique
- when that technique is not worth its cost

---

# Structure

## Build modular

A useful unit can be tested and replaced without opening unrelated neighbours.

A file boundary alone does not make something modular.

## Single responsibility

Prefer one reason to change at each meaningful level.

A useful test is whether the responsibility can be named without “and”.

Do not split things that necessarily change together merely to satisfy the wording.

## Keep domain decisions independently testable

Domain behavior should remain testable without requiring infrastructure.

Prefer plain data and explicit seams around concerns such as:

- storage
- network
- filesystem
- clock
- rendering
- external services

Do not introduce an interface merely to create architectural ceremony where no independently testable behavior benefits from it.

## Time is an input

Behavior depending on time should receive time through an explicit seam.

Important behavior should not obtain “now” invisibly.

## Keep computation outside rendering

Rendering should consume decisions rather than contain unrelated computation.

Replacing a renderer should not imply rewriting domain or interaction logic.

## Commands change; queries answer

A call should not combine a caller-visible state change with the semantics of a question.

Invisible internal mutation such as caching is acceptable where it does not alter caller-visible semantics.

## Centralize meaningful read semantics

Where filtering, projection, visibility, or interpretation of canonical state carries business or application meaning, give it an intentional seam.

Do not let every consumer reinvent the same read rule.

Do not introduce projection machinery where state and consumption are trivial.

## DRY decisions, not resemblance

Deduplicate a rule when multiple places must agree on one decision.

Do not couple unrelated code merely because its current implementation happens to look similar.

## Treat mutable global state as suspect

Constants may be globally shared.

Other process-wide state needs explicit ownership and lifetime justification.

## Fail loudly where failure is cheap

Reject invalid internal state early when continuing would produce a plausible but incorrect result.

## Keep the core understandable

Prefer essential behavior that can be understood without reconstructing excessive indirection.

Complexity must earn its place.

---

# Testing

## Name tests after behavior

A failing test should communicate what behavior broke before the reader opens implementation code.

## Organize tests for findability

Tests need not mirror source layout.

Mirror only where doing so materially helps expose missing coverage.

## Prove behavior at the lowest truthful layer

Place behavioral coverage at the lowest layer that can genuinely prove the behavior.

Use surface tests for:

- wiring
- rendering
- integration
- interaction behavior that genuinely exists only at the surface

Do not use expensive surface tests for behavior a lower layer can prove just as truthfully.

Do not force genuine surface behavior into lower-level abstractions that can pass while the real product remains wrong.

## Independent expectations prove generated data

Checking generated output against the same logic that generated it proves consistency, not correctness.

Where correctness matters, use expected evidence independent from the generator.

If no independent source exists, make that limitation visible.

## Make nondeterminism reproducible

Seed randomness where tests depend on it.

Break equally valid ties deterministically rather than through incidental ordering.

---

# Development Affordances

## Build useful dev-only affordances

Examples:

- fixed fixture state
- preview pages
- inspection surfaces
- debugging entry points

Prefer using real project code so the affordance exposes drift rather than hiding it.

## Gate them

Developer affordances must not silently ship enabled in production.

## Test through the gate

If a production gate also makes an affordance unreachable to the normal test suite, provide an explicit development/test entry path.

Do not remove the protection merely to make the test easy.

## Document affordances when created

Record how to reach developer affordances as part of building them.

They are otherwise easy to forget and difficult to rediscover.

---

# Exceptions

When implementation deliberately departs from this guide:

1. identify the relevant rule
2. establish why this project is different
3. record the project-specific architecture decision in Tech when appropriate

A quiet departure becomes an accidental rule.
