#!/usr/bin/env python3
"""Exercise installed lifecycle and detached transmitters against local SDK stubs.

Usage: python3 installed_codex_transmission.py /absolute/installed/plugin/root
No real org, credentials or backend are used. This checks the packaged pipeline,
not collector acceptance or a model-driven host callback.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def main():
    root = Path(sys.argv[1]).resolve(strict=True)
    node = shutil.which('node')
    assert node, 'Node is required for this transmission check'
    with tempfile.TemporaryDirectory(prefix='sf-installed-transmit-', dir='/tmp') as raw:
        base = Path(raw)
        home = base / 'home'
        home.mkdir()
        project = base / 'project with spaces'
        project.mkdir()
        (project / 'sfdx-project.json').write_text('{}')
        tools = base / 'cli/bin'
        tools.mkdir(parents=True)
        (tools / 'node').symlink_to(node)
        calls, capture = base / 'cli-calls.jsonl', base / 'sends.jsonl'
        fake = tools / 'sf'
        fake.write_text('#!' + sys.executable + '\n' + '''
import json, os, sys
with open(os.environ['FIXTURE_CALLS'], 'a') as stream:
    stream.write(json.dumps({'args': sys.argv[1:], 'cwd': os.getcwd()}) + '\\n')
if sys.argv[1:] != ['org', 'display', '--json']:
    sys.exit(99)
print(json.dumps({'status': 0, 'result': {
    'id': '00D000000000001', 'username': 'fixture@example.invalid',
    'instanceUrl': 'https://fixture.invalid', 'isSandbox': True}}))
''')
        fake.chmod(0o755)
        modules = base / 'cli/node_modules/@salesforce'
        for name in ('core', 'telemetry'):
            package = modules / name
            package.mkdir(parents=True)
            (package / 'package.json').write_text(json.dumps({'name': '@salesforce/' + name,
                                                             'main': 'index.js'}))
        (modules / 'core/index.js').write_text('''
class Org {
  static async create() { return new Org(); }
  async getConnection() { return { instanceUrl: 'https://fixture.invalid' }; }
}
module.exports = { Org };
''')
        (modules / 'telemetry/index.js').write_text('''
const fs = require('fs');
const record = (row) => fs.appendFileSync(process.env.FIXTURE_CAPTURE, JSON.stringify(row)+'\\n');
class TelemetryReporter {
  static async create(options) { return new TelemetryReporter(options); }
  constructor(options) {
    if (!options.enableO11y || options.enableAppInsights) throw Error('unexpected transport');
    if (options.o11yUploadEndpoint !== 'https://fixture.invalid/services/data/v65.0/connect/proxy/ui-telemetry')
      throw Error('unexpected endpoint');
    this.o11yReporter = {
      sendPdpEvent: async event => record({kind:'pdp', event}),
      sendTelemetryEvent: async (name, attributes) => record({kind:'uip', name, attributes})
    };
  }
  async flush() { record({kind:'flush'}); }
  async stopAsync() { record({kind:'stop'}); }
}
module.exports = { TelemetryReporter };
''')
        # Presentation probes are covered separately; this fixture pins only the
        # telemetry path so exact org-probe and hard opt-out assertions stay strict.
        env = dict(HOME=str(home), LANG='C', TMPDIR=raw, PYTHONDONTWRITEBYTECODE='1',
                   PATH=os.pathsep.join((str(tools), os.defpath)),
                   SF_AGENT_CLIENT='codex', CODEX_THREAD_ID='transmission-fixture',
                   SF_PLUGIN_UI_MODE='off',
                   SF_DEV_TELEMETRY_HOME=str(base / 'consent'),
                   FIXTURE_CALLS=str(calls), FIXTURE_CAPTURE=str(capture))

        def run(args, payload=None):
            proc = subprocess.run(args, input=json.dumps(payload) if payload else None,
                                  text=True, capture_output=True, cwd=project,
                                  env=env, timeout=15)
            assert proc.returncode == 0, proc.stderr
            return json.loads(proc.stdout or '{}')

        payload = {'cwd': str(project), 'session_id': 'transmission-fixture', 'source': 'startup'}
        adapter = [sys.executable, str(root / 'scripts/codex_hooks.py')]
        assert 'Telemetry Usage' in run(adapter + ['SessionStart'], payload)['systemMessage']
        feedback = [sys.executable, str(root / 'scripts/sf_telemetry.py'), 'feedback-record', '3']
        assert run(feedback)['result'] == 'recorded'
        assert run(feedback[:-1] + ['private-rejected-feedback'])['reason'] == 'invalid_rating'
        run(adapter + ['SessionEnd'], payload)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            rows = [json.loads(line) for line in capture.read_text().splitlines()] if capture.exists() else []
            pending = list((project / '.sf').glob('telemetry-pending-*'))
            snapshots = list((project / '.sf').glob('telemetry-snapshot-*'))
            if any(row['kind'] == 'stop' for row in rows) and not pending and not snapshots:
                break
            time.sleep(0.05)
        else:
            log = project / '.sf/telemetry-transmit.log'
            raise AssertionError(log.read_text() if log.exists() else 'transmitter did not finish')
        pdp = [row for row in rows if row['kind'] == 'pdp']
        uip = [row for row in rows if row['kind'] == 'uip']
        assert len(pdp) == len(uip) == 3, rows
        assert [row['event']['eventName'] for row in pdp] == [row['name'] for row in uip]
        assert pdp[0]['event']['eventName'] == 'session.started'
        assert pdp[1]['event']['eventName'] == 'feedback.submitted'
        assert pdp[1]['event']['eventVolume'] == 3
        assert pdp[-1]['event']['eventName'] == 'session.ended'
        assert all(row['attributes']['harness'] == 'codex' for row in uip)
        assert all(row['attributes']['session_Id'] == 'transmission-fixture' for row in uip)
        assert all(row['attributes']['org_id'] == '00D000000000001' for row in uip)
        assert '00D000000000001' not in json.dumps(pdp)
        assert [row['kind'] for row in rows] == ['pdp'] * 3 + ['uip'] * 3 + ['flush', 'stop']
        wire = json.dumps(rows)
        assert str(project) not in wire and 'fixture@example.invalid' not in wire
        assert 'private-rejected-feedback' not in wire
        assert [json.loads(line) for line in calls.read_text().splitlines()] == [
            {'args': ['org', 'display', '--json'], 'cwd': str(project.resolve())}]
        assert not list((project / '.sf').glob('telemetry-buffer-*'))
        assert not (project / '.sf/telemetry-org.json').exists()
        # Abrupt-exit recovery uses the installed hook and real detached sender,
        # with only the local SDK/CLI stubs above providing transport.
        env['CODEX_THREAD_ID'] = 'abrupt-session'
        payload['session_id'] = 'abrupt-session'
        run(adapter + ['SessionStart'], payload)
        [stranded] = list((project / '.sf').glob('telemetry-buffer-*'))
        aged = time.time() - 24 * 60 * 60 - 10
        os.utime(stranded, (aged, aged))
        env['CODEX_THREAD_ID'] = 'recovery-session'
        payload['session_id'] = 'recovery-session'
        run(adapter + ['SessionStart'], payload)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            recovered = [json.loads(line) for line in capture.read_text().splitlines()]
            if (sum(row['kind'] == 'stop' for row in recovered) == 2
                    and not list((project / '.sf').glob('telemetry-snapshot-*'))
                    and not list((project / '.sf').glob('telemetry-pending-*'))):
                break
            time.sleep(0.05)
        else:
            raise AssertionError('abrupt-session recovery did not finish')
        recovered_uip = [row for row in recovered if row['kind'] == 'uip'
                         and row['attributes']['session_Id'] == 'abrupt-session']
        assert [row['name'] for row in recovered_uip] == ['session.started'], recovered_uip
        assert not stranded.exists()
        payload['source'] = 'compact'
        run(adapter + ['SessionStart'], payload)
        assert [json.loads(line) for line in capture.read_text().splitlines()] == recovered
        run(adapter + ['SessionEnd'], payload)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            completed = [json.loads(line) for line in capture.read_text().splitlines()]
            if (sum(row['kind'] == 'stop' for row in completed) == 3
                    and not list((project / '.sf').glob('telemetry-snapshot-*'))
                    and not list((project / '.sf').glob('telemetry-pending-*'))):
                break
            time.sleep(0.05)
        else:
            raise AssertionError('recovery-session flush did not finish')
        assert len([row for row in completed if row['kind'] == 'uip'
                    and row['attributes']['session_Id'] == 'abrupt-session']) == 1
        assert not list((project / '.sf').glob('telemetry-buffer-*'))
        before = capture.read_bytes(), calls.read_bytes()
        env['CODEX_THREAD_ID'] = 'opted-out-fresh-session'
        payload['session_id'] = 'opted-out-fresh-session'
        env['DO_NOT_TRACK'] = 'true'
        run(adapter + ['SessionStart'], payload)
        assert run(feedback)['result'] == 'skipped'
        run(adapter + ['SessionEnd'], payload)
        assert (capture.read_bytes(), calls.read_bytes()) == before
        assert not list((project / '.sf').glob('telemetry-buffer-*'))
        print(json.dumps({'installed_root': str(root), 'pdp_events': len(pdp),
                          'uip_events': len(uip), 'detached_pipeline': 'pass',
                          'opt_out': 'pass', 'abrupt_exit_recovery': 'pass', 'backend_delivery': 'not attempted'}))


if __name__ == '__main__':
    main()
