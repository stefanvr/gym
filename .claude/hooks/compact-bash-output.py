#!/usr/bin/env python3
"""Claude Code PreToolUse middleware for compact test/check output.

Hook mode reads Claude Code's JSON payload from stdin. For a small allowlist of
simple commands it rewrites the Bash tool input so this file runs the command
and emits a compact pass/fail summary. Compound/dynamic shell commands are left
untouched.
"""

from __future__ import annotations

import base64
from collections import deque
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from typing import Any

FAILURE_RE = re.compile(
    r"(?:\bFAIL(?:ED|URE)?\b|\bERROR\b|\bAssertionError\b|\bTraceback\b|"
    r"\bnot ok\b|\bfailed\b|\bError:|\bExpected\b|\bReceived\b)",
    re.IGNORECASE,
)
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
SHELL_META_RE = re.compile(r"[;&|<>`\n\r$]")


def _parse_simple_target(command: str) -> tuple[str, list[str]] | None:
    """Return (label, argv) for a supported simple command, else None."""
    if not command or SHELL_META_RE.search(command):
        return None
    try:
        argv = shlex.split(command, posix=True)
    except ValueError:
        return None
    if not argv:
        return None

    if argv[:2] == ["npm", "test"]:
        return "npm test", argv
    if argv[:3] == ["npm", "run", "test:e2e"]:
        return "npm run test:e2e", argv

    exe = Path(argv[0]).name.lower()
    if re.fullmatch(r"python(?:3(?:\.\d+)*)?(?:\.exe)?", exe) and len(argv) >= 3:
        script = argv[1].replace("\\", "/")
        if script == ".harness/runtime/harness.py" and argv[2] == "check":
            return "harness.py check", argv
    return None


def _runner_command(command: str, label: str) -> str:
    encoded = base64.urlsafe_b64encode(command.encode("utf-8")).decode("ascii")
    python = shlex.quote(sys.executable)
    script = shlex.quote(str(Path(__file__).resolve()))
    return f"{python} {script} --run {shlex.quote(label)} {shlex.quote(encoded)}"


def rewrite_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("tool_name") != "Bash":
        return {}
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return {}
    command = tool_input.get("command")
    if not isinstance(command, str):
        return {}

    target = _parse_simple_target(command)
    if target is None:
        return {}
    label, _ = target
    updated = dict(tool_input)
    updated["command"] = _runner_command(command, label)
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Compact repetitive test/check output before adding it to context.",
            "updatedInput": updated,
        }
    }


def _human_bytes(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KiB"
    return f"{value / (1024 * 1024):.1f} MiB"


def _resolved_argv(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    if Path(argv[0]).is_absolute():
        return argv
    resolved = shutil.which(argv[0])
    if resolved:
        argv = list(argv)
        argv[0] = resolved
    return argv


def run_compact(command: str, label: str) -> int:
    target = _parse_simple_target(command)
    if target is None or target[0] != label:
        print(f"FAIL {label}: compact-output runner rejected an unsupported command", file=sys.stderr)
        return 126

    _, argv = target
    argv = _resolved_argv(argv)
    line_count = 0
    byte_count = 0
    tail: deque[tuple[int, str]] = deque(maxlen=30)
    relevant: dict[int, str] = {}
    previous: deque[tuple[int, str]] = deque(maxlen=2)
    after = 0

    popen_argv: list[str] = argv
    if os.name == "nt" and argv[0].lower().endswith((".cmd", ".bat")):
        # npm is commonly npm.cmd on Windows; invoke batch launchers through
        # COMSPEC while retaining the same simple argv that the hook validated.
        comspec = os.environ.get("COMSPEC", "cmd.exe")
        popen_argv = [comspec, "/d", "/s", "/c", subprocess.list2cmdline(argv)]

    try:
        proc = subprocess.Popen(
            popen_argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.getcwd(),
            env=os.environ.copy(),
        )
    except OSError as exc:
        print(f"FAIL {label}: could not start command: {exc}", file=sys.stderr)
        return 127

    assert proc.stdout is not None
    try:
        for raw in iter(proc.stdout.readline, b""):
            line_count += 1
            byte_count += len(raw)
            text = ANSI_RE.sub("", raw.decode("utf-8", errors="replace")).rstrip("\r\n")
            item = (line_count, text)
            tail.append(item)

            matched = bool(FAILURE_RE.search(text))
            if matched:
                for n, prior in previous:
                    relevant.setdefault(n, prior)
                relevant.setdefault(line_count, text)
                after = max(after, 3)
            elif after > 0:
                relevant.setdefault(line_count, text)
                after -= 1
            previous.append(item)
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
        raise
    finally:
        proc.stdout.close()

    rc = proc.wait()
    if rc == 0:
        print(f"PASS {label} — {line_count} lines / {_human_bytes(byte_count)} suppressed")
        return 0

    for n, text in tail:
        relevant.setdefault(n, text)
    rows = sorted(relevant.items())
    if len(rows) > 80:
        rows = rows[:40] + [(-1, "… failure output truncated …")] + rows[-40:]

    print(f"FAIL {label} — exit {rc}; {line_count} lines / {_human_bytes(byte_count)} captured")
    if rows:
        print("--- compact failure excerpt ---")
        for _, text in rows:
            print(text)
    else:
        print("(command produced no output)")
    return rc


def _decode_command(encoded: str) -> str:
    return base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8")


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "--run":
        if len(sys.argv) != 4:
            print("usage: compact-bash-output.py --run LABEL BASE64_COMMAND", file=sys.stderr)
            return 2
        label = sys.argv[2]
        try:
            command = _decode_command(sys.argv[3])
        except Exception as exc:  # malformed internal invocation
            print(f"invalid encoded command: {exc}", file=sys.stderr)
            return 2
        return run_compact(command, label)

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": f"invalid hook input: {exc}"}))
        return 0
    print(json.dumps(rewrite_payload(payload), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
