# Story Mapping

App/product-structure method for understanding user activities, progression, slices, and outcome-oriented sequencing before authoritative App structure is written.

## Purpose

Use a story map to make the user's journey and the minimum useful slices visible, especially when a Goal spans several activities or when sequence and release slicing are unclear.

This method is broader than the authoritative App Story Map skill. The method explores and structures candidates; App Story Map remains the authority-editing skill for accepted user activity/step/detail structure.

## Inputs

May consume:

- current Goal
- current App authority
- relevant Domain authority
- owner/user intent
- Interview Me findings
- existing product behavior

## Working outputs

Prefer transient mapping where practical.

When durable working state is useful, Story Mapping may create non-authoritative material under:

`doc/working/story-mapping/`

A working map may contain:

- backbone activities
- user steps
- candidate details/stories
- walking skeleton
- outcome slices or releases
- assumptions/questions
- dependency or sequencing notes

## Authority interaction

Story Mapping owns no App authority state.

Accepted user activities/steps/details route through the App orchestrator to App Story Map. Interaction details route to App Interaction; surface/location conclusions route to App Surfaces. Domain rules, Style decisions, and Tech constraints remain owned elsewhere.

## Invocation

Use when the product behavior needs discovery, sequencing, minimum slicing, or whole-journey context before one App skill can safely edit authority.

For a narrow already-understood change to activities/steps/details, invoke App Story Map directly.

## Method

1. state the user outcome relevant to the current Goal
2. identify the smallest meaningful backbone of user activities
3. order the steps a user takes through those activities
4. add only details that clarify completion or meaningful alternatives
5. identify a walking skeleton/minimum coherent slice
6. form additional slices only when they represent meaningful outcome increments
7. surface dependencies, assumptions, and gaps rather than hiding them
8. separate user behavior from implementation tasks and perceptual styling
9. route accepted structure to App authority skills

## Completion

Complete when the current Goal has a coherent user journey/slice model sufficient for App authority work, and important assumptions or unresolved slices are explicit.

## Invariants

- activities describe user outcomes, not developer tasks
- slices are outcome-oriented rather than arbitrary implementation batches
- future behavior is not pulled into the current Goal merely because it appears on the map
- Story Mapping does not own App truth
- Domain, Style, and Tech concerns remain routed to their owners
