# Knowledge Lookup

Loads reusable technology knowledge relevant to the current work.

## Define

Load only reusable technology knowledge that materially informs the current Tech, Proof, Setup, Build, or diagnostic question.

## Started
- Tech names a technology
- Build Proof is about to exercise a technology
- Setup is configuring a chosen technology
- a failure may match known technology behavior

## Method

1. Identify the named technology/tool.
2. Find matching knowledge entries.
3. Load only entries relevant to the current question.
4. Treat them as operational knowledge, not project decisions.
5. Surface constraints/traps that materially affect the current work.

## Inputs

Required:

- named technology/tool or a concrete failure suspected to match known behavior
- current question/goal

Optional: configured external knowledge-base location.

## Outputs

A bounded set of relevant operational constraints, traps, examples, and verification patterns supplied as context to the requesting skill.

## Owns

No durable state. Lookup reads knowledge and never copies it into project authority merely to make it locally convenient.

## Modes

### `lookup`

Retrieve relevant entries for the current question. Broad preloading is deliberately not a mode.

## Approval

No approval.

## Invariants

- load by named technology/current need
- knowledge is advisory operational memory, not project authority
- do not flood context with unrelated entries
- unresolved freshness is visible

## Completion

Complete when relevant known knowledge has been considered without flooding the session with unrelated entries.
