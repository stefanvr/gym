#!/usr/bin/env python3
"""Low-level deterministic runtime support.

Owns process execution, Git/repository facts, lifecycle locking, configured-mainline
resolution, and persisted landing state primitives. Command orchestration remains in
`kernel.py` so agents can inspect lifecycle policy without loading these mechanics.
"""
from __future__ import annotations

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
MAIN_SHADOW_BRANCH = "main-shadow"
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
    if input_text is not None and proc.stdin is not None:
        # Deterministic protocol input must preserve LF bytes exactly. In text mode,
        # Windows otherwise translates ``\n`` to ``\r\n`` before writing to the
        # child process. That corrupts line-oriented Git plumbing such as ``mktree``:
        # the carriage return becomes part of the tree entry name (for example,
        # ``goal.md\r``), making the object unreadable by its intended path.
        proc.stdin.reconfigure(newline="\n")
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


def configure_main_shadow(repo: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Create the guarded onboarding shadow and make it Harness mainline.

    Main-shadow onboarding is deliberately limited to repositories that already
    have committed history. The existing repository mainline remains untouched;
    Harness configuration is rewritten only on the new shadow branch so all
    subsequent lifecycle mechanics treat `main-shadow` as configured mainline.
    """
    if not has_commits(repo):
        fail("main-shadow onboarding requires an existing repository with committed history")

    configured = str(config.get("mainline", "auto"))
    if configured == MAIN_SHADOW_BRANCH:
        if not ref_exists(repo, branch_ref(MAIN_SHADOW_BRANCH)):
            fail("runtime config selects main-shadow but refs/heads/main-shadow does not exist")
        if current_branch(repo) != MAIN_SHADOW_BRANCH:
            git(["switch", MAIN_SHADOW_BRANCH], repo)
        return {
            "mainline": MAIN_SHADOW_BRANCH,
            "shadow_source_mainline": None,
            "shadow_source_head": None,
            "main_shadow_created": False,
            "main_shadow_reused": True,
        }

    source_mainline = resolve_mainline(repo, config)
    if source_mainline == MAIN_SHADOW_BRANCH:
        fail("main-shadow cannot be its own onboarding source mainline")
    source_head = rev(repo, branch_ref(source_mainline))

    created = False
    reused = False
    if ref_exists(repo, branch_ref(MAIN_SHADOW_BRANCH)):
        shadow_head = rev(repo, branch_ref(MAIN_SHADOW_BRANCH))
        if shadow_head != source_head:
            fail(
                "main-shadow already exists at a different commit; refusing to repurpose it for onboarding "
                f"(source {source_mainline}={source_head}, main-shadow={shadow_head})"
            )
        reused = True
    else:
        update_ref(repo, branch_ref(MAIN_SHADOW_BRANCH), source_head)
        created = True

    if current_branch(repo) != MAIN_SHADOW_BRANCH:
        git(["switch", MAIN_SHADOW_BRANCH], repo)

    shadow_config = dict(config)
    shadow_config["mainline"] = MAIN_SHADOW_BRANCH
    shadow_config["bootstrap_mainline"] = MAIN_SHADOW_BRANCH
    atomic_json(CONFIG_PATH, shadow_config)
    return {
        "mainline": MAIN_SHADOW_BRANCH,
        "shadow_source_mainline": source_mainline,
        "shadow_source_head": source_head,
        "main_shadow_created": created,
        "main_shadow_reused": reused,
    }


def preflight_main_shadow_bootstrap(args: argparse.Namespace) -> dict[str, Any]:
    """Validate shadow onboarding without mutating Git, config, or composition."""
    config = load_config()
    repo = discover_git_root()
    if repo is None:
        fail("main-shadow onboarding is only available for an existing repository with committed history")
    repo = validate_repository_topology(repo)
    if not has_commits(repo):
        fail("main-shadow onboarding is only available for an existing repository with committed history")
    try:
        CONFIG_PATH.relative_to(repo)
    except ValueError:
        fail("main-shadow onboarding requires .harness/runtime/config.json to live inside the repository")

    if getattr(args, "require_clean", False):
        require_clean(repo)

    pre_staged = [
        line.strip()
        for line in git(["diff", "--cached", "--name-only", "HEAD"], repo).stdout.splitlines()
        if line.strip()
    ]
    if pre_staged and not getattr(args, "all_seed_files", False):
        fail(
            "bootstrap index is not empty; refusing to inherit pre-staged content into the main-shadow baseline "
            "unless --all-seed-files is explicitly selected:\n" + "\n".join(pre_staged[:50])
        )

    ident_name = git(["var", "GIT_AUTHOR_IDENT"], repo, check=False)
    ident_committer = git(["var", "GIT_COMMITTER_IDENT"], repo, check=False)
    if ident_name.returncode != 0 or ident_committer.returncode != 0:
        fail("Git author/committer identity is unavailable; main-shadow onboarding was not started")

    configured = str(config.get("mainline", "auto"))
    if configured == MAIN_SHADOW_BRANCH:
        if not ref_exists(repo, branch_ref(MAIN_SHADOW_BRANCH)):
            fail("runtime config selects main-shadow but refs/heads/main-shadow does not exist")
        return {"repo": repo, "config": config, "source_mainline": None, "source_head": None}

    source_mainline = resolve_mainline(repo, config)
    if source_mainline == MAIN_SHADOW_BRANCH:
        fail("main-shadow cannot be its own onboarding source mainline")
    source_head = rev(repo, branch_ref(source_mainline))
    if ref_exists(repo, branch_ref(MAIN_SHADOW_BRANCH)):
        shadow_head = rev(repo, branch_ref(MAIN_SHADOW_BRANCH))
        if shadow_head != source_head:
            fail(
                "main-shadow already exists at a different commit; refusing to repurpose it for onboarding "
                f"(source {source_mainline}={source_head}, main-shadow={shadow_head})"
            )
    return {
        "repo": repo,
        "config": config,
        "source_mainline": source_mainline,
        "source_head": source_head,
    }


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



