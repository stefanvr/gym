# Continuity

Optimizes session restart and token use without creating another source of truth.

## Principle

Persist authority.

Cache pointers.

Load context by need.

## Skills

- **Session Checkpoint** — optionally writes/clears `doc/session.md` when transient context would otherwise be lost.
- **Session Resume** — reconstructs trustworthy context after a new/cleared session and never treats the pointer as authority.

## Context layers

### Layer 1 — always

`.harness/workflow/context-manifest.yaml` owns Layer 1 membership. Load every path in its `always` set and inspect every state source in its `always_state` set; do not maintain a partial duplicate here. Session Resume owns the reconstruction order.

### Layer 2 — current capability

Load only:

- relevant guide
- current skill
- owning specification(s)

### Layer 3 — conditional

Load only when triggered:

- technology knowledge
- setup documentation
- neighboring capability specs required by the current decision

## Before a deliberate clear/handoff

If meaningful transient state is not recoverable from Git, the branch-derived Goal file, or specifications, run Session Checkpoint `update`.

If everything important is already authoritative, do not create a session pointer merely for ceremony.

## Restart

Session Resume owns the restart procedure and uses Deterministic Runtime `resume` as the mechanical Git/ref/transaction source. Follow `.harness/skills/continuity/resume.md`; do not maintain a second restart or Git-state reconstruction checklist here.

Session state is a pointer/cache, never authority.
