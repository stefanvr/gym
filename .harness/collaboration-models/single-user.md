# Single-user Collaboration Model

Defines the supported single-user lifecycle-collaboration model. Whether it is active is decided only by `.harness/composition/active.json`. Selecting it gives the simpler one-human/one-main-operator posture without changing Project truth ownership. Its assured operating profile is defined in [Harness Assurance](../harness-assurance.md).

This model supports one human authority working through one main/orchestrating AI lifecycle operator. Task-execution subagents may perform bounded delegated work, but Harness lifecycle mutations remain initiated through the main/orchestrating agent and mechanically serialized by the Deterministic Runtime where the runtime owns those transitions.

## Rules

- one human authority owns approval/discard decisions within the Harness operating model
- one main/orchestrating agent acts as the lifecycle operator
- delegated subagents do not independently record/withdraw approvals, bootstrap repositories, land/abandon Goal branches, or recover landing transactions
- runtime-owned lifecycle mutation is serialized inside the supported Git common directory
- a process with unrestricted repository access can bypass Harness mechanics; this model is cooperative, not adversarial

## Boundary

This collaboration model does not decide where Project truth lives. The selected Project model owns that dimension independently.

It also does not provide distributed coordination between independent clones. Cooperative multi-user support is provided by `.harness/collaboration-models/cooperative-multi-user.md`; it remains a separate selectable Collaboration model rather than an extension implicitly active here.
