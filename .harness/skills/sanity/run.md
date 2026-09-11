# Sanity Run

Orchestrates the independent checks that make up a Sanity pass.

## Define

Run the appropriate Sanity checks for the current request/context, preserve each check's ownership, and return one evidence-backed routed finding set.

Use this skill for `run sanity`, a general consistency pass, or when several Sanity checks should be coordinated. Invoke an individual check directly when only that concern is requested.

## Inputs

Required:

- current repository state; when Git exists, Deterministic Runtime `resume` facts for selected checks that need lifecycle transactions
- requested Sanity scope, or enough context to select the default run
- the Sanity Finding test

As applicable:

- relevant specifications, implementation, tests, setup documents, and knowledge entries required by the checks that actually run

## Outputs

One grouped Sanity result containing the outputs of the selected checks. Findings remain owned by the check/capability that discovered them and are grouped by repair owner.

## Owns

No durable project state or fixes. Owns only orchestration of the run and aggregation/routing of its findings.

## Modes

### `run`

Run the default or explicitly narrowed Sanity pass.

## Method

### Default run

Unless the request is narrower, run in this order:

1. Specification Check
2. Trace Check
3. Repository Check

Harness Check is not part of the default Sanity pass. Invoke it directly when harness consistency is the requested concern. Harness Change owns re-running the affected Harness Check concern after harness maintenance.

### Trigger-driven checks

Setup and Knowledge checks are not part of every default run. Invoke them only when their trigger is present:

- Setup Dev `check` when `doc/setup-dev-env.md` exists and development setup may have drifted, especially after dependency/toolchain/environment changes or when reproducible onboarding is being relied upon.
- Setup App `check` when `doc/setup-app-env.md` exists and runtime/deployment/hosting setup may have drifted, especially before a release affected by those concerns.
- Knowledge Check when a knowledge entry changed, observed behavior conflicts with loaded knowledge, a materially relied-upon learning needs freshness/validity checking, or dedicated knowledge maintenance was requested.

Knowledge Check is not a blanket web-freshness scan on every Sanity run.

Do not reimplement the invoked checks. Preserve their findings and ownership.

## Completion

Complete when:

- every selected core check has run
- every trigger-driven check required by the current context has run
- findings are evidenced
- every finding has a repair owner
- unresolved findings remain visible
- Sanity Run has not silently repaired them

## Approval

No approval. Sanity discovers state; owning skills govern any later fixes or validation.

## Invariants

- individual checks retain their own scrutiny and finding ownership
- trigger-driven checks run because their trigger exists, not by ritual
- no finding is converted into a fix inside Sanity Run
- narrower requested runs do not expand without reason
