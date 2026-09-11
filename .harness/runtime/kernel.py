#!/usr/bin/env python3
"""Universal deterministic runtime kernel.

Owns process/Git facts, repository lifecycle state, approval/landing mechanics,
and guarded mutations. Project- and Collaboration-model mechanics live in
their own modules; the few lifecycle integration hooks are loaded lazily.
"""

import argparse
import contextlib
import hashlib
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

RUNTIME_ROOT = Path(__file__).resolve().parent
VERSION_PATH = RUNTIME_ROOT / "VERSION"
CONFIG_SCHEMA_VERSION = 1
TRANSACTION_SCHEMA_VERSION = 2
PROJECT_ROOT = RUNTIME_ROOT.parents[1]
CONFIG_PATH = RUNTIME_ROOT / "config.json"
CONFIG_KEYS = {"schema_version", "mainline", "bootstrap_mainline", "remote"}
DEFAULT_COMMAND_TIMEOUT_SECONDS = 120.0
MAX_COMMAND_TIMEOUT_SECONDS = 3600.0
MUTATING_COMMANDS = {
    ("repo", "bootstrap"),
    ("branch", "start"),
    ("approval", "record"),
    ("approval", "drop"),
    ("land", "prepare"),
    ("land", "merge"),
    ("land", "abort"),
    ("abandon", "discard"),
    ("collaboration", "configure"),
    ("handoff", "publish"),
    ("handoff", "withdraw"),
    ("handoff", "accept"),
    ("handoff", "release"),
}

class HarnessError(RuntimeError):
    pass


def fail(message: str) -> "None":
    raise HarnessError(message)


def harness_version() -> str:
    """Read the Harness release lazily so a damaged install reports normalized JSON errors."""
    try:
        text = VERSION_PATH.read_text(encoding="utf-8").strip()
    except OSError as exc:
        fail(f"cannot read Harness version specification {VERSION_PATH}: {exc}")
    if not text:
        fail(f"empty Harness version specification: {VERSION_PATH}")
    return text


def load_config() -> dict[str, Any]:
    defaults = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "mainline": "auto",
        "bootstrap_mainline": "main",
        "remote": "origin",
    }
    if not CONFIG_PATH.exists():
        return defaults
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid runtime config: {exc}")
    if not isinstance(data, dict):
        fail("runtime config must be a JSON object")
    unknown = sorted(set(data) - CONFIG_KEYS)
    if unknown:
        fail("runtime config contains unsupported keys: " + ", ".join(unknown))
    merged = {**defaults, **data}
    if merged.get("schema_version") != CONFIG_SCHEMA_VERSION:
        fail(f"unsupported runtime config schema_version: {merged.get('schema_version')!r}")
    for key in ("mainline", "bootstrap_mainline", "remote"):
        if not isinstance(merged.get(key), str) or not merged[key].strip():
            fail(f"runtime config `{key}` must be a non-empty string")
        merged[key] = merged[key].strip()
    if merged["remote"].startswith("-") or any(ch in merged["remote"] for ch in "\r\n\0"):
        fail("runtime config `remote` must be a plain Git remote name, not an option/control string")
    for key in ("bootstrap_mainline",):
        cp = run(["git", "check-ref-format", "--branch", merged[key]], check=False)
        if cp.returncode != 0:
            fail(f"runtime config `{key}` is not a valid Git branch name: {merged[key]!r}")
    if merged["mainline"] != "auto":
        cp = run(["git", "check-ref-format", "--branch", merged["mainline"]], check=False)
        if cp.returncode != 0:
            fail(f"runtime config `mainline` is not a valid Git branch name: {merged['mainline']!r}")
        if merged["bootstrap_mainline"] != merged["mainline"]:
            fail(
                "runtime config is inconsistent: explicit `mainline` and `bootstrap_mainline` must match "
                f"({merged['mainline']!r} != {merged['bootstrap_mainline']!r})"
            )
    return merged


def command_timeout_seconds() -> float:
    raw = os.environ.get("HARNESS_COMMAND_TIMEOUT_SECONDS")
    if raw is None or not raw.strip():
        return DEFAULT_COMMAND_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        fail("HARNESS_COMMAND_TIMEOUT_SECONDS must be a number of seconds")
    if not (0 < value <= MAX_COMMAND_TIMEOUT_SECONDS):
        fail(
            "HARNESS_COMMAND_TIMEOUT_SECONDS must be greater than 0 and no more than "
            f"{int(MAX_COMMAND_TIMEOUT_SECONDS)} seconds"
        )
    return value


def _noninteractive_environment() -> dict[str, str]:
    env = os.environ.copy()
    # Prevent Git/credential helpers from waiting for terminal input. Commands that
    # genuinely require human interaction are outside the deterministic runtime.
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "Never"
    return env


def _kill_process_tree(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGKILL)
            return
        except ProcessLookupError:
            return
        except OSError:
            pass
    elif os.name == "nt":
        # `taskkill /T` is the platform-provided process-tree termination path.
        # It prevents descendants that inherited stdout/stderr handles from
        # keeping timeout cleanup blocked after the direct Git process exits.
        try:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
        if proc.poll() is not None:
            return
    proc.kill()


