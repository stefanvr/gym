from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_RUNTIME = Path(__file__).resolve().parents[1]

_RUNTIME_SPEC = importlib.util.spec_from_file_location("harness_runtime_under_test", SOURCE_RUNTIME / "harness.py")
if _RUNTIME_SPEC is None or _RUNTIME_SPEC.loader is None:
    raise RuntimeError("cannot load harness runtime under test")
HARNESS = importlib.util.module_from_spec(_RUNTIME_SPEC)
_RUNTIME_SPEC.loader.exec_module(HARNESS)


def run(cmd, cwd, check=True):
    cp = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and cp.returncode != 0:
        raise AssertionError(f"command failed {cmd}:\nstdout={cp.stdout}\nstderr={cp.stderr}")
    return cp


def invoke_harness(root: Path, *args, check=True, config_path: Path | None = None):
    previous_root = HARNESS.PROJECT_ROOT
    previous_config = HARNESS.CONFIG_PATH
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        HARNESS.set_runtime_context(root, config_path or root / ".harness" / "runtime" / "config.json")
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            returncode = HARNESS.main(list(args))
    finally:
        HARNESS.set_runtime_context(previous_root, previous_config)

    cp = subprocess.CompletedProcess(
        ["harness.py", *args], returncode, stdout.getvalue(), stderr.getvalue()
    )
    if check and cp.returncode != 0:
        raise AssertionError(
            f"command failed {cp.args}:\nstdout={cp.stdout}\nstderr={cp.stderr}"
        )
    if cp.returncode == 0:
        return json.loads(cp.stdout)
    return cp


