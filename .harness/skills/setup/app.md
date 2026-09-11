# Setup App

Documents and verifies how the chosen application actually runs in its target environment and how to tell that it is running correctly.

## Define

Document and verify the project-specific operational steps required to run/deploy the chosen application in its target environment and to prove that it is actually running correctly.


## Source of truth

The content is project-specific and is often a consequence of Tech choices.

Do not assume the operational details are known when Tech makes the choice.

Build Proof or subsequent deployment/setup work may discover them.

## Content

May include:

- runtime model
- deployment path
- external service configuration
- environment variables/secrets by name
- hosting/provider setup
- one-time manual actions
- production verification
- rollback/recovery steps where required by current goals

## Manual boundaries

Explicitly mark actions requiring:

- human authority
- provider UI
- privilege
- secrets/credentials
- physical device access
- approvals outside the repository

For each, record:

1. who performs it
2. why automation cannot/should not
3. exact action
4. expected resulting state
5. verification

## Verification

Prefer verification against the actual resulting artifact/service rather than only the control-plane claim.

## Inputs

Required:

- chosen Tech/runtime architecture relevant to deployment
- verified operational findings from Build Proof or real setup/deployment work

As relevant: provider/service state, existing app setup doc, manual-boundary information, and reusable Knowledge.

## Outputs

A verified/updateable `doc/setup-app-env.md` describing runtime/deployment preparation, manual boundaries, and observable verification.

## Owns

`doc/setup-app-env.md`. It does not own Tech choices, product specifications, provider state, or reusable cross-project Knowledge.

## Modes

### `document`

Create or update app/runtime setup instructions from verified operational knowledge.

### `check`

Verify the current target environment against the documented setup without silently changing architecture decisions.

## Approval

No approval for documentation/checking. A required human/provider/privileged action is an execution boundary, not an approval; Tech decisions discovered during setup route to Tech.

## Invariants

- operational facts are verified rather than inferred from Tech alone
- Workflow manual boundaries are explicit in the setup artifact
- secrets are named by requirement, never committed
- verify resulting artifact/service where practical

## Completion

Complete when required runtime setup is either verified or explicitly blocked on a named manual step.
