# App Story Map

Defines the minimum user activity required by the current goal.

## Define

Describe what a user does in the product as:

1. **Activities**
2. **Steps**
3. **Details**

Use story mapping to establish user behavior before deciding where or how it surfaces.

## Inputs

May consume:

- current Goal
- Domain specification
- Brainstorm findings
- existing App specification
- owner intent

## Outputs

An authoritative user story map.

## Owns

May modify the story-map portion of:

the affected App Spec scope(s) selected by Spec Topology

## Method

### Minimum at every level

Every level contains the minimum needed to complete the level above.

Ask:

- Does this detail need to exist for the step to be complete?
- Does this step need to exist for the activity to be complete?
- Does this activity need to exist for the current goal to be complete?

If removing an item still leaves its parent complete, the item does not belong in the current iteration.

### Minimal extension

Do not pre-design later iterations.

The next iteration should extend the story map minimally from what exists.

### User, not developer

Activities represent what a product user does.

Developer workflows and development affordances do not belong in the story map.

## Modes

No separate modes. Invoking the skill creates or minimally revises the story map needed by the current goal.

## Approval

No separate lifecycle approval is expected. Owner validation is required only where the story map would otherwise invent user intent; normal acceptance remains at the Goal landing boundary.

## Completion

Complete when:

- the current goal's user capability is represented
- each activity has the minimum required steps
- each step has the minimum required details
- no activity extends beyond the current Goal
- downstream Interaction and Surfaces work has enough structure to proceed

## Invariants

- activities describe user outcomes
- steps describe user progression
- details are discrete interactions
- every level is minimal
- future behavior is not specified merely because it is foreseeable
- developer activity is excluded
