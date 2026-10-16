"""Bounded, local-only Codex startup presentation over the shared banner renderer."""
from __future__ import annotations

from pathlib import Path
import shlex
import os
import signal
import subprocess
import sys
import sf_context as context

ROOT = Path(__file__).resolve().parents[1]


def run_renderer(argv: list[str], timeout: float = 4,
                 input: str | None = None) -> subprocess.CompletedProcess:
    """Bound live probes to the renderer's process group on supported POSIX hosts."""
    if os.name != 'posix':
        raise OSError('Bounded process-tree cleanup unavailable on this host')
    with subprocess.Popen(argv, stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, start_new_session=True) as process:
        try:
            stdout, stderr = process.communicate(input=input, timeout=timeout)
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except OSError:
                process.kill()
            finally:
                process.communicate()
            raise
        return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)


_CACHE_DIR = context._PROMPT_RUNTIME_DIR / 'codex-startup'
_SURFACE_BUDGET = 16000


def _cache_path(payload: dict):
    session_id = context._plugin_session_id(payload.get('session_id') or '', 'codex')
    return _CACHE_DIR / (context._runtime_key(session_id) + '.txt') if session_id else None


def _cached_surface(path) -> str:
    try:
        if path is None or path.stat().st_size > _SURFACE_BUDGET * 4:
            return ''
        return path.read_text(encoding='utf-8').strip()
    except (OSError, UnicodeDecodeError):
        return ''


def presentation(payload: dict) -> dict:
    if context._ui_mode() == 'off' or payload.get('source') == 'compact':
        return {'continue': True}
    cache = _cache_path(payload)
    if payload.get('source') == 'resume':
        surface = _cached_surface(cache)
        if surface:
            return {'continue': True, 'systemMessage': surface}
    try:
        result = run_renderer(
            [sys.executable, str(ROOT / 'scripts/codex_command_surface.py'), 'startup'])
        if result.returncode or not result.stdout.strip():
            raise ValueError('Startup renderer unavailable')
        surface = result.stdout.strip()
        if len(surface) > _SURFACE_BUDGET:
            raise ValueError('Startup renderer exceeded presentation budget')
        if cache is not None and context._ensure_private_runtime_dir(_CACHE_DIR):
            context._atomic_private_text(cache, surface, encoding='utf-8')
        return {'continue': True, 'systemMessage': surface}
    except (OSError, subprocess.SubprocessError, ValueError):
        entry = shlex.quote(str(ROOT / 'scripts/codex_command_surface.py'))
        return {'continue': True, 'systemMessage':
                'Salesforce Development · Codex: startup details unavailable. '
                'Ask for Salesforce status, or run ' + shlex.quote(sys.executable) +
                ' ' + entry + ' welcome for the current project and org details.'}
