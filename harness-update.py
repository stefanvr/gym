#!/usr/bin/env python3
"""Replace an installed Harness with a newer standalone Harness release.

Usage:
    python3 harness-update.py /path/to/harness-v18.4.0.zip
    python3 harness-update.py /path/to/extracted/harness-v18.4.0

The updater replaces only Harness-owned surfaces. Project files such as README.md,
application source, docs, and existing .gitignore entries are left intact.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile


MANIFEST = Path('.harness/update-manifest.json')
VERSION = Path('.harness/runtime/VERSION')
SEMVER_RE = re.compile(r'^(\d+)\.(\d+)(?:\.(\d+))?(?:[-+].*)?$')


class UpdateError(RuntimeError):
    pass


def read_json(path: Path, label: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise UpdateError(f'missing {label}: {path}') from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise UpdateError(f'invalid {label}: {path}: {exc}') from exc
    if not isinstance(data, dict):
        raise UpdateError(f'{label} must be a JSON object: {path}')
    return data


def semver(value: str) -> tuple[int, int, int]:
    match = SEMVER_RE.fullmatch(value.strip())
    if not match:
        raise UpdateError(f'unsupported Harness version format: {value!r}')
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch or 0)


def find_project_root(start: Path) -> Path | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / VERSION).is_file():
            return candidate
    return None


def safe_extract_zip(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as zf:
        base = destination.resolve()
        for info in zf.infolist():
            target = (destination / info.filename).resolve()
            try:
                target.relative_to(base)
            except ValueError as exc:
                raise UpdateError(f'archive contains unsafe path: {info.filename}') from exc
        zf.extractall(destination)


def find_release_root(base: Path) -> Path:
    direct = base / VERSION
    if direct.is_file():
        return base.resolve()
    matches = [p.parent.parent.parent for p in base.rglob(VERSION.name)
               if p.as_posix().endswith(VERSION.as_posix())]
    unique = []
    seen: set[Path] = set()
    for item in matches:
        resolved = item.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    if len(unique) != 1:
        raise UpdateError('new Harness source must contain exactly one .harness/runtime/VERSION')
    return unique[0]


def load_manifest(release_root: Path) -> dict:
    data = read_json(release_root / MANIFEST, 'Harness update manifest')
    if data.get('schema_version') != 1:
        raise UpdateError('unsupported Harness update manifest schema')
    for key in ('replace', 'merge_line_files', 'preserve_trees', 'preserve_files'):
        value = data.get(key, [])
        if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
            raise UpdateError(f'update manifest {key} must be a list of non-empty paths')
    preserve_json = data.get('preserve_json', {})
    if not isinstance(preserve_json, dict):
        raise UpdateError('update manifest preserve_json must be an object')
    for rel, keys in preserve_json.items():
        if not isinstance(rel, str) or not rel or not isinstance(keys, list) or any(not isinstance(k, str) or not k for k in keys):
            raise UpdateError('update manifest preserve_json entries must map paths to key lists')
    return data


def ensure_relative_paths(manifest: dict) -> None:
    paths: list[str] = []
    for key in ('replace', 'merge_line_files', 'preserve_trees', 'preserve_files'):
        paths.extend(manifest.get(key, []))
    paths.extend(manifest.get('preserve_json', {}).keys())
    for rel in paths:
        p = Path(rel)
        if p.is_absolute() or '..' in p.parts:
            raise UpdateError(f'update manifest path must stay inside repository: {rel}')


def copy_path(src: Path, dst: Path) -> None:
    if src.is_dir() and not src.is_symlink():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def snapshot_path(src: Path, backup_root: Path, rel: str) -> bool:
    if not src.exists() and not src.is_symlink():
        return False
    copy_path(src, backup_root / rel)
    return True


def merge_line_file(current: Path, incoming: Path) -> None:
    if not incoming.exists():
        return
    incoming_lines = incoming.read_text(encoding='utf-8').splitlines()
    if not current.exists():
        current.parent.mkdir(parents=True, exist_ok=True)
        current.write_text('\n'.join(incoming_lines) + '\n', encoding='utf-8')
        return
    existing_text = current.read_text(encoding='utf-8')
    existing_lines = existing_text.splitlines()
    existing_nonblank = {line for line in existing_lines if line.strip()}
    missing = [line for line in incoming_lines if line.strip() and line not in existing_nonblank]
    if not missing:
        return
    separator = '' if existing_text.endswith('\n\n') or not existing_text.strip() else '\n'
    addition = '\n'.join(missing) + '\n'
    current.write_text(existing_text + separator + addition, encoding='utf-8')


def compatible_selection(active: dict) -> None:
    selection = active.get('selection')
    supported = active.get('supported')
    if not isinstance(selection, dict) or not isinstance(supported, dict):
        raise UpdateError('new Harness composition is missing selection/supported registries')
    project = selection.get('project_model')
    collaboration = selection.get('collaboration_model')
    methods = selection.get('method_packs', [])
    if isinstance(project, str) and project not in supported.get('project_models', []):
        raise UpdateError(f'current project model is not supported by new Harness: {project}')
    if isinstance(collaboration, str) and collaboration not in supported.get('collaboration_models', []):
        raise UpdateError(f'current collaboration model is not supported by new Harness: {collaboration}')
    if isinstance(methods, list):
        unsupported = [m for m in methods if m not in supported.get('method_packs', [])]
        if unsupported:
            raise UpdateError('current method packs are not supported by new Harness: ' + ', '.join(unsupported))


def run_check(root: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(root / '.harness/runtime/harness.py'), 'check'],
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=180,
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
    )
    if proc.returncode != 0:
        detail = (proc.stdout or proc.stderr).strip()
        if len(detail) > 4000:
            detail = detail[-4000:]
        raise UpdateError(f'new Harness failed deterministic check after update:\n{detail}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Update this repository to a newer Harness release.')
    parser.add_argument('source', help='new Harness release zip or extracted release directory')
    parser.add_argument('--root', help='project root; defaults to the repository containing this script/current directory')
    args = parser.parse_args()

    if args.root:
        root = Path(args.root).expanduser().resolve()
    else:
        root = find_project_root(Path.cwd()) or find_project_root(Path(__file__))
        if root is None:
            raise UpdateError('cannot find installed Harness; run from the project root or pass --root')

    current_version_path = root / VERSION
    if not current_version_path.is_file():
        raise UpdateError(f'no installed Harness found at {root}')
    old_version = current_version_path.read_text(encoding='utf-8').strip()

    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        raise UpdateError(f'new Harness source does not exist: {source}')

    with tempfile.TemporaryDirectory(prefix='harness-update-') as td:
        temp = Path(td)
        if source.is_file():
            if not zipfile.is_zipfile(source):
                raise UpdateError('new Harness source file must be a zip archive')
            extracted = temp / 'new'
            extracted.mkdir()
            safe_extract_zip(source, extracted)
            new_root = find_release_root(extracted)
        else:
            new_root = find_release_root(source)

        new_version = (new_root / VERSION).read_text(encoding='utf-8').strip()
        if semver(new_version) <= semver(old_version):
            raise UpdateError(f'new Harness must be newer than installed Harness ({old_version} -> {new_version})')

        manifest = load_manifest(new_root)
        ensure_relative_paths(manifest)

        # Capture repository-specific state before replacing Harness-owned surfaces.
        preserved_json: dict[str, dict] = {}
        for rel, keys in manifest.get('preserve_json', {}).items():
            old_path = root / rel
            if not old_path.exists():
                continue
            old_data = read_json(old_path, f'current preserved JSON {rel}')
            preserved_json[rel] = {key: copy.deepcopy(old_data[key]) for key in keys if key in old_data}

        # Check that the current composition can exist in the new distribution before touching the tree.
        if '.harness/composition/active.json' in preserved_json:
            candidate_active = read_json(new_root / '.harness/composition/active.json', 'new Harness composition')
            candidate_active.update(preserved_json['.harness/composition/active.json'])
            compatible_selection(candidate_active)

        backup = temp / 'backup'
        backup.mkdir()
        existed: dict[str, bool] = {}
        rollback_paths = list(dict.fromkeys(
            manifest.get('replace', []) + manifest.get('merge_line_files', [])
        ))
        for rel in rollback_paths:
            existed[rel] = snapshot_path(root / rel, backup, rel)

        preserve_backup = temp / 'preserve'
        preserve_backup.mkdir()
        preserved_paths: dict[str, bool] = {}
        for rel in manifest.get('preserve_trees', []) + manifest.get('preserve_files', []):
            preserved_paths[rel] = snapshot_path(root / rel, preserve_backup, rel)

        try:
            # Replace exactly the Harness-owned surfaces declared by the new release.
            for rel in manifest.get('replace', []):
                src = new_root / rel
                dst = root / rel
                if not src.exists() and not src.is_symlink():
                    raise UpdateError(f'new Harness is missing managed path: {rel}')
                remove_path(dst)
                copy_path(src, dst)

            # Carry repository-specific values into the new schemas rather than restoring old files wholesale.
            for rel, values in preserved_json.items():
                target = root / rel
                new_data = read_json(target, f'new preserved JSON {rel}')
                new_data.update(copy.deepcopy(values))
                target.write_text(json.dumps(new_data, indent=2) + '\n', encoding='utf-8')

            # Restore project/local material that legitimately lives under Harness-owned directories.
            for rel, was_present in preserved_paths.items():
                if not was_present:
                    continue
                src = preserve_backup / rel
                dst = root / rel
                if src.is_dir() and not src.is_symlink():
                    dst.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)

            # Keep project .gitignore content and only add missing Harness rules from the new release.
            for rel in manifest.get('merge_line_files', []):
                merge_line_file(root / rel, new_root / rel)

            run_check(root)
        except Exception:
            # Restore every surface the updater may have changed.
            for rel in reversed(rollback_paths):
                dst = root / rel
                remove_path(dst)
                if existed.get(rel):
                    copy_path(backup / rel, dst)
            raise

    print(json.dumps({
        'status': 'updated',
        'from': old_version,
        'to': new_version,
        'root': str(root),
        'preserved': {
            'repository_config': '.harness/runtime/config.json',
            'composition_selection': '.harness/composition/active.json#selection',
            'project_extensions': '.harness/extensions/project/',
            'local_extensions': '.harness/extensions/local/',
            'assurance_evidence': '.harness/evals/behavior/evidence/',
            'project_gitignore_entries': '.gitignore',
        },
    }, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except UpdateError as exc:
        print(f'harness update failed: {exc}', file=sys.stderr)
        raise SystemExit(2)
