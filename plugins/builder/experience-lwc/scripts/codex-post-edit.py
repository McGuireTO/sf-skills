#!/usr/bin/env python3
"""Translate completed Codex patches into the bundled one-file LWC advisory."""
from __future__ import annotations
import json
import os
import shlex
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
BUDGET = 8.0
MAX_PATCH_CHARS = 1024 * 1024
MAX_PATCH_FILES = 256
EXTENSIONS = {'.html', '.css', '.js'}


def patch_paths(patch: str) -> list[tuple[str, str | None]]:
    """Parse apply_patch structure, returning surviving add/update destinations.

    Context and added lines retain their prefix, so header-like file contents
    cannot become paths. Reject the entire patch if its structure is malformed.
    """
    if not isinstance(patch, str):
        raise ValueError("Patch must be text")
    if len(patch) > MAX_PATCH_CHARS:
        raise ValueError("Patch exceeds advisory size limit")
    lines = patch.strip().splitlines()
    if len(lines) < 3 or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise ValueError("Invalid patch envelope")
    paths = []
    i = 1
    while i < len(lines) - 1:
        if len(paths) >= MAX_PATCH_FILES:
            raise ValueError("Patch exceeds advisory file limit")
        header = lines[i]
        kind = next((k for k in ("Add", "Update", "Delete")
                     if header.startswith(f"*** {k} File: ")), None)
        if kind is None:
            raise ValueError("Invalid patch file header")
        source = header.split(": ", 1)[1]
        if not source or "\x00" in source:
            raise ValueError("Invalid patch path")
        destination = source
        i += 1
        if kind == "Update" and i < len(lines) - 1 and lines[i].startswith("*** Move to: "):
            destination = lines[i][13:]
            if not destination or "\x00" in destination:
                raise ValueError("Invalid move destination")
            i += 1
        body = []
        while i < len(lines) - 1 and not any(lines[i].startswith(f"*** {k} File: ") for k in ("Add", "Update", "Delete")):
            body.append(lines[i])
            i += 1
        if kind == "Delete" and body:
            raise ValueError("Delete section has a body")
        if kind == "Add" and any(not line.startswith("+") for line in body):
            raise ValueError("Invalid add section")
        if kind == "Update":
            if not body:
                raise ValueError("Update requires content")
            content, header, ended = False, False, False
            for line in body:
                if ended:
                    if not line.strip():
                        continue
                    if line == "@@" or line.startswith("@@ "):
                        ended = False
                    else:
                        raise ValueError("Content after end-of-file marker")
                if line == "*** End of File":
                    if not content:
                        raise ValueError("Empty update chunk")
                    ended = True
                elif line == "@@" or line.startswith("@@ "):
                    if header and not content:
                        raise ValueError("Empty update chunk")
                    header, content = True, False
                elif not line or line.startswith((" ", "+", "-")):
                    content = True
                else:
                    raise ValueError("Invalid update section")
            if not content:
                raise ValueError("Empty update chunk")
        # Include both sides for containment checks; deleted/old paths are not read.
        paths.append((source, destination if kind != "Delete" else None))
    return paths


def contained_path(root: Path, name: str) -> Path:
    root = root.resolve()
    path = (root / name).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        raise ValueError("Patch path escapes event cwd") from None
    if path == root:
        raise ValueError("Patch path escapes event cwd")
    return path


def advisory(message: str) -> dict:
    return {'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': message}}


def run_validator(path: Path, root: Path, timeout: float) -> dict:
    script = ROOT / 'scripts/codex-local-validate.py'
    if not script.is_file():
        raise ValueError('Bundled validator is unavailable')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    proc = subprocess.run([sys.executable, str(script), str(path)], stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, cwd=root, env=env, timeout=timeout)
    if proc.returncode:
        raise ValueError('Bundled validator failed')
    result = json.loads(proc.stdout)
    if not isinstance(result, dict) or result.get('continue') is not True:
        raise ValueError('Invalid validator advisory')
    if result.get('output') is not None and not isinstance(result['output'], str):
        raise ValueError('Invalid validator findings')
    return result


def check_budget(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("LWC validation budget exceeded")
    return remaining


def dispatch(event: dict) -> dict:
    deadline = time.monotonic() + BUDGET
    if event.get('tool_name') != 'apply_patch':
        return {'continue': True}
    response = event.get('tool_response')
    if isinstance(response, dict) and (response.get('success') is False or response.get('error') or response.get('isError')):
        return {'continue': True}
    if isinstance(response, str) and response.lstrip().lower().startswith((
            'error:', 'failed to', 'apply_patch verification failed', 'patch rejected')):
        return {'continue': True}
    cwd = event.get('cwd')
    if not isinstance(cwd, str) or not Path(cwd).is_absolute():
        raise ValueError('Absolute event cwd required')
    root = Path(cwd).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Event cwd must be a directory')
    inputs = event.get('tool_input')
    if not isinstance(inputs, dict):
        raise ValueError('Patch input must be an object')
    entries = patch_paths(inputs.get('command'))
    check_budget(deadline)
    project = next((directory for directory in (root, *root.parents)
                    if (directory / 'sfdx-project.json').is_file()), None)
    paths = []
    for source, destination in entries:
        check_budget(deadline)
        contained_path(root, source)
        if destination is not None:
            path = contained_path(root, destination)
            if (project is not None and path.suffix.lower() in EXTENSIONS
                    and 'lwc' in path.relative_to(project).parts and path not in paths):
                paths.append(path)
    check_budget(deadline)
    if project is None:
        return {'continue': True}
    reports = []
    for path in paths:
        check_budget(deadline)
        if not path.is_file():
            continue
        remaining = check_budget(deadline)
        result = run_validator(path, root, remaining)
        if result.get('output'):
            reports.append(str(path.relative_to(root)) + ':\n' + result['output'])
    return advisory('LWC local validation:\n' + '\n'.join(reports)) if reports else {'continue': True}


def main() -> int:
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError('Event must be an object')
        output = json.dumps(dispatch(event))
    except Exception as exc:
        command = shlex.join([sys.executable, str(ROOT / 'scripts/codex-local-validate.py'), 'FILE'])
        output = json.dumps(advisory(
            'LWC local validation unavailable (' + type(exc).__name__ + '). Run: ' + command +
            ' (replace FILE with the absolute edited .html, .css or .js path). '
            'This advisory does not block edits.'))
    print(output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
