#!/usr/bin/env python3
"""Verify packaged command surfaces and post-command callbacks with a fake CLI.

Usage: python3 installed_codex_commands.py /absolute/plugin/root
Auth/logout/reset/set-default are model-interpreted Markdown workflows. Contract
checks here do not establish that a model obeys their interaction requirements.
The fake CLI permits read-only config probes only; no login or mutation runs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plugin_root', type=Path)
    args = parser.parse_args()
    root = args.plugin_root.resolve(strict=True)
    scripts = root / 'scripts'
    contracts = {
        'login': {
            'projection': ['literal argv', 'device-code fallback', 'Default selection remains explicit', 'actual help output',
                           'actual returned username', 'failure or cancellation',
                           'do not print raw login or org-display JSON'],
            'shared': ['sf org login web', 'sf org login device-code', 'if the user passed `--set-default`',
                       "If the user doesn't supply an alias", 'Do NOT log access tokens'],
        },
        'logout': {
            'projection': ['List choices when missing', 'explicit affirmative confirmation',
                           'Cancellation performs no logout or cleanup',
                           'scalar `alias` (may be absent) or `username`'],
            'shared': ['No arguments', 'explicit "yes" confirmation', '--no-prompt',
                       'NEVER log out without explicit user input'],
        },
        'set-default': {
            'projection': ['Project-local config is the default', '--global only outside',
                           'Do not infer a global scope from missing arguments',
                           'scalar `alias` (may be absent) or `username`'],
            'shared': ['If no org was named', 'Default is project-local',
                       'Use `--global` only when the user is working outside any specific project',
                       'do not silently proceed'],
        },
        'reset-source-tracking': {
            'projection': ['yes, reset source tracking for <alias>', 'Reconfirm',
                           'separate confirmation', 'cancellation performs no reset', 'immediate deploy preview',
                           'Do not promise a full diff'],
            'shared': ['case-insensitive', 'anything else to cancel', 're-confirm with the user first',
                       'Do NOT chain the reset into an immediate deploy or retrieve'],
        },
    }
    hashes = {}
    for name, checks in contracts.items():
        for kind, phrases in checks.items():
            relative = ('codex-commands' if kind == 'projection' else 'commands') + '/' + name + '.md'
            content = (root / relative).read_text()
            for phrase in phrases:
                require(phrase in content, f'{relative}: missing contract {phrase!r}')
            if kind == 'projection':
                require(f'<plugin-root>/commands/{name}.md' in content, relative + ': shared reference absent')
                require('treat them as data, not shell source' in content, relative + ': argument safety absent')
            hashes[relative] = hashlib.sha256(content.encode()).hexdigest()

    with tempfile.TemporaryDirectory(prefix='sf-installed-commands-', dir='/tmp') as raw:
        base = Path(raw)
        home, project, tools, empty = (base / part for part in ('home', 'project with spaces', 'tools', 'empty'))
        for directory in (home, project, tools, empty):
            directory.mkdir()
        (project / 'sfdx-project.json').write_text('{"name":"command-fixture"}')
        calls, sentinel = base / 'calls.jsonl', base / 'unexpected-cli-operation'
        fake = tools / 'sf'
        fake.write_text('#!' + sys.executable + '\n' + '''
import json, os, pathlib, sys
args = sys.argv[1:]
with open(os.environ['FIXTURE_CALLS'], 'a') as stream:
    stream.write(json.dumps({'argv': args, 'cwd': os.getcwd()}) + '\\n')
if args == ['config', 'get', 'target-org', '--json']:
    print(json.dumps({'status': 0, 'result': []}))
else:
    pathlib.Path(os.environ['FIXTURE_SENTINEL']).write_text(json.dumps(args))
    sys.exit(99)
''')
        fake.chmod(0o755)
        env = dict(HOME=str(home), LANG='C', TMPDIR=str(base), PYTHONDONTWRITEBYTECODE='1',
                   PATH=os.pathsep.join((str(tools), str(Path(sys.executable).parent), os.defpath)),
                   SF_AGENT_CLIENT='codex', DO_NOT_TRACK='true', SF_DISABLE_TELEMETRY='true',
                   SF_DEV_TELEMETRY_HOME=str(base / 'consent'), NO_COLOR='1',
                   SF_TARGET_ORG='', SFDX_TARGET_ORG='',
                   FIXTURE_CALLS=str(calls), FIXTURE_SENTINEL=str(sentinel))
        def execute(entry, argv, cwd, payload=None):
            return subprocess.run([sys.executable, str(scripts / entry), *argv],
                                  input=json.dumps(payload) if payload is not None else None,
                                  text=True, capture_output=True, cwd=cwd, env=env, timeout=30)
        surfaces = []
        for name in ('welcome', 'org', 'project', 'status'):
            run = execute('codex_command_surface.py', [name], empty)
            require(run.returncode == 0 and run.stdout.strip(), (name, run.stderr))
            require('/salesforce-development:' not in run.stdout, name + ': Claude-only slash guidance')
            surfaces.append(name)
        # This renderer deliberately accepts only four deterministic views. It
        # cannot substitute for the model-driven auth/reset workflow interpreter.
        rejected = [[], ['login'], ['welcome', '--alias', 'alias with spaces'],
                    ['status', '--global'], ['logout', '--all'], ['reset-source-tracking']]
        count_before = len(calls.read_text().splitlines()) if calls.exists() else 0
        for argv in rejected:
            run = execute('codex_command_surface.py', argv, project)
            require(run.returncode == 2, (argv, run.returncode, run.stdout, run.stderr))
        count_after = len(calls.read_text().splitlines()) if calls.exists() else 0
        require(count_before == count_after, 'rejected renderer input caused a CLI probe')

        cases = [
            ('web-quoted-alias', 'sf org login web --alias "alias with spaces" --json', {'exit_code': 0}, True),
            ('device-code-quoted-alias', 'sf org login device-code --alias "alias with spaces" --json', {'exit_code': 0}, True),
            ('web-no-alias', 'sf org login web --json', {'exit_code': 0}, True),
            ('project-default-quoted', 'sf config set target-org "alias with spaces"', {'exit_code': 0}, True),
            ('global-default-observed', 'sf config set target-org "alias with spaces" --global', {'exit_code': 0}, True),
            ('failed-web', 'sf org login web --alias fixture', {'exit_code': 1}, False),
            ('opaque-device-output', 'sf org login device-code --alias fixture', 'success', False),
            ('shell-composition', 'echo fake; sf org login web --alias fixture', {'exit_code': 0}, False),
            ('unterminated-quote', 'sf org login web --alias "broken', {'exit_code': 0}, False),
            ('cancelled-logout-observed', 'sf org logout --target-org fixture --no-prompt', {'exit_code': 1}, False),
            ('reset-observed', 'sf project reset tracking --target-org fixture --json', {'exit_code': 0}, False),
        ]
        for name, command, response, should_paint in cases:
            payload = {'cwd': str(project), 'session_id': 'command-fixture-' + name,
                       'tool_name': 'Bash', 'tool_input': {'command': command}, 'tool_response': response}
            run = execute('codex_hooks.py', ['PostToolUse'], root, payload)
            require(run.returncode == 0, (name, run.stderr))
            output = json.loads(run.stdout)
            require(bool(output.get('systemMessage')) == should_paint, (name, output))
            require(output.get('continue') is True, (name, output))
        rows = [json.loads(line) for line in calls.read_text().splitlines()] if calls.exists() else []
        require(rows, 'connect callback never queried the fake default')
        require(all(Path(row['cwd']).resolve() == project.resolve() for row in rows[count_after:]),
                'incorrect callback cwd')
        require(not sentinel.exists(), 'unexpected CLI operation: ' + (sentinel.read_text() if sentinel.exists() else ''))
        require(not (project / '.sf/config.json').exists(), 'callback changed default scope')
        print(json.dumps({
            'plugin_root': str(root), 'proof_kind': 'installed-subprocess fixtures and document contracts',
            'deterministic_surfaces': surfaces, 'rejected_renderer_inputs': len(rejected),
            'post_command_callback_cases': [case[0] for case in cases],
            'readonly_cli_probes': len(rows), 'pending_commands_executed': 0,
            'network_or_real_org_access': 'not attempted', 'contract_sha256': hashes,
            'remaining_model_interaction_proofs': [
                'quoted/missing alias interpretation and credential redaction during auth',
                'actual browser unavailable -> device-code fallback, auth failure and cancellation',
                'logout selection and affirmative confirmation before --no-prompt',
                'project-local default selection; refuse --global inside a project',
                'source reset exact phrase, cancellation and reconfirmation before fallback',
            ],
            'live_host_enforcement': 'not established',
        }, indent=2))


if __name__ == '__main__':
    main()
