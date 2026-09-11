# Build Check

Verifies implementation against its owning decisions and the evidence used to claim completion.

## Define

Establish whether executable work is actually complete.

May run after implementation, repair, proof, or independently during sanity checking.

## Checks

### Design

Implementation conforms to Software Design and project Tech rules.

### Behavioral coverage

Tests sit at the lowest layer that can truthfully prove the claimed behavior.

### Artifact verification

Verify the actual artifact through the appropriate repeatable suite.

### Check validity

For a new high-value check whose ability to detect the defect is not otherwise established, demonstrate that it detects a meaningful failure.

Do not ritualistically mutate every test.

### Safe mutation

When intentionally altering code to prove a check:

- preserve the unmutated version
- never use a revert method that may destroy uncommitted work
- finish with a successful unmutated run

### Silent failures

When a tool/environment claims success while producing the wrong result, record:

- what claimed success
- what actually happened
- the check that distinguishes the two

Route generic environment behavior to setup documentation.

Route technology-specific behavior to technology lessons.

## Inputs

Required:

- current repository state
- the implementation or proof being checked
- its owning goal/specification or bounded proof question; if product behavior has no owner, route through Build Implement/owning capability rather than treating Build Check as orphan-discovery

As relevant:

- Software Design guide
- project Tech rules
- test/build/deployment suites

## Outputs

Either `no change` / `passes` or evidence-backed implementation findings. It may also route silent tooling/environment failures to Setup or Knowledge.

## Owns

No durable product or specification state. Build Check may create transient mutation/evidence state while checking, but must restore it.

Build Check uniquely owns closure/deletion of Build's shared temporary `doc/scratchpad/`; it may delete that directory only after all findings in it are resolved or routed. It does not own the implementation/specification fixes those findings require.

## Modes

### `check`

Run the relevant executable checks for the bounded work. There are no partial modes that silently lower the completion bar.

### `close`

Close Build temporary working state.

Preconditions:

- Build Check has established that every `doc/scratchpad/` finding is resolved or routed
- no remaining work depends on the scratchpad state

Then delete `doc/scratchpad/` if it exists.

If unresolved findings remain, do not clear them; route the work instead.

## Approval

No approval merely to run or pass Build Check. User validation is governed by Goal and Branch Land when the result exposes something meaningful to inspect.

## Completion

For `check`, complete when:

- behavior matches authority
- design constraints hold
- meaningful checks pass
- test evidence is trustworthy
- deliberate mutations are restored
- discovered tooling failures are routed

For `close`, complete when `doc/scratchpad/` is absent and no unresolved finding was discarded.

## Invariants

- Build Check can run independently
- a green suite is evidence only for what it can distinguish
- design departures are explicit
- silent failures become recorded knowledge
- scratchpad closure never discards unresolved work
