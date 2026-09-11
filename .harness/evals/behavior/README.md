# LLM Behavioral Regression Suite

This suite tests the probabilistic control plane above the deterministic Git runtime. It protects both lifecycle behavior and the constitutional semantics that keep a Harness-governed Project internally coherent under either supported Collaboration model (single-user or cooperative multi-user).

## Coverage model

The suite is **invariant-coverage based**, not scenario-count based.

`.harness/harness/invariants.json` indexes stable constitutional invariant IDs and points each ID to its one authoritative prose source. Scenarios declare `covers` IDs. The registry is not a second rulebook: it contains no duplicated invariant prose.

`harness.py check` and this evaluator both reject a corpus when any `behavior_required` constitutional invariant is uncovered.

Current constitutional families include:

- Harness vs Project jurisdiction
- universal Guides and explicit Project departures
- jurisdiction-first authority / one-rule-one-authority
- evidence and implementation not manufacturing authority
- change propagation through affected owners
- semantic-evidence freshness

Lifecycle scenarios remain in the same corpus even when they do not map to one of these constitutional IDs.

## Hidden expectations

Scenario expectations and `covers` metadata are **not sent to the model runner**. A runner receives the declared constitutional Harness authority documents, the scenario id/family/situation, and catalogs of valid decision/action labels. It returns structured JSON; this evaluator compares that result with the hidden expectations.

## Constitutional evaluation provenance and semantic surface

Harness Assurance uses **constitutional evaluation (Option A)**. `AUTHORITY_PATHS` in `run.py` declares the compact constitutional authority set supplied to every behavior scenario. The evaluator constructs each runner request, deterministically serializes that exact request, sends those exact serialized bytes to the runner, and hashes the ordered request sequence as `evaluation_input_digest`.

A real-model pass is current evidence only for that exact evaluation-input digest and the current scenario-suite digest. Any change to the runner instruction, supplied authority content/order, visible scenario fields, decision/action catalogs, or response schema changes the input digest automatically. Hidden expectations remain outside model input and are covered by the suite digest.

`.harness/evals/behavior/semantic-surface.json` has a different role: it is the broader model-facing governance/change-impact inventory. It helps identify semantic edits that may require routing or additional evaluation, but it is **not** evidence that a constitutional behavior run supplied all matched files to the model.

## Validate the suite in CI

```text
python .harness/evals/behavior/run.py --validate-only
python -m unittest discover -s .harness/evals/behavior/tests -v
```

These deterministic checks validate the corpus, invariant coverage, authority files, semantic-surface configuration, and evaluator. They do not claim that a real model passed.

## Run against an LLM

Provide a runner command that reads one JSON request from stdin and writes exactly one JSON response to stdout:

```json
{"decision":"...","actions":["..."],"claims":["..."]}
```

Then run:

```text
python .harness/evals/behavior/run.py --runner "path/to/your-llm-runner"
```

The runner owns provider/API details. This keeps the Harness evaluator provider-neutral and lets ChatGPT/OpenAI, Claude, Gemini, local models, or future providers use the same scenarios.

## Capture, replay, and retain Assurance evidence

A live runner can write a response capture already bound to the exact model-facing authority and scenario suite it saw:

```text
python .harness/evals/behavior/run.py \
  --runner "path/to/your-llm-runner" \
  --profile "provider/model/profile" \
  --capture-out path/to/captured-responses.jsonl
```

The capture begins with metadata:

```json
{"type":"capture","schema_version":2,"profile":"provider/model/profile","evaluation_input_digest":"...","suite_digest":"..."}
```

followed by one row per scenario:

```json
{"id":"scenario-id","response":{"decision":"...","actions":[],"claims":[]}}
```

Replay it with:

```text
python .harness/evals/behavior/run.py --responses path/to/captured-responses.jsonl
```

Unbound response JSONL without capture metadata can still be replayed as evaluator regression input, but its `capture_freshness` is `unknown` and it **cannot mint current Harness Assurance evidence**. Capture metadata that does not bind the current evaluation input is `stale` for Assurance. A schema-v2 replay whose captured evaluation-input or suite digest differs from current provenance is likewise `stale`, even if its answers happen to pass current expectations.

After a passing live run, or a replay whose bound capture metadata is current, retain compact Assurance evidence metadata:

```text
python .harness/evals/behavior/run.py \
  --responses path/to/captured-responses.jsonl \
  --profile "provider/model/profile" \
  --evidence-out .harness/evals/behavior/evidence/provider-model.json
```

The schema-v2 evidence file records the profile, evaluation source, exact constitutional `evaluation_input_digest`, and suite digest. `harness.py check` reports supplied evidence as current, stale, or absent without treating freshness as structural coherence. `harness.py assure --profile ...` requires current evidence for the named profile before it can report GREEN.
