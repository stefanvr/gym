from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("harness_behavior_eval", SOURCE / "run.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load behavior evaluator")
EVAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVAL)


class BehaviorSuiteTests(unittest.TestCase):
    def test_suite_authority_and_constitutional_coverage_validate(self):
        suite = EVAL.load_suite()
        invariants = EVAL.load_invariant_registry()
        covered = {iid for scenario in suite["scenarios"] for iid in scenario.get("covers", [])}
        required = {iid for iid, row in invariants.items() if row["behavior_required"]}
        self.assertGreaterEqual(len(suite["scenarios"]), 10)
        self.assertEqual(required - covered, set())
        authority = EVAL.authority_context()
        self.assertIn("Workflow", authority)
        self.assertIn("Harness Assurance", authority)
        self.assertIn("Change Impact", authority)
        self.assertIn("Authority Orchestrator Contract", authority)
        self.assertIn("Method Pack Contract", authority)

    def test_missing_required_constitutional_coverage_is_invalid(self):
        suite = copy.deepcopy(EVAL.load_suite())
        for scenario in suite["scenarios"]:
            scenario["covers"] = []
        with self.assertRaises(EVAL.EvalError) as ctx:
            EVAL.validate_suite(suite)
        self.assertIn("does not cover required constitutional invariants", str(ctx.exception))

    def test_expected_synthetic_responses_pass_all_scenarios(self):
        suite = EVAL.load_suite()
        for scenario in suite["scenarios"]:
            response = {
                "decision": scenario["expected_decision"],
                "actions": list(dict.fromkeys(scenario.get("required_actions", []))),
                "claims": [],
            }
            self.assertEqual(EVAL.evaluate_response(scenario, response), [], scenario["id"])

    def test_unknown_action_outside_catalog_is_a_failure(self):
        suite = EVAL.load_suite()
        scenario = suite["scenarios"][0]
        response = {
            "decision": scenario["expected_decision"],
            "actions": scenario["required_actions"] + ["git.force.push"],
            "claims": [],
        }
        failures = EVAL.evaluate_response(scenario, response, set(suite["action_catalog"]))
        self.assertTrue(any("unknown actions" in item for item in failures))

    def test_forbidden_action_is_a_failure(self):
        suite = EVAL.load_suite()
        scenario = next(item for item in suite["scenarios"] if item["forbidden_actions"])
        response = {
            "decision": scenario["expected_decision"],
            "actions": scenario["required_actions"] + [scenario["forbidden_actions"][0]],
            "claims": [],
        }
        failures = EVAL.evaluate_response(scenario, response)
        self.assertTrue(any("forbidden action" in item for item in failures))

    def test_runner_payload_withholds_expectations_coverage_and_runner_contract_works(self):
        suite = EVAL.load_suite()
        scenario = suite["scenarios"][0]
        payload = EVAL.runner_payload(suite, scenario, "authority")
        serialized = json.dumps(payload)
        self.assertNotIn("expected_decision", serialized)
        self.assertNotIn("required_actions", serialized)
        self.assertNotIn('"covers"', serialized)
        with tempfile.TemporaryDirectory() as td:
            script = Path(td) / "runner.py"
            script.write_text(
                "import json,sys\n"
                "request=json.load(sys.stdin)\n"
                "assert 'expected_decision' not in request['scenario']\n"
                "assert 'covers' not in request['scenario']\n"
                "print(json.dumps({'decision':'ask_for_explicit_approval','actions':['ask.explicit_approval'],'claims':[]}))\n",
                encoding="utf-8",
            )
            response = EVAL.invoke_runner(f'"{sys.executable}" "{script}"', payload, timeout=10)
            checked = EVAL.validate_response_shape(response, scenario["id"])
            self.assertEqual(EVAL.evaluate_response(scenario, checked), [])

    def test_runner_timeout_is_bounded(self):
        suite = EVAL.load_suite()
        scenario = suite["scenarios"][0]
        payload = EVAL.runner_payload(suite, scenario, "authority")
        with tempfile.TemporaryDirectory() as td:
            script = Path(td) / "slow_runner.py"
            script.write_text("import time; time.sleep(5)\n", encoding="utf-8")
            with self.assertRaises(EVAL.EvalError) as ctx:
                EVAL.invoke_runner(f'"{sys.executable}" "{script}"', payload, timeout=0.05)
            self.assertIn("timed out", str(ctx.exception))

    def test_ordered_actions_in_wrong_order_fail(self):
        suite = EVAL.load_suite()
        scenario = next(item for item in suite["scenarios"] if item.get("ordered_actions"))
        response = {
            "decision": scenario["expected_decision"],
            "actions": list(reversed(scenario["ordered_actions"])),
            "claims": [],
        }
        failures = EVAL.evaluate_response(scenario, response)
        self.assertTrue(any("wrong order" in item for item in failures))

    def test_forbidden_manual_completion_claim_is_a_failure(self):
        suite = EVAL.load_suite()
        scenario = next(item for item in suite["scenarios"] if item.get("forbidden_claims"))
        response = {
            "decision": scenario["expected_decision"],
            "actions": scenario["required_actions"],
            "claims": ["The manual step completed successfully."],
        }
        failures = EVAL.evaluate_response(scenario, response)
        self.assertTrue(any("forbidden completion claim" in item for item in failures))

    def test_captured_response_replay_reports_pass_and_digest(self):
        suite = EVAL.load_suite()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "responses.jsonl"
            context = EVAL.authority_context()
            input_digest = EVAL.evaluation_input_digest(suite, context)
            rows = [json.dumps({
                "type": "capture",
                "schema_version": 2,
                "profile": "test/profile",
                "evaluation_input_digest": input_digest,
                "suite_digest": EVAL.suite_digest(),
            })]
            for scenario in suite["scenarios"]:
                rows.append(json.dumps({
                    "id": scenario["id"],
                    "response": {
                        "decision": scenario["expected_decision"],
                        "actions": scenario.get("required_actions", []),
                        "claims": [],
                    },
                }))
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            report = EVAL.run_suite(suite, runner=None, responses_path=path, timeout=1)
            self.assertEqual(report["result"], "pass")
            self.assertEqual(report["passed"], report["total"])
            self.assertEqual(report["capture_freshness"], "current")
            self.assertEqual(len(report["evaluation_input_digest"]), 64)
            self.assertEqual(len(report["semantic_surface_digest"]), 64)
            self.assertGreater(report["semantic_surface_file_count"], 20)

            evidence = Path(td) / "evidence.json"
            EVAL.write_evidence(evidence, report, "test/profile", "response_replay")
            stored = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(stored["schema_version"], 2)
            self.assertEqual(stored["evaluation_input_digest"], report["evaluation_input_digest"])
            self.assertEqual(stored["profile"], "test/profile")
            self.assertEqual(stored["evaluation_source"], "response_replay")
            self.assertEqual(stored["result"], "pass")


    def test_evaluation_input_digest_hashes_exact_serialized_runner_requests(self):
        suite = EVAL.load_suite()
        context = EVAL.authority_context()
        baseline = EVAL.evaluation_input_digest(suite, context)

        changed_authority = EVAL.evaluation_input_digest(suite, context + "\nchanged authority")
        self.assertNotEqual(baseline, changed_authority)

        changed_visible = copy.deepcopy(suite)
        changed_visible["scenarios"][0]["situation"] += " visible change"
        self.assertNotEqual(baseline, EVAL.evaluation_input_digest(changed_visible, context))

        changed_hidden = copy.deepcopy(suite)
        changed_hidden["scenarios"][0]["expected_decision"] = next(
            decision for decision in suite["decision_catalog"]
            if decision != suite["scenarios"][0]["expected_decision"]
        )
        self.assertEqual(baseline, EVAL.evaluation_input_digest(changed_hidden, context))

        original_payload = EVAL.runner_payload
        try:
            def changed_instruction(suite_arg, scenario_arg, context_arg):
                payload = original_payload(suite_arg, scenario_arg, context_arg)
                payload["instruction"] += " changed instruction"
                return payload
            EVAL.runner_payload = changed_instruction
            self.assertNotEqual(baseline, EVAL.evaluation_input_digest(suite, context))
        finally:
            EVAL.runner_payload = original_payload

    def test_option_a_separates_broader_semantic_surface_from_constitutional_input(self):
        suite = EVAL.load_suite()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            shutil.copytree(EVAL.ROOT, root)

            surface_before, _ = EVAL.semantic_surface_digest(root)
            input_before = EVAL.evaluation_input_digest(suite, EVAL.authority_context(root))

            vocabulary = root / ".harness" / "README-vocabulary.md"
            self.assertNotIn(".harness/README-vocabulary.md", EVAL.AUTHORITY_PATHS)
            self.assertNotIn(".harness/harness-extended-vocabulary.md", EVAL.AUTHORITY_PATHS)
            vocabulary.write_text(vocabulary.read_text(encoding="utf-8") + "\nnon-constitutional surface edit\n", encoding="utf-8")
            surface_after, _ = EVAL.semantic_surface_digest(root)
            input_after_surface_edit = EVAL.evaluation_input_digest(suite, EVAL.authority_context(root))
            self.assertNotEqual(surface_before, surface_after)
            self.assertEqual(input_before, input_after_surface_edit)

            workflow = root / ".harness" / "workflow" / "WORKFLOW.md"
            self.assertIn(".harness/workflow/WORKFLOW.md", EVAL.AUTHORITY_PATHS)
            workflow.write_text(workflow.read_text(encoding="utf-8") + "\nconstitutional input edit\n", encoding="utf-8")
            self.assertNotEqual(
                input_before,
                EVAL.evaluation_input_digest(suite, EVAL.authority_context(root)),
            )

    def test_runner_uses_same_serialization_that_is_hashed(self):
        suite = EVAL.load_suite()
        scenario = suite["scenarios"][0]
        payload = EVAL.runner_payload(suite, scenario, "authority")
        serialized = EVAL.serialize_runner_request(payload)
        self.assertEqual(json.loads(serialized), payload)
        self.assertEqual(serialized, EVAL.serialize_runner_request(payload))

    def test_schema_v1_semantic_surface_capture_is_stale_not_current(self):
        metadata = {
            "type": "capture",
            "schema_version": 1,
            "profile": "test/profile",
            "semantic_surface_digest": "a" * 64,
            "suite_digest": EVAL.suite_digest(),
        }
        self.assertEqual(
            EVAL.capture_freshness(metadata, "b" * 64, EVAL.suite_digest()),
            "stale",
        )


    def test_unbound_response_replay_is_not_current_capture_evidence(self):
        suite = EVAL.load_suite()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "responses.jsonl"
            rows = [json.dumps({
                "id": scenario["id"],
                "response": {
                    "decision": scenario["expected_decision"],
                    "actions": scenario.get("required_actions", []),
                    "claims": [],
                },
            }) for scenario in suite["scenarios"]]
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            report = EVAL.run_suite(suite, runner=None, responses_path=path, timeout=1)
            self.assertEqual(report["result"], "pass")
            self.assertEqual(report["capture_freshness"], "unknown")



if __name__ == "__main__":
    unittest.main()
