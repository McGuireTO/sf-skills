#!/usr/bin/env python3
"""Check fresh installed-cache discovery without creating a thread or model turn.

Usage: python3 installed_codex_discovery.py SMOKE_ROOT SFDEV_CACHE LWC_CACHE
The smoke root must contain isolated home/ and codex-home/ directories.
"""
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time


def main():
    base, sfdev, lwc = (Path(arg).resolve(strict=True) for arg in sys.argv[1:])
    for folder in (base / 'home', base / 'codex-home'):
        if not folder.is_dir():
            raise ValueError(f'Missing isolated directory: {folder}')
    env = dict(os.environ, CODEX_HOME=str(base / 'codex-home'),
               HOME=str(base / 'home'), DO_NOT_TRACK='1')
    rows = []
    with (base / 'native-stderr.log').open('w') as stderr:
        process = subprocess.Popen(['codex', 'app-server', '--stdio'],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=stderr, env=env, cwd=base)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)

        pending = b''

        def request(identifier, method, params):
            nonlocal pending
            process.stdin.write(json.dumps({'id': identifier, 'method': method,
                                            'params': params}).encode() + b'\n')
            process.stdin.flush()
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline:
                if b'\n' not in pending:
                    if not selector.select(1):
                        continue
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise RuntimeError('Codex app-server closed its output')
                    pending += chunk
                    if b'\n' not in pending:
                        continue
                line, pending = pending.split(b'\n', 1)
                row = json.loads(line)
                rows.append(row)
                if row.get('id') == identifier:
                    if 'error' in row:
                        raise RuntimeError(str(row['error']))
                    return row['result']
            raise TimeoutError(f'Codex app-server timed out: {method}')

        try:
            request(1, 'initialize', {
                'clientInfo': {'name': 'sf-plugin-installed-discovery', 'version': '1'},
                'capabilities': {'experimentalApi': True}})
            process.stdin.write(json.dumps({'method': 'initialized'}).encode() + b'\n')
            process.stdin.flush()
            request(2, 'plugin/list', {'cwds': [str(base)], 'forceRefetch': False,
                                       'marketplaceKinds': ['local']})
            skills = request(3, 'skills/list', {'cwds': [str(base)], 'forceReload': True})
            entries = skills.get('data', [])
            for cache in (sfdev, lwc):
                paths = [Path(skill['path']).resolve()
                         for entry in entries for skill in entry.get('skills', [])
                         if skill.get('enabled') and isinstance(skill.get('path'), str)]
                if not any(path.is_relative_to(cache) and path.is_file() for path in paths):
                    raise RuntimeError(f'Enabled installed skill not discovered: {cache}')
                for entry in entries:
                    for error in entry.get('errors', []):
                        if str(cache) in json.dumps(error):
                            raise RuntimeError(f'Installed cache discovery error: {error}')
            print('PASS fresh app-server discovery of both installed caches; no thread/model turn')
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            selector.close()
            process.stdin.close()
            process.stdout.close()
            (base / 'native-discovery.json').write_text(json.dumps(rows, indent=2) + '\n')


if __name__ == '__main__':
    main()
