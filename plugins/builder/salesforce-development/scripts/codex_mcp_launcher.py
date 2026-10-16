#!/usr/bin/env python3
"""Launch a bundled MCP server in one bounded project and explicit org."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys


SERVERS = {
    "salesforce-api-context": ("scripts/sf-mcp-proxy.bundled.js", "salesforce-api-context"),
    "salesforce-metadata-experts": ("scripts/sf-mcp-proxy.bundled.js", "metadata-experts"),
    "salesforce-lsp": ("bin/sf-lsp-host.bundled.js",),
}


def _resolved_dir(raw: str | None) -> Path | None:
    if not raw:
        return None
    try:
        candidate = Path(raw).resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    return candidate if candidate.is_dir() else None


def _find_ancestor_project(start: Path, *, plugin_root: Path,
                           boundary: Path | None = None) -> Path | None:
    for directory in (start, *start.parents):
        if boundary is not None and directory != boundary and boundary not in directory.parents:
            break
        if directory == plugin_root or plugin_root in directory.parents:
            break
        if (directory / "sfdx-project.json").is_file():
            return directory
    return None


def _find_nested_project(root: Path, *, plugin_root: Path, max_depth: int = 3) -> Path | None:
    """Accept one project only after a complete, bounded scan proves uniqueness."""
    frontier = [root]
    found = None
    scanned = 0
    for _ in range(max_depth + 1):
        next_frontier: list[Path] = []
        for directory in frontier:
            if directory == plugin_root or plugin_root in directory.parents:
                continue
            if (directory / "sfdx-project.json").is_file():
                if found is not None:
                    return None
                found = directory
                continue
            try:
                for entry in directory.iterdir():
                    scanned += 1
                    if scanned > 4096:
                        return None
                    if entry.is_dir() and not entry.is_symlink():
                        next_frontier.append(entry)
            except OSError:
                return None
        frontier = next_frontier
        if not frontier:
            break
    return found


def resolve_project_cwd(*, plugin_root: Path, environment: dict[str, str]) -> Path | None:
    """Resolve one nearest project without escaping the Codex workspace boundary."""
    plugin_root = plugin_root.resolve()
    if "CODEX_WORKSPACE_ROOT" in environment:
        workspace_root = _resolved_dir(environment.get("CODEX_WORKSPACE_ROOT"))
        if workspace_root is None:
            return None
        for key in ("PWD", "INIT_CWD"):
            candidate = _resolved_dir(environment.get(key))
            if candidate is None:
                continue
            found = _find_ancestor_project(candidate, plugin_root=plugin_root,
                                           boundary=workspace_root)
            if found is not None:
                return found
        return (
            _find_ancestor_project(workspace_root, plugin_root=plugin_root,
                                   boundary=workspace_root)
            or _find_nested_project(workspace_root, plugin_root=plugin_root)
        )
    for key in ("INIT_CWD", "PWD"):
        candidate = _resolved_dir(environment.get(key))
        if candidate is None:
            continue
        found = _find_ancestor_project(candidate, plugin_root=plugin_root)
        if found is not None:
            return found
    return None


# Project-local CLI config files and the keys that name the default org, most
# authoritative first: the current CLI's `.sf/config.json` wins over the legacy file.
_PROJECT_ORG_CONFIG = (
    (".sf/config.json", "target-org"),
    (".sfdx/sfdx-config.json", "defaultusername"),
)


def _project_target_org(project: Path | None) -> str | None:
    if project is None:
        return None
    for relative, key in _PROJECT_ORG_CONFIG:
        try:
            data = json.loads((project / relative).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            continue
        value = data.get(key) if isinstance(data, dict) else None
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def resolve_target_org(environment: dict[str, str], project: Path | None = None) -> str | None:
    """Return exactly one org: the explicit environment value, else the project's.

    Explicit SF_TARGET_ORG/SFDX_TARGET_ORG values must agree. Without either, the
    selected project's own CLI config is used: `.sf/config.json` takes precedence over
    the legacy `.sfdx/sfdx-config.json` when both name an org. Global (home-directory)
    defaults are never consulted.
    """
    values = {
        value.strip()
        for key in ("SF_TARGET_ORG", "SFDX_TARGET_ORG")
        if (value := environment.get(key)) and value.strip()
    }
    if values:
        return next(iter(values)) if len(values) == 1 else None
    return _project_target_org(project)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1 or args[0] not in SERVERS:
        print("codex_mcp_launcher: unknown server", file=sys.stderr)
        return 2
    plugin_root = Path(__file__).resolve().parent.parent
    project = resolve_project_cwd(plugin_root=plugin_root, environment=dict(os.environ))
    if project is None:
        print("codex_mcp_launcher: no Salesforce project in the bounded workspace", file=sys.stderr)
        return 2
    target_org = resolve_target_org(dict(os.environ), project)
    if target_org is None:
        print(
            "codex_mcp_launcher: no single target org. Run "
            "`sf config set target-org <alias>` in the project, or set SF_TARGET_ORG "
            "(or SFDX_TARGET_ORG, with the same value) in the environment that starts "
            "Codex.",
            file=sys.stderr,
        )
        return 2
    server = SERVERS[args[0]]
    executable = (plugin_root / server[0]).resolve()
    if not executable.is_file() or plugin_root not in executable.parents:
        print("codex_mcp_launcher: bundled server is missing", file=sys.stderr)
        return 2
    os.environ["CODEX_WORKSPACE_ROOT"] = str(project)
    os.environ["SF_TARGET_ORG"] = target_org
    os.environ["SFDX_TARGET_ORG"] = target_org
    os.chdir(project)
    try:
        os.execvp("node", ["node", str(executable), *server[1:]])
    except OSError as exc:
        print(f"codex_mcp_launcher: unable to start node: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
