# Guides

Defines the role of Harness Guides.

Guides are **Harness-owned universal judgment**: principles intended to remain useful across substantially different projects. They govern how the Harness reasons when project authority has not already settled the same concern.

They are not project specifications and do not become project truth merely because they are universal.

## Boundary

**[GUIDE-01]** A rule belongs in a Guide only when it is intended to remain useful across materially different projects. Technology-, domain-, product-, environment-, or architecture-specific truth belongs to the Project owner for that concern instead.

**[GUIDE-02]** Explicit Project authority may specialize or deliberately depart from a Guide when that Project authority owns the same concern. The departure governs that Project; it does not weaken, rewrite, or silently fork the universal Guide.

Universality is an authority property, not a context-loading policy. Load Guides by need through the context manifest rather than preloading all of them.

## Relation to authority

Routing determines the concern and its owner before same-subject precedence is considered. Project authority can therefore specialize a Guide only inside Project jurisdiction; it cannot redefine Harness workflow, lifecycle, routing, contracts, or other Harness-owned operation.

Where the Project is silent on a concern governed by a specialized Guide, that Guide applies. Where no specialized Guide applies, General provides the universal fallback judgment.

## Belonging test

Before adding a Guide rule, ask:

- Would this still be useful on a substantially different project?
- Does it rule out or prefer something in a way that can change a decision?
- Is it independent of a specific technology, product/domain fact, deployment environment, or project architecture?
- Is this judgment already authoritative somewhere else?

If the answer depends on project context, route it to the Project owner instead.

## Change rule

Guides are Harness authority. A change to what a Guide decides is a Harness Change `design`; a consistency correction is Harness Change `repair`.

A Project exception never edits a Guide as a side effect.

## Invariants

- Guide rules are universal Harness judgment, not project facts.
- Project-specific departures are explicit and owned by the Project concern that needs them.
- One universal rule has one authoritative source.
- Universal does not mean always loaded.
