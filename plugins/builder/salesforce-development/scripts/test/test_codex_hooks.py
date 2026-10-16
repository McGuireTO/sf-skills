#!/usr/bin/env python3
"""Dual-host runtime contracts and isolated Codex lifecycle regression checks."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import codex_hooks as hooks
import sf_context as context
import sf_telemetry as telemetry


class CodexHooksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / 'project'
        self.project.mkdir()
        (self.project / 'sfdx-project.json').write_text('{}')
        self.original = Path.cwd()
        self.addCleanup(os.chdir, self.original)
        self.env = mock.patch.dict(os.environ, {
            'SF_AGENT_CLIENT': 'codex', 'SF_DEV_TELEMETRY_HOME': self.tmp.name + '/consent',
            'SF_DISABLE_TELEMETRY': '', 'DO_NOT_TRACK': '', 'CI': '',
            'GITHUB_ACTIONS': '', 'CONTINUOUS_INTEGRATION': '', 'BUILD_NUMBER': '',
            'CODEX_SESSION_ID': 'test-thread', 'CODEX_THREAD_ID': 'test-thread', 'CLAUDE_CODE_SESSION_ID': 'claude-thread',
        })
        startup = mock.patch.object(hooks.codex_startup, 'presentation', return_value={'continue': True})
        startup.start()
        self.addCleanup(startup.stop)
        self.env.start()
        self.addCleanup(self.env.stop)
        confirm = mock.patch.object(context, '_PROD_DEPLOY_CONFIRM_DIR',
                                    Path(self.tmp.name) / 'prod-deploy-confirm')
        confirm.start()
        self.addCleanup(confirm.stop)

    def per_alias_sf(self):
        """A fake `sf` where `prod` is production, every other alias is a sandbox
        and the default org is the sandbox `dev`."""
        stub = Path(self.tmp.name) / 'per-alias-tools'
        stub.mkdir(exist_ok=True)
        executable = stub / 'sf'
        executable.write_text("#!" + sys.executable + "\n" +
            "import json, sys\n" +
            "args=sys.argv[1:]\n" +
            "def org(a):\n" +
            "    prod = a.lower().startswith('prod')\n" +
            "    return {'alias':a, 'username':a+'@example.invalid', 'isSandbox':not prod, 'isScratch':False,\n" +
            "            'instanceUrl':'https://acme.my.salesforce.com' if prod else 'https://acme--'+a+'.sandbox.my.salesforce.com'}\n" +
            "target = next((args[i+1] for i, x in enumerate(args[:-1]) if x in ('--target-org', '-o')), 'dev')\n" +
            "result = ([{'name':'target-org','value':'dev'}] if args[:2]==['config','get'] else\n" +
            "          {'nonScratchOrgs':[org('prod'), org('dev')]} if args[:2]==['org','list'] else org(target))\n" +
            "print(json.dumps({'status':0,'result':result}))\n")
        executable.chmod(0o755)
        return mock.patch.dict(os.environ, {'PATH': str(stub) + os.pathsep + os.environ['PATH'],
                                            'SF_TARGET_ORG': '', 'SFDX_TARGET_ORG': '',
                                            'SFDX_LSP_DEPLOY_GATE': 'off'})

    def decision(self, command, **extra):
        output = hooks.dispatch('PreToolUse', self.payload(command, **extra))
        specific = output.get('hookSpecificOutput', {})
        return ('deny' if specific.get('permissionDecision') == 'deny' else 'allow',
                specific.get('permissionDecisionReason', '') + output.get('systemMessage', ''))

    def payload(self, command='ls', **extra):
        return dict(cwd=str(self.project), session_id='test-thread', tool_name='Bash',
                    tool_input={'command': command}, **extra)

    def stale_buffer(self, sid='old-thread', age=None):
        os.chdir(self.project)
        telemetry._notified_file().parent.mkdir(parents=True, exist_ok=True)
        telemetry._notified_file().write_text('notified')
        buffer = telemetry._session_buffer(sid)
        buffer.parent.mkdir(exist_ok=True)
        buffer.write_text('{"event":"session_start","session_id":"' + sid + '"}\n')
        modified = hooks.time.time() - (age if age is not None else hooks._RECOVERY_AGE_SECONDS + 10)
        os.utime(buffer, (modified, modified))
        return buffer

    def test_recovery_hands_off_stale_records_once_without_fabricating_end(self):
        old = self.stale_buffer()
        original = old.read_bytes()
        with mock.patch.object(telemetry, '_spawn_sender', return_value=True) as sender:
            hooks.recover_stale_buffers('test-thread')
            hooks.recover_stale_buffers('test-thread')
        sender.assert_called_once()
        snapshot = sender.call_args.args[0]
        self.assertEqual(original, snapshot.read_bytes())
        self.assertFalse(old.exists())

    def test_recovery_preserves_current_recent_empty_and_symlink_buffers(self):
        current = self.stale_buffer('test-thread')
        recent = self.stale_buffer('recent', age=10)
        empty = self.stale_buffer('empty'); empty.write_text('')
        link = telemetry._session_buffer('link'); link.symlink_to(recent.resolve())
        with mock.patch.object(telemetry, '_spawn_sender') as sender:
            hooks.recover_stale_buffers('test-thread')
        sender.assert_not_called()
        self.assertTrue(all(p.exists() for p in (current, recent, empty, link)))

    def test_recovery_opt_out_consent_disclosure_and_project_gates(self):
        old = self.stale_buffer()
        for gate in ('_is_enabled', '_notice_shown', '_in_sf_project'):
            with self.subTest(gate=gate), mock.patch.object(telemetry, gate, return_value=False), \
                    mock.patch.object(telemetry, '_spawn_sender') as sender:
                hooks.recover_stale_buffers('test-thread')
                sender.assert_not_called()
                self.assertTrue(old.exists())
        for flag in ('SF_DISABLE_TELEMETRY', 'DO_NOT_TRACK'):
            with self.subTest(flag=flag), mock.patch.dict(os.environ, {flag: '1'}), \
                    mock.patch.object(telemetry, '_spawn_sender') as sender:
                hooks.recover_stale_buffers('test-thread')
                sender.assert_not_called()
        telemetry._consent_file().write_text('{"enabled":false}')
        with mock.patch.object(telemetry, '_spawn_sender') as sender:
            hooks.recover_stale_buffers('test-thread')
            sender.assert_not_called()

    def test_recovery_has_bounded_send_and_scan_counts(self):
        for i in range(5):
            self.stale_buffer('stale-' + str(i))
        with mock.patch.object(hooks, '_RECOVERY_SEND_LIMIT', 2), \
                mock.patch.object(telemetry, '_spawn_sender', return_value=True) as sender:
            hooks.recover_stale_buffers('test-thread')
            self.assertEqual(2, sender.call_count)
        with mock.patch.object(hooks, '_RECOVERY_SCAN_LIMIT', 1), \
                mock.patch.object(telemetry, '_spawn_sender', return_value=True) as sender:
            hooks.recover_stale_buffers('test-thread')
            self.assertLessEqual(sender.call_count, 1)

    def test_recovery_rename_race_and_sender_failure_are_silent(self):
        old = self.stale_buffer()
        with mock.patch.object(hooks.os, 'replace', side_effect=FileNotFoundError), \
                mock.patch.object(telemetry, '_spawn_sender') as sender:
            hooks.recover_stale_buffers('test-thread')
            sender.assert_not_called()
        self.assertTrue(old.exists())
        self.assertFalse(list(telemetry._STATE_DIR.glob('telemetry-snapshot-*')))
        for failure in (False, RuntimeError('sender failed')):
            self.stale_buffer()
            with mock.patch.object(telemetry, '_spawn_sender', side_effect=(failure if isinstance(failure, Exception) else None),
                                   return_value=failure):
                hooks.recover_stale_buffers('test-thread')
            self.assertFalse(list(telemetry._STATE_DIR.glob('telemetry-snapshot-*')))

    def test_recovery_progresses_past_ineligible_entries(self):
        os.chdir(self.project)
        state = telemetry._STATE_DIR
        state.mkdir()
        for i in range(12):
            (state / ('other-' + str(i))).write_text('not a buffer')
        old = self.stale_buffer()
        with mock.patch.object(hooks, '_RECOVERY_SCAN_LIMIT', 3), \
                mock.patch.object(telemetry, '_spawn_sender', return_value=True) as sender:
            for _ in range(12):
                hooks.recover_stale_buffers('test-thread')
            sender.assert_called_once()
        self.assertFalse(old.exists())

    def test_recovery_tightens_legacy_snapshot_permissions(self):
        old = self.stale_buffer(); old.chmod(0o644)
        with mock.patch.object(telemetry, '_spawn_sender', return_value=True) as sender:
            hooks.recover_stale_buffers('test-thread')
        self.assertEqual(0o600, sender.call_args.args[0].stat().st_mode & 0o777)

    def test_recovery_drops_claim_when_consent_changes(self):
        old = self.stale_buffer()
        replace = hooks.os.replace
        def revoke(source, destination):
            replace(source, destination)
            telemetry._consent_file().write_text('{"enabled":false}')
        with mock.patch.object(hooks.os, 'replace', side_effect=revoke), \
                mock.patch.object(telemetry, '_spawn_sender') as sender:
            hooks.recover_stale_buffers('test-thread')
            sender.assert_not_called()
        self.assertFalse(list(telemetry._STATE_DIR.glob('telemetry-snapshot-*')))

    def test_concurrent_recovery_claims_each_record_once(self):
        self.stale_buffer()
        script = (
            "import sys;sys.path.insert(0,sys.argv[1]);import codex_hooks as h;"
            "h.telemetry._spawn_sender=lambda snapshot: True;"
            "h.recover_stale_buffers('test-thread')"
        )
        jobs = [subprocess.Popen([sys.executable, '-c', script, str(ROOT / 'scripts')],
                                 cwd=self.project, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for _ in range(2)]
        for job in jobs:
            stdout, stderr = job.communicate(timeout=10)
            self.assertEqual(0, job.returncode, stderr)
        snapshots = list(telemetry._STATE_DIR.glob('telemetry-snapshot-*'))
        self.assertEqual(1, len(snapshots))
        self.assertEqual(1, len(snapshots[0].read_text().splitlines()))

    def test_session_start_recovers_but_other_hooks_do_not(self):
        with mock.patch.object(hooks, 'recover_stale_buffers') as recovery:
            hooks.dispatch('SessionStart', self.payload())
            recovery.assert_called_once_with('test-thread')
            hooks.dispatch('SubagentStart', self.payload())
            recovery.assert_called_once()

    def test_codex_session_start_forces_plain_visible_output(self):
        def colored_surface(_payload):
            return {'continue': True, 'systemMessage': context._paint_line(
                [('Codex hook output', 'link')],
                color=context._banner_color_enabled(),
            )}

        with mock.patch.dict(os.environ, {'NO_COLOR': ''}), \
                mock.patch.object(hooks.codex_startup, 'presentation',
                                  side_effect=colored_surface):
            result = hooks.dispatch('SessionStart', self.payload())
            self.assertEqual('1', os.environ.get('NO_COLOR'))

        self.assertNotIn('\x1b', result['systemMessage'])

    def test_absolute_event_cwd_and_same_pending_command(self):
        payload = self.payload('sf project deploy start -o sandbox')
        with mock.patch.object(hooks, 'pre_shell', return_value={'continue': True}) as pre:
            hooks.dispatch('PreToolUse', payload)
        self.assertEqual(self.project.resolve(), Path.cwd())
        self.assertEqual(payload, pre.call_args.args[0])

    def test_invalid_cwd_does_not_run_safety_checks_or_capture(self):
        for raw in (None, 'relative', self.tmp.name + '/absent'):
            os.chdir(self.original)
            p = self.payload('sf project deploy start'); p['cwd'] = raw
            with mock.patch.object(hooks, 'pre_shell') as pre:
                result = hooks.dispatch('PreToolUse', p)
            self.assertEqual('deny', result['hookSpecificOutput']['permissionDecision'])
            pre.assert_not_called()
            with mock.patch.object(telemetry, 'cmd_capture') as capture:
                hooks.dispatch('SessionStart', p)
            capture.assert_not_called()
            self.assertEqual(self.original, Path.cwd())
            p['tool_input']['command'] = 'sf version'
            self.assertEqual({'continue': True}, hooks.dispatch('PreToolUse', p))

    def test_claude_directory_boundary_stays_unchanged(self):
        context._activate_host_working_directory(self.payload(), 'claude')
        self.assertEqual(self.original, Path.cwd())

    def test_structured_outcomes_route_once_and_never_mint_success_from_stdout(self):
        for response in ('Process exited with code 0', '{"exit_code": 0}', 'failed', None,
                         {'process_id': 77}, {'exit_code': False}):
            with mock.patch.object(context, 'cmd_post_bash') as success, \
                    mock.patch.object(context, 'cmd_post_deploy_failure') as failure, \
                    mock.patch.object(telemetry, 'capture_event') as capture:
                hooks.dispatch('PostToolUse', self.payload('sf project deploy start', tool_response=response))
            success.assert_not_called(); failure.assert_not_called(); capture.assert_not_called()
        with mock.patch.object(context, 'cmd_post_bash', return_value=0) as success, \
                mock.patch.object(context, 'cmd_post_deploy_failure', return_value=0) as failure, \
                mock.patch.object(telemetry, 'capture_event') as capture:
            hooks.dispatch('PostToolUse', self.payload('sf project deploy start', tool_response={'exit_code': 0}))
            success.assert_called_once(); failure.assert_not_called(); capture.assert_not_called()
        with mock.patch.object(context, 'cmd_post_bash') as success, \
                mock.patch.object(context, 'cmd_post_deploy_failure', return_value=0) as failure, \
                mock.patch.object(telemetry, 'capture_event') as capture:
            hooks.dispatch('PostToolUse', self.payload('sf project deploy start', tool_response={'exit_code': 1}))
            failure.assert_called_once(); success.assert_not_called()
            self.assertEqual(('command_invoked', 'failure'), capture.call_args.args[:2])

    def test_mcp_success_failure_and_subagent_mapping_are_allowlisted(self):
        p = self.payload(); p['tool_name'] = 'mcp__salesforce-lsp__diagnostics'
        for failed in (True, False):
            p['tool_response'] = {'isError': failed}
            with mock.patch.object(telemetry, 'capture_event') as capture:
                hooks.dispatch('PostToolUse', p)
            self.assertEqual('failure' if failed else 'success', capture.call_args.args[1])
        p['tool_response'] = 'opaque MCP error'
        with mock.patch.object(telemetry, 'capture_event') as capture:
            hooks.dispatch('PostToolUse', p)
        capture.assert_not_called()
        with mock.patch.object(telemetry, 'capture_event') as capture:
            hooks.dispatch('SubagentStart', dict(self.payload(), agent_type='salesforce-development:salesforce-dev', prompt='SECRET'))
        self.assertEqual({'agent_type': 'salesforce-development:salesforce-dev'}, capture.call_args.args[2]['tool_input'])

    def test_session_disclosure_capture_feedback_flush_once_and_optout(self):
        result = hooks.dispatch('SessionStart', self.payload())
        self.assertIn('Telemetry Usage', result['systemMessage'])
        self.assertIn('Skill usage is not recorded.', result['systemMessage'])
        self.assertNotIn('skills,', result['systemMessage'])
        self.assertNotIn('/feedback', result['systemMessage'])
        self.assertNotIn('/salesforce-development:', result['systemMessage'])
        buf = telemetry._session_buffer('test-thread')
        records = [json.loads(line) for line in buf.read_text().splitlines()]
        self.assertEqual(['session_start'], [r['event'] for r in records])
        self.assertEqual('codex', records[0]['harness'])
        result = hooks.invoke(telemetry.cmd_feedback_record, {}, ['sf-context', 'feedback-record', '4'])
        self.assertEqual('recorded', result['result'])
        records = [json.loads(line) for line in buf.read_text().splitlines()]
        self.assertEqual('test-thread', records[-1]['session_id'])
        self.assertEqual(4, records[-1]['payload']['rating'])
        rejected = hooks.invoke(telemetry.cmd_feedback_record, {}, ['sf-context', 'feedback-record', 'secret comments'])
        self.assertEqual('invalid_rating', rejected['reason'])
        with mock.patch.object(telemetry, '_spawn_sender', return_value=True) as sender:
            hooks.dispatch('SessionEnd', self.payload())
            hooks.dispatch('SessionEnd', self.payload())
        sender.assert_called_once()
        rows = [json.loads(line) for line in sender.call_args.args[0].read_text().splitlines()]
        self.assertEqual(['session_start', 'feedback', 'session_end'], [r['event'] for r in rows])
        with mock.patch.dict(os.environ, {'DO_NOT_TRACK': 'true'}), \
                mock.patch.object(telemetry, '_spawn_sender') as sender:
            hooks.dispatch('SessionStart', self.payload())
            hooks.dispatch('SessionEnd', self.payload())
            self.assertEqual('skipped', hooks.invoke(telemetry.cmd_feedback_record, {}, ['sf-context', 'feedback-record', '5'])['result'])
        sender.assert_not_called()
        self.assertFalse(buf.exists())

    def test_ci_suppresses_disclosure_without_consuming_human_notice(self):
        for marker in ('CI', 'GITHUB_ACTIONS', 'CONTINUOUS_INTEGRATION', 'BUILD_NUMBER'):
            with self.subTest(marker=marker), mock.patch.dict(os.environ, {marker: 'true'}):
                result = hooks.dispatch('SessionStart', self.payload())
                self.assertNotIn('systemMessage', result)
                self.assertFalse(telemetry._notified_file().exists())
        result = hooks.dispatch('SessionStart', self.payload())
        self.assertIn('Telemetry Usage', result['systemMessage'])
        self.assertTrue(telemetry._notified_file().exists())

    def test_numeric_feedback_identity_preserves_claude_and_event_precedence(self):
        self.assertEqual('event-id', telemetry.session_identity({'session_id': 'event-id'}))
        self.assertEqual('test-thread', telemetry.session_identity())
        with mock.patch.dict(os.environ, {'CODEX_SESSION_ID': 'outer-session'}):
            self.assertEqual('test-thread', telemetry.session_identity())
        with mock.patch.dict(os.environ, {'CODEX_THREAD_ID': '../escape'}):
            self.assertEqual('', telemetry.session_identity())
            self.assertEqual('', context._plugin_session_id('', 'codex'))
        with mock.patch.dict(os.environ, {'SF_AGENT_CLIENT': 'claude', 'CODEX_THREAD_ID': '', 'CODEX_SESSION_ID': ''}):
            self.assertEqual('claude-thread', telemetry.session_identity())

    def test_one_mutation_and_one_target_per_pending_call(self):
        result = hooks.dispatch('PreToolUse', self.payload('sf project deploy start -o one --target-org two'))
        self.assertEqual('deny', result['hookSpecificOutput']['permissionDecision'])
        with mock.patch.object(context, 'cmd_verify_org') as verify:
            result = hooks.dispatch('PreToolUse', self.payload('sf project deploy start -o one; sf project delete source -o two'))
        self.assertEqual('deny', result['hookSpecificOutput']['permissionDecision'])
        verify.assert_not_called()

    def test_shell_context_changes_cannot_verify_another_org(self):
        for command in (
            'SF_TARGET_ORG=production sf project deploy start',
            'env SF_TARGET_ORG=production sf project deploy start',
            'env -- sf project deploy start',
            'nice -n 5 sf project deploy start',
            'sudo -u user sf project deploy start',
            'cd ../production-project && sf project deploy start',
            'command cd ../prod && sf project deploy start',
            'builtin cd ../prod && sf project deploy start',
            'command env SF_TARGET_ORG=prod sf project deploy start',
            'exec env SF_TARGET_ORG=prod sf project deploy start',
            'exec -a custom env SF_TARGET_ORG=prod sf project deploy start',
            'command /usr/bin/env SF_TARGET_ORG=prod sf project deploy start',
            '/usr/bin/env -- sf project deploy start',
            'exec -a custom cd ../prod && sf project deploy start',
            'echo hi\ncd ../prod\nsf project deploy start',
            '>out cd ../prod && sf project deploy start',
            'sf config set target-org prod; sf project deploy start',
            'source org-env; sf project deploy start',
            'sf project deploy start -o "$ORG"',
        ):
            with self.subTest(command=command), mock.patch.object(context, 'cmd_verify_org') as verify:
                output = hooks.dispatch('PreToolUse', self.payload(command))
                self.assertEqual('deny', output['hookSpecificOutput']['permissionDecision'])
                verify.assert_not_called()

    def test_negation_wrappers_and_redirects_preserve_mutation_target(self):
        for command in (
            '! sf project deploy start -o prod',
            'command -p sf project deploy start -o prod',
            'sf >deploy.json project deploy start -o prod',
            'sf project deploy start >deploy.json --target-org prod',
            'sf project deploy start 2>error.log -o prod',
            'sf 2>&1 project deploy start -o prod',
        ):
            with self.subTest(command=command), mock.patch.object(hooks, 'invoke', return_value={'continue': True}) as verify, \
                    mock.patch.object(hooks, 'external', return_value=hooks.deny('production')) as gate:
                output = hooks.pre_shell(self.payload(command))
                self.assertEqual('deny', output['hookSpecificOutput']['permissionDecision'])
                verify.assert_called_once()
                self.assertEqual('prod-check', gate.call_args.args[2])

    def test_mutation_hint_covers_every_spelling_the_scanner_normalizes(self):
        shim = hooks.shim
        spellings = [' '.join(alias) for alias, _ in shim._COMMAND_ALIASES]
        spellings += [':'.join(alias) for alias, _ in shim._COMMAND_ALIASES]
        spellings += ['deploy', 'project deploy start', 'project:deploy:start',
                      'project delete source', 'project:delete:source']
        for cli in ('sf', 'sfdx', 'sf.cmd', 'npx -y @salesforce/cli@latest'):
            for spelling in spellings:
                command = f'{cli} {spelling} -o prod'
                with self.subTest(command=command):
                    calls = shim.scan_sf(command).calls
                    self.assertTrue(calls and shim.mutation_verb(calls[0].argv), command)
                    self.assertTrue(shim.mutation_hint(command))
                    self.assertTrue(shim.mutation_hint(f"sh -c '{command}'"))

    def test_escaped_backslash_does_not_escape_the_separator_after_it(self):
        shim = hooks.shim
        for command, expected in (
            ('sf project deploy start -o dev \\\\; sf project deploy start', 2),
            ('sf project deploy start -o dev "\\\\"; sf project deploy start', 2),
            ('sf project deploy start -o dev \\; sf project deploy start', 1),
            ('sf project deploy start --source-dir ";" -o dev', 1),
        ):
            with self.subTest(command=command):
                self.assertEqual(expected, len(shim.scan_sf(command).calls))

    def test_text_that_only_mentions_a_deploy_is_refused(self):
        # Without a literal call the gate cannot tell data from an unknown wrapper, so a
        # deploy-looking command that resolves to no sf call is denied.
        for command in ('cat >script.sh <<EOF\nsf project deploy start -o prod\nEOF',
                        'echo "sf project deploy start -o prod"'):
            with self.subTest(command=command), \
                    mock.patch.object(context, 'cmd_verify_org') as verify, \
                    mock.patch.object(hooks, 'external') as gate:
                output = hooks.pre_shell(self.payload(command))
                self.assertEqual('deny', output['hookSpecificOutput']['permissionDecision'])
                verify.assert_not_called()
                gate.assert_not_called()

    def test_offline_dual_host_production_destructive_and_org_verification(self):
        stub = Path(self.tmp.name) / 'tools'
        stub.mkdir()
        executable = stub / 'sf'
        executable.write_text("#!" + sys.executable + "\n" +
            "import json, os, sys\n" +
            "args=sys.argv[1:]\n" +
            "org={'alias':'fixture', 'username':'fixture@example.invalid', 'instanceUrl':'https://fixture.my.salesforce.com', 'isSandbox':os.environ.get('FIXTURE_BUCKET')=='sandbox'}\n" +
            "result = ([{'name':'target-org','value':'fixture'}] if args[:2]==['config','get'] else {'nonScratchOrgs':[org]} if args[:2]==['org','list'] else org)\n" +
            "print(json.dumps({'status':0,'result':result}))\n")
        executable.chmod(0o755)
        with mock.patch.dict(os.environ, {'PATH': str(stub) + os.pathsep + os.environ['PATH'],
                                         'SF_TARGET_ORG': '', 'SFDX_TARGET_ORG': '',
                                         'SFDX_LSP_DEPLOY_GATE': 'off'}):
            for bucket, command, mode, denied in [
                ('production', "sf project deploy start --target-org 'fixture'", 'prod-check', True),
                ('production', "echo --target-org sandbox; sf project deploy start -o fixture", 'prod-check', True),

                ('production', 'CONFIRM_PROD=1 sf project deploy start -o fixture', 'prod-check', 'claude-only'),
                ('sandbox', 'sf project deploy start --target-org=fixture', 'prod-check', False),
                ('production', 'sf project deploy start -o fixture --post-destructive-changes destructiveChanges.xml', 'prod-check', True),
                ('production', 'sf project delete source -o fixture', 'destructive', True),
                ('sandbox', 'sf project delete source -o fixture', 'destructive', False),
            ]:
                with self.subTest(bucket=bucket, command=command), mock.patch.dict(os.environ, {'FIXTURE_BUCKET': bucket}):
                    payload = self.payload(command)
                    legacy = hooks.external('scripts/sf-deploy-gate', payload, mode, timeout=5)
                    native = hooks.dispatch('PreToolUse', payload)
                    # The Claude gate honors the inline override; Codex requires the user's reply.
                    self.assertEqual(denied is True, legacy.get('hookSpecificOutput', {}).get('permissionDecision') == 'deny')
                    self.assertEqual(bool(denied), native.get('hookSpecificOutput', {}).get('permissionDecision') == 'deny')
            with mock.patch.object(context, 'resolve_executable', return_value=None):
                result = hooks.dispatch('PreToolUse', self.payload('"sf" "project" "deploy" "start"'))
                self.assertEqual('deny', result['hookSpecificOutput']['permissionDecision'])
            with mock.patch.object(context, 'resolve_executable', return_value=None):
                result = hooks.dispatch('PreToolUse', self.payload('sf project generate --name sample'))
                self.assertEqual('deny', result['hookSpecificOutput']['permissionDecision'])

    def test_real_gate_denies_every_production_spelling_and_allows_the_sandbox(self):
        denied = (
            '! sf project deploy start -o prod',
            'true && ! sf project deploy start -o prod',
            'command -p sf project deploy start -o prod',
            '>out sf project deploy start -o prod',
            '{ sf project deploy start -o prod; }',
            'timeout 60 sf project deploy start -o prod',
            'timeout -s KILL 60 sf project deploy start -o prod',
            'sf project deploy start --post-destructive-changes destructiveChanges.xml -o prod',
            'sf project deploy quick --job-id 0Af000000000001 -o prod',
            'sf project:deploy:start -o prod',
            'sfdx project deploy start -o prod',
            'sfdx force:source:deploy -u prod',
            'sfdx force:source:push -u prod',
            'sfdx force:mdapi:deploy -u prod',
            'sf deploy metadata -o prod',
            'npx @salesforce/cli project deploy start -o prod',
            'npx -y @salesforce/cli@latest project deploy start -o prod',
            'sf project deploy start -oprod',
            'sf project deploy start -o=prod',
            'sf project deploy start --targetusername prod',
            'sf project deploy start --targetusername=prod',
            'echo ok#note && sf project deploy start -o prod',
            'curl http://example.com/a#b && sf project deploy start -o prod',
            'sf project deploy start -u prod',
            '! sf project delete source -o prod -m ApexClass:A',
            'sfdx force:source:delete -u prod -m ApexClass:A',
            # Forms whose execution or target cannot be read.
            'bash -c "sf project deploy start -o prod"',
            'sh -lc "sf project deploy start -o prod"',
            'sudo -u ci bash -c "sf project deploy start -o prod"',
            'eval "sf project deploy start -o prod"',
            "sh -c 'sf deploy --target-org prod'",
            "bash -c 'sfdx deploy -o prod'",
            "eval 'npx @salesforce/cli@latest deploy -o prod'",
            'sf project deploy start -o $(echo prod)',
            'bash <<EOF\nsf project deploy start -o prod\nEOF',
            'echo sf project deploy start -o prod | bash',
            'bash <<< "sf project deploy start -o prod"',
            'echo -o prod | xargs sf project deploy start',
            'find . -exec sf project deploy start -o prod \\;',
            'python3 -c "import subprocess; subprocess.run([\'sf\',\'project\',\'deploy\',\'start\',\'-o\',\'prod\'])"',
            "env -S 'sf project deploy start -o prod'",
            'SF=sf; $SF project deploy start -o prod',
            'sf project deploy start -o',
            'sf project deploy start --target-org',
            # Unlisted execution wrappers and text that merely mentions a deploy resolve to
            # no literal call, so they are refused rather than guessed at.
            'chronic sf project deploy start -o prod',
            # Quote-splitting or a variable cannot hide the verb of an opaque execution.
            "eval 's''f project deploy start -o prod'",
            "chronic s''f project deploy start -o prod",
            "X=sf; $X project dep''loy start -o prod",
            # A quoted separator is an argument, not the end of the command.
            'sf project deploy start --source-dir ";" -o prod',
            'sf project deploy start --source-dir \\; --target-org prod',
            # An escaped backslash does not escape the separator after it.
            'sf project deploy start -o dev \\\\; sf project deploy start -o prod',
            'sf project deploy start -o dev "\\\\"; sf project deploy start -o prod',
            # Repeat-capable constructs could reuse one verification or confirmation.
            'f() (sf project deploy start -o prod); f; f',
            'watch -n 5 sf project deploy start -o prod',
            'while true; do sf project deploy start -o prod; done',
            'until false; do sf project deploy start -o prod; done',
            'for i in 1 2; do sf project deploy start -o prod; done',
            'f(){ sf project deploy start -o prod; }; f; f',
            'f () { sf project deploy start -o dev; }; f',
            # A literal sandbox deploy never vouches for an untraced one in the same line.
            'sf project deploy start -o dev; chronic sf project deploy start -o prod',
            'sf project deploy start -o dev && script -q /dev/null sf project deploy start -o prod',
            'echo "sf project deploy start -o prod"; sf project deploy start -o dev',
            'script -q /dev/null sf project deploy start -o prod',
            'echo "sf project deploy start -o prod"',
            'grep -r "sf project deploy start -o prod" .',
            'cat >deploy.sh <<EOF\nsf project deploy start -o prod\nEOF',
            'sf project deploy start --target-org="$ORG',
        )
        allowed = (
            '! sf project deploy start -o dev',
            'sf project deploy start',
            'sfdx force:source:deploy -u dev',
            'npx @salesforce/cli project deploy start -odev',
            'timeout 60 sf project deploy start --targetusername=dev',
            'npx sf project deploy start -o dev',
            'sf project deploy start --source-dir ";" -o dev',
            'npx -y sfdx force:source:deploy -u dev',
            'stdbuf -o0 sf project deploy start -o dev',
            '{ sf project delete source -o dev -m ApexClass:A; }',
        )
        os.chdir(self.project)
        with self.per_alias_sf():
            for command in denied:
                with self.subTest(command=command):
                    self.assertEqual('deny', self.decision(command)[0])
            for command in allowed:
                with self.subTest(command=command):
                    self.assertEqual('allow', self.decision(command)[0], self.decision(command)[1])

    def test_unrecognized_payload_shapes_and_other_workdirs_deny(self):
        os.chdir(self.project)
        with self.per_alias_sf():
            for tool_input in ({'command': ['bash', '-lc', 'sf project deploy start -o dev']},
                               'sf project deploy start -o dev'):
                with self.subTest(tool_input=tool_input):
                    payload = dict(self.payload(), tool_input=tool_input)
                    output = hooks.dispatch('PreToolUse', payload)
                    self.assertEqual('deny', output['hookSpecificOutput']['permissionDecision'])
            other = Path(self.tmp.name) / 'other'
            other.mkdir()
            for key in ('workdir', 'cwd'):
                with self.subTest(key=key):
                    payload = self.payload('sf project deploy start -o dev')
                    payload['tool_input'][key] = str(other)
                    output = hooks.dispatch('PreToolUse', payload)
                    self.assertEqual('deny', output['hookSpecificOutput']['permissionDecision'])
            payload = self.payload('sf project deploy start -o dev')
            payload['tool_input']['workdir'] = str(self.project)
            self.assertEqual('allow', 'deny' if hooks.dispatch('PreToolUse', payload).get(
                'hookSpecificOutput', {}).get('permissionDecision') == 'deny' else 'allow')
            self.assertEqual({'continue': True}, hooks.dispatch('PreToolUse', dict(
                self.payload(), tool_input={'command': ['ls', '-la']})))

    def test_codex_production_deploy_needs_the_users_own_confirmation(self):
        os.chdir(self.project)
        with self.per_alias_sf():
            for command in ('sf project deploy start -o prod # CONFIRM_PROD=1',
                            'echo CONFIRM_PROD=1; sf project deploy start -o prod',
                            'CONFIRM_PROD=1 sf project deploy start -o prod',
                            'sf project deploy start --I-CONFIRM-PROD -o prod'):
                with self.subTest(command=command):
                    decision, reason = self.decision(command)
                    self.assertEqual('deny', decision)
                    self.assertIn('confirm production deploy to prod', reason)
                    self.assertNotIn('CONFIRM_PROD', reason)
                    self.assertNotIn('--I-CONFIRM-PROD', reason)

            def user_says(prompt, session='test-thread'):
                hooks.invoke(context.cmd_prompt_dispatch, {
                    'hook_event_name': 'UserPromptSubmit', 'prompt': prompt,
                    'session_id': session, 'cwd': str(self.project)})

            user_says('confirm production deploy to prod')
            decision, reason = self.decision('sf project deploy start -o prod')
            self.assertEqual('allow', decision)
            self.assertIn('explicit confirmation present', reason)
            self.assertEqual('deny', self.decision('sf project deploy start -o prod')[0], 'single use')

            user_says('confirm production deploy to prod2')
            self.assertEqual('deny', self.decision('sf project deploy start -o prod')[0], 'other org')

            user_says('confirm production deploy to prod', session='other-thread')
            self.assertEqual('deny', self.decision('sf project deploy start -o prod')[0], 'other session')

            user_says('Yes, confirm production deployment to PROD.')
            marker = context._prod_deploy_confirm_path(context._plugin_session_id('test-thread', 'codex'))
            data = json.loads(marker.read_text())
            data['createdAt'] -= context._PROD_DEPLOY_CONFIRM_TTL_SECONDS + 5
            marker.write_text(json.dumps(data))
            self.assertEqual('deny', self.decision('sf project deploy start -o prod')[0], 'expired')

            marker.unlink(missing_ok=True)
            with mock.patch.dict(os.environ, {'SF_AGENT_CLIENT': 'claude'}):
                user_says('confirm production deploy to prod')
            self.assertFalse(marker.exists(), 'Claude prompts never record Codex consent')

    def confirm_prod(self, alias='prod', session='test-thread'):
        hooks.invoke(context.cmd_prompt_dispatch, {
            'hook_event_name': 'UserPromptSubmit', 'prompt': f'confirm production deploy to {alias}',
            'session_id': session, 'cwd': str(self.project)})

    def test_confirmation_survives_an_unrelated_deploy(self):
        os.chdir(self.project)
        with self.per_alias_sf():
            self.confirm_prod()
            self.assertEqual('allow', self.decision('sf project deploy start -o dev')[0])
            self.assertEqual('allow', self.decision('sf project deploy start -o prod')[0],
                             'a sandbox deploy must not spend the production confirmation')
            self.assertEqual('deny', self.decision('sf project deploy start -o prod')[0], 'single use')

    def test_confirmation_survives_a_later_denial(self):
        os.chdir(self.project)
        with self.per_alias_sf():
            self.confirm_prod()
            deny_precheck = {'hookSpecificOutput': {
                'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                'permissionDecisionReason': 'fixture diagnostics deny'}}
            real_external = hooks.external
            def external(relative, *args, **kwargs):
                if relative == 'bin/lsp-precheck':
                    return deny_precheck
                return real_external(relative, *args, **kwargs)
            with mock.patch.object(hooks, 'external', side_effect=external):
                self.assertEqual('deny', self.decision('sf project deploy start -o prod')[0])
            self.assertEqual('allow', self.decision('sf project deploy start -o prod')[0],
                             'a denial by a later check must not spend the confirmation')

    def test_confirmation_matches_the_alias_exactly(self):
        os.chdir(self.project)
        with self.per_alias_sf():
            self.confirm_prod('Prod')
            self.assertEqual('deny', self.decision('sf project deploy start -o prod')[0],
                             'aliases are case-sensitive, so Prod does not authorize prod')
            self.assertEqual('allow', self.decision('sf project deploy start -o Prod')[0])

    def test_confirmation_for_a_sandbox_alias_is_never_spent(self):
        os.chdir(self.project)
        with self.per_alias_sf():
            self.confirm_prod('dev')
            self.assertEqual('allow', self.decision('sf project deploy start -o dev')[0])
            self.assertTrue(context._peek_prod_deploy_confirmation('test-thread', 'dev'),
                            'a sandbox deploy must leave the confirmation unspent')

    def run_hook_main(self, event, payload, runtime_available):
        stdout = io.StringIO()
        with mock.patch.object(sys, 'argv', ['codex_hooks.py', event]), \
                mock.patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))), \
                mock.patch.object(hooks, '_RUNTIME_UNAVAILABLE', not runtime_available), \
                mock.patch.object(hooks, 'dispatch', side_effect=RuntimeError('fixture failure')), \
                contextlib.redirect_stdout(stdout):
            self.assertEqual(0, hooks.main())
        return json.loads(stdout.getvalue())

    def test_undecodable_hook_input_still_fails_closed_for_a_deploy(self):
        class Stdin:
            buffer = io.BytesIO(json.dumps(self.payload('sf project deploy start -o prod'))
                                .encode() + b'\xff')
        stdout = io.StringIO()
        with mock.patch.object(sys, 'argv', ['codex_hooks.py', 'PreToolUse']), \
                mock.patch.object(sys, 'stdin', Stdin()), \
                mock.patch.object(hooks, 'dispatch', side_effect=RuntimeError('fixture failure')), \
                contextlib.redirect_stdout(stdout):
            self.assertEqual(0, hooks.main())
        self.assertEqual('deny', json.loads(stdout.getvalue())['hookSpecificOutput']['permissionDecision'])

    def test_hook_failure_blocks_only_possible_org_mutations(self):
        for runtime_available in (True, False):
            with self.subTest(runtime_available=runtime_available):
                for command in ('ls', 'git status', 'echo hello'):
                    output = self.run_hook_main('PreToolUse', self.payload(command), runtime_available)
                    self.assertNotIn('hookSpecificOutput', output, command)
                    self.assertTrue(output['continue'])
                    self.assertIn('could not run', output['systemMessage'])
                edit = dict(self.payload(), tool_name='apply_patch',
                            tool_input={'command': '*** Begin Patch\n*** End Patch'})
                self.assertNotIn('hookSpecificOutput',
                                 self.run_hook_main('PreToolUse', edit, runtime_available))
                # Text inside a patch is file content, never a command to run.
                doc_edit = dict(edit, tool_input={'command':
                    '*** Begin Patch\n+Run sf project deploy start -o prod\n*** End Patch'})
                output = self.run_hook_main('PreToolUse', doc_edit, runtime_available)
                self.assertNotIn('hookSpecificOutput', output)
                self.assertTrue(output['continue'])
                for command in ('sf project deploy start -o prod', 'npx sf project delete source -o x',
                                "bash -c 'sfdx force:source:deploy -u prod'"):
                    output = self.run_hook_main('PreToolUse', self.payload(command), runtime_available)
                    self.assertEqual('deny', output['hookSpecificOutput']['permissionDecision'], command)
        self.assertEqual({'continue': True},
                         self.run_hook_main('SessionStart', self.payload(), True))

    def test_prod_confirmation_phrase_must_be_the_whole_affirmative_prompt(self):
        accepted = {
            'confirm production deploy to prod': 'prod',
            'Yes, confirm production deployment to prod.': 'prod',
            '  CONFIRM PRODUCTION DEPLOY TO Prod!  ': 'Prod',
            'confirm production deploy to admin@acme.com': 'admin@acme.com',
        }
        for prompt, alias in accepted.items():
            with self.subTest(prompt=prompt):
                self.assertEqual(alias, context._prod_deploy_confirmation_alias(prompt))
        for prompt in ('do not confirm production deploy to prod',
                       '"confirm production deploy to prod"',
                       'please confirm production deploy to prod',
                       'confirm production deploy to prod and then delete everything',
                       'I will type confirm production deploy to prod later',
                       'confirm production deploy to',
                       'confirm production deploy to prod; rm -rf /',
                       'no, confirm production deploy to prod'):
            with self.subTest(prompt=prompt):
                self.assertIsNone(context._prod_deploy_confirmation_alias(prompt))

    def test_stop_feedback_nudge_numeric_only_once_and_optout(self):
        hooks.dispatch('SessionStart', self.payload())
        telemetry.capture_event('command_invoked', 'success', {
            'session_id': 'test-thread', 'tool_input': {'command': 'sf-context discover'}})
        with mock.patch.dict(os.environ, {'SFDX_FEEDBACK': '1'}):
            first = hooks.dispatch('Stop', self.payload())
            self.assertIn('feedback-record RATING', first['hookSpecificOutput']['additionalContext'])
            self.assertNotIn('/feedback', json.dumps(first))
            self.assertEqual({'continue': True}, hooks.dispatch('Stop', self.payload()))
        with mock.patch.dict(os.environ, {'SFDX_FEEDBACK': '1', 'DO_NOT_TRACK': 'true'}):
            self.assertEqual({'continue': True}, hooks.dispatch('Stop', self.payload()))

    @unittest.skipUnless(os.name == 'posix', 'POSIX process-group cleanup')
    def test_external_timeout_kills_callback_descendants(self):
        marker = Path(self.tmp.name) / 'leaked-child'
        executable = Path(self.tmp.name) / 'callback'
        child = "import time,pathlib;time.sleep(.4);pathlib.Path(" + repr(str(marker)) + ").write_text('leaked')"
        executable.write_text('#!' + sys.executable + '\nimport subprocess,sys,time\n'
                              'assert sys.stdin.read()\nsubprocess.Popen([sys.executable,"-c",' +
                              repr(child) + '])\ntime.sleep(20)\n')
        executable.chmod(0o755)
        with mock.patch.object(hooks, 'ROOT', Path(self.tmp.name)):
            with self.assertRaises(subprocess.TimeoutExpired):
                hooks.external('callback', self.payload(), timeout=.15)
        hooks.time.sleep(.5)
        self.assertFalse(marker.exists(), 'callback child survived timeout')

    def test_safety_callback_errors_deny_but_lsp_errors_allow(self):
        payload = self.payload('sf project deploy start -o sandbox')
        os.chdir(self.project)
        with mock.patch.object(context, 'cmd_verify_org', return_value=0), \
                mock.patch.object(hooks, 'external', side_effect=[
                    {'continue': True, 'systemMessage': 'gate'}, subprocess.TimeoutExpired('lsp', 45)]):
            self.assertEqual({'continue': True, 'systemMessage': 'gate'}, hooks.pre_shell(payload))
        with mock.patch.object(context, 'cmd_verify_org', return_value=0), \
                mock.patch.object(hooks, 'external', return_value={'continue': True}):
            self.assertEqual('deny', hooks.pre_shell(payload)['hookSpecificOutput']['permissionDecision'])
        with mock.patch.object(sys, 'argv', ['codex_hooks.py', 'PreToolUse']), \
                mock.patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))), \
                mock.patch.object(hooks, 'dispatch', side_effect=subprocess.TimeoutExpired('gate', 35)), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, hooks.main())
        self.assertEqual('deny', json.loads(output.getvalue())['hookSpecificOutput']['permissionDecision'])

    def test_unavailable_runtime_dependency_denies_pretooluse(self):
        scripts = Path(self.tmp.name) / 'broken-plugin' / 'scripts'
        scripts.mkdir(parents=True)
        shutil.copyfile(ROOT / 'scripts/codex_hooks.py', scripts / 'codex_hooks.py')
        (scripts / 'sf_context.py').write_text("raise ImportError('fixture runtime unavailable')\n")
        for event in ('PreToolUse', 'SessionStart'):
            with self.subTest(event=event):
                result = subprocess.run(
                    [sys.executable, str(scripts / 'codex_hooks.py'), event],
                    input=json.dumps(self.payload('sf project deploy start -o prod')),
                    text=True, capture_output=True, timeout=5, check=False,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                output = json.loads(result.stdout)
                if event == 'PreToolUse':
                    self.assertEqual('deny', output['hookSpecificOutput']['permissionDecision'])
                else:
                    self.assertEqual({'continue': True}, output)

    def test_unserializable_safety_result_denies_pretooluse(self):
        with mock.patch.object(sys, 'argv', ['codex_hooks.py', 'PreToolUse']), \
                mock.patch.object(sys, 'stdin', io.StringIO(json.dumps(
                    self.payload('sf project deploy start -o prod')))), \
                mock.patch.object(hooks, 'dispatch', return_value={'bad': object()}), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, hooks.main())
        self.assertEqual('deny', json.loads(output.getvalue())['hookSpecificOutput']['permissionDecision'])

    def test_ui_precedence_preserves_claude_option(self):
        with mock.patch.dict(os.environ, {'SF_PLUGIN_UI_MODE': 'plain', 'CLAUDE_PLUGIN_OPTION_UI_MODE': 'off'}):
            self.assertEqual('plain', context._ui_mode())
        with mock.patch.dict(os.environ, {'SF_PLUGIN_UI_MODE': '', 'CLAUDE_PLUGIN_OPTION_UI_MODE': 'off'}):
            self.assertEqual('off', context._ui_mode())

    def test_manifest_timeout_matchers_and_no_unsupported_events(self):
        manifest = json.loads((ROOT / 'hooks/codex-hooks.json').read_text())['hooks']
        self.assertEqual(3, manifest['SessionEnd'][0]['hooks'][0]['timeout'])
        self.assertEqual('Bash|apply_patch|Write|Edit', manifest['PreToolUse'][0]['matcher'])
        self.assertNotIn('PostToolUseFailure', manifest)
        self.assertNotIn('StopFailure', manifest)
        self.assertNotIn('Skill', manifest['PreToolUse'][0]['matcher'])
        for event, blocks in manifest.items():
            self.assertEqual(1, len(blocks))
            self.assertEqual(1, len(blocks[0]['hooks']))

    def test_sf_lexical_matching_ignores_quoted_mentions(self):
        self.assertEqual([], hooks.sf_segments('grep "sf project deploy start" README.md'))
        self.assertEqual([], hooks.sf_segments('echo sf project deploy start'))
        self.assertEqual([['sf', 'project', 'deploy', 'start']], hooks.sf_segments('ls && CONFIRM_PROD=1 sf project deploy start'))

    def test_mutation_hint_ignores_org_aliases_containing_deploy_or_delete(self):
        from sf_shim import mutation_hint
        for command in (
            'sf project retrieve start --target-org deploy-test',
            'sf project retrieve start -o my-delete-org',
        ):
            self.assertFalse(mutation_hint(command), command)
        for command in (
            'sf project deploy start -o x', 'sf project delete source -o x',
            'sf project "${ACTION:-deploy}" start --target-org prod',
            'sf project ${ACTION:-delete} source -o prod',
        ):
            self.assertTrue(mutation_hint(command), command)

    def test_parameter_expanded_deploy_verb_is_denied(self):
        for command in (
            'sf project "${ACTION:-deploy}" start --target-org prod',
            'sf project ${ACTION:-delete} source -o prod',
        ):
            output = hooks.pre_shell(self.payload(command))
            self.assertEqual('deny', output['hookSpecificOutput']['permissionDecision'], command)


if __name__ == '__main__':
    unittest.main()