def copy_runtime_sources(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("harness.py", "kernel.py", "project_model.py", "collaboration_model.py", "checker.py"):
        shutil.copy2(SOURCE_RUNTIME / name, destination / name)


class RepoFixture:
    def __init__(self, mainline="trunk"):
        shm = Path("/dev/shm")
        temp_root = str(shm) if shm.is_dir() and os.access(shm, os.W_OK) else None
        self.tmp = tempfile.TemporaryDirectory(dir=temp_root)
        self.root = Path(self.tmp.name)
        runtime = self.root / ".harness" / "runtime"
        runtime.mkdir(parents=True)
        copy_runtime_sources(runtime)
        (runtime / "config.json").write_text(json.dumps({
            "schema_version": 1,
            "mainline": mainline,
            "bootstrap_mainline": mainline,
            "remote": "origin",
        }), encoding="utf-8")
        (self.root / ".gitignore").write_text("doc/goals/\ndoc/session.md\n", encoding="utf-8")
        run(["git", "init", "-b", mainline], self.root)
        run(["git", "config", "user.name", "Harness Test"], self.root)
        run(["git", "config", "user.email", "harness@example.test"], self.root)
        self.h("repo", "bootstrap", "--all-seed-files", "--message", "baseline")
        self.mainline = mainline
        self.remote = self.root / ".git" / "harness-test-origin.git"
        run(["git", "init", "--bare", str(self.remote)], self.root)
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-u", "origin", self.mainline)

    def close(self):
        self.tmp.cleanup()

    def h(self, *args, check=True):
        return invoke_harness(self.root, *args, check=check)

    def git(self, *args, check=True):
        return run(["git", *args], self.root, check=check)

    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def goal_path(self, branch=None):
        branch = branch or self.git("branch", "--show-current").stdout.strip()
        return self.root / "doc" / "goals" / f"{branch}.md"

    def ensure_goal(self, branch=None, outcome="Test Goal outcome"):
        branch = branch or self.git("branch", "--show-current").stdout.strip()
        if not branch or branch == self.mainline:
            return
        path = self.goal_path(branch)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# Goal\n\n{outcome}\n", encoding="utf-8")

    def commit(self, message):
        self.ensure_goal()
        self.git("add", "-A")
        self.git("commit", "-m", message)



class HarnessRuntimeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fx = RepoFixture()

    def tearDown(self):
        self.fx.close()

    def prepare_branch(self, branch="feature/demo", commits=1):
        self.fx.h("branch", "start", "--name", branch)
        for i in range(commits):
            self.fx.write(f"work-{i}.txt", f"value {i}\n")
            self.fx.commit(f"step {i + 1}")
        approval = self.fx.h("approval", "record")
        prepared = self.fx.h("land", "prepare")
        return approval, prepared

    def test_branch_start_rejects_cli_unsafe_name_and_base(self):
        bad_name = self.fx.h("branch", "start", "--name=-f", check=False)
        self.assertEqual(bad_name.returncode, 2)
        self.assertIn("branch --name is not a valid Git branch name", bad_name.stderr)

        # A raw ref can exist even when its short name is unsafe as a Git CLI
        # branch argument. It must not be accepted as a branch-start base.
        self.fx.git("update-ref", "refs/heads/-f", "HEAD")
        bad_base = self.fx.h(
            "branch", "start", "--name", "feature/safe", "--base=-f", check=False
        )
        self.assertEqual(bad_base.returncode, 2)
        self.assertIn("branch --base is not a valid Git branch name", bad_base.stderr)
        self.assertNotEqual(
            self.fx.git("show-ref", "--verify", "--quiet", "refs/heads/feature/safe", check=False).returncode,
            0,
        )

    def test_lifecycle_branch_selectors_reject_cli_unsafe_names(self):
        cases = (
            ("approval", "validate", "--branch=-f"),
            ("land", "abort", "--branch=-f"),
            ("abandon", "discard", "--target=-f", "--mode", "explicit"),
        )
        for args in cases:
            with self.subTest(args=args):
                cp = self.fx.h(*args, check=False)
                self.assertEqual(cp.returncode, 2)
                self.assertIn("not a valid Git branch name", cp.stderr)

    def test_resume_reports_branch_derived_goal_document(self):
        self.fx.h("branch", "start", "--name", "feature/recoverable")
        self.fx.write("app.txt", "work\n")
        self.fx.commit("work")
        resume = self.fx.h("resume")
        self.assertEqual(resume["goal_path"], "doc/goals/feature/recoverable.md")
        self.assertTrue(resume["goal_document_exists"])
        self.assertTrue(self.fx.goal_path("feature/recoverable").exists())
        self.assertEqual(self.fx.git("status", "--porcelain").stdout.strip(), "")

    def test_approval_requires_active_goal_document(self):
        self.fx.h("branch", "start", "--name", "feature/no-goal")
        self.fx.git("commit", "--allow-empty", "-m", "work without Goal state")
        cp = self.fx.h("approval", "record", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("active Goal document is required", cp.stderr)

    def test_approval_cannot_move_without_explicit_drop(self):
        self.fx.h("branch", "start", "--name", "feature/approval")
        self.fx.write("app.txt", "one\n")
        self.fx.commit("one")
        first = self.fx.h("approval", "record")
        self.fx.write("app.txt", "two\n")
        self.fx.commit("two")
        cp = self.fx.h("approval", "record", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("approval already exists at a different boundary", cp.stderr)
        self.fx.h("approval", "drop")
        second = self.fx.h("approval", "record")
        self.assertNotEqual(first["commit"], second["commit"])

    def test_history_cleanup_before_prepare_may_rewrite_commits_but_not_tree(self):
        self.fx.h("branch", "start", "--name", "feature/rewrite")
        self.fx.write("a.txt", "a\n")
        self.fx.commit("step a")
        self.fx.write("b.txt", "b\n")
        self.fx.commit("step b")
        approval = self.fx.h("approval", "record")
        approved_tree = approval["tree"]

        base = self.fx.git("merge-base", self.fx.mainline, "feature/rewrite").stdout.strip()
        self.fx.git("reset", "--soft", base)
        self.fx.git("commit", "-m", "clean goal history")
        rewritten = self.fx.git("rev-parse", "HEAD").stdout.strip()
        self.assertNotEqual(rewritten, approval["commit"])
        self.assertEqual(self.fx.git("rev-parse", "HEAD^{tree}").stdout.strip(), approved_tree)
        self.assertTrue(self.fx.h("approval", "validate")["valid"])

        prepared = self.fx.h("land", "prepare")
        self.assertEqual(prepared["ready_commit"], rewritten)

    def test_prepare_requires_recorded_approval(self):
        self.fx.h("branch", "start", "--name", "feature/no-approval")
        self.fx.write("app.txt", "work\n")
        self.fx.commit("work")
        cp = self.fx.h("land", "prepare", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("requires recorded approval", cp.stderr)

    def test_prepare_rejects_tree_changed_after_approval(self):
        self.fx.h("branch", "start", "--name", "feature/tree-changed")
        self.fx.write("app.txt", "one\n")
        self.fx.commit("one")
        self.fx.h("approval", "record")
        self.fx.write("app.txt", "two\n")
        self.fx.commit("two")
        cp = self.fx.h("land", "prepare", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("no longer equals the recorded approval tree", cp.stderr)

    def test_prepare_refuses_remote_mainline_ahead_of_local_mainline(self):
        self.fx.h("branch", "start", "--name", "feature/remote-mainline")
        self.fx.write("app.txt", "work\n")
        self.fx.commit("work")
        self.fx.h("approval", "record")

        with tempfile.TemporaryDirectory() as td:
            clone = Path(td) / "remote-writer"
            run(["git", "clone", str(self.fx.remote), str(clone)], self.fx.root)
            run(["git", "config", "user.name", "Remote Writer"], clone)
            run(["git", "config", "user.email", "remote@example.test"], clone)
            run(["git", "switch", self.fx.mainline], clone)
            run(["git", "commit", "--allow-empty", "-m", "remote mainline advance"], clone)
            run(["git", "push", "origin", self.fx.mainline], clone)

        cp = self.fx.h("land", "prepare", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("configured mainline is not up to date", cp.stderr)

    def test_prepare_refuses_existing_remote_goal_branch_at_different_commit(self):
        self.fx.h("branch", "start", "--name", "feature/remote-goal")
        self.fx.write("app.txt", "one\n")
        self.fx.commit("one")
        self.fx.git("push", "-u", "origin", "feature/remote-goal")
        self.fx.write("app.txt", "two\n")
        self.fx.commit("two")
        self.fx.h("approval", "record")

        cp = self.fx.h("land", "prepare", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("work branch is not up to date", cp.stderr)

    def test_single_commit_goal_fast_forwards_without_merge_commit(self):
        self.prepare_branch(commits=1)
        ready = self.fx.git("rev-parse", "feature/demo").stdout.strip()
        landed = self.fx.h("land", "merge", "--message", "Land single commit")
        self.assertEqual(landed["result"], "landed")
        self.assertEqual(self.fx.git("rev-parse", "HEAD").stdout.strip(), ready)
        parents = self.fx.git("show", "-s", "--format=%P", "HEAD").stdout.split()
        self.assertEqual(len(parents), 1)

    def test_multi_commit_goal_gets_merge_boundary(self):
        self.prepare_branch(commits=2)
        landed = self.fx.h("land", "merge", "--message", "Land multi-step goal")
        self.assertEqual(landed["result"], "landed")
        parents = self.fx.git("show", "-s", "--format=%P", "HEAD").stdout.split()
        self.assertEqual(len(parents), 2)

    def test_local_landing_pushes_mainline_before_finalization(self):
        self.prepare_branch()
        ready = self.fx.git("rev-parse", "feature/demo").stdout.strip()
        landed = self.fx.h("land", "merge", "--message", "Publish landing")
        self.assertEqual(landed["result"], "landed")
        remote_head = self.fx.git("ls-remote", "--heads", "origin", f"refs/heads/{self.fx.mainline}").stdout.split()[0]
        self.assertEqual(remote_head, ready)

    def test_failed_mainline_push_keeps_merged_transaction_and_local_recovery_state(self):
        self.prepare_branch()
        goal_path = self.fx.goal_path("feature/demo")
        session = self.fx.root / "doc" / "session.md"
        session.parent.mkdir(parents=True, exist_ok=True)
        session.write_text("# Session\n\ncontinue\n", encoding="utf-8")
        hook = self.fx.remote / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        cp = self.fx.h("land", "merge", "--message", "Push must succeed", check=False)
        self.assertEqual(cp.returncode, 2)
        resume = self.fx.h("resume")
        self.assertEqual(resume["land_transactions"][0]["phase"], "merged")
        self.assertTrue(goal_path.exists())
        self.assertTrue(session.exists())
        self.assertEqual(self.fx.git("show-ref", "--verify", "refs/heads/feature/demo").returncode, 0)

    def test_work_branch_movement_after_prepare_is_rejected_even_if_tree_is_same(self):
        self.prepare_branch()
        self.fx.git("reset", "--soft", "HEAD~1")
        self.fx.git("commit", "-m", "rewrite after prepare")
        cp = self.fx.h("land", "merge", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("work branch moved after `land prepare`", cp.stderr)

    def test_remote_mainline_move_after_prepare_is_refused_before_integration(self):
        self.prepare_branch()
        with tempfile.TemporaryDirectory() as td:
            clone = Path(td) / "remote-writer"
            run(["git", "clone", str(self.fx.remote), str(clone)], self.fx.root)
            run(["git", "config", "user.name", "Remote Writer"], clone)
            run(["git", "config", "user.email", "remote@example.test"], clone)
            run(["git", "switch", self.fx.mainline], clone)
            run(["git", "commit", "--allow-empty", "-m", "remote mainline advance"], clone)
            run(["git", "push", "origin", self.fx.mainline], clone)

        cp = self.fx.h("land", "merge", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("configured mainline is not up to date", cp.stderr)
        resume = self.fx.h("resume")
        self.assertEqual(resume["land_transactions"][0]["phase"], "ready")

    def test_moved_mainline_requires_recheck_and_prepare_again(self):
        self.prepare_branch()
        self.fx.git("switch", self.fx.mainline)
        self.fx.git("commit", "--allow-empty", "-m", "advance mainline")
        self.fx.git("switch", "feature/demo")
        cp = self.fx.h("land", "merge", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("mainline moved after `land prepare`", cp.stderr)

    def test_withdrawing_approval_invalidates_ready_transaction(self):
        approval, _ = self.prepare_branch()
        dropped = self.fx.h("approval", "drop", "--branch", "feature/demo")
        self.assertEqual(dropped["invalidated_land_transactions"], ["feature/demo"])
        self.assertEqual(dropped["preserved_land_transactions"], [])
        self.assertNotEqual(self.fx.git("show-ref", "--verify", approval["ref"], check=False).returncode, 0)
        self.assertEqual(self.fx.h("resume")["land_transactions"], [])

    def test_withdrawing_approval_cancels_integrating_transaction_before_mainline_crosses(self):
        approval, _ = self.prepare_branch(commits=2)
        data = HARNESS.read_land_state(self.fx.root, "feature/demo")
        candidate = HARNESS.prepare_local_integration(self.fx.root, data, "candidate")
        data["phase"] = "integrating"
        data["merge_commit"] = candidate
        HARNESS.write_land_state(self.fx.root, "feature/demo", data)

        dropped = self.fx.h("approval", "drop", "--branch", "feature/demo")
        self.assertEqual(dropped["invalidated_land_transactions"], ["feature/demo"])
        self.assertEqual(dropped["preserved_land_transactions"], [])
        self.assertNotEqual(self.fx.git("show-ref", "--verify", approval["ref"], check=False).returncode, 0)
        self.assertEqual(self.fx.git("rev-parse", self.fx.mainline).stdout.strip(), data["base_commit"])
        self.assertEqual(self.fx.h("resume")["land_transactions"], [])
        self.assertFalse(HARNESS.ref_exists(self.fx.root, HARNESS.land_runtime_ref("feature/demo", "candidate")))

    def test_withdrawing_approval_preserves_integrating_transaction_after_mainline_crosses(self):
        approval, _ = self.prepare_branch(commits=2)
        data = HARNESS.read_land_state(self.fx.root, "feature/demo")
        candidate = HARNESS.prepare_local_integration(self.fx.root, data, "candidate")
        data["phase"] = "integrating"
        data["merge_commit"] = candidate
        HARNESS.write_land_state(self.fx.root, "feature/demo", data)
        HARNESS.update_ref(self.fx.root, HARNESS.branch_ref(self.fx.mainline), candidate, data["base_commit"])

        dropped = self.fx.h("approval", "drop", "--branch", "feature/demo")
        self.assertEqual(dropped["invalidated_land_transactions"], [])
        self.assertEqual(dropped["preserved_land_transactions"], ["feature/demo"])
        self.assertNotEqual(self.fx.git("show-ref", "--verify", approval["ref"], check=False).returncode, 0)
        self.assertEqual(self.fx.h("resume")["land_transactions"][0]["phase"], "integrating")

        landed = self.fx.h("land", "merge", "--branch", "feature/demo")
        self.assertEqual(landed["result"], "landed")
        self.assertEqual(self.fx.git("rev-parse", self.fx.mainline).stdout.strip(), candidate)

    def test_withdrawing_approval_preserves_merged_transaction(self):
        approval, _ = self.prepare_branch(commits=2)
        data = HARNESS.read_land_state(self.fx.root, "feature/demo")
        candidate = HARNESS.prepare_local_integration(self.fx.root, data, "candidate")
        data["phase"] = "merged"
        data["merge_commit"] = candidate
        HARNESS.write_land_state(self.fx.root, "feature/demo", data)
        HARNESS.update_ref(self.fx.root, HARNESS.branch_ref(self.fx.mainline), candidate, data["base_commit"])
        HARNESS.update_ref(self.fx.root, HARNESS.land_runtime_ref("feature/demo", "merged"), candidate)

        dropped = self.fx.h("approval", "drop", "--branch", "feature/demo")
        self.assertEqual(dropped["invalidated_land_transactions"], [])
        self.assertEqual(dropped["preserved_land_transactions"], ["feature/demo"])
        self.assertEqual(self.fx.h("resume")["land_transactions"][0]["phase"], "merged")
        self.assertEqual(self.fx.h("land", "merge", "--branch", "feature/demo")["result"], "landed")

    def test_withdrawing_approval_preserves_published_transaction(self):
        approval, _ = self.prepare_branch(commits=2)
        data = HARNESS.read_land_state(self.fx.root, "feature/demo")
        candidate = HARNESS.prepare_local_integration(self.fx.root, data, "candidate")
        HARNESS.update_ref(self.fx.root, HARNESS.branch_ref(self.fx.mainline), candidate, data["base_commit"])
        self.fx.git("push", "origin", f"{candidate}:refs/heads/{self.fx.mainline}")
        data["phase"] = "published"
        data["merge_commit"] = candidate
        HARNESS.write_land_state(self.fx.root, "feature/demo", data)
        HARNESS.update_ref(self.fx.root, HARNESS.land_runtime_ref("feature/demo", "published"), candidate)

        dropped = self.fx.h("approval", "drop", "--branch", "feature/demo")
        self.assertEqual(dropped["invalidated_land_transactions"], [])
        self.assertEqual(dropped["preserved_land_transactions"], ["feature/demo"])
        self.assertEqual(self.fx.h("resume")["land_transactions"][0]["phase"], "published")
        self.assertEqual(self.fx.h("land", "merge", "--branch", "feature/demo")["result"], "landed")

    def test_withdrawing_approval_refuses_ambiguous_integrating_state_before_mutation(self):
        approval, _ = self.prepare_branch(commits=2)
        data = HARNESS.read_land_state(self.fx.root, "feature/demo")
        candidate = HARNESS.prepare_local_integration(self.fx.root, data, "candidate")
        data["phase"] = "integrating"
        data["merge_commit"] = candidate
        HARNESS.write_land_state(self.fx.root, "feature/demo", data)
        self.fx.git("switch", self.fx.mainline)
        self.fx.git("commit", "--allow-empty", "-m", "unexpected mainline move")
        self.fx.git("switch", "feature/demo")

        cp = self.fx.h("approval", "drop", "--branch", "feature/demo", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("ambiguous mainline state", cp.stderr)
        self.assertEqual(self.fx.git("show-ref", "--verify", approval["ref"]).returncode, 0)
        self.assertEqual(self.fx.h("resume")["land_transactions"][0]["phase"], "integrating")

    def test_merge_rechecks_live_approval(self):
        approval, _ = self.prepare_branch()
        self.fx.git("update-ref", "-d", approval["ref"])
        cp = self.fx.h("land", "merge", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("landing approval is no longer valid", cp.stderr)

    def test_land_abort_allows_prepare_again_after_mainline_moves(self):
        approval, _ = self.prepare_branch()
        self.fx.git("switch", self.fx.mainline)
        self.fx.git("commit", "--allow-empty", "-m", "advance mainline")
        self.fx.git("push", "origin", self.fx.mainline)
        self.fx.git("switch", "feature/demo")
        self.fx.h("land", "abort")
        prepared = self.fx.h("land", "prepare")
        self.assertEqual(prepared["approval_source_commit"], approval["commit"])
        self.assertEqual(prepared["base_commit"], self.fx.git("rev-parse", self.fx.mainline).stdout.strip())

    def test_land_abort_refuses_after_integration_has_started(self):
        self.prepare_branch(commits=2)
        data = HARNESS.read_land_state(self.fx.root, "feature/demo")
        candidate = HARNESS.prepare_local_integration(self.fx.root, data, "candidate")
        data["phase"] = "integrating"
        data["merge_commit"] = candidate
        HARNESS.write_land_state(self.fx.root, "feature/demo", data)
        cp = self.fx.h("land", "abort", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("cannot abort after integration has started", cp.stderr)

    def test_merged_recovery_refuses_to_delete_locally_advanced_work_branch(self):
        self.prepare_branch(commits=2)
        data = HARNESS.read_land_state(self.fx.root, "feature/demo")
        candidate = HARNESS.prepare_local_integration(self.fx.root, data, "candidate")
        data["phase"] = "merged"
        data["merge_commit"] = candidate
        HARNESS.write_land_state(self.fx.root, "feature/demo", data)
        HARNESS.update_ref(self.fx.root, HARNESS.land_runtime_ref("feature/demo", "merged"), candidate)
        self.fx.git("update-ref", f"refs/heads/{self.fx.mainline}", candidate, data["base_commit"])

        self.fx.git("switch", "feature/demo")
        self.fx.write("after.txt", "later\n")
        self.fx.commit("later work")
        advanced = self.fx.git("rev-parse", "HEAD").stdout.strip()
        self.fx.git("switch", self.fx.mainline)

        cp = self.fx.h("land", "merge", "--branch", "feature/demo", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("local work branch moved from prepared ready boundary", cp.stderr)
        self.assertEqual(self.fx.git("rev-parse", "feature/demo").stdout.strip(), advanced)

    def test_merged_recovery_requires_receipt_reachable_from_mainline(self):
        self.prepare_branch()
        data = HARNESS.read_land_state(self.fx.root, "feature/demo")
        feature_commit = self.fx.git("rev-parse", "feature/demo").stdout.strip()
        data["phase"] = "merged"
        data["merge_commit"] = feature_commit
        HARNESS.write_land_state(self.fx.root, "feature/demo", data)
        HARNESS.update_ref(self.fx.root, HARNESS.land_runtime_ref("feature/demo", "merged"), feature_commit)
        self.fx.git("switch", self.fx.mainline)

        cp = self.fx.h("land", "merge", "--branch", "feature/demo", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("merge receipt is no longer reachable", cp.stderr)

    def test_successful_landing_removes_goal_and_session_state(self):
        approval, _ = self.prepare_branch()
        goal_path = self.fx.goal_path("feature/demo")
        session = self.fx.root / "doc" / "session.md"
        session.parent.mkdir(parents=True, exist_ok=True)
        session.write_text("# Session\n\ncontinue\n", encoding="utf-8")
        self.assertEqual(self.fx.git("status", "--porcelain").stdout.strip(), "")
        landed = self.fx.h("land", "merge", "--message", "Land Goal")
        self.assertEqual(landed["result"], "landed")
        self.assertFalse(goal_path.exists())
        self.assertFalse(session.exists())
        self.assertNotEqual(self.fx.git("show-ref", "--verify", approval["ref"], check=False).returncode, 0)

    def test_no_op_abandonment_rejects_unique_durable_tree_changes(self):
        self.fx.h("branch", "start", "--name", "not-a-no-op")
        self.fx.write("unique.txt", "durable\n")
        self.fx.commit("unique work")
        cp = self.fx.h("abandon", "discard", "--target", "not-a-no-op", "--mode", "no-op", check=False)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("unique durable branch changes require --mode explicit", cp.stderr)

    def test_no_op_abandonment_accepts_history_that_returns_to_base_tree(self):
        self.fx.h("branch", "start", "--name", "actual-no-op")
        self.fx.write("temporary.txt", "temporary\n")
        self.fx.commit("temporary change")
        (self.fx.root / "temporary.txt").unlink()
        self.fx.commit("revert temporary change")
        result = self.fx.h("abandon", "discard", "--target", "actual-no-op", "--mode", "no-op")
        self.assertEqual(result["result"], "discarded")
        self.assertNotEqual(self.fx.git("show-ref", "--verify", "refs/heads/actual-no-op", check=False).returncode, 0)

    def test_explicit_abandonment_clears_goal_session_approval_and_ready_transaction(self):
        self.fx.h("branch", "start", "--name", "discard-goal")
        self.fx.write("discard.txt", "unique\n")
        self.fx.commit("discard work")
        approval = self.fx.h("approval", "record")
        self.fx.h("land", "prepare")
        session = self.fx.root / "doc" / "session.md"
        session.parent.mkdir(parents=True, exist_ok=True)
        session.write_text("# Session\n", encoding="utf-8")
        result = self.fx.h("abandon", "discard", "--target", "discard-goal", "--mode", "explicit")
        self.assertEqual(result["result"], "discarded")
        self.assertFalse(self.fx.goal_path("discard-goal").exists())
        self.assertFalse(session.exists())
        self.assertNotEqual(self.fx.git("show-ref", "--verify", approval["ref"], check=False).returncode, 0)
        self.assertEqual(self.fx.h("resume")["land_transactions"], [])

    def test_remote_discard_is_exact_and_explicit(self):
        self.fx.h("branch", "start", "--name", "remote-discard")
        self.fx.write("discard.txt", "unique\n")
        self.fx.commit("remote discard")
        self.fx.git("push", "-u", "origin", "remote-discard")
        result = self.fx.h(
            "abandon", "discard", "--target", "remote-discard", "--mode", "explicit", "--delete-remote"
        )
        self.assertEqual(result["result"], "discarded")
        remote_head = self.fx.git("ls-remote", "--heads", "origin", "refs/heads/remote-discard").stdout.strip()
        self.assertEqual(remote_head, "")


class HarnessRuntimeLandingSafetyTests(unittest.TestCase):
    def test_failed_merge_hook_leaves_mainline_untouched_and_contains_worktree_side_effects(self):
        fx = RepoFixture()
        try:
            fx.h("branch", "start", "--name", "feature/hook-failure")
            fx.write("one.txt", "one\n")
            fx.commit("one")
            fx.write("two.txt", "two\n")
            fx.commit("two")
            fx.h("approval", "record")
            fx.h("land", "prepare")
            base = fx.git("rev-parse", fx.mainline).stdout.strip()

            hook = fx.root / ".git" / "hooks" / "pre-merge-commit"
            hook.write_text("#!/bin/sh\ntouch hook-side-effect.txt\nexit 1\n", encoding="utf-8")
            hook.chmod(0o755)
            cp = fx.h("land", "merge", "--message", "blocked", check=False)
            self.assertEqual(cp.returncode, 2)
            self.assertIn("landing preparation failed before mainline update", cp.stderr)
            self.assertEqual(fx.git("rev-parse", fx.mainline).stdout.strip(), base)
            self.assertEqual(fx.git("status", "--porcelain").stdout, "")
            self.assertFalse((fx.root / "hook-side-effect.txt").exists())
            self.assertEqual(len(fx.h("resume")["land_transactions"]), 1)
        finally:
            fx.close()

    def test_local_landing_refuses_mainline_checked_out_in_linked_worktree(self):
        fx = RepoFixture()
        try:
            fx.h("branch", "start", "--name", "feature/linked-worktree")
            fx.write("one.txt", "one\n")
            fx.commit("one")
            fx.write("two.txt", "two\n")
            fx.commit("two")
            fx.h("approval", "record")
            fx.h("land", "prepare")
            base = fx.git("rev-parse", fx.mainline).stdout.strip()
            with tempfile.TemporaryDirectory(dir=fx.root.parent) as td:
                linked = Path(td) / "mainline-worktree"
                fx.git("worktree", "add", str(linked), fx.mainline)
                try:
                    cp = fx.h("land", "merge", "--branch", "feature/linked-worktree", check=False)
                    self.assertEqual(cp.returncode, 2)
                    self.assertIn("checked out in another linked Git worktree", cp.stderr)
                    self.assertEqual(fx.git("rev-parse", fx.mainline).stdout.strip(), base)
                finally:
                    fx.git("worktree", "remove", "--force", str(linked), check=False)
        finally:
            fx.close()

    def test_integrating_transaction_recovers_after_mainline_ref_update(self):
        fx = RepoFixture()
        original_complete = HARNESS.kernel.complete_local_integration
        try:
            fx.h("branch", "start", "--name", "feature/restart")
            fx.write("one.txt", "one\n")
            fx.commit("one")
            fx.write("two.txt", "two\n")
            fx.commit("two")
            fx.h("approval", "record")
            fx.h("land", "prepare")

            def interrupt_after_prepare(repo, data):
                raise HARNESS.HarnessError("simulated interruption")

            HARNESS.kernel.complete_local_integration = interrupt_after_prepare
            cp = fx.h("land", "merge", "--message", "Restart-safe landing", check=False)
            self.assertEqual(cp.returncode, 2)
            self.assertIn("simulated interruption", cp.stderr)
            tx = fx.h("resume")["land_transactions"][0]
            self.assertEqual(tx["phase"], "integrating")
            candidate = tx["merge_commit"]
            base = tx["base_commit"]

            fx.git("update-ref", f"refs/heads/{fx.mainline}", candidate, base)
            HARNESS.kernel.complete_local_integration = original_complete
            landed = fx.h("land", "merge", "--branch", "feature/restart")
            self.assertEqual(landed["result"], "landed")
            self.assertEqual(fx.git("rev-parse", fx.mainline).stdout.strip(), candidate)
        finally:
            HARNESS.kernel.complete_local_integration = original_complete
            fx.close()


class HarnessRuntimeConfigAndCheckTests(unittest.TestCase):
    def test_release_composition_and_classification_are_valid(self):
        project_root = SOURCE_RUNTIME.parents[1]
        self.assertEqual(HARNESS.composition_findings(project_root), [])

    def test_release_method_packs_and_authority_orchestrators_are_valid(self):
        project_root = SOURCE_RUNTIME.parents[1]
        self.assertEqual(HARNESS.method_pack_contract_findings(project_root), [])
        self.assertEqual(HARNESS.authority_orchestrator_findings(project_root), [])

    def test_release_spec_topology_contract_is_valid(self):
        project_root = SOURCE_RUNTIME.parents[1]
        self.assertEqual(HARNESS.spec_topology_contract_findings(project_root), [])

    def test_release_collaboration_model_contract_is_valid(self):
        project_root = SOURCE_RUNTIME.parents[1]
        self.assertEqual(HARNESS.collaboration_model_contract_findings(project_root), [])

    def test_release_runtime_modules_are_separated(self):
        project_root = SOURCE_RUNTIME.parents[1]
        self.assertEqual(HARNESS.runtime_module_findings(project_root), [])

    def test_release_startup_context_is_bounded(self):
        project_root = SOURCE_RUNTIME.parents[1]
        self.assertEqual(HARNESS.startup_context_findings(project_root), [])

    def test_release_split_vocabularies_are_valid_and_disjoint(self):
        project_root = SOURCE_RUNTIME.parents[1]
        self.assertEqual(HARNESS.vocabulary_findings(project_root), [])

    def test_vocabulary_split_detects_duplicate_term_across_authorities(self):
        project_root = SOURCE_RUNTIME.parents[1]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            harness = root / ".harness"
            harness.mkdir(parents=True)
            shutil.copy2(project_root / ".harness" / "README-vocabulary.md", harness / "README-vocabulary.md")
            shutil.copy2(project_root / ".harness" / "harness-extended-vocabulary.md", harness / "harness-extended-vocabulary.md")
            extended = harness / "harness-extended-vocabulary.md"
            extended.write_text(
                extended.read_text(encoding="utf-8") + "\n| **Goal** | competing definition |\n",
                encoding="utf-8",
            )
            findings = HARNESS.vocabulary_findings(root)
            self.assertTrue(any("defined in both" in finding and "Goal" in finding for finding in findings))

    def test_spec_topology_explicit_scopes_and_affected_closure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".harness" / "composition").mkdir(parents=True)
            (root / ".harness" / "composition" / "active.json").write_text(json.dumps({
                "selection": {"project_model": "spec"}
            }), encoding="utf-8")
            for rel in (
                "doc/spec/domain/identity.md",
                "doc/spec/domain/billing.md",
                "doc/spec/app/customer.md",
                "doc/spec/style/foundation.md",
            ):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"# {path.stem}\n", encoding="utf-8")
            manifest = root / "doc" / "spec" / "topology.json"
            manifest.write_text(json.dumps({
                "schema_version": 1,
                "project_model": "spec",
                "scopes": [
                    {"id": "domain.identity", "authority": "domain", "path": "doc/spec/domain/identity.md", "depends_on": []},
                    {"id": "domain.billing", "authority": "domain", "path": "doc/spec/domain/billing.md", "depends_on": ["domain.identity"]},
                    {"id": "app.customer", "authority": "app", "path": "doc/spec/app/customer.md", "depends_on": ["domain.billing"]},
                    {"id": "style.foundation", "authority": "style", "path": "doc/spec/style/foundation.md", "depends_on": []},
                ],
            }), encoding="utf-8")

            state = HARNESS.spec_topology_state(root)
            self.assertEqual(state["result"], "valid")
            self.assertEqual(state["mode"], "explicit")
            affected = invoke_harness(root, "spec", "affected", "--scope", "domain.billing")
            self.assertEqual(affected["load_scopes"], ["domain.billing", "domain.identity"])
            self.assertEqual(affected["impact_scopes"], ["app.customer", "domain.billing"])
            self.assertEqual(
                affected["graph_check_scopes"],
                ["app.customer", "domain.billing", "domain.identity"],
            )
            self.assertNotIn("style.foundation", affected["graph_check_scopes"])

    def test_spec_topology_command_exits_one_on_project_topology_findings(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".harness" / "composition").mkdir(parents=True)
            (root / ".harness" / "composition" / "active.json").write_text(json.dumps({
                "selection": {"project_model": "spec"}
            }), encoding="utf-8")
            topology = root / "doc/spec/topology.json"
            topology.parent.mkdir(parents=True, exist_ok=True)
            topology.write_text(json.dumps({
                "schema_version": 1,
                "project_model": "spec",
                "scopes": [{"id": "domain.billing", "authority": "domain", "path": "doc/spec/domain/missing.md", "depends_on": []}],
            }), encoding="utf-8")
            cp = invoke_harness(root, "spec", "topology", check=False)
            self.assertEqual(cp.returncode, 1)
            payload = json.loads(cp.stdout)
            self.assertEqual(payload["result"], "findings")
            self.assertTrue(any("missing" in finding for finding in payload["findings"]))

    def test_spec_topology_file_move_preserves_scope_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / "doc/spec/domain/billing.md"
            old.parent.mkdir(parents=True, exist_ok=True)
            old.write_text("# Billing\n", encoding="utf-8")
            manifest = root / "doc/spec/topology.json"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "schema_version": 1, "project_model": "spec",
                "scopes": [{"id": "domain.billing", "authority": "domain", "path": "doc/spec/domain/billing.md", "depends_on": []}],
            }
            manifest.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(HARNESS.spec_topology_state(root)["scopes"][0]["id"], "domain.billing")

            new = root / "doc/product/domain/billing.md"
            new.parent.mkdir(parents=True, exist_ok=True)
            old.replace(new)
            data["scopes"][0]["path"] = "doc/product/domain/billing.md"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            state = HARNESS.spec_topology_state(root)
            self.assertEqual(state["finding_count"], 0)
            self.assertEqual(state["scopes"][0]["id"], "domain.billing")
            self.assertEqual(state["scopes"][0]["path"], "doc/product/domain/billing.md")

    def test_spec_topology_requires_explicit_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old_shape = root / "doc/spec-domain.md"
            old_shape.parent.mkdir(parents=True, exist_ok=True)
            old_shape.write_text("# Domain\n", encoding="utf-8")

            state = HARNESS.spec_topology_state(root)
            self.assertEqual(state["result"], "unconfigured")
            self.assertEqual(state["mode"], "unconfigured")
            self.assertEqual(state["scopes"], [])

            modular = root / "doc/spec/domain/billing.md"
            modular.parent.mkdir(parents=True, exist_ok=True)
            modular.write_text("# Billing\n", encoding="utf-8")
            topology = root / "doc/spec/topology.json"
            topology.write_text(json.dumps({
                "schema_version": 1,
                "project_model": "spec",
                "scopes": [{"id": "domain.billing", "authority": "domain", "path": "doc/spec/domain/billing.md", "depends_on": []}],
            }), encoding="utf-8")
            state = HARNESS.spec_topology_state(root)
            self.assertEqual(state["result"], "valid")
            self.assertEqual(state["mode"], "explicit")
            self.assertEqual(state["scopes"][0]["id"], "domain.billing")

    def test_composition_rejects_supported_method_without_source_binding(self):
        project_root = SOURCE_RUNTIME.parents[1]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "copy"
            shutil.copytree(project_root, root)
            active_path = root / ".harness" / "composition" / "active.json"
            active = json.loads(active_path.read_text(encoding="utf-8"))
            active["sources"]["method_packs"].pop("event-storming")
            active_path.write_text(json.dumps(active), encoding="utf-8")
            findings = HARNESS.composition_findings(root)
            self.assertTrue(any("event-storming" in finding and "source binding" in finding for finding in findings))

    def test_method_pack_contract_reports_missing_required_section(self):
        project_root = SOURCE_RUNTIME.parents[1]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "copy"
            shutil.copytree(project_root, root)
            method = root / ".harness" / "methods" / "interview-me.md"
            method.write_text(method.read_text(encoding="utf-8").replace("## Completion", "## Done"), encoding="utf-8")
            findings = HARNESS.method_pack_contract_findings(root)
            self.assertTrue(any("Completion" in finding and "interview-me.md" in finding for finding in findings))

    def test_composition_rejects_unsupported_project_model(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            composition = root / ".harness" / "composition"
            runtime = root / ".harness" / "runtime"
            project_models = root / ".harness" / "project-models"
            collaboration_models = root / ".harness" / "collaboration-models"
            for directory in (composition, runtime, project_models, collaboration_models):
                directory.mkdir(parents=True, exist_ok=True)
            (runtime / "VERSION").write_text("17\n", encoding="utf-8")
            (project_models / "spec.md").write_text("# Spec\n", encoding="utf-8")
            (collaboration_models / "single-user.md").write_text("# Single\n", encoding="utf-8")
            (composition / "active.json").write_text(json.dumps({
                "schema_version": 1,
                "release": "17",
                "selection": {"project_model": "repository-native", "collaboration_model": "single-user", "method_packs": []},
                "supported": {"project_models": ["spec"], "collaboration_models": ["single-user"], "method_packs": []},
                "sources": {
                    "project_models": {"spec": ".harness/project-models/spec.md"},
                    "collaboration_models": {"single-user": ".harness/collaboration-models/single-user.md"},
                    "method_packs": {},
                },
            }), encoding="utf-8")
            paths = [
                ".harness/composition/active.json",
                ".harness/composition/classification.json",
                ".harness/runtime/VERSION",
                ".harness/project-models/spec.md",
                ".harness/collaboration-models/single-user.md",
            ]
            (composition / "classification.json").write_text(json.dumps({
                "schema_version": 1,
                "entries": [
                    {"path": rel, "layer": "kernel", "kind": "test", "authority": "test", "couplings": []}
                    for rel in paths
                ],
                "dynamic_rules": [],
            }), encoding="utf-8")
            findings = HARNESS.composition_findings(root)
            self.assertTrue(any("not supported" in finding and "repository-native" in finding for finding in findings))

    def test_composition_reports_unclassified_shipped_artifact(self):
        project_root = SOURCE_RUNTIME.parents[1]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "copy"
            shutil.copytree(project_root, root)
            extra = root / ".harness" / "unexpected.md"
            extra.write_text("# unexpected\n", encoding="utf-8")
            findings = HARNESS.composition_findings(root)
            self.assertIn("unclassified shipped Harness artifact: .harness/unexpected.md", findings)

    def test_explicit_mainline_must_match_bootstrap_mainline(self):
        fx = RepoFixture()
        try:
            config = fx.root / ".harness" / "runtime" / "config.json"
            data = json.loads(config.read_text(encoding="utf-8"))
            data["mainline"] = "trunk"
            data["bootstrap_mainline"] = "main"
            config.write_text(json.dumps(data), encoding="utf-8")
            previous_root = HARNESS.PROJECT_ROOT
            previous_config = HARNESS.CONFIG_PATH
            try:
                HARNESS.set_runtime_context(fx.root, config)
                with self.assertRaises(HARNESS.HarnessError):
                    HARNESS.load_config()
            finally:
                HARNESS.set_runtime_context(previous_root, previous_config)
        finally:
            fx.close()

    def test_bootstrap_defaults_to_empty_and_requires_explicit_seed_staging(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "empty-default"
            root.mkdir()
            run(["git", "init", "-b", "main"], root)
            run(["git", "config", "user.name", "Harness Test"], root)
            run(["git", "config", "user.email", "harness@example.test"], root)
            (root / "secret.env").write_text("SECRET=value\n", encoding="utf-8")
            result = invoke_harness(root, "repo", "bootstrap", "--message", "baseline", config_path=SOURCE_RUNTIME / "config.json")
            self.assertEqual(result["result"], "baseline created")
            self.assertEqual(run(["git", "ls-tree", "-r", "--name-only", "HEAD"], root).stdout.strip(), "")
            self.assertIn("?? secret.env", run(["git", "status", "--porcelain"], root).stdout)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "selected-seed"
            root.mkdir()
            run(["git", "init", "-b", "main"], root)
            run(["git", "config", "user.name", "Harness Test"], root)
            run(["git", "config", "user.email", "harness@example.test"], root)
            (root / "seed.txt").write_text("seed\n", encoding="utf-8")
            (root / "secret.env").write_text("SECRET=value\n", encoding="utf-8")
            invoke_harness(
                root, "repo", "bootstrap", "--seed-path", "seed.txt", "--message", "baseline",
                config_path=SOURCE_RUNTIME / "config.json",
            )
            tracked = run(["git", "ls-tree", "-r", "--name-only", "HEAD"], root).stdout.splitlines()
            self.assertEqual(tracked, ["seed.txt"])
            self.assertIn("?? secret.env", run(["git", "status", "--porcelain"], root).stdout)

    def test_auto_mainline_refuses_multiple_common_local_candidates_without_remote_default(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run(["git", "init", "-b", "main"], root)
            run(["git", "config", "user.name", "Harness Test"], root)
            run(["git", "config", "user.email", "harness@example.test"], root)
            (root / "base.txt").write_text("base\n", encoding="utf-8")
            run(["git", "add", "base.txt"], root)
            run(["git", "commit", "-m", "base"], root)
            run(["git", "branch", "master"], root)

            cp = invoke_harness(
                root, "repo", "status", check=False, config_path=SOURCE_RUNTIME / "config.json"
            )
            self.assertEqual(cp.returncode, 2)
            self.assertIn("cannot resolve mainline unambiguously", cp.stderr)
            self.assertIn("main, master", cp.stderr)

    def test_auto_mainline_remote_head_disambiguates_multiple_local_candidates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run(["git", "init", "-b", "main"], root)
            run(["git", "config", "user.name", "Harness Test"], root)
            run(["git", "config", "user.email", "harness@example.test"], root)
            (root / "base.txt").write_text("base\n", encoding="utf-8")
            run(["git", "add", "base.txt"], root)
            run(["git", "commit", "-m", "base"], root)
            run(["git", "branch", "master"], root)
            run(["git", "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/master"], root)

            result = invoke_harness(
                root, "repo", "status", config_path=SOURCE_RUNTIME / "config.json"
            )
            self.assertEqual(result["mainline"], "master")

    def test_bootstrap_refuses_pre_staged_index_without_all_seed_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run(["git", "init", "-b", "main"], root)
            run(["git", "config", "user.name", "Harness Test"], root)
            run(["git", "config", "user.email", "harness@example.test"], root)
            (root / "pre_staged_secret.txt").write_text("SECRET=value\n", encoding="utf-8")
            run(["git", "add", "pre_staged_secret.txt"], root)

            cp = invoke_harness(
                root, "repo", "bootstrap", "--message", "baseline",
                check=False, config_path=SOURCE_RUNTIME / "config.json",
            )
            self.assertEqual(cp.returncode, 2)
            self.assertIn("bootstrap index is not empty", cp.stderr)
            self.assertIn("pre_staged_secret.txt", cp.stderr)
            self.assertNotEqual(run(["git", "rev-parse", "--verify", "HEAD"], root, check=False).returncode, 0)

            cp_seed = invoke_harness(
                root, "repo", "bootstrap", "--seed-path", "pre_staged_secret.txt", "--message", "baseline",
                check=False, config_path=SOURCE_RUNTIME / "config.json",
            )
            self.assertEqual(cp_seed.returncode, 2)
            self.assertIn("bootstrap index is not empty", cp_seed.stderr)
            self.assertNotEqual(run(["git", "rev-parse", "--verify", "HEAD"], root, check=False).returncode, 0)

    def test_bootstrap_all_seed_files_is_explicit_opt_in_for_existing_index(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run(["git", "init", "-b", "main"], root)
            run(["git", "config", "user.name", "Harness Test"], root)
            run(["git", "config", "user.email", "harness@example.test"], root)
            (root / "already-staged.txt").write_text("staged\n", encoding="utf-8")
            (root / "also-seed.txt").write_text("seed\n", encoding="utf-8")
            run(["git", "add", "already-staged.txt"], root)

            result = invoke_harness(
                root, "repo", "bootstrap", "--all-seed-files", "--message", "baseline",
                config_path=SOURCE_RUNTIME / "config.json",
            )
            self.assertEqual(result["result"], "baseline created")
            tracked = run(["git", "ls-tree", "-r", "--name-only", "HEAD"], root).stdout.splitlines()
            self.assertEqual(sorted(tracked), ["already-staged.txt", "also-seed.txt"])

    def test_unexpected_runtime_failure_is_normalized_to_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            previous = HARNESS.kernel.discover_git_root
            try:
                def explode():
                    raise OSError("synthetic failure")

                HARNESS.kernel.discover_git_root = explode
                cp = invoke_harness(
                    root, "repo", "status", check=False, config_path=SOURCE_RUNTIME / "config.json"
                )
            finally:
                HARNESS.kernel.discover_git_root = previous

            self.assertEqual(cp.returncode, 3)
            payload = json.loads(cp.stderr)
            self.assertEqual(payload["error_kind"], "unexpected")
            self.assertIn("OSError: synthetic failure", payload["error"])
            self.assertNotIn("Traceback", cp.stderr)

    def test_remote_cleanup_requires_configured_remote_name_not_transport_string(self):
        fx = RepoFixture()
        try:
            with tempfile.TemporaryDirectory() as remote_td:
                remote = Path(remote_td) / "origin.git"
                run(["git", "init", "--bare", str(remote)], Path(remote_td))
                fx.git("remote", "set-url", "origin", str(remote))
                config = fx.root / ".harness" / "runtime" / "config.json"
                data = json.loads(config.read_text(encoding="utf-8"))
                data["remote"] = str(remote)
                config.write_text(json.dumps(data), encoding="utf-8")
                fx.commit("configure hostile remote transport string")
                fx.git("push", "-u", "origin", fx.mainline)
                fx.h("branch", "start", "--name", "remote-name-boundary")
                fx.write("discard.txt", "discard\n")
                fx.commit("discard")
                fx.git("push", "-u", "origin", "remote-name-boundary")
                cp = fx.h(
                    "abandon", "discard", "--target", "remote-name-boundary",
                    "--mode", "explicit", "--delete-remote", check=False
                )
                self.assertEqual(cp.returncode, 2)
                self.assertIn("must name a configured Git remote", cp.stderr)
                remote_head = run(
                    ["git", "ls-remote", "--heads", str(remote), "refs/heads/remote-name-boundary"],
                    fx.root,
                ).stdout.strip()
                self.assertNotEqual(remote_head, "")
        finally:
            fx.close()

    def test_parent_repository_is_rejected_instead_of_becoming_project_repository(self):
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td)
            project = parent / "project"
            runtime = project / ".harness" / "runtime"
            runtime.mkdir(parents=True)
            copy_runtime_sources(runtime)
            shutil.copy2(SOURCE_RUNTIME / "config.json", runtime / "config.json")
            run(["git", "init", "-b", "main"], parent)

            cp = invoke_harness(project, "repo", "status", check=False)
            self.assertEqual(cp.returncode, 2)
            self.assertIn("unsupported nested repository layout", cp.stderr)

    def test_independent_repository_embedded_in_parent_repository_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td)
            project = parent / "project"
            project.mkdir()
            run(["git", "init", "-b", "main"], parent)
            run(["git", "init", "-b", "main"], project)
            runtime = project / ".harness" / "runtime"
            runtime.mkdir(parents=True)
            copy_runtime_sources(runtime)
            shutil.copy2(SOURCE_RUNTIME / "config.json", runtime / "config.json")

            cp = invoke_harness(project, "repo", "status", check=False)
            self.assertEqual(cp.returncode, 2)
            self.assertIn("embedded inside parent Git repository", cp.stderr)

    def test_repository_with_submodule_gitlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "root"
            child = Path(td) / "child"
            root.mkdir()
            child.mkdir()
            for repo in (root, child):
                run(["git", "init", "-b", "main"], repo)
                run(["git", "config", "user.name", "Harness Test"], repo)
                run(["git", "config", "user.email", "harness@example.test"], repo)
            (child / "child.txt").write_text("child\n", encoding="utf-8")
            run(["git", "add", "-A"], child)
            run(["git", "commit", "-m", "child"], child)
            (root / "root.txt").write_text("root\n", encoding="utf-8")
            run(["git", "add", "-A"], root)
            run(["git", "commit", "-m", "root"], root)
            run(["git", "-c", "protocol.file.allow=always", "submodule", "add", str(child), "vendor/child"], root)
            run(["git", "commit", "-am", "add submodule"], root)

            runtime = root / ".harness" / "runtime"
            runtime.mkdir(parents=True)
            copy_runtime_sources(runtime)
            shutil.copy2(SOURCE_RUNTIME / "config.json", runtime / "config.json")
            cp = invoke_harness(root, "repo", "status", check=False)
            self.assertEqual(cp.returncode, 2)
            self.assertIn("Git submodules/gitlinks are present", cp.stderr)

    def test_structural_check_requires_assurance_operating_context_in_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            harness = root / ".harness"
            workflow = harness / "workflow"
            runtime = harness / "runtime"
            skills = harness / "skills"
            claude_skills = root / ".claude" / "skills"
            adapters = workflow / "agent"
            for directory in (workflow, runtime, skills, claude_skills, adapters):
                directory.mkdir(parents=True, exist_ok=True)
            (runtime / "config.json").write_text(json.dumps({
                "schema_version": 1,
                "mainline": "auto",
                "bootstrap_mainline": "main",
                "remote": "origin",
            }), encoding="utf-8")
            # Paths may exist on disk, but omission from the manifest must still be a finding.
            (harness / "harness-limitations.md").write_text("# limitations\n", encoding="utf-8")
            (harness / "harness-assurance.md").write_text("# assurance\n", encoding="utf-8")
            (workflow / "context-manifest.yaml").write_text("version: 1\n", encoding="utf-8")
            previous_root = HARNESS.PROJECT_ROOT
            previous_config = HARNESS.CONFIG_PATH
            try:
                HARNESS.set_runtime_context(root, runtime / "config.json")
                result = HARNESS.checker.cmd_check(type("Args", (), {})())
            finally:
                HARNESS.set_runtime_context(previous_root, previous_config)
            self.assertEqual(result["result"], "findings")
            self.assertTrue(any(".harness/harness-limitations.md" in finding for finding in result["findings"]))
            self.assertTrue(any(".harness/harness-assurance.md" in finding for finding in result["findings"]))

    def test_routing_check_rejects_duplicate_concern(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            routing = root / ".harness" / "workflow" / "routing.md"
            routing.parent.mkdir(parents=True)
            routing.write_text(
                "# Routing\n\n| Concern | Owner |\n|---|---|\n| Same | One |\n| Same | Two |\n",
                encoding="utf-8",
            )
            findings = HARNESS.routing_findings(root)
            self.assertTrue(any("appears more than once" in finding for finding in findings))

    def test_behavior_coverage_check_rejects_uncovered_required_invariant(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            behavior = root / ".harness" / "evals" / "behavior"
            behavior.mkdir(parents=True)
            (behavior / "scenarios.json").write_text(json.dumps({
                "schema_version": 2,
                "scenarios": [{"id": "s1", "family": "x", "covers": []}],
            }), encoding="utf-8")
            findings, summary = HARNESS.behavior_coverage_findings(root, [{
                "id": "AUTH-01", "behavior_required": True,
            }])
            self.assertEqual(summary["uncovered"], ["AUTH-01"])
            self.assertTrue(any("AUTH-01" in finding for finding in findings))

    def test_semantic_evidence_check_reports_old_input_digest_stale_without_structural_finding(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = root / ".harness" / "evals" / "behavior" / "evidence"
            evidence.mkdir(parents=True)
            (evidence / "old.json").write_text(json.dumps({
                "schema_version": 2,
                "profile": "test/profile",
                "evaluation_source": "live_runner",
                "result": "pass",
                "passed": 17,
                "total": 17,
                "evaluation_input_digest": "0" * 64,
                "suite_digest": "1" * 64,
            }), encoding="utf-8")
            evidence_findings, summary = HARNESS.semantic_evidence_findings(root, "a" * 64, "2" * 64)
            self.assertEqual(summary["status"], "stale")
            self.assertEqual(summary["stale_profiles"], {"test/profile": [".harness/evals/behavior/evidence/old.json"]})
            self.assertEqual(evidence_findings, [])

    def test_schema_v1_semantic_surface_evidence_is_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = root / ".harness" / "evals" / "behavior" / "evidence"
            evidence.mkdir(parents=True)
            (evidence / "schema-v1.json").write_text(json.dumps({
                "schema_version": 1,
                "profile": "test/profile",
                "evaluation_source": "live_runner",
                "result": "pass",
                "passed": 17,
                "total": 17,
                "semantic_surface_digest": "a" * 64,
                "suite_digest": "b" * 64,
            }), encoding="utf-8")
            findings, summary = HARNESS.semantic_evidence_findings(root, "a" * 64, "b" * 64)
            self.assertEqual(findings, [])
            self.assertEqual(summary["status"], "stale")
            self.assertIn("test/profile", summary["stale_profiles"])


    def test_assure_is_green_only_for_current_named_profile(self):
        current_check = {
            "result": "no change",
            "finding_count": 0,
            "maturity_dimensions": {},
            "semantic_regression": {
                "assurance_scope": "constitutional",
                "evaluation_input_digest": "c" * 64,
                "semantic_surface_digest": "a" * 64,
                "suite_digest": "b" * 64,
                "evidence": {
                    "status": "current",
                    "current_profiles": {"openai/gpt/test": ["evidence.json"]},
                    "stale_profiles": {},
                },
            },
        }
        previous_check = HARNESS.checker.cmd_check
        previous_verify = HARNESS.checker.run_assurance_verification
        try:
            HARNESS.checker.cmd_check = lambda args: current_check
            HARNESS.checker.run_assurance_verification = lambda root: [{
                "name": "tests", "status": "pass", "returncode": 0, "stdout_tail": "", "stderr_tail": ""
            }]
            green = HARNESS.cmd_assure(type("Args", (), {"profile": "openai/gpt/test"})())
            unknown = HARNESS.cmd_assure(type("Args", (), {"profile": "anthropic/claude/test"})())
        finally:
            HARNESS.checker.cmd_check = previous_check
            HARNESS.checker.run_assurance_verification = previous_verify
        self.assertEqual(green["result"], "GREEN")
        self.assertEqual(unknown["result"], "UNKNOWN")

    def test_assure_is_unknown_for_stale_named_profile(self):
        stale_check = {
            "result": "no change",
            "finding_count": 0,
            "maturity_dimensions": {},
            "semantic_regression": {
                "assurance_scope": "constitutional",
                "evaluation_input_digest": "c" * 64,
                "semantic_surface_digest": "a" * 64,
                "suite_digest": "b" * 64,
                "evidence": {
                    "status": "stale",
                    "current_profiles": {},
                    "stale_profiles": {"openai/gpt/test": ["old.json"]},
                },
            },
        }
        previous_check = HARNESS.checker.cmd_check
        previous_verify = HARNESS.checker.run_assurance_verification
        try:
            HARNESS.checker.cmd_check = lambda args: stale_check
            HARNESS.checker.run_assurance_verification = lambda root: [{
                "name": "tests", "status": "pass", "returncode": 0, "stdout_tail": "", "stderr_tail": ""
            }]
            result = HARNESS.cmd_assure(type("Args", (), {"profile": "openai/gpt/test"})())
        finally:
            HARNESS.checker.cmd_check = previous_check
            HARNESS.checker.run_assurance_verification = previous_verify
        self.assertEqual(result["result"], "UNKNOWN")
        self.assertIn("stale", result["reason"])

    def test_structural_check_requires_semantic_and_runtime_regression_inputs_in_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            harness = root / ".harness"
            workflow = harness / "workflow"
            runtime = harness / "runtime"
            behavior = harness / "evals" / "behavior"
            behavior_tests = behavior / "tests"
            runtime_tests = runtime / "tests"
            for directory in (workflow, runtime, behavior_tests, runtime_tests):
                directory.mkdir(parents=True, exist_ok=True)

            (runtime / "config.json").write_text(json.dumps({
                "schema_version": 1,
                "mainline": "auto",
                "bootstrap_mainline": "main",
                "remote": "origin",
            }), encoding="utf-8")
            # These files exist, so the finding must be about missing manifest registration,
            # not ordinary missing-artifact detection.
            for path, content in {
                behavior / "README.md": "# behavior\n",
                behavior / "semantic-surface.json": json.dumps({"schema_version": 1, "include_globs": [".harness/workflow/*.md"]}),
                behavior / "scenarios.json": json.dumps({"schema_version": 2, "scenarios": []}),
                behavior / "run.py": "# evaluator\n",
                behavior_tests / "test_behavior.py": "# tests\n",
                runtime_tests / "test_harness.py": "# tests\n",
            }.items():
                path.write_text(content, encoding="utf-8")
            (workflow / "context-manifest.yaml").write_text("version: 1\n", encoding="utf-8")

            previous_root = HARNESS.PROJECT_ROOT
            previous_config = HARNESS.CONFIG_PATH
            try:
                HARNESS.set_runtime_context(root, runtime / "config.json")
                result = HARNESS.checker.cmd_check(type("Args", (), {})())
            finally:
                HARNESS.set_runtime_context(previous_root, previous_config)

            self.assertEqual(result["result"], "findings")
            manifest_findings = result["checks"]["context_manifest"]["findings"]
            required_paths = {
                ".harness/evals/behavior/README.md",
                ".harness/evals/behavior/semantic-surface.json",
                ".harness/evals/behavior/scenarios.json",
                ".harness/evals/behavior/run.py",
                ".harness/evals/behavior/tests/test_behavior.py",
                ".harness/runtime/tests/test_harness.py",
            }
            for required_path in required_paths:
                self.assertTrue(
                    any(required_path in finding for finding in manifest_findings),
                    f"missing manifest-registration finding for {required_path}: {manifest_findings}",
                )

    def test_guide_registry_requires_each_guide_in_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            guides = root / ".harness" / "guides"
            guides.mkdir(parents=True)
            (guides / "definition.md").write_text("# Guides\n", encoding="utf-8")
            (guides / "general.md").write_text("# General\n", encoding="utf-8")
            findings = HARNESS.guide_registry_findings(root, [".harness/guides/definition.md"])
            self.assertTrue(any("general.md" in finding for finding in findings))

    def test_invalid_runtime_config_is_reported_as_structural_check_finding(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / ".harness" / "runtime"
            runtime.mkdir(parents=True)
            (runtime / "config.json").write_text(json.dumps({
                "schema_version": 1,
                "mainline": "auto",
                "bootstrap_mainline": "main",
                "remote": "--upload-pack=surprise",
            }), encoding="utf-8")
            previous_root = HARNESS.PROJECT_ROOT
            previous_config = HARNESS.CONFIG_PATH
            try:
                HARNESS.set_runtime_context(root, runtime / "config.json")
                result = HARNESS.checker.cmd_check(type("Args", (), {})())
            finally:
                HARNESS.set_runtime_context(previous_root, previous_config)
            self.assertEqual(result["result"], "findings")
            self.assertTrue(any("remote" in finding for finding in result["findings"]))

    def test_corrupt_transaction_metadata_is_refused_and_visible_on_resume(self):
        fx = RepoFixture()
        try:
            fx.h("branch", "start", "--name", "feature/corrupt-state")
            fx.write("state.txt", "ready\n")
            fx.commit("feature")
            fx.h("approval", "record")
            fx.h("land", "prepare")

            state_files = list((fx.root / ".git" / "harness" / "land").glob("*.json"))
            self.assertEqual(len(state_files), 1)
            state = json.loads(state_files[0].read_text(encoding="utf-8"))
            state["phase"] = "impossible-phase"
            state_files[0].write_text(json.dumps(state), encoding="utf-8")

            cp = fx.h("land", "merge", check=False)
            self.assertEqual(cp.returncode, 2)
            self.assertIn("unsupported phase", cp.stderr)

            resume = fx.h("resume")
            self.assertEqual(len(resume["land_transactions"]), 1)
            self.assertIn("unsupported phase", resume["land_transactions"][0]["error"])
        finally:
            fx.close()

    def test_harness_link_check_ignores_unowned_project_markdown(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".harness").mkdir()
            (root / ".harness" / "owned.md").write_text("[ok](target.md)\n", encoding="utf-8")
            (root / ".harness" / "target.md").write_text("ok\n", encoding="utf-8")
            (root / "README.md").write_text("[project-broken](missing.md)\n", encoding="utf-8")
            self.assertEqual(HARNESS.link_findings(root), [])

    def test_wrapper_check_detects_duplicate_mapping_and_missing_authoritative_skill(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            skills = root / ".harness" / "skills"
            skills.mkdir(parents=True)
            (skills / "a.md").write_text("a\n", encoding="utf-8")
            (skills / "b.md").write_text("b\n", encoding="utf-8")
            for name in ("one", "two"):
                wrapper = root / ".claude" / "skills" / name / "SKILL.md"
                wrapper.parent.mkdir(parents=True, exist_ok=True)
                wrapper.write_text("Use .harness/skills/a.md\n", encoding="utf-8")

            findings = HARNESS.wrapper_findings(root)
            self.assertTrue(any("duplicate Claude wrappers" in finding for finding in findings))
            self.assertTrue(any(".harness/skills/b.md has no Claude wrapper" in finding for finding in findings))



class HarnessRelease17CheckTests(unittest.TestCase):
    def copy_release(self, td: str) -> Path:
        root = Path(td) / "copy"
        shutil.copytree(SOURCE_RUNTIME.parents[1], root, ignore=shutil.ignore_patterns("__pycache__"))
        return root

    def test_release_manifest_does_not_restate_selection_and_profiles_exist(self):
        project_root = SOURCE_RUNTIME.parents[1]
        self.assertEqual(HARNESS.manifest_composition_findings(project_root), [])
        self.assertEqual(HARNESS.assurance_profile_findings(project_root), [])

    def test_manifest_restating_active_selection_is_a_finding(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.copy_release(td)
            manifest = root / ".harness" / "workflow" / "context-manifest.yaml"
            text = manifest.read_text(encoding="utf-8").replace(
                "  project_models:\n",
                "  active_collaboration_model: .harness/collaboration-models/cooperative-multi-user.md\n  project_models:\n",
                1,
            )
            manifest.write_text(text, encoding="utf-8")
            findings = HARNESS.manifest_composition_findings(root)
            self.assertTrue(any("composition.active_collaboration_model" in finding for finding in findings))

    def test_manifest_inventory_must_match_active_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.copy_release(td)
            manifest = root / ".harness" / "workflow" / "context-manifest.yaml"
            text = manifest.read_text(encoding="utf-8")
            text = text.replace("    single-user: .harness/collaboration-models/single-user.md\n", "", 1)
            manifest.write_text(text, encoding="utf-8")
            findings = HARNESS.manifest_composition_findings(root)
            self.assertTrue(any("collaboration_models inventory" in finding for finding in findings))

    def test_selecting_single_user_keeps_harness_coherent_without_prose_edits(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.copy_release(td)
            active_path = root / ".harness" / "composition" / "active.json"
            active = json.loads(active_path.read_text(encoding="utf-8"))
            active["selection"]["collaboration_model"] = "single-user"
            active_path.write_text(json.dumps(active, indent=2) + "\n", encoding="utf-8")
            self.assertEqual(HARNESS.composition_findings(root), [])
            self.assertEqual(HARNESS.manifest_composition_findings(root), [])
            self.assertEqual(HARNESS.assurance_profile_findings(root), [])
            self.assertEqual(HARNESS.active_collaboration_model(root), "single-user")

    def test_supported_collaboration_model_without_assurance_profile_is_a_finding(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.copy_release(td)
            assurance = root / ".harness" / "harness-assurance.md"
            assurance.write_text(
                assurance.read_text(encoding="utf-8").replace("### Operating profile: `cooperative-multi-user`", "### Cooperative profile"),
                encoding="utf-8",
            )
            findings = HARNESS.assurance_profile_findings(root)
            self.assertTrue(any("`cooperative-multi-user`" in finding for finding in findings))

    def test_claude_skill_directory_without_skill_file_is_a_finding(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.copy_release(td)
            (root / ".claude" / "skills" / "orphan").mkdir()
            findings = HARNESS.wrapper_findings(root)
            self.assertTrue(any(".claude/skills/orphan" in finding and "without SKILL.md" in finding for finding in findings))

    def test_ci_must_trigger_on_claude_wrappers(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.copy_release(td)
            workflow = root / ".github" / "workflows" / "harness-ci.yml"
            workflow.write_text(workflow.read_text(encoding="utf-8").replace('      - ".claude/**"\n', ""), encoding="utf-8")
            findings = HARNESS.release_evidence_findings(root)
            self.assertTrue(any('.claude/**' in finding for finding in findings))

    def test_release_note_is_derived_from_version(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.copy_release(td)
            version = (root / ".harness" / "runtime" / "VERSION").read_text(encoding="utf-8").strip()
            (root / ".harness" / "releases" / f"{version}.md").unlink()
            findings = HARNESS.release_evidence_findings(root)
            self.assertTrue(any(f"releases/{version}.md" in finding for finding in findings))


class HarnessRuntimeHardeningTests(unittest.TestCase):
    def test_missing_version_file_is_normalized_json_error(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / ".harness" / "runtime"
            runtime.mkdir(parents=True)
            copy_runtime_sources(runtime)
            cp = run([sys.executable, str(runtime / "harness.py"), "repo", "status"], Path(td), check=False)
            self.assertEqual(cp.returncode, 2, cp.stderr)
            error = json.loads(cp.stderr)
            self.assertIn("cannot read Harness version specification", error["error"])
            self.assertNotIn("Traceback", cp.stderr)

    def test_runtime_command_timeout_is_bounded_and_kills_stuck_process(self):
        with self.assertRaises(HARNESS.HarnessError) as ctx:
            HARNESS.run(
                [sys.executable, "-c", "import time; time.sleep(5)"],
                timeout_seconds=0.05,
            )
        self.assertIn("command timed out", str(ctx.exception))

    def test_runtime_subprocess_environment_is_noninteractive(self):
        cp = HARNESS.run(
            [
                sys.executable,
                "-c",
                (
                    "import os,sys; "
                    "print(os.environ.get('GIT_TERMINAL_PROMPT')); "
                    "print(os.environ.get('GCM_INTERACTIVE')); "
                    "print(sys.stdin.read())"
                ),
            ],
            timeout_seconds=2,
        )
        lines = cp.stdout.splitlines()
        self.assertEqual(lines[:2], ["0", "Never"])

    def test_mutating_command_fails_fast_when_repository_lifecycle_lock_is_held(self):
        fx = RepoFixture()
        holder = None
        try:
            code = (
                "import importlib.util,pathlib,sys,time; "
                "spec=importlib.util.spec_from_file_location('holder', sys.argv[1]); "
                "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); "
                "repo=pathlib.Path(sys.argv[2]); "
                "lock=m.advisory_lock(m.repository_lifecycle_lock_path(repo),'test holder'); "
                "lock.__enter__(); print('READY', flush=True); time.sleep(10)"
            )
            holder = subprocess.Popen(
                [sys.executable, "-c", code, str(SOURCE_RUNTIME / "harness.py"), str(fx.root)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(holder.stdout.readline().strip(), "READY")
            cp = fx.h("branch", "start", "--name", "feature/blocked", check=False)
            self.assertEqual(cp.returncode, 2)
            self.assertIn("lifecycle mutation already in progress", cp.stderr)
            # Read-only inspection remains available while a mutation is locked.
            status = fx.h("repo", "status")
            self.assertEqual(status["git"], "initialized")
        finally:
            if holder is not None:
                holder.terminate()
                try:
                    holder.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    holder.kill()
                    holder.wait(timeout=2)
                if holder.stdout is not None:
                    holder.stdout.close()
                if holder.stderr is not None:
                    holder.stderr.close()
            fx.close()

    def test_linked_worktrees_share_repository_lifecycle_lock(self):
        fx = RepoFixture()
        linked_td = tempfile.TemporaryDirectory()
        try:
            linked = Path(linked_td.name) / "linked"
            fx.git("worktree", "add", "--detach", str(linked), fx.mainline)
            self.assertEqual(
                HARNESS.repository_lifecycle_lock_path(fx.root),
                HARNESS.repository_lifecycle_lock_path(linked),
            )
        finally:
            fx.git("worktree", "remove", "--force", str(Path(linked_td.name) / "linked"), check=False)
            linked_td.cleanup()
            fx.close()

    def test_invalid_timeout_environment_is_rejected(self):
        old = os.environ.get("HARNESS_COMMAND_TIMEOUT_SECONDS")
        try:
            os.environ["HARNESS_COMMAND_TIMEOUT_SECONDS"] = "nan"
            with self.assertRaises(HARNESS.HarnessError):
                HARNESS.command_timeout_seconds()
        finally:
            if old is None:
                os.environ.pop("HARNESS_COMMAND_TIMEOUT_SECONDS", None)
            else:
                os.environ["HARNESS_COMMAND_TIMEOUT_SECONDS"] = old


if __name__ == "__main__":
    unittest.main()


class HarnessCooperativeMultiUserTests(unittest.TestCase):
    def setUp(self):
        self.fx = RepoFixture()
        self.clones: list[tempfile.TemporaryDirectory] = []
        active = {
            "schema_version": 1,
            "release": "17",
            "selection": {
                "project_model": "spec",
                "collaboration_model": "cooperative-multi-user",
                "method_packs": [],
            },
        }
        self.fx.write(".harness/composition/active.json", json.dumps(active, indent=2) + "\n")
        self.fx.commit("test: enable cooperative collaboration")
        self.fx.git("push", "origin", self.fx.mainline)
        self.fx.h("collaboration", "configure", "--actor", "alice", "--role", "contributor")

    def tearDown(self):
        for tmp in reversed(self.clones):
            tmp.cleanup()
        self.fx.close()

    def clone_workspace(self, actor: str, role: str) -> Path:
        shm = Path("/dev/shm")
        temp_root = str(shm) if shm.is_dir() and os.access(shm, os.W_OK) else None
        tmp = tempfile.TemporaryDirectory(dir=temp_root)
        self.clones.append(tmp)
        root = Path(tmp.name) / "workspace"
        run(["git", "clone", "--branch", self.fx.mainline, str(self.fx.remote), str(root)], self.fx.root)
        run(["git", "config", "user.name", f"Harness {actor}"], root)
        run(["git", "config", "user.email", f"{actor}@example.test"], root)
        invoke_harness(root, "collaboration", "configure", "--actor", actor, "--role", role)
        return root

    def publish_goal(self, root: Path, branch: str, filename: str, text: str, approved_by: str = "owner") -> dict[str, object]:
        invoke_harness(root, "branch", "start", "--name", branch)
        goal = root / "doc" / "goals" / f"{branch}.md"
        goal.parent.mkdir(parents=True, exist_ok=True)
        goal.write_text(f"# Goal\n\n{text}\n", encoding="utf-8")
        target = root / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text + "\n", encoding="utf-8")
        run(["git", "add", "-A"], root)
        run(["git", "commit", "-m", f"work: {branch}"], root)
        invoke_harness(root, "approval", "record")
        return invoke_harness(root, "handoff", "publish", "--approved-by", approved_by)

    def test_contributor_cannot_land_and_integration_authority_can_consume_handoff(self):
        published = self.publish_goal(self.fx.root, "feature/alice", "alice.txt", "alice outcome")
        blocked = self.fx.h("land", "prepare", check=False)
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("integration-authority", blocked.stderr)

        integration = self.clone_workspace("integrator", "integration-authority")
        accepted = invoke_harness(integration, "handoff", "accept", "--branch", "feature/alice")
        self.assertEqual(accepted["handoff_commit"], published["handoff_commit"])
        assessed = invoke_harness(integration, "land", "assess", "--branch", "feature/alice")
        self.assertEqual(assessed["result"], "READY_FOR_LANDING")
        invoke_harness(integration, "land", "prepare", "--branch", "feature/alice")
        landed = invoke_harness(integration, "land", "merge", "--branch", "feature/alice")
        self.assertEqual(landed["result"], "landed")
        remote_mainline = run(["git", "--git-dir", str(self.fx.remote), "rev-parse", self.fx.mainline], self.fx.root).stdout.strip()
        self.assertEqual(remote_mainline, landed["merge_commit"])
        refs = run(["git", "--git-dir", str(self.fx.remote), "for-each-ref", "--format=%(refname)", "refs/harness"], self.fx.root).stdout
        self.assertNotIn("feature/alice", refs)
        remote_goal = run(["git", "--git-dir", str(self.fx.remote), "show-ref", "--verify", "--quiet", "refs/heads/feature/alice"], self.fx.root, check=False)
        self.assertNotEqual(remote_goal.returncode, 0)

    def test_accepted_handoff_cannot_be_withdrawn_by_contributor_until_release(self):
        self.publish_goal(self.fx.root, "feature/held", "held.txt", "held outcome")
        integration = self.clone_workspace("integrator", "integration-authority")
        invoke_harness(integration, "handoff", "accept", "--branch", "feature/held")

        refused = self.fx.h("handoff", "withdraw", "--branch", "feature/held", check=False)
        self.assertEqual(refused.returncode, 2)
        self.assertIn("accepted by the integration authority", refused.stderr)

        drop = invoke_harness(integration, "approval", "drop", "--branch", "feature/held", check=False)
        self.assertEqual(drop.returncode, 2)
        self.assertIn("cannot be dropped independently", drop.stderr)
        discard = invoke_harness(integration, "abandon", "discard", "--target", "feature/held", "--mode", "explicit", check=False)
        self.assertEqual(discard.returncode, 2)
        self.assertIn("cannot be abandoned independently", discard.stderr)

        released = invoke_harness(integration, "handoff", "release", "--branch", "feature/held")
        self.assertEqual(released["result"], "released")
        withdrawn = self.fx.h("handoff", "withdraw", "--branch", "feature/held")
        self.assertEqual(withdrawn["result"], "withdrawn")

    def test_second_independent_handoff_blocks_after_first_goal_moves_mainline(self):
        bob = self.clone_workspace("bob", "contributor")
        integration = self.clone_workspace("integrator", "integration-authority")

        self.publish_goal(self.fx.root, "feature/alice-first", "alice-first.txt", "alice first")
        self.publish_goal(bob, "feature/bob-second", "bob-second.txt", "bob second")

        invoke_harness(integration, "handoff", "accept", "--branch", "feature/alice-first")
        invoke_harness(integration, "land", "prepare", "--branch", "feature/alice-first")
        invoke_harness(integration, "land", "merge", "--branch", "feature/alice-first")

        accepted_bob = invoke_harness(integration, "handoff", "accept", "--branch", "feature/bob-second")
        self.assertEqual(accepted_bob["contributor_actor"], "bob")
        assessed = invoke_harness(integration, "land", "assess", "--branch", "feature/bob-second")
        self.assertEqual(assessed["result"], "LANDING_BLOCKED")
        self.assertIn("mainline moved", assessed["cause"])
        self.assertNotEqual(assessed["evidence"]["handoff_base"], assessed["evidence"]["current_mainline"])

        prepare = invoke_harness(integration, "land", "prepare", "--branch", "feature/bob-second", check=False)
        self.assertEqual(prepare.returncode, 2)
        self.assertIn("LANDING_BLOCKED", prepare.stderr)

        invoke_harness(integration, "handoff", "release", "--branch", "feature/bob-second")
        withdrawn = invoke_harness(bob, "handoff", "withdraw", "--branch", "feature/bob-second")
        self.assertEqual(withdrawn["result"], "withdrawn")

    def test_release_recovers_after_acceptance_rewind_and_partial_local_cleanup(self):
        self.publish_goal(self.fx.root, "feature/release-retry", "release-retry.txt", "release retry")
        integration = self.clone_workspace("integrator", "integration-authority")
        accepted = invoke_harness(integration, "handoff", "accept", "--branch", "feature/release-retry")
        # Simulate a release interrupted after its remote compare-and-swap (handoff ref back at
        # the handoff commit) and after part of the local cleanup.
        run(["git", "switch", self.fx.mainline], integration)
        run(["git", "push", "--force", "origin", f"{accepted['handoff_commit']}:refs/harness/handoff/feature/release-retry"], integration)
        run(["git", "update-ref", "-d", "refs/heads/feature/release-retry", accepted["ready_commit"]], integration)

        released = invoke_harness(integration, "handoff", "release", "--branch", "feature/release-retry")
        self.assertEqual(released["result"], "released")
        self.assertTrue(released["remote_handoff_retained"])
        self.assertFalse((integration / "doc/goals/feature/release-retry.md").exists())
        approval = run(["git", "show-ref", "--verify", "--quiet", "refs/harness/landing-approval/feature/release-retry"], integration, check=False)
        self.assertNotEqual(approval.returncode, 0)

        withdrawn = self.fx.h("handoff", "withdraw", "--branch", "feature/release-retry")
        self.assertEqual(withdrawn["result"], "withdrawn")

    def test_interrupted_release_completes_after_contributor_already_withdrew(self):
        self.publish_goal(self.fx.root, "feature/release-late", "release-late.txt", "release late")
        integration = self.clone_workspace("integrator", "integration-authority")
        accepted = invoke_harness(integration, "handoff", "accept", "--branch", "feature/release-late")
        run(["git", "switch", self.fx.mainline], integration)
        run(["git", "push", "--force", "origin", f"{accepted['handoff_commit']}:refs/harness/handoff/feature/release-late"], integration)
        self.assertEqual(self.fx.h("handoff", "withdraw", "--branch", "feature/release-late")["result"], "withdrawn")

        released = invoke_harness(integration, "handoff", "release", "--branch", "feature/release-late")
        self.assertEqual(released["result"], "released")
        self.assertFalse(released["remote_handoff_retained"])
        self.assertIsNone(invoke_harness(integration, "resume")["accepted_handoff"])

    def remote_ref(self, ref: str) -> str | None:
        cp = run(["git", "--git-dir", str(self.fx.remote), "rev-parse", "--verify", "--quiet", ref], self.fx.root, check=False)
        return cp.stdout.strip() or None

    def test_accept_racing_withdraw_preflight_blocks_withdrawal(self):
        published = self.publish_goal(self.fx.root, "feature/race-a", "race-a.txt", "race a")
        integration = self.clone_workspace("integrator", "integration-authority")
        original = HARNESS.collaboration_model.fetch_remote_handoff
        accepted: dict[str, object] = {}

        def fetch_then_accept(repo, branch):
            # Withdrawal has passed its "not accepted" preflight; the integrator now accepts.
            result = original(repo, branch)
            HARNESS.collaboration_model.fetch_remote_handoff = original
            accepted.update(invoke_harness(integration, "handoff", "accept", "--branch", branch))
            return result

        HARNESS.collaboration_model.fetch_remote_handoff = fetch_then_accept
        try:
            refused = self.fx.h("handoff", "withdraw", "--branch", "feature/race-a", check=False)
        finally:
            HARNESS.collaboration_model.fetch_remote_handoff = original

        self.assertEqual(accepted["result"], "accepted")
        self.assertEqual(refused.returncode, 2)
        self.assertIn("nothing was withdrawn", refused.stderr)
        self.assertEqual(self.remote_ref("refs/harness/handoff/feature/race-a"), accepted["acceptance_commit"])
        self.assertEqual(self.remote_ref("refs/heads/feature/race-a"), published["ready_commit"])
        assessed = invoke_harness(integration, "land", "assess", "--branch", "feature/race-a")
        self.assertEqual(assessed["result"], "READY_FOR_LANDING")
        invoke_harness(integration, "land", "prepare", "--branch", "feature/race-a")
        landed = invoke_harness(integration, "land", "merge", "--branch", "feature/race-a")
        self.assertEqual(landed["result"], "landed")
        self.assertIsNone(self.remote_ref("refs/harness/handoff/feature/race-a"))
        self.assertIsNone(self.remote_ref("refs/heads/feature/race-a"))

    def test_withdraw_racing_accept_preflight_blocks_acceptance(self):
        self.publish_goal(self.fx.root, "feature/race-b", "race-b.txt", "race b")
        integration = self.clone_workspace("integrator", "integration-authority")
        original = HARNESS.collaboration_model.fetch_remote_handoff
        withdrawn: dict[str, object] = {}

        def fetch_then_withdraw(repo, branch):
            # Acceptance has fetched/validated the handoff; the contributor now withdraws.
            result = original(repo, branch)
            HARNESS.collaboration_model.fetch_remote_handoff = original
            withdrawn.update(invoke_harness(self.fx.root, "handoff", "withdraw", "--branch", branch))
            return result

        HARNESS.collaboration_model.fetch_remote_handoff = fetch_then_withdraw
        try:
            refused = invoke_harness(integration, "handoff", "accept", "--branch", "feature/race-b", check=False)
        finally:
            HARNESS.collaboration_model.fetch_remote_handoff = original

        self.assertEqual(withdrawn["result"], "withdrawn")
        self.assertEqual(refused.returncode, 2)
        self.assertIn("nothing was accepted", refused.stderr)
        self.assertIsNone(self.remote_ref("refs/harness/handoff/feature/race-b"))
        self.assertIsNone(self.remote_ref("refs/heads/feature/race-b"))
        self.assertIsNone(invoke_harness(integration, "resume")["accepted_handoff"])
        local = run(["git", "show-ref", "--verify", "--quiet", "refs/heads/feature/race-b"], integration, check=False)
        self.assertNotEqual(local.returncode, 0)

    def test_accept_resumes_after_interruption_between_remote_acceptance_and_local_state(self):
        self.publish_goal(self.fx.root, "feature/resume-accept", "resume-accept.txt", "resume accept")
        integration = self.clone_workspace("integrator", "integration-authority")
        original = HARNESS.collaboration_model.atomic_json

        def crash(path, data):
            raise RuntimeError("simulated crash before accepted-handoff state is persisted")

        HARNESS.collaboration_model.atomic_json = crash
        try:
            crashed = invoke_harness(integration, "handoff", "accept", "--branch", "feature/resume-accept", check=False)
        finally:
            HARNESS.collaboration_model.atomic_json = original
        self.assertEqual(crashed.returncode, 3)
        live = self.remote_ref("refs/harness/handoff/feature/resume-accept")
        self.assertIsNotNone(live)

        resumed = invoke_harness(integration, "handoff", "accept", "--branch", "feature/resume-accept")
        self.assertEqual(resumed["result"], "accepted")
        self.assertEqual(resumed["acceptance_commit"], live)
        again = invoke_harness(integration, "handoff", "accept", "--branch", "feature/resume-accept")
        self.assertEqual(again["result"], "already accepted")
        invoke_harness(integration, "land", "prepare", "--branch", "feature/resume-accept")
        self.assertEqual(invoke_harness(integration, "land", "merge", "--branch", "feature/resume-accept")["result"], "landed")

    def test_second_integration_workspace_cannot_take_over_acceptance(self):
        self.publish_goal(self.fx.root, "feature/held-once", "held-once.txt", "held once")
        first = self.clone_workspace("integrator", "integration-authority")
        invoke_harness(first, "handoff", "accept", "--branch", "feature/held-once")
        second = self.clone_workspace("integrator-2", "integration-authority")
        refused = invoke_harness(second, "handoff", "accept", "--branch", "feature/held-once", check=False)
        self.assertEqual(refused.returncode, 2)
        self.assertIn("already accepted by integration authority 'integrator'", refused.stderr)

    def test_handoff_is_immutable_until_explicit_withdrawal(self):
        first = self.publish_goal(self.fx.root, "feature/immutable", "immutable.txt", "one")
        same = self.fx.h("handoff", "publish", "--approved-by", "owner")
        self.assertEqual(same["result"], "already published")
        self.assertEqual(same["handoff_commit"], first["handoff_commit"])

        self.fx.h("handoff", "withdraw", "--branch", "feature/immutable")
        remote_branch = run(["git", "--git-dir", str(self.fx.remote), "show-ref", "--verify", "--quiet", "refs/heads/feature/immutable"], self.fx.root, check=False)
        remote_handoff = run(["git", "--git-dir", str(self.fx.remote), "show-ref", "--verify", "--quiet", "refs/harness/handoff/feature/immutable"], self.fx.root, check=False)
        self.assertNotEqual(remote_branch.returncode, 0)
        self.assertNotEqual(remote_handoff.returncode, 0)
        self.fx.write("immutable.txt", "two\n")
        self.fx.commit("work: revised immutable handoff")
        self.fx.h("approval", "drop")
        self.fx.h("approval", "record")
        second = self.fx.h("handoff", "publish", "--approved-by", "owner")
        self.assertNotEqual(second["handoff_commit"], first["handoff_commit"])