def run(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
    timeout_seconds: float | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    timeout = command_timeout_seconds() if timeout_seconds is None else timeout_seconds
    if not (0 < timeout <= MAX_COMMAND_TIMEOUT_SECONDS):
        fail(
            "command timeout must be greater than 0 and no more than "
            f"{int(MAX_COMMAND_TIMEOUT_SECONDS)} seconds"
        )
    kwargs: dict[str, Any] = {}
    if os.name == "posix":
        # A separate process group lets timeout recovery terminate Git hooks and
        # other descendants instead of leaving a stuck child behind.
        kwargs["start_new_session"] = True
    elif os.name == "nt" and hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_noninteractive_environment(),
        **kwargs,
    )
    try:
        stdout, stderr = proc.communicate(input=input_text, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        _kill_process_tree(proc)
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            # Do not turn timeout recovery itself into another indefinite wait.
            if proc.stdout is not None:
                proc.stdout.close()
            if proc.stderr is not None:
                proc.stderr.close()
            try:
                proc.kill()
                proc.wait(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                pass
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        detail = (stderr or "").strip() or (stdout or "").strip()
        suffix = f"\n{detail}" if detail else ""
        fail(f"command timed out after {timeout:g}s: {' '.join(cmd)}{suffix}")

    cp = subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
    if check and cp.returncode != 0:
        detail = cp.stderr.strip() or cp.stdout.strip() or f"exit {cp.returncode}"
        fail(f"command failed: {' '.join(cmd)}\n{detail}")
    return cp


def git(args: Iterable[str], repo: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=repo, check=check)


def git_input(args: Iterable[str], repo: Path, input_text: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=repo, check=check, input_text=input_text)


def discover_git_root() -> Path | None:
    cp = run(["git", "-C", str(PROJECT_ROOT), "rev-parse", "--show-toplevel"], check=False)
    if cp.returncode != 0:
        return None
    return Path(cp.stdout.strip()).resolve()


def validate_repository_topology(repo: Path) -> Path:
    """Require the single-root repository topology supported by this runtime.

    The runtime intentionally does not model parent repositories, submodules, or
    other nested repository authority. Refusing those layouts keeps every Git/ref
    transition scoped to exactly the project that owns this runtime.
    """
    project = PROJECT_ROOT.resolve()
    repo = repo.resolve()
    if repo != project:
        fail(
            "unsupported nested repository layout: the Harness project root is inside a different Git repository "
            f"({project} inside {repo}); use the Harness only at a standalone repository root"
        )

    # An independently initialized repository can still be embedded inside a
    # parent repository. `rev-parse` from PROJECT_ROOT would select the inner
    # repository, so explicitly probe the parent directory as well.
    parent = project.parent
    if parent != project:
        outer = run(["git", "-C", str(parent), "rev-parse", "--show-toplevel"], check=False)
        if outer.returncode == 0 and outer.stdout.strip():
            outer_root = Path(outer.stdout.strip()).resolve()
            fail(
                "unsupported nested repository layout: the standalone Harness repository is embedded inside "
                f"parent Git repository {outer_root}; use the Harness only at a top-level repository root"
            )

    superproject = git(["rev-parse", "--show-superproject-working-tree"], repo, check=False)
    if superproject.returncode == 0 and superproject.stdout.strip():
        fail(
            "unsupported sub-repository layout: this Harness repository is a Git submodule; "
            "use the Harness only at a standalone repository root"
        )

    # Mode 160000 is a tracked Gitlink/submodule. The runtime intentionally does
    # not attempt to coordinate independent nested repository state/authority.
    staged = git(["ls-files", "--stage"], repo, check=False)
    if staged.returncode == 0:
        gitlinks = []
        for line in staged.stdout.splitlines():
            if line.startswith("160000 "):
                path = line.split("\t", 1)[1] if "\t" in line else line
                gitlinks.append(path)
        if gitlinks:
            shown = ", ".join(gitlinks[:5])
            suffix = " ..." if len(gitlinks) > 5 else ""
            fail(
                "unsupported sub-repository layout: Git submodules/gitlinks are present "
                f"({shown}{suffix}); the Harness supports one repository root only"
            )
    return repo


def require_repo() -> Path:
    root = discover_git_root()
    if root is None:
        fail("Git repository is not initialized; use `repo bootstrap` after lifecycle classification")
    return validate_repository_topology(root)


def git_dir(repo: Path) -> Path:
    value = git(["rev-parse", "--git-dir"], repo).stdout.strip()
    path = Path(value)
    if not path.is_absolute():
        path = repo / path
    return path.resolve()


def git_common_dir(repo: Path) -> Path:
    value = git(["rev-parse", "--git-common-dir"], repo).stdout.strip()
    path = Path(value)
    if not path.is_absolute():
        path = repo / path
    return path.resolve()


def project_lifecycle_lock_path(project_root: Path | None = None) -> Path:
    root = (project_root or PROJECT_ROOT).resolve()
    key = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:32]
    return Path(tempfile.gettempdir()) / "harness-lifecycle-locks" / f"{key}.lock"


def repository_lifecycle_lock_path(repo: Path) -> Path:
    return git_common_dir(repo) / "harness" / "lifecycle.lock"


@contextlib.contextmanager
def advisory_lock(path: Path, label: str) -> Iterator[None]:
    """Hold a crash-safe, non-blocking OS advisory lock for one mutation boundary."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    locked = False
    try:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            if path.stat().st_size == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                locked = True
            except OSError:
                fail(f"lifecycle mutation already in progress ({label}); lock busy: {path}")
        else:
            import fcntl

            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except BlockingIOError:
                fail(f"lifecycle mutation already in progress ({label}); lock busy: {path}")

        metadata = json.dumps({"pid": os.getpid(), "project_root": str(PROJECT_ROOT.resolve()), "label": label})
        handle.seek(0)
        handle.truncate()
        handle.write(metadata.encode("utf-8"))
        handle.flush()
        try:
            os.fsync(handle.fileno())
        except OSError:
            pass
        yield
    finally:
        if locked:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        handle.close()


def mutation_command_key(args: argparse.Namespace) -> tuple[str, str | None]:
    command = str(getattr(args, "command", ""))
    subcommand = getattr(args, f"{command}_command", None)
    return command, subcommand


def command_mutates_lifecycle(args: argparse.Namespace) -> bool:
    return mutation_command_key(args) in MUTATING_COMMANDS


@contextlib.contextmanager
def lifecycle_mutation_lock(args: argparse.Namespace) -> Iterator[None]:
    """Serialize all runtime-owned mutations, including across linked worktrees."""
    key = mutation_command_key(args)
    label = " ".join(part for part in key if part)
    with contextlib.ExitStack() as stack:
        # This lock also covers pre-Git bootstrap and serializes commands from the
        # same project root before a common Git directory exists.
        stack.enter_context(advisory_lock(project_lifecycle_lock_path(), label))
        repo = discover_git_root()
        if repo is not None:
            # Linked worktrees have distinct worktree roots but share this common
            # Git-directory lock, so lifecycle mutations cannot overlap.
            stack.enter_context(advisory_lock(repository_lifecycle_lock_path(repo), label))
        yield


def current_branch(repo: Path) -> str | None:
    cp = git(["symbolic-ref", "--quiet", "--short", "HEAD"], repo, check=False)
    return cp.stdout.strip() if cp.returncode == 0 else None


def has_commits(repo: Path) -> bool:
    return git(["rev-parse", "--verify", "HEAD"], repo, check=False).returncode == 0


def ref_exists(repo: Path, ref: str) -> bool:
    return git(["show-ref", "--verify", "--quiet", ref], repo, check=False).returncode == 0


def rev(repo: Path, name: str) -> str:
    cp = git(["rev-parse", "--verify", name], repo)
    return cp.stdout.strip()


def tree(repo: Path, name: str) -> str:
    return rev(repo, f"{name}^{{tree}}")


def commit_count(repo: Path, base: str, head: str) -> int:
    cp = git(["rev-list", "--count", f"{base}..{head}"], repo)
    try:
        return int(cp.stdout.strip())
    except ValueError:
        fail(f"cannot determine commit count between {base} and {head}")


def blob(repo: Path, commit: str, path: str) -> str | None:
    cp = git(["rev-parse", "--verify", f"{commit}:{path}"], repo, check=False)
    return cp.stdout.strip() if cp.returncode == 0 else None


def file_at(repo: Path, commit: str, path: str) -> str | None:
    cp = git(["show", f"{commit}:{path}"], repo, check=False)
    return cp.stdout if cp.returncode == 0 else None


def worktree_status(repo: Path) -> list[str]:
    out = git(["status", "--porcelain=v1", "--untracked-files=all"], repo).stdout
    return [line for line in out.splitlines() if line.strip()]


def require_clean(repo: Path) -> None:
    lines = worktree_status(repo)
    if lines:
        fail("working tree is not clean:\n" + "\n".join(lines[:50]))


def branch_ref(branch: str) -> str:
    return f"refs/heads/{branch}"


def require_valid_branch_name(branch: str, label: str = "branch") -> str:
    """Require a CLI-safe Git branch name before it enters lifecycle mechanics."""
    if not isinstance(branch, str) or not branch:
        fail(f"{label} must be a non-empty Git branch name")
    cp = run(["git", "check-ref-format", "--branch", branch], check=False)
    if cp.returncode != 0:
        fail(f"{label} is not a valid Git branch name: {branch!r}")
    return branch


def goal_document_path(branch: str) -> str:
    """Return the branch-derived local Goal document path."""
    return f"doc/goals/{branch}.md"


def goal_document_file(repo: Path, branch: str) -> Path:
    return repo / goal_document_path(branch)


def require_goal_document(repo: Path, branch: str) -> str:
    """Return non-empty branch-local Goal text or refuse the lifecycle transition."""
    path = goal_document_file(repo, branch)
    goal_path = goal_document_path(branch)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"active Goal document is required: {goal_path}")
    except OSError as exc:
        fail(f"cannot read active Goal document {goal_path}: {exc}")
    if not text.strip():
        fail(f"active Goal document must be non-empty: {goal_path}")
    return text


def delete_session_document(repo: Path) -> None:
    """Remove local ignored restart cache after a Goal is durably finished."""
    path = repo / "doc" / "session.md"
    try:
        path.unlink()
    except FileNotFoundError:
        return
    except OSError as exc:
        fail(f"cannot remove completed Session checkpoint {path}: {exc}")


def delete_goal_document(repo: Path, branch: str) -> None:
    """Remove local ignored Goal state after its branch is durably finished."""
    path = goal_document_file(repo, branch)
    try:
        path.unlink()
    except FileNotFoundError:
        return
    except OSError as exc:
        fail(f"cannot remove completed Goal document {path}: {exc}")
    # Remove only empty branch-derived parent directories up to doc/goals.
    stop = repo / "doc" / "goals"
    parent = path.parent
    while parent != stop and parent != repo:
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent
    try:
        stop.rmdir()
    except OSError:
        pass


def resolve_mainline(repo: Path, config: dict[str, Any]) -> str:
    configured = str(config.get("mainline", "auto"))
    if configured != "auto":
        if has_commits(repo) and not ref_exists(repo, branch_ref(configured)):
            fail(f"configured mainline branch does not exist: {configured}")
        return configured

    remote = str(config.get("remote", "origin"))
    symbolic = git(["symbolic-ref", "--quiet", f"refs/remotes/{remote}/HEAD"], repo, check=False)
    if symbolic.returncode == 0:
        target = symbolic.stdout.strip()
        prefix = f"refs/remotes/{remote}/"
        if target.startswith(prefix):
            candidate = target[len(prefix):]
            if ref_exists(repo, branch_ref(candidate)):
                return candidate

    candidates = [
        candidate
        for candidate in ("main", "master", "trunk", "develop")
        if ref_exists(repo, branch_ref(candidate))
    ]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        fail(
            "cannot resolve mainline unambiguously; multiple common local mainline branches exist "
            f"({', '.join(candidates)}); set .harness/runtime/config.json `mainline` explicitly"
        )

    if not has_commits(repo):
        return str(config.get("bootstrap_mainline", "main"))
    fail("cannot resolve mainline; set .harness/runtime/config.json `mainline` explicitly")



def resolve_bootstrap_mainline(config: dict[str, Any]) -> str:
    configured = str(config.get("mainline", "auto"))
    bootstrap = str(config.get("bootstrap_mainline", "main"))
    if configured != "auto" and bootstrap != configured:
        fail(
            "runtime config is inconsistent: explicit `mainline` and `bootstrap_mainline` must match "
            f"({configured!r} != {bootstrap!r})"
        )
    if not bootstrap:
        fail("runtime config requires a non-empty bootstrap_mainline")
    return configured if configured != "auto" else bootstrap


def atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    except OSError as exc:
        fail(f"cannot create transaction metadata temp file for {path}: {exc}")
    try:
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, sort_keys=True)
                fh.write("\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(temp_name, path)
            # On POSIX, fsync the containing directory as well so the rename is
            # durable across a sudden crash/power loss. Windows does not offer
            # equivalent directory-fsync semantics through os.open.
            if os.name == "posix":
                dir_fd = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
        except OSError as exc:
            fail(f"cannot persist transaction metadata {path}: {exc}")
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def key_for_branch(branch: str) -> str:
    digest = hashlib.sha256(branch.encode("utf-8")).hexdigest()[:16]
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", branch).strip("-")[:48] or "branch"
    return f"{safe}-{digest}"


def validate_land_state(branch: str, data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        fail(f"invalid land transaction metadata for {branch}: expected JSON object")
    if data.get("schema_version") != TRANSACTION_SCHEMA_VERSION:
        fail(f"invalid land transaction metadata for {branch}: unsupported transaction schema_version")
    if data.get("branch") != branch:
        fail(f"invalid land transaction metadata for {branch}: branch binding mismatch")

    required = {
        "mainline": str,
        "approval_ref": str,
        "approval_source_commit": str,
        "approved_tree": str,
        "base_commit": str,
        "ready_commit": str,
        "phase": str,
    }
    for key, expected_type in required.items():
        if key not in data or not isinstance(data[key], expected_type):
            fail(f"invalid land transaction metadata for {branch}: `{key}` has invalid type or is missing")

    if data["phase"] not in {"ready", "integrating", "merged", "published"}:
        fail(f"invalid land transaction metadata for {branch}: unsupported phase {data['phase']!r}")

    for key in ("approval_source_commit", "approved_tree", "base_commit", "ready_commit", "merge_commit", "handoff_commit", "acceptance_commit"):
        value = data.get(key)
        if value is not None and (not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{40,64}", value)):
            fail(f"invalid land transaction metadata for {branch}: `{key}` is not a Git object id")
    return data


def land_state_dir(repo: Path) -> Path:
    return git_dir(repo) / "harness" / "land"


def land_state_path(repo: Path, branch: str) -> Path:
    return land_state_dir(repo) / f"{key_for_branch(branch)}.json"


def read_land_state(repo: Path, branch: str) -> dict[str, Any]:
    path = land_state_path(repo, branch)
    if not path.exists():
        fail(f"no land transaction for branch: {branch}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read land transaction {path}: {exc}")
    return validate_land_state(branch, data)


def write_land_state(repo: Path, branch: str, data: dict[str, Any]) -> None:
    data = dict(data)
    data["schema_version"] = TRANSACTION_SCHEMA_VERSION
    data["branch"] = branch
    validate_land_state(branch, data)
    atomic_json(land_state_path(repo, branch), data)


def delete_land_state(repo: Path, branch: str) -> None:
    path = land_state_path(repo, branch)
    if path.exists():
        path.unlink()

def update_ref(repo: Path, ref: str, value: str | None, old: str | None = None) -> None:
    if value is None:
        args = ["update-ref", "-d", ref]
        if old is not None:
            args.append(old)
        git(args, repo)
    else:
        args = ["update-ref", ref, value]
        if old is not None:
            args.append(old)
        git(args, repo)


def land_runtime_ref(branch: str, name: str) -> str:
    return f"refs/harness/runtime/land/{key_for_branch(branch)}/{name}"


def delete_land_runtime_refs(repo: Path, branch: str) -> None:
    prefix = f"refs/harness/runtime/land/{key_for_branch(branch)}/"
    cp = git(["for-each-ref", "--format=%(refname)", prefix], repo)
    for ref in [x.strip() for x in cp.stdout.splitlines() if x.strip()]:
        update_ref(repo, ref, None)


def list_refs(repo: Path, prefix: str) -> list[dict[str, str]]:
    cp = git(["for-each-ref", "--format=%(refname)|%(objectname)", prefix], repo)
    result = []
    for line in cp.stdout.splitlines():
        if not line.strip():
            continue
        name, oid = line.split("|", 1)
        result.append({"ref": name, "commit": oid, "tree": tree(repo, oid)})
    return result


def is_ancestor(repo: Path, older: str, newer: str) -> bool:
    return git(["merge-base", "--is-ancestor", older, newer], repo, check=False).returncode == 0



def configured_remote_names(repo: Path) -> set[str]:
    cp = git(["remote"], repo, check=False)
    if cp.returncode != 0:
        fail(f"cannot enumerate configured Git remotes: {cp.stderr.strip() or cp.stdout.strip()}")
    return {line.strip() for line in cp.stdout.splitlines() if line.strip()}


def require_configured_remote(repo: Path, remote: str) -> None:
    remotes = configured_remote_names(repo)
    if remote not in remotes:
        available = ", ".join(sorted(remotes)) or "none"
        fail(
            f"runtime config `remote` must name a configured Git remote; "
            f"{remote!r} is not configured (available: {available})"
        )


def remote_head(repo: Path, remote: str, branch: str) -> str | None:
    require_configured_remote(repo, remote)
    cp = git(["ls-remote", "--heads", remote, f"refs/heads/{branch}"], repo, check=False)
    if cp.returncode != 0:
        fail(f"cannot verify remote {remote}/{branch}: {cp.stderr.strip() or cp.stdout.strip()}")
    line = cp.stdout.strip()
    if not line:
        return None
    return line.split()[0]


def remote_ref_oid(repo: Path, remote: str, ref: str) -> str | None:
    require_configured_remote(repo, remote)
    cp = git(["ls-remote", remote, ref], repo, check=False)
    if cp.returncode != 0:
        fail(f"cannot verify remote ref {remote}:{ref}: {cp.stderr.strip() or cp.stdout.strip()}")
    lines = [line for line in cp.stdout.splitlines() if line.strip()]
    for line in lines:
        oid, name = line.split(None, 1)
        if name.strip() == ref:
            return oid
    return None


def remote_ref_oids(repo: Path, remote: str, refs: list[str]) -> dict[str, str | None]:
    """Read several exact remote refs with one ls-remote round trip."""
    require_configured_remote(repo, remote)
    cp = git(["ls-remote", remote, *refs], repo, check=False)
    if cp.returncode != 0:
        fail(f"cannot verify remote refs on {remote}: {cp.stderr.strip() or cp.stdout.strip()}")
    wanted = set(refs)
    found: dict[str, str] = {}
    for line in cp.stdout.splitlines():
        if not line.strip():
            continue
        oid, name = line.split(None, 1)
        name = name.strip()
        if name in wanted:
            found[name] = oid
    return {ref: found.get(ref) for ref in refs}


def delete_remote_refs_exact(repo: Path, remote: str, expected: dict[str, str]) -> None:
    """Atomically delete exact remote refs; retry-safe when some/all are already absent."""
    live = remote_ref_oids(repo, remote, list(expected))
    present: dict[str, str] = {}
    for ref, oid in expected.items():
        actual = live.get(ref)
        if actual is None:
            continue
        if actual != oid:
            fail(f"remote ref moved: {remote}:{ref} is {actual}, expected exact boundary {oid}; refusing deletion")
        present[ref] = oid
    if not present:
        return
    args = ["push", "--atomic"]
    args += [f"--force-with-lease={ref}:{oid}" for ref, oid in present.items()]
    args += [remote, *[f":{ref}" for ref in present]]
    cp = git(args, repo, check=False)
    if cp.returncode == 0:
        return
    after = remote_ref_oids(repo, remote, list(present))
    if all(value is None for value in after.values()):
        return
    moved = {ref: value for ref, value in after.items() if value is not None and value != present[ref]}
    if moved:
        fail(f"remote refs moved during exact deletion on {remote}: {moved}; refusing ambiguous cleanup")
    fail(f"atomic remote deletion failed on {remote}: {cp.stderr.strip() or cp.stdout.strip()}")


def require_remote_landing_alignment(repo: Path, remote: str, mainline: str, branch: str, ready: str) -> None:
    """Require live remote refs to match the local landing boundary when they exist."""
    local_mainline = rev(repo, branch_ref(mainline))
    remote_mainline = remote_head(repo, remote, mainline)
    if remote_mainline is not None and remote_mainline != local_mainline:
        fail(
            f"configured mainline is not up to date with {remote}/{mainline}: "
            f"local {local_mainline}, remote {remote_mainline}; synchronize before landing"
        )
    remote_branch = remote_head(repo, remote, branch)
    if remote_branch is not None and remote_branch != ready:
        fail(
            f"work branch is not up to date with {remote}/{branch}: "
            f"local {ready}, remote {remote_branch}; synchronize before landing"
        )


def delete_remote_exact(repo: Path, remote: str, branch: str, expected: str) -> None:
    actual = remote_head(repo, remote, branch)
    if actual is None:
        return
    if actual != expected:
        fail(
            f"remote branch moved: {remote}/{branch} is {actual}, expected exact boundary {expected}; refusing deletion"
        )
    # The initial read gives a useful diagnostic, but only the lease makes the
    # destructive update atomic with respect to the exact expected commit.
    ref = f"refs/heads/{branch}"
    cp = git(
        ["push", f"--force-with-lease={ref}:{expected}", remote, f":{ref}"],
        repo,
        check=False,
    )
    if cp.returncode == 0:
        return
    after = remote_head(repo, remote, branch)
    if after is None:
        # Another actor removed exactly the branch we intended to remove.
        return
    if after != expected:
        fail(
            f"remote branch moved during deletion: {remote}/{branch} is {after}, "
            f"expected exact boundary {expected}; refusing deletion"
        )
    fail(f"remote deletion failed for {remote}/{branch}: {cp.stderr.strip() or cp.stdout.strip()}")



def _collaboration():
    """Load Collaboration-model mechanics only at the lifecycle integration seam."""
    import collaboration_model
    return collaboration_model

def cmd_land_assess(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    config = load_config()
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("land assess requires a branch")
    branch = require_valid_branch_name(branch, "land --branch" if args.branch is not None else "current branch")
    mainline = resolve_mainline(repo, config)
    current_mainline = rev(repo, branch_ref(mainline))
    if _collaboration().active_collaboration_model(PROJECT_ROOT) != "cooperative-multi-user":
        valid = cmd_approval_validate(argparse.Namespace(branch=branch))
        return {
            "result": "READY_FOR_LANDING" if valid.get("valid") else "LANDING_BLOCKED",
            "collaboration_model": "single-user",
            "branch": branch,
            "mainline": mainline,
            "current_mainline": current_mainline,
            "approval": valid,
        }
    actor = _collaboration().require_integration_authority(repo)
    assert actor is not None
    state = _collaboration().read_handoff_state(repo, branch, required=False)
    if state is None:
        return {
            "result": "LANDING_BLOCKED",
            "cause": "Goal branch has not been accepted through the cooperative handoff boundary",
            "evidence": {"branch": branch, "current_mainline": current_mainline},
            "next": ["accept a published contributor handoff", "or abandon/supersede intentionally"],
        }
    metadata = _collaboration().validate_handoff_metadata(branch, state["metadata"])
    remote = str(config.get("remote", "origin"))
    refs = remote_ref_oids(repo, remote, [_collaboration().handoff_ref(branch), f"refs/heads/{branch}"])
    live = {
        "handoff_ref": refs[_collaboration().handoff_ref(branch)],
        "branch": refs[f"refs/heads/{branch}"],
    }
    expected = {
        "handoff_ref": state["acceptance_commit"],
        "branch": metadata["ready_commit"],
    }
    if live != expected:
        return {
            "result": "LANDING_BLOCKED",
            "cause": "accepted handoff no longer matches the exact remote coordination boundary",
            "evidence": {"branch": branch, "expected_remote": expected, "live_remote": live},
            "next": ["integration authority releases the local handoff if safe", "coordinate with the publishing contributor"],
        }
    if current_mainline != metadata["handoff_base"]:
        return {
            "result": "LANDING_BLOCKED",
            "cause": "configured mainline moved after the contributor's approved handoff base",
            "evidence": {
                "branch": branch,
                "handoff_base": metadata["handoff_base"],
                "current_mainline": current_mainline,
                "ready_commit": metadata["ready_commit"],
                "contributor_actor": metadata["contributor_actor"],
                "approval_actor": metadata.get("approval_actor"),
                "integration_actor": actor["actor"],
            },
            "next": [
                "integration authority releases the handoff",
                "publishing contributor withdraws it, reconciles with current mainline, re-checks/re-approves as required, and republishes",
                "or a human intentionally supersedes/abandons the Goal",
            ],
        }
    return {
        "result": "READY_FOR_LANDING",
        "branch": branch,
        "mainline": mainline,
        "handoff_commit": state["handoff_commit"],
        "acceptance_commit": state["acceptance_commit"],
        "handoff_base": metadata["handoff_base"],
        "ready_commit": metadata["ready_commit"],
        "contributor_actor": metadata["contributor_actor"],
        "approval_actor": metadata.get("approval_actor"),
        "integration_actor": actor["actor"],
    }


def publish_landed_mainline(repo: Path, data: dict[str, Any]) -> dict[str, Any]:
    """Publish an already-integrated local landing before destructive finalization.

    The landing receipt itself is the push source, so retrying a transaction never
    pushes unrelated mainline commits that may have appeared after integration.
    A remote that already contains the receipt is accepted as already published.
    """
    branch = data["branch"]
    mainline = data["mainline"]
    receipt = data.get("merge_commit")
    if not receipt:
        fail("merged landing transaction has no recorded merge receipt to publish")
    if not ref_exists(repo, branch_ref(mainline)):
        fail(f"configured mainline branch no longer exists: {mainline}")
    if not is_ancestor(repo, receipt, rev(repo, branch_ref(mainline))):
        fail("recorded landing merge receipt is no longer reachable from configured mainline")

    remote = str(load_config().get("remote", "origin"))
    require_configured_remote(repo, remote)
    remote_commit = remote_head(repo, remote, mainline)
    if remote_commit == receipt:
        pass
    else:
        remote_ref = land_runtime_ref(branch, "remote-mainline")
        try:
            if remote_commit is not None:
                cp = git(
                    ["fetch", "--no-tags", remote, f"refs/heads/{mainline}:{remote_ref}"],
                    repo,
                    check=False,
                )
                if cp.returncode != 0:
                    fail(
                        f"cannot inspect remote {remote}/{mainline} before landing publication: "
                        f"{cp.stderr.strip() or cp.stdout.strip()}"
                    )
                fetched = rev(repo, remote_ref)
                if is_ancestor(repo, receipt, fetched):
                    data["phase"] = "published"
                    write_land_state(repo, branch, data)
                    update_ref(repo, land_runtime_ref(branch, "published"), receipt)
                    return data

            cp = git(
                ["push", remote, f"{receipt}:refs/heads/{mainline}"],
                repo,
                check=False,
            )
            if cp.returncode != 0:
                fail(
                    f"landing integrated locally but pushing {mainline} to {remote} failed; "
                    f"landing remains recoverable and is not finalized: "
                    f"{cp.stderr.strip() or cp.stdout.strip()}"
                )
        finally:
            if ref_exists(repo, remote_ref):
                update_ref(repo, remote_ref, None)

    data["phase"] = "published"
    write_land_state(repo, branch, data)
    update_ref(repo, land_runtime_ref(branch, "published"), receipt)
    return data


def cmd_repo_status(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config()
    repo = discover_git_root()
    if repo is None:
        return {
            "harness_version": harness_version(),
            "git": "uninitialized",
            "project_root": str(PROJECT_ROOT),
            "configured_mainline": config.get("mainline"),
            "bootstrap_mainline": config.get("bootstrap_mainline"),
        }
    repo = validate_repository_topology(repo)
    mainline = resolve_mainline(repo, config)
    return {
        "harness_version": harness_version(),
        "git": "initialized",
        "project_root": str(PROJECT_ROOT),
        "git_root": str(repo),
        "head": rev(repo, "HEAD") if has_commits(repo) else None,
        "branch": current_branch(repo),
        "clean": not worktree_status(repo),
        "mainline": mainline,
        "mainline_head": rev(repo, branch_ref(mainline)) if ref_exists(repo, branch_ref(mainline)) else None,
    }


def cmd_repo_bootstrap(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config()
    bootstrap_mainline = resolve_bootstrap_mainline(config)
    repo = discover_git_root()
    if repo is None:
        mainline = bootstrap_mainline
        cp = run(["git", "init", "-b", mainline, str(PROJECT_ROOT)], check=False)
        if cp.returncode != 0:
            fail(cp.stderr.strip() or cp.stdout.strip() or "git init failed")
        repo = require_repo()
    else:
        repo = validate_repository_topology(repo)
        mainline = resolve_mainline(repo, config)

    if has_commits(repo):
        return {
            "result": "already established",
            "git_root": str(repo),
            "mainline": resolve_mainline(repo, config),
            "head": rev(repo, "HEAD"),
        }

    mainline = bootstrap_mainline
    branch = current_branch(repo)
    if branch != mainline:
        git(["symbolic-ref", "HEAD", branch_ref(mainline)], repo)

    # Git itself is authoritative for whether identity is configured/usable.
    ident_name = git(["var", "GIT_AUTHOR_IDENT"], repo, check=False)
    ident_committer = git(["var", "GIT_COMMITTER_IDENT"], repo, check=False)
    if ident_name.returncode != 0 or ident_committer.returncode != 0:
        fail("Git author/committer identity is unavailable; repository may remain initialized/unborn")

    require_clean(repo) if args.require_clean else None
    seed_paths = list(args.seed_path or [])
    pre_staged = []
    for line in git(["ls-files", "--stage"], repo).stdout.splitlines():
        if not line.strip():
            continue
        pre_staged.append(line.split("\t", 1)[1] if "\t" in line else line.strip())
    if pre_staged and not args.all_seed_files:
        fail(
            "bootstrap index is not empty; refusing to inherit pre-staged content into the baseline "
            "unless --all-seed-files is explicitly selected:\n" + "\n".join(pre_staged[:50])
        )
    if args.all_seed_files:
        git(["add", "-A"], repo)
    elif seed_paths:
        # `--` prevents seed paths beginning with '-' from being parsed as Git options.
        git(["add", "--", *seed_paths], repo)
    # Safe default: create an empty baseline unless seed content was explicitly selected for staging.
    git(["commit", "--allow-empty", "-m", args.message], repo)
    return {
        "result": "baseline created",
        "mainline": mainline,
        "head": rev(repo, "HEAD"),
        "tree": tree(repo, "HEAD"),
    }


def cmd_branch_start(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    config = load_config()
    if not has_commits(repo):
        fail("repository is unborn; run `repo bootstrap` first")
    mainline = resolve_mainline(repo, config)
    name = require_valid_branch_name(args.name, "branch --name")
    base = require_valid_branch_name(
        args.base or mainline,
        "branch --base" if args.base is not None else "configured mainline",
    )
    if not ref_exists(repo, branch_ref(base)):
        fail(f"base branch does not exist: {base}")
    if ref_exists(repo, branch_ref(name)):
        if current_branch(repo) == name and args.reuse:
            return {"result": "reused", "branch": name, "base": base, "head": rev(repo, "HEAD")}
        fail(f"branch already exists: {name}")
    require_clean(repo)
    # Use the full starting ref as defense in depth so a branch-like token can
    # never be reinterpreted as a `git switch` option.
    git(["switch", "-c", name, branch_ref(base)], repo)
    return {"result": "created", "branch": name, "base": base, "head": rev(repo, "HEAD")}


def approval_ref(branch: str) -> str:
    return f"refs/harness/landing-approval/{branch}"


def landing_approval_ref_reason(approval: str | None, branch: str) -> tuple[bool, str]:
    """Validate the single landing-approval namespace and branch binding."""
    if not approval:
        return False, "transaction has no approval ref"
    expected = approval_ref(branch)
    if approval != expected:
        return False, f"landing approval ref must be the branch's own Harness approval ref; expected {expected}, got {approval}"
    return True, "valid branch-bound approval ref"


def cmd_approval_record(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    require_clean(repo)
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("approval requires a named branch")
    branch = require_valid_branch_name(branch, "approval --branch" if args.branch is not None else "current branch")
    if not ref_exists(repo, branch_ref(branch)):
        fail(f"branch does not exist: {branch}")
    require_goal_document(repo, branch)
    commit = rev(repo, branch_ref(branch))
    ref = approval_ref(branch)
    if ref_exists(repo, ref):
        if rev(repo, ref) == commit:
            return {"result": "already recorded", "branch": branch, "ref": ref, "commit": commit, "tree": tree(repo, commit)}
        fail(f"approval already exists at a different boundary: {ref}; drop it after renewed user authorization")
    update_ref(repo, ref, commit)
    return {"result": "recorded", "branch": branch, "ref": ref, "commit": commit, "tree": tree(repo, commit)}


def cmd_approval_validate(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("approval validation requires a named branch")
    branch = require_valid_branch_name(branch, "approval --branch" if args.branch is not None else "current branch")
    ref = approval_ref(branch)
    if not ref_exists(repo, ref):
        return {"valid": False, "reason": "missing", "ref": ref}
    commit = rev(repo, ref)
    approved_tree = tree(repo, ref)
    branch_commit = rev(repo, branch_ref(branch)) if ref_exists(repo, branch_ref(branch)) else None
    same_tree = branch_commit is not None and tree(repo, branch_commit) == approved_tree
    return {
        "valid": bool(same_tree),
        "ref": ref,
        "commit": commit,
        "tree": approved_tree,
        "branch": branch,
        "branch_commit": branch_commit,
        "same_tree": same_tree,
    }


def land_approval_valid(repo: Path, data: dict[str, Any]) -> tuple[bool, str]:
    """Return whether an unmerged landing transaction still has live exact authority."""
    approval = data.get("approval_ref")
    branch = data.get("branch")
    if not branch:
        return False, "transaction has no branch"
    ref_ok, ref_reason = landing_approval_ref_reason(approval, branch)
    if not ref_ok:
        return False, ref_reason
    if not ref_exists(repo, approval):
        return False, f"approval ref is missing: {approval}"
    actual = rev(repo, approval)
    expected = data.get("approval_source_commit")
    if expected and actual != expected:
        return False, f"approval ref moved from {expected} to {actual}"
    return True, "valid"

def abort_land_transaction(repo: Path, branch: str) -> None:
    delete_land_runtime_refs(repo, branch)
    delete_land_state(repo, branch)


def approval_withdrawal_plan(repo: Path, approval: str) -> tuple[list[str], list[str]]:
    """Classify dependent landing transactions before mutating approval state.

    A transaction may be discarded only while its candidate has not crossed the
    configured mainline ref. Once mainline equals the recorded candidate, receipt
    state is recovery authority and must survive approval withdrawal.
    """
    cancel: list[str] = []
    preserve: list[str] = []
    directory = land_state_dir(repo)
    if not directory.exists():
        return cancel, preserve
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(f"cannot inspect landing transaction during approval withdrawal: {path}: {exc}")
        branch = data.get("branch")
        if not isinstance(branch, str) or not branch:
            fail(f"invalid landing transaction metadata during approval withdrawal: {path} has no branch binding")
        data = validate_land_state(branch, data)
        if data.get("approval_ref") != approval:
            continue
        phase = data.get("phase")
        if phase == "ready":
            cancel.append(branch)
            continue
        if phase in {"merged", "published"}:
            preserve.append(branch)
            continue
        if phase != "integrating":
            fail(f"unsupported landing phase during approval withdrawal: {phase!r}")

        mainline = data["mainline"]
        if not ref_exists(repo, branch_ref(mainline)):
            fail(f"cannot withdraw approval while integrating: configured mainline is missing: {mainline}")
        candidate = data.get("merge_commit")
        if not candidate:
            fail("cannot withdraw approval while integrating: transaction has no candidate receipt")
        current_mainline = rev(repo, branch_ref(mainline))
        if current_mainline == data.get("base_commit"):
            # Candidate exists, but the irreversible mainline boundary has not
            # been crossed. Withdrawal may safely cancel the prepared attempt.
            cancel.append(branch)
        elif current_mainline == candidate:
            # A crash may have happened after the atomic CAS but before `merged`
            # was persisted. Keep the transaction so deterministic recovery can
            # finish without needing the withdrawn approval.
            preserve.append(branch)
        else:
            fail(
                "cannot withdraw approval while an integrating landing has ambiguous mainline state; "
                f"{mainline} is neither prepared base {data.get('base_commit')} nor candidate {candidate}"
            )
    return cancel, preserve


def cmd_approval_drop(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("approval invalidation requires a branch name")
    branch = require_valid_branch_name(branch, "approval --branch" if args.branch is not None else "current branch")
    if _collaboration().active_collaboration_model(PROJECT_ROOT) == "cooperative-multi-user" and _collaboration().read_handoff_state(repo, branch, required=False) is not None:
        fail(
            "accepted cooperative handoff approval cannot be dropped independently; "
            "abort any ready landing transaction and release the handoff instead"
        )
    ref = approval_ref(branch)
    # Preflight every dependent transaction before deleting the approval ref so
    # a corrupt/diverged recovery state cannot cause a partial withdrawal.
    cancel, preserved = approval_withdrawal_plan(repo, ref)
    existed = ref_exists(repo, ref)
    if existed:
        update_ref(repo, ref, None)
    for dependent_branch in cancel:
        abort_land_transaction(repo, dependent_branch)
    return {
        "result": "removed" if existed else "already absent",
        "ref": ref,
        "invalidated_land_transactions": cancel,
        "preserved_land_transactions": preserved,
    }


def land_state_summary(repo: Path, data: dict[str, Any]) -> dict[str, Any]:
    branch = data["branch"]
    branch_exists_now = ref_exists(repo, branch_ref(branch))
    head = rev(repo, branch_ref(branch)) if branch_exists_now else None
    mainline = data["mainline"]
    mainline_head = rev(repo, branch_ref(mainline)) if ref_exists(repo, branch_ref(mainline)) else None
    approval_live, approval_reason = land_approval_valid(repo, data)
    return {
        **data,
        "branch_exists": branch_exists_now,
        "current_branch_head": head,
        "current_mainline_head": mainline_head,
        "base_unchanged": mainline_head == data.get("base_commit"),
        "head_at_ready": bool(head and data.get("ready_commit") == head),
        "approval_live": approval_live,
        "approval_status": approval_reason,
    }


def cmd_land_prepare(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    integration_actor = _collaboration().require_integration_authority(repo)
    config = load_config()
    require_clean(repo)
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("landing preparation requires a named work branch")
    branch = require_valid_branch_name(branch, "land --branch" if args.branch is not None else "current branch")
    if current_branch(repo) != branch:
        fail(f"switch to landing branch before prepare: {branch}")
    mainline = resolve_mainline(repo, config)
    if branch == mainline:
        fail("cannot prepare configured mainline as a work branch")
    if not ref_exists(repo, branch_ref(branch)):
        fail(f"branch does not exist: {branch}")
    require_goal_document(repo, branch)

    path = land_state_path(repo, branch)
    if path.exists():
        old = read_land_state(repo, branch)
        if old.get("phase") in {"merged", "published"}:
            fail("landing already crossed mainline; finish deterministic recovery instead")
        head = rev(repo, branch_ref(branch))
        base = rev(repo, branch_ref(mainline))
        if old.get("ready_commit") == head and old.get("base_commit") == base:
            approval_ok, _ = land_approval_valid(repo, old)
            if approval_ok:
                return {"result": "already prepared", **land_state_summary(repo, old)}
        fail("landing transaction already exists at a different boundary; abort it before preparing again")

    approval = approval_ref(branch)
    if not ref_exists(repo, approval):
        fail(f"landing preparation requires recorded approval: {approval}")
    approval_source_commit = rev(repo, approval)
    approved_tree = tree(repo, approval)
    head = rev(repo, branch_ref(branch))
    if tree(repo, head) != approved_tree:
        fail("branch full tree no longer equals the recorded approval tree")
    base = rev(repo, branch_ref(mainline))
    accepted_handoff = _collaboration().require_live_accepted_handoff(repo, branch)
    if accepted_handoff is not None:
        handoff_metadata = _collaboration().validate_handoff_metadata(branch, accepted_handoff["metadata"])
        if handoff_metadata["handoff_base"] != base:
            fail(
                "LANDING_BLOCKED: configured mainline moved after the contributor's approved handoff base; "
                "run `land assess --branch <branch>` for human-resolvable evidence"
            )
    else:
        handoff_metadata = None
    remote = str(config.get("remote", "origin"))
    require_remote_landing_alignment(repo, remote, mainline, branch, head)

    data = {
        "branch": branch,
        "mainline": mainline,
        "approval_ref": approval,
        "approval_source_commit": approval_source_commit,
        "approved_tree": approved_tree,
        "base_commit": base,
        "ready_commit": head,
        "phase": "ready",
    }
    if accepted_handoff is not None and handoff_metadata is not None:
        data.update({
            "handoff_commit": accepted_handoff["handoff_commit"],
            "acceptance_commit": accepted_handoff["acceptance_commit"],
            "handoff_base": handoff_metadata["handoff_base"],
            "contributor_actor": handoff_metadata["contributor_actor"],
            "approval_actor": handoff_metadata.get("approval_actor"),
            "integration_actor": integration_actor["actor"] if integration_actor else None,
        })
    write_land_state(repo, branch, data)
    update_ref(repo, land_runtime_ref(branch, "base"), base)
    update_ref(repo, land_runtime_ref(branch, "ready"), head)
    return {"result": "prepared", **land_state_summary(repo, data)}


def finalize_land(repo: Path, data: dict[str, Any], delete_remote: bool) -> dict[str, Any]:
    branch = data["branch"]
    mainline = data["mainline"]
    remote = str(load_config().get("remote", "origin"))
    branch_commit = data.get("ready_commit")
    merge_commit = data.get("merge_commit")
    if not merge_commit:
        fail("merged landing transaction has no recorded merge receipt")
    if not ref_exists(repo, branch_ref(mainline)):
        fail(f"configured mainline branch no longer exists: {mainline}")
    mainline_head = rev(repo, branch_ref(mainline))
    if not is_ancestor(repo, merge_commit, mainline_head):
        fail("recorded landing merge receipt is no longer reachable from configured mainline")
    local_branch_exists = ref_exists(repo, branch_ref(branch))
    if local_branch_exists:
        if current_branch(repo) == branch:
            fail("cannot finalize landing while still on the work branch")
        if not branch_commit:
            fail("cannot delete local work branch without a prepared ready boundary")
        actual_branch_commit = rev(repo, branch_ref(branch))
        if actual_branch_commit != branch_commit:
            fail(
                "local work branch moved from prepared ready boundary after merge; refusing deletion "
                f"({branch_commit} -> {actual_branch_commit})"
            )
    # Preflight local exactness before any destructive remote/local cleanup so a
    # locally advanced branch cannot cause partial finalization.
    handoff_commit = data.get("handoff_commit")
    if handoff_commit and branch_commit:
        # A consumed cooperative handoff is runtime coordination state, not Project
        # history. Finalization atomically removes the accepted handoff ref and the
        # published Goal branch. Exact leases keep cleanup fail-closed and retry-safe.
        acceptance_commit = data.get("acceptance_commit")
        if not acceptance_commit:
            fail(
                "landing transaction carries a cooperative handoff without an acceptance commit; "
                "the transaction is incomplete and cannot be finalized safely"
            )
        delete_remote_refs_exact(
            repo,
            remote,
            {_collaboration().handoff_ref(branch): acceptance_commit, f"refs/heads/{branch}": branch_commit},
        )
    elif delete_remote and branch_commit:
        delete_remote_exact(repo, remote, branch, branch_commit)
    if local_branch_exists:
        update_ref(repo, branch_ref(branch), None, branch_commit)
    delete_goal_document(repo, branch)
    delete_session_document(repo)
    approval = data.get("approval_ref")
    if approval and approval.startswith("refs/harness/landing-approval/") and ref_exists(repo, approval):
        update_ref(repo, approval, None)
    delete_land_runtime_refs(repo, branch)
    delete_land_state(repo, branch)
    handoff_path = _collaboration().handoff_state_path(repo, branch)
    if handoff_path.exists():
        handoff_path.unlink()
    _collaboration().delete_handoff_runtime_refs(repo, branch)
    result = {"result": "landed", "branch": branch, "mainline": data["mainline"], "merge_commit": data.get("merge_commit")}
    return result


def prepare_local_integration(repo: Path, data: dict[str, Any], message: str) -> str:
    """Build the configured landing shape without moving mainline."""
    branch = data["branch"]
    base = data["base_commit"]
    ready = data["ready_commit"]
    with tempfile.TemporaryDirectory(prefix="harness-land-") as td:
        worktree = Path(td) / "integration"
        cp = git(["worktree", "add", "--detach", str(worktree), base], repo, check=False)
        if cp.returncode != 0:
            detail = cp.stderr.strip() or cp.stdout.strip() or f"exit {cp.returncode}"
            fail(f"cannot create disposable landing worktree: {detail}")
        try:
            if is_ancestor(repo, base, ready) and commit_count(repo, base, ready) == 1:
                git(["merge", "--ff-only", ready], worktree)
            else:
                git(["merge", "--no-ff", ready, "-m", message], worktree)
            candidate = rev(worktree, "HEAD")
            if tree(worktree, candidate) != tree(repo, ready):
                fail("landing candidate tree does not equal prepared branch tree")
            update_ref(repo, land_runtime_ref(branch, "candidate"), candidate)
            return candidate
        except HarnessError as exc:
            fail(f"landing preparation failed before mainline update: {exc}")
        finally:
            git(["worktree", "remove", "--force", str(worktree)], repo, check=False)


def worktrees_with_branch(repo: Path, branch: str) -> list[Path]:
    """Return linked worktrees whose HEAD is attached to the exact branch ref."""
    cp = git(["worktree", "list", "--porcelain"], repo)
    target = branch_ref(branch)
    matches: list[Path] = []
    current_path: Path | None = None
    for line in cp.stdout.splitlines():
        if line.startswith("worktree "):
            current_path = Path(line[len("worktree "):]).resolve()
        elif line == f"branch {target}" and current_path is not None:
            matches.append(current_path)
    return matches


def refuse_mainline_checked_out_elsewhere(repo: Path, mainline: str) -> None:
    current = repo.resolve()
    elsewhere = [path for path in worktrees_with_branch(repo, mainline) if path != current]
    if elsewhere:
        rendered = ", ".join(str(path) for path in elsewhere)
        fail(
            f"mainline branch {mainline!r} is checked out in another linked Git worktree: {rendered}; "
            "refusing to move its ref behind that worktree"
        )


def complete_local_integration(repo: Path, data: dict[str, Any]) -> dict[str, Any]:
    """Atomically cross a prepared local candidate onto mainline, restart-safely."""
    branch = data["branch"]
    mainline = data["mainline"]
    base = data["base_commit"]
    ready = data.get("ready_commit")
    candidate = data.get("merge_commit")
    candidate_ref = land_runtime_ref(branch, "candidate")
    if not candidate or not ready:
        fail("integrating landing transaction is missing its candidate/ready boundary")
    if not ref_exists(repo, candidate_ref) or rev(repo, candidate_ref) != candidate:
        fail("integrating landing candidate anchor is missing or moved")
    if tree(repo, candidate) != tree(repo, ready):
        fail("integrating landing candidate no longer has the verified ready tree")
    if not ref_exists(repo, branch_ref(mainline)):
        fail(f"mainline branch no longer exists: {mainline}")

    current_mainline = rev(repo, branch_ref(mainline))
    if current_mainline == base:
        if data.get("handoff_commit"):
            _collaboration().require_live_accepted_handoff(repo, branch)
        remote = str(load_config().get("remote", "origin"))
        require_remote_landing_alignment(repo, remote, mainline, branch, ready)
        approval_ok, approval_reason = land_approval_valid(repo, data)
        if not approval_ok:
            fail(f"landing approval is no longer valid: {approval_reason}; refusing mainline update")
        if not ref_exists(repo, branch_ref(branch)) or rev(repo, branch_ref(branch)) != ready:
            fail("work branch moved from verified ready boundary before mainline update")
        refuse_mainline_checked_out_elsewhere(repo, mainline)
        # A checked-out branch must not have its ref moved behind its worktree.
        # Detach only in the uncommon recovery/invocation case where mainline is
        # currently checked out; ordinary Branch Land enters here from work branch.
        if current_branch(repo) == mainline:
            git(["switch", "--detach", base], repo)
        update_ref(repo, branch_ref(mainline), candidate, base)
    elif current_mainline != candidate:
        fail(
            "mainline moved while a local landing candidate was prepared; "
            "refusing to extend the prepared authority to a different boundary"
        )

    # If a previous process crossed the atomic ref update and stopped before
    # persisting `merged`, this is the restart-safe completion point.
    data["phase"] = "merged"
    write_land_state(repo, branch, data)
    update_ref(repo, land_runtime_ref(branch, "merged"), candidate)
    if current_branch(repo) != mainline:
        git(["switch", mainline], repo)
    return data


def cmd_land_merge(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    _collaboration().require_integration_authority(repo)
    require_clean(repo)
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("landing merge requires a branch")
    branch = require_valid_branch_name(branch, "land --branch" if args.branch is not None else "current branch")
    data = read_land_state(repo, branch)
    mainline = data["mainline"]
    if not ref_exists(repo, branch_ref(mainline)):
        fail(f"mainline branch no longer exists: {mainline}")

    if data.get("phase") == "published":
        if current_branch(repo) != mainline:
            git(["switch", mainline], repo)
        return finalize_land(repo, data, args.delete_remote)

    if data.get("phase") == "merged":
        if current_branch(repo) != mainline:
            git(["switch", mainline], repo)
        data = publish_landed_mainline(repo, data)
        return finalize_land(repo, data, args.delete_remote)

    if data.get("phase") == "integrating":
        data = complete_local_integration(repo, data)
        data = publish_landed_mainline(repo, data)
        return finalize_land(repo, data, args.delete_remote)

    if data.get("handoff_commit"):
        _collaboration().require_live_accepted_handoff(repo, branch)
    approval_ok, approval_reason = land_approval_valid(repo, data)
    if not approval_ok:
        fail(f"landing approval is no longer valid: {approval_reason}; re-check and prepare again before landing")

    if not ref_exists(repo, branch_ref(branch)):
        fail("work branch is missing before landing")
    head = rev(repo, branch_ref(branch))
    if data.get("ready_commit") != head:
        fail("work branch moved after `land prepare`; abort and prepare the current boundary")
    if tree(repo, head) != data.get("approved_tree"):
        fail("prepared branch tree no longer equals the approved tree")
    if rev(repo, branch_ref(mainline)) != data.get("base_commit"):
        fail("mainline moved after `land prepare`; re-check the Goal against current mainline and prepare again")

    message = args.message or f"Land {branch}"
    candidate = prepare_local_integration(repo, data, message)
    candidate_ref = land_runtime_ref(branch, "candidate")
    try:
        approval_ok, approval_reason = land_approval_valid(repo, data)
        if not approval_ok:
            fail(f"landing approval is no longer valid after candidate preparation: {approval_reason}")
        if rev(repo, branch_ref(branch)) != head:
            fail("work branch moved while landing candidate was being prepared")
        if rev(repo, branch_ref(mainline)) != data.get("base_commit"):
            fail("mainline moved while landing candidate was being prepared; re-check and prepare again")
        remote = str(load_config().get("remote", "origin"))
        require_remote_landing_alignment(repo, remote, mainline, branch, head)

        data["phase"] = "integrating"
        data["merge_commit"] = candidate
        write_land_state(repo, branch, data)
    except HarnessError:
        if ref_exists(repo, candidate_ref):
            update_ref(repo, candidate_ref, None)
        raise
    data = complete_local_integration(repo, data)
    data = publish_landed_mainline(repo, data)
    return finalize_land(repo, data, args.delete_remote)


def cmd_land_abort(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    _collaboration().require_integration_authority(repo)
    branch = args.branch or current_branch(repo)
    if not branch:
        fail("land abort requires a branch")
    branch = require_valid_branch_name(branch, "land --branch" if args.branch is not None else "current branch")
    data = read_land_state(repo, branch)
    if data.get("phase") != "ready":
        fail("cannot abort after integration has started; resume deterministic landing recovery instead")
    abort_land_transaction(repo, branch)
    return {"result": "transaction removed", "branch": branch}


def cmd_abandon_discard(args: argparse.Namespace) -> dict[str, Any]:
    repo = require_repo()
    config = load_config()
    require_clean(repo)
    target = require_valid_branch_name(args.target, "abandon --target")
    if _collaboration().active_collaboration_model(PROJECT_ROOT) == "cooperative-multi-user" and _collaboration().read_handoff_state(repo, target, required=False) is not None:
        fail(
            "accepted cooperative handoff cannot be abandoned independently; "
            "abort any ready landing transaction and release the handoff first"
        )
    if not ref_exists(repo, branch_ref(target)):
        fail(f"target branch does not exist: {target}")
    mainline = resolve_mainline(repo, config)
    if target == mainline:
        fail("cannot abandon configured mainline")

    target_commit = rev(repo, branch_ref(target))
    if args.mode == "no-op":
        mb = git(["merge-base", branch_ref(mainline), branch_ref(target)], repo, check=False)
        if mb.returncode != 0 or not mb.stdout.strip():
            fail("cannot prove no-op abandonment because target has no merge base with configured mainline")
        merge_base_commit = mb.stdout.strip()
        if tree(repo, target_commit) != tree(repo, merge_base_commit):
            fail(
                "no-op abandonment requires the target tree to equal its merge-base tree; "
                "unique durable branch changes require --mode explicit"
            )

    if args.delete_remote:
        remote = str(config.get("remote", "origin"))
        delete_remote_exact(repo, remote, target, target_commit)

    if current_branch(repo) == target:
        if not ref_exists(repo, branch_ref(mainline)):
            fail(f"cannot switch away from target; fallback branch missing: {mainline}")
        git(["switch", mainline], repo)

    update_ref(repo, branch_ref(target), None, target_commit)
    delete_goal_document(repo, target)
    delete_session_document(repo)
    approval = approval_ref(target)
    if ref_exists(repo, approval):
        update_ref(repo, approval, None)
    abort_land_transaction(repo, target)
    return {"result": "discarded", "target": target, "discarded_commit": target_commit, "mode": args.mode}


def list_land_transaction_states(repo: Path) -> list[dict[str, Any]]:
    directory = land_state_dir(repo)
    if not directory.exists():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            result.append({"state_file": str(path), "error": str(exc)})
            continue
        branch = data.get("branch")
        if not isinstance(branch, str) or not branch:
            result.append({"state_file": str(path), "error": "invalid land transaction: missing branch binding"})
            continue
        try:
            data = validate_land_state(branch, data)
            result.append(land_state_summary(repo, data))
        except HarnessError as exc:
            result.append({**data, "state_file": str(path), "error": str(exc)})
    return result


def cmd_resume(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config()
    repo = discover_git_root()
    if repo is None:
        return {
            "git": "uninitialized",
            "project_root": str(PROJECT_ROOT),
            "next_git_action": "after lifecycle classification, Branch Start may invoke `repo bootstrap`",
        }
    repo = validate_repository_topology(repo)
    mainline = resolve_mainline(repo, config)
    branch = current_branch(repo)
    approvals = list_refs(repo, "refs/harness/landing-approval/")
    current_approval = None
    if branch:
        ref = approval_ref(branch)
        if ref_exists(repo, ref):
            current_approval = {
                "ref": ref,
                "commit": rev(repo, ref),
                "tree": tree(repo, ref),
                "current_branch_tree_matches": tree(repo, ref) == tree(repo, branch_ref(branch)),
            }
    collaboration_model = _collaboration().active_collaboration_model(PROJECT_ROOT)
    local_actor = _collaboration().read_collaboration_state(repo, required=False)
    accepted_handoff = _collaboration().read_handoff_state(repo, branch, required=False) if branch else None
    result = {
        "git": "initialized",
        "collaboration_model": collaboration_model,
        "local_actor": local_actor,
        "accepted_handoff": accepted_handoff,
        "git_root": str(repo),
        "branch": branch,
        "head": rev(repo, "HEAD") if has_commits(repo) else None,
        "clean": not worktree_status(repo),
        "working_tree_changes": worktree_status(repo),
        "mainline": mainline,
        "mainline_head": rev(repo, branch_ref(mainline)) if ref_exists(repo, branch_ref(mainline)) else None,
        "goal_path": goal_document_path(branch) if branch and branch != mainline else None,
        "goal_document_exists": bool(
            branch and branch != mainline and goal_document_file(repo, branch).is_file()
        ),
        "current_landing_approval": current_approval,
        "approvals": approvals,
        "land_transactions": list_land_transaction_states(repo),
    }
    if branch and branch != mainline and ref_exists(repo, branch_ref(mainline)):
        mb = git(["merge-base", branch_ref(mainline), branch_ref(branch)], repo, check=False)
        result["merge_base"] = mb.stdout.strip() if mb.returncode == 0 else None
    return result


