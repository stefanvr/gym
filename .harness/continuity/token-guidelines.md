# Token and Context Guidelines

## Load by need

Do not preload the entire harness.

Use the routing manifest to find the smallest relevant context set.

## Avoid repeated policy

Skills should point to shared Guides/Mechanisms rather than restating them.

## Compact skills still obey the Skill Contract

The [Task / Capability Skill Contract](../contracts/task-capability-skill-contract.md) is the authority for skill shape. It owns which sections a skill must answer, which are optional, and what they are called.

Compactness comes from short answers, including explicit `no durable state` or `no separate modes` where true. It never comes from omitting a required boundary, or from renaming one to make a skill look smaller.

## Keep session state small

Session state stores pointers and current unresolved transient work.

Do not copy:

- full specifications
- full history
- completed task lists
- general rules already owned elsewhere

## Trust authority, verify cache

A restart note saying work is complete is not proof.

Use Deterministic Runtime/repository/spec/check state to verify before continuing. Do not spend context reconstructing approval refs, ancestry, landing phases that runtime `resume` computes deterministically.
