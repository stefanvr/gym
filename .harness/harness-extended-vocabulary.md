# Harness Extended Vocabulary

Terms used mainly while developing, validating, recovering, or assuring the Harness itself. Read [Working Vocabulary](README-vocabulary.md) for normal operating terms.

The split is an audience boundary, not a precedence rule. Harness Change owns both files, and no term may have competing definitions across them.

| Term | Meaning |
|---|---|
| **Deterministic Runtime** | The `.harness/runtime/` executable package. `kernel.py` owns repository/lifecycle mechanics, model modules own model mechanics, `checker.py` owns deterministic/Assurance validation, and `harness.py` is the CLI entry point. |
| **Landing boundary** | The durable configured-mainline result for one authorized Goal branch: the branch commit for an exact one-commit fast-forward, otherwise one merge commit. |
| **Landing transaction** | Local runtime recovery state beginning at `land prepare`, pinning the approval source, approved tree, exact Goal commit, and exact mainline base through integration/publication/finalization. |
| **Abandonment safety commit** | Temporary commit made only on a branch being explicitly discarded when attributable uncommitted target work would otherwise be destroyed. |
| **Integration receipt** | Durable evidence that an authorized branch outcome reached configured mainline; not every landing requires a merge commit. |
| **Invariant** | A rule that must remain true throughout the lifecycle where it applies. |
| **Persisted Dream proposal** | `doc/dreams/<proposal>.md`, Learning-owned non-authoritative proposal state retained only when proposal context/evidence must survive loss. |
| **Temporary state** | Development/runtime state with an explicit owner and lifetime; it is not authority merely because it is persisted. |
| **Provenance class** | Classification of how a Brainstorm finding became known, owned by the [Provenance mechanism](mechanisms/provenance.md). |
| **Surface** | A structurally distinct place where user interaction occurs, such as a page, panel, dialog, overlay, persistent chrome, or app mode. |
| **Harness Check** | Sanity check for deterministic internal Harness consistency and constitutional wiring. |
| **Harness Change** | Skill that edits Harness authority: `repair` corrects implementation/documentation without changing what the Harness decides; `design` changes what it decides after owner approval. |
| **Harness Assurance** | Profile-qualified assessment of whether current evidence supports Harness guarantees for a supported operating profile; never a grade of the managed Project. |
| **Change Impact** | Mechanism that reconsiders materially dependent conclusions after authoritative meaning changes and routes that reconsideration to existing owners. |
| **Semantic surface digest** | Hash of the configured broader model-facing Harness surface, used for governance/change visibility rather than as proof of exact evaluator input. |
| **Evaluation input digest** | Hash of the ordered exact requests supplied by the constitutional behavior evaluator to its model runner. |
| **Specification Check** | Sanity check for coherence within and across authoritative Project specifications. |
| **Trace Check** | Bidirectional sanity check across authoritative specification identifiers, implementation, and tests. |
| **Repository Check** | Sanity check for stale/orphan Goal recovery state, runtime artifacts, broken references, and repository-convention drift. |
| **Workflow authority** | Agent-independent operating contract shared by all execution agents. |
| **Agent adapter** | Thin runtime-specific entry instructions for loading/executing shared Workflow; never a fork of Project truth. |
| **Grill** | Pressure-test mechanism that challenges one candidate at a time without owning its decision. |
| **Learning** | Support area that compounds experience into non-authoritative improvement proposals. |
| **Dream proposal** | Non-authoritative candidate change requiring explicit owner acceptance before an owning skill may promote it. |
| **Knowledge** | Reusable technology-conditioned operational learning that does not choose the technology. |
| **Continuity** | Session-restart/context-loading design that preserves authority while minimizing repeated context. |
| **Session pointer** | Small transient restart cache containing pointers/current state, never authoritative Project truth. |
| **Session Checkpoint** | Continuity skill that creates, refreshes, or clears the optional session pointer. |
| **Context manifest** | Routing inventory telling an agent which files exist for a concern; startup uses only its small `always` set. |
