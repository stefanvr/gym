# Personal Note

## Define
Capture or review developer-local reminders and ideas without turning them into Project state, a roadmap, or Goal work.

## Inputs
A note to capture, or an explicit owner request to review/prune personal notes.

## Outputs
Optional local `doc/notes.md` content.

## Owns
Only `doc/notes.md`, which is ignored by Git and never Project authority.

## Modes
### `add`
Append or fold a concise personal note.
### `review`
Read notes only because the owner explicitly requested it.
### `prune`
Remove or consolidate stale local notes at the owner's request.

## Completion
The requested note operation is complete without changing Project authority or Goal state.

## Approval
No approval expected; promotion of a note into Goal work is a separate explicit owner decision.

## Invariants
- notes never enter Git history
- notes are never auto-loaded into agent context
- notes are not a backlog, roadmap, or Project authority
- note existence never implies priority or planned work
- promotion to Goal is explicit
