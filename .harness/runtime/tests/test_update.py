from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class HarnessUpdateTests(unittest.TestCase):
    def test_update_preserves_repository_state_and_project_files(self):
        with tempfile.TemporaryDirectory(prefix="harness-update-test-") as td:
            old = Path(td) / "project"
            old.mkdir()

            # Build an older installation from the current release surfaces.
            for rel in [
                ".harness",
                ".claude",
                ".github/workflows/harness-ci.yml",
                "AGENTS.md",
                "CLAUDE.md",
                "GEMINI.md",
                "HARNESS-FEATURES.md",
                "harness-update.py",
                ".gitignore",
                "README.md",
            ]:
                src = PROJECT_ROOT / rel
                dst = old / rel
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)

            (old / ".harness/runtime/VERSION").write_text("18.1\n", encoding="utf-8")
            for rel in [".harness/composition/active.json", ".harness/composition/classification.json"]:
                path = old / rel
                data = json.loads(path.read_text(encoding="utf-8"))
                data["release"] = "18.1"
                path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

            config_path = old / ".harness/runtime/config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config.update({"mainline": "develop", "bootstrap_mainline": "develop", "remote": "upstream"})
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            active_path = old / ".harness/composition/active.json"
            active = json.loads(active_path.read_text(encoding="utf-8"))
            active["selection"]["project_model"] = "spec"
            active["selection"]["collaboration_model"] = "single-user"
            active_path.write_text(json.dumps(active, indent=2) + "\n", encoding="utf-8")

            (old / "README.md").write_text("# Existing project\nkeep this\n", encoding="utf-8")
            with (old / ".gitignore").open("a", encoding="utf-8") as handle:
                handle.write("\nproject-secret.env\n")
            extension = old / ".harness/extensions/project/example/SKILL.md"
            extension.parent.mkdir(parents=True, exist_ok=True)
            extension.write_text("# Project extension\n", encoding="utf-8")
            local_settings = old / ".claude/settings.local.json"
            local_settings.write_text('{"local": true}\n', encoding="utf-8")

            proc = subprocess.run(
                [sys.executable, str(old / "harness-update.py"), str(PROJECT_ROOT)],
                cwd=old,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=180,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

            self.assertEqual((old / ".harness/runtime/VERSION").read_text(encoding="utf-8").strip(), "18.3.2")
            new_config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(new_config["mainline"], "develop")
            self.assertEqual(new_config["bootstrap_mainline"], "develop")
            self.assertEqual(new_config["remote"], "upstream")

            new_active = json.loads(active_path.read_text(encoding="utf-8"))
            self.assertEqual(new_active["release"], "18.3.2")
            self.assertEqual(new_active["selection"]["project_model"], "spec")
            self.assertEqual(new_active["selection"]["collaboration_model"], "single-user")

            self.assertEqual((old / "README.md").read_text(encoding="utf-8"), "# Existing project\nkeep this\n")
            self.assertIn("project-secret.env", (old / ".gitignore").read_text(encoding="utf-8"))
            self.assertTrue(extension.exists())
            self.assertEqual(local_settings.read_text(encoding="utf-8"), '{"local": true}\n')


if __name__ == "__main__":
    unittest.main()
