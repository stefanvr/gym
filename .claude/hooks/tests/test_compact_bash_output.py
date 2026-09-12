from __future__ import annotations

import base64
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "compact-bash-output.py"
spec = importlib.util.spec_from_file_location("compact_bash_output", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class HookRewriteTests(unittest.TestCase):
    def payload(self, command: str) -> dict:
        return {
            "tool_name": "Bash",
            "tool_input": {
                "command": command,
                "description": "verification",
                "timeout": 120000,
            },
        }

    def test_rewrites_supported_commands_and_preserves_other_input(self):
        for command in (
            "npm test",
            "npm test -- --runInBand",
            "npm run test:e2e",
            "npm run test:e2e -- --project chromium",
            "python .harness/runtime/harness.py check",
            "python3 .harness/runtime/harness.py check",
        ):
            with self.subTest(command=command):
                result = mod.rewrite_payload(self.payload(command))
                out = result["hookSpecificOutput"]
                self.assertEqual(out["hookEventName"], "PreToolUse")
                self.assertEqual(out["permissionDecision"], "allow")
                self.assertEqual(out["updatedInput"]["description"], "verification")
                self.assertEqual(out["updatedInput"]["timeout"], 120000)
                self.assertIn("--run", out["updatedInput"]["command"])

    def test_leaves_unrelated_and_compound_commands_untouched(self):
        for command in (
            "npm run build",
            "node scripts/build.js",
            "npx playwright test",
            "npm test && echo done",
            "npm run test:e2e | tee output.log",
            "python .harness/runtime/harness.py check; git status",
            "FOO=1 npm test",
        ):
            with self.subTest(command=command):
                self.assertEqual(mod.rewrite_payload(self.payload(command)), {})

    def test_hook_cli_returns_valid_json(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(self.payload("npm test")),
            text=True,
            capture_output=True,
            check=True,
        )
        data = json.loads(proc.stdout)
        self.assertEqual(data["hookSpecificOutput"]["permissionDecision"], "allow")

    def test_runner_rejects_tampered_command(self):
        encoded = base64.urlsafe_b64encode(b"npm test && echo nope").decode("ascii")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--run", "npm test", encoded],
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 126)
        self.assertIn("rejected an unsupported command", proc.stderr)

    def test_runner_success_collapses_output_to_one_summary_line(self):
        class FakeProc:
            def __init__(self):
                self.stdout = io.BytesIO(b"alpha\nbeta\ngamma\n")
            def wait(self):
                return 0
            def terminate(self):
                pass

        out = io.StringIO()
        with mock.patch.object(mod.subprocess, "Popen", return_value=FakeProc()), redirect_stdout(out):
            rc = mod.run_compact("npm test", "npm test")
        self.assertEqual(rc, 0)
        self.assertEqual(out.getvalue().strip(), "PASS npm test — 3 lines / 17 B suppressed")
        self.assertNotIn("alpha", out.getvalue())

    def test_runner_failure_preserves_exit_and_compact_diagnostics(self):
        class FakeProc:
            def __init__(self):
                self.stdout = io.BytesIO(b"setup\nFAIL expected 2 got 3\nstack detail\ncleanup\n")
            def wait(self):
                return 7
            def terminate(self):
                pass

        out = io.StringIO()
        with mock.patch.object(mod.subprocess, "Popen", return_value=FakeProc()), redirect_stdout(out):
            rc = mod.run_compact("npm test", "npm test")
        text = out.getvalue()
        self.assertEqual(rc, 7)
        self.assertIn("FAIL npm test — exit 7", text)
        self.assertIn("FAIL expected 2 got 3", text)
        self.assertIn("compact failure excerpt", text)


if __name__ == "__main__":
    unittest.main()
