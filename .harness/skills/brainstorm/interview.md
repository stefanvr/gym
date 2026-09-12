# Brainstorm Interview

Extracts and explores an owner's thinking without supplying the product on their behalf.

## Define

Use conversation to uncover:

- intent
- preferences
- constraints
- possibilities
- tensions
- unknowns
- candidate goals

The outcome is trustworthy draft material with clear provenance.

Not a finished design.

## Inputs

Required:

- an area or idea to explore
- access to the owner

Optional:

- references
- screenshots
- examples
- existing brainstorms
- current specifications
- current Goal

## Outputs

Using the classes defined by the shared Provenance mechanism, draft findings may include:

- Said
- Suggested and accepted
- Open

May additionally identify:

- tensions
- free dimensions
- candidate goals
- constraints
- specification gaps

## Owns

By default owns no file. When temporary working material must survive context loss, may create:

`doc/brainstorm/<session>.md`

That path is Git-ignored and is not Project state.

Does not modify:

- current Goal
- Domain specification
- App specification
- Style specification
- Tech decisions

## Modes
### `run`

Conduct one exploration session.

## Method

### One topic at a time

Ask one meaningful question or closely related thread at a time.

Do not send a questionnaire when conversation can uncover the answer more reliably.

### Ask about the thing

Ask about the product, behavior, world, feeling, or constraint.

Do not ask the owner to design the harness artifact.

Route their answers yourself.

### Prefer grounded questions

Use existing references where possible.

Ask comparative or concrete questions before abstract blank-page questions.

### Suggestions stay suggestions

When the harness has a useful view:

1. present alternatives when useful
2. make a recommendation
3. wait for the owner

If accepted, record it as **Suggested and accepted**, never as **Said**.

### Follow information value

Dig where the owner:

- elaborates
- reacts strongly
- distinguishes examples
- identifies something as important

Stop pushing where the owner genuinely does not care.

Record that dimension as free.

### Chase goal edges

When something sounds like a goal, apply the shared Goals and Decisions guide.

Establish what would make it done.

Do not promote the candidate into the current Goal from inside this skill.

### Confirm interpretations

When interpretation matters, play it back before recording it as owner intent.

Do not retroactively convert an inference into something the owner supposedly said.

### Preserve tensions

If two wishes conflict, record both.

Do not resolve them merely to make the session coherent.

## Coverage

Do not use specification categories as the interview agenda.

Before ending, check whether useful material or significant gaps exist for:

- Domain
- App
- Style
- Tech constraints
- Goal candidates

Coverage is a final routing check, not a mandatory questionnaire.

## Approval

No lifecycle approval. Playback/confirmation of an interpretation is provenance validation—confirming what the owner meant—not approval to land or proceed.

## Completion

Complete when:

- the useful current thread has been explored
- important statements have reliable provenance
- tensions are explicit
- gaps are named
- candidate goals have identifiable edges or are marked unresolved
- downstream capabilities have enough signal to know what needs work next

## Invariants

- extract before supplying
- ask about the subject, not its destination document
- do not manufacture owner preference
- do not hide indifference
- do not silently resolve tensions
- do not settle technology choices
- do not create specifications
- do not create or widen the Goal
