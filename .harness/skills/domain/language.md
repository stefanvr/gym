# Domain Language

Establishes the words used consistently by the domain, specification, code, and tests.

## Authority target

Follow the [Project Authority Target Contract](../../contracts/project-authority-target-contract.md). Under `spec`, edit/check the affected stable Spec scope(s). Under `repository-native`, edit/check the corresponding section of the current transient Goal Spec and relevant named native constraints. Any scope-ID, Spec Topology, reverse-dependency, or scoped identifier requirement below is `spec`-only unless the repository already uses an equivalent native identifier deliberately.


## Define

Name domain concepts precisely enough that later rules, events, data, code, and tests can refer to the same thing.

## Inputs

May consume:

- current goal
- brainstorm findings
- existing Domain specification
- existing code or tests
- owner terminology
- outputs from Domain Events, Rules, or Data

## Outputs

Authoritative domain terms and their meanings.

## Owns

May modify the language section of:

the active Domain authority target

## Authorship stance

Choose before starting:

- `owner-led`
- `harness-proposed`
- `already-settled`

Proposed names must be put to the owner before they become authoritative.

## Method

1. Identify the concept that needs a name.
2. Prefer domain language over implementation language.
3. Ensure the name describes the thing itself rather than one incidental consequence.
4. Check how the term behaves when used by events, rules, and data.
5. Revise names when downstream use exposes a mismatch.
6. Remove proposal/provenance markers once the name is accepted.

## Modes

No separate execution modes. Authorship stance (`owner-led`, `harness-proposed`, `already-settled`) controls collaboration without changing the skill operation.

## Approval

No separate lifecycle approval is expected. A harness-proposed term must be confirmed by the owner before it becomes authoritative; that confirmation is part of specification work, not a release checkpoint.

## Completion

Language work is complete when:

- required concepts have usable names
- terms are internally distinct
- relevant rules/events/data can use them without ambiguity
- proposed names requiring owner validation have been resolved

A term is not considered stable merely because Language first introduced it.

It becomes settled after surviving the Domain activities that use it.

## Invariants

- approved terms are simply terms
- provenance does not survive into the specification
- do not preserve “coined”, “owner word”, or similar metadata
- terminology remains open to revision while Domain work is still exposing its meaning
