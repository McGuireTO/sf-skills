#!/usr/bin/env python3
"""Check installed safety callbacks against a local fake CLI, without org access.

Usage: python3 installed_codex_safety.py /absolute/installed/plugin/root
These subprocess checks establish packaged callback behavior, not host enforcement.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    root = Path(sys.argv[1]).resolve(strict=True)
    adapter = root / 'scripts/codex_hooks.py'
    manifest = json.loads((root / 'hooks/codex-hooks.json').read_text())
    pre = manifest['hooks']['PreToolUse'][0]
    assert pre['matcher'] == 'Bash|apply_patch|Write|Edit'
    assert 'scripts/codex_hooks.py PreToolUse' in pre['hooks'][0]['command']
    assert adapter.is_file()
    with tempfile.TemporaryDirectory(prefix='sf-installed-safety-', dir='/tmp') as raw:
        base = Path(raw)
        project = base / 'project with spaces'
        project.mkdir()
        (project / 'sfdx-project.json').write_text('{}')
        tools = base / 'tools'
        tools.mkdir()
        calls = base / 'calls.jsonl'
        sentinel = base / 'mutation-executed'
        fake = tools / 'sf'
        fake.write_text('#!' + sys.executable + '\n' + '''
import json, os, pathlib, sys
args = sys.argv[1:]
with open(os.environ['FIXTURE_CALLS'], 'a') as stream:
    stream.write(json.dumps({'args': args, 'cwd': os.getcwd()}) + '\\n')
# Each alias is classified on its own: `prod` is production, every other alias
# is a sandbox, and the default org is the sandbox `dev`.
def org(alias):
    prod = alias == 'prod'
    return {'alias': alias, 'username': alias + '@example.invalid', 'isSandbox': not prod,
            'instanceUrl': 'https://acme.my.salesforce.com' if prod
            else 'https://acme--' + alias + '.sandbox.my.salesforce.com'}
target = next((args[i + 1] for i, arg in enumerate(args[:-1])
               if arg in ('--target-org', '-o')), 'dev')
if args[:2] == ['config', 'get']:
    result = [{'name': 'target-org', 'value': 'dev'}]
elif args[:2] == ['org', 'list']:
    result = {'nonScratchOrgs': [org('prod'), org('dev')]}
elif args[:2] == ['org', 'display']:
    result = org(target)
else:
    pathlib.Path(os.environ['FIXTURE_SENTINEL']).write_text('unexpected execution')
    sys.exit(99)
print(json.dumps({'status': 0, 'result': result}))
''')
        fake.chmod(0o755)
        home = base / 'home'
        home.mkdir()
        # Shell startup files and exported functions cannot override the fixture CLI.
        env = dict(HOME=str(home), LANG='C', TMPDIR=str(base), PYTHONDONTWRITEBYTECODE='1')
        env.update(PATH=os.pathsep.join((str(tools), str(Path(sys.executable).parent), os.defpath)),
                   SF_AGENT_CLIENT='codex', DO_NOT_TRACK='true', SF_DISABLE_TELEMETRY='true',
                   SF_DEV_TELEMETRY_HOME=str(base / 'consent'),
                   SF_TARGET_ORG='', SFDX_TARGET_ORG='', CONFIRM_PROD='',
                   CONFIRM_DELETE='', SFDX_LSP_DEPLOY_GATE='off',
                   FIXTURE_CALLS=str(calls), FIXTURE_SENTINEL=str(sentinel))
        cases = [
            ('sf project deploy start -o prod', True),
            ('echo --target-org dev; sf project deploy start -o prod', True),
            ('CONFIRM_PROD=1 sf project deploy start -o prod', True),
            ('sf project deploy start -o prod # CONFIRM_PROD=1', True),
            ('! sf project deploy start -o prod', True),
            ('command -p sf project deploy start -o prod', True),
            ('timeout 60 sf project deploy start -o prod', True),
            ('sfdx force:source:deploy -u prod', True),
            ('npx @salesforce/cli project deploy start -oprod', True),
            ('bash -c "sf project deploy start -o prod"', True),
            ('sf project deploy start --target-org=dev', False),
            ('! sf project deploy start -o dev', False),
            ('sf project deploy start', False),
            ('echo "sf project deploy start -o prod"', True),
            ('chronic sf project deploy start -o prod', True),
            ('watch -n 5 sf project deploy start -o prod', True),
            ('while true; do sf project deploy start -o prod; done', True),
            ('f(){ sf project deploy start -o prod; }; f; f', True),
            ('sf project deploy start -o dev; chronic sf project deploy start -o prod', True),
            ('sf project delete source -o prod', True),
            ('sf project delete source -o dev', False),
            ('sf project deploy start -o prod --target-org another', True),
            ('sf project deploy start -o dev; sf project delete source -o dev', True),
        ]
        for command, denied in cases:
            payload = {'cwd': str(project), 'session_id': 'installed-safety-fixture',
                       'tool_name': 'Bash', 'tool_input': {'command': command}}
            result = subprocess.run([sys.executable, str(adapter), 'PreToolUse'],
                                    input=json.dumps(payload), text=True, capture_output=True,
                                    env=env, cwd=root, timeout=30, check=True)
            output = json.loads(result.stdout)
            actual = output.get('hookSpecificOutput', {}).get('permissionDecision') == 'deny'
            assert actual == denied, (command, output)
        rows = [json.loads(line) for line in calls.read_text().splitlines()]
        assert rows, 'installed gates did not call the fake org probes'
        assert all(Path(row['cwd']).resolve() == project.resolve() for row in rows)
        assert not sentinel.exists(), 'a pending command or unexpected CLI operation was executed'
        assert not (project / '.sf-plugin').exists(), 'unexpected project telemetry state'
        print(json.dumps({'installed_root': str(root), 'cases': len(cases),
                          'org_probes': len(rows), 'pending_commands_executed': 0,
                          'project_cwd': 'pass', 'network_or_org_access': 'not attempted',
                          'live_host_enforcement': 'not established'}))


if __name__ == '__main__':
    main()
