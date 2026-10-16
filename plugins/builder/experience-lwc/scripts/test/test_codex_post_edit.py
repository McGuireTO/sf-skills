"""Patch decoding and packaged one-file advisory contracts for Codex."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('lwc_codex', ROOT / 'scripts/codex-post-edit.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class PostEditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'project with spaces'
        self.root.mkdir()
        (self.root / 'sfdx-project.json').write_text('{}')
        self.component = self.root / 'force-app/main/default/lwc/example'
        self.component.mkdir(parents=True)

    def file(self, name):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('fixture')
        return path

    def event(self, body, **extra):
        return dict(cwd=str(self.root), tool_name='apply_patch',
                    tool_input={'command': '*** Begin Patch\n' + body + '\n*** End Patch'}, **extra)

    def test_all_extensions_deduplicated_surviving_paths_and_unchanged_files(self):
        names = ['force-app/main/default/lwc/example/example' + ext for ext in ('.html', '.css', '.js')]
        for name in names:
            self.file(name)
        self.file('unrelated.js')
        patch = '\n'.join('*** Add File: ' + name + '\n+fixture' for name in names)
        patch += '\n*** Update File: ' + names[0] + '\n@@\n-fixture\n+fixture'
        patch += '\n*** Add File: unrelated.js\n+fixture\n*** Delete File: force-app/main/default/lwc/example/deleted.js'
        before = {name: (self.root / name).read_bytes() for name in names}
        with mock.patch.object(adapter, 'run_validator', return_value={'continue': True, 'output': 'finding'}) as run:
            result = adapter.dispatch(self.event(patch))
        self.assertEqual(3, run.call_count)
        self.assertEqual([self.root / name for name in names], [call.args[0] for call in run.call_args_list])
        self.assertIn('finding', result['hookSpecificOutput']['additionalContext'])
        self.assertEqual(before, {name: (self.root / name).read_bytes() for name in names})

    def test_rename_destination_only_missing_and_metadata_skipped(self):
        name = 'force-app/main/default/lwc/example/new.js'
        path = self.file(name)
        event = self.event('*** Update File: force-app/main/default/lwc/example/old.js\n*** Move to: ' + name +
                           '\n@@\n-old\n+new\n*** Add File: force-app/main/default/lwc/example/absent.css\n+text\n'
                           '*** Add File: force-app/main/default/lwc/example/example.js-meta.xml\n+text')
        with mock.patch.object(adapter, 'run_validator', return_value={'continue': True}) as run:
            self.assertEqual({'continue': True}, adapter.dispatch(event))
        self.assertEqual([path], [call.args[0] for call in run.call_args_list])

    def test_any_escaping_path_rejects_whole_patch_before_validation(self):
        name = 'force-app/main/default/lwc/example/example.js'
        self.file(name)
        for tail in ('*** Delete File: ../outside.js', '*** Add File: /tmp/outside.js\n+text',
                     '*** Update File: ' + name + '\n*** Move to: ../outside.js\n@@\n-old\n+new'):
            with self.subTest(tail=tail), mock.patch.object(adapter, 'run_validator') as run:
                with self.assertRaises(ValueError):
                    adapter.dispatch(self.event('*** Add File: ' + name + '\n+text\n' + tail))
                run.assert_not_called()

    def test_symlink_escape_rejected(self):
        outside = Path(self.temp.name) / 'outside.js'
        outside.write_text('fixture')
        (self.component / 'escaped.js').symlink_to(outside)
        with mock.patch.object(adapter, 'run_validator') as run:
            with self.assertRaises(ValueError):
                adapter.dispatch(self.event('*** Add File: force-app/main/default/lwc/example/escaped.js\n+text'))
            run.assert_not_called()

    def test_malformed_and_header_like_content(self):
        for body in ('*** Add File: a.js\nnot-prefixed', '*** Update File: a.js',
                     '*** Update File: a.js\n@@', '*** Update File: a.js\n@@\n@@\n+text',
                     '*** Delete File: a.js\n+body', '*** Move to: a.js'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                adapter.dispatch(self.event(body))
        self.assertEqual([('a.js', 'a.js')], adapter.patch_paths(
            '*** Begin Patch\n*** Add File: a.js\n+*** Delete File: ../escape\n*** End Patch'))

    def test_host_update_grammar(self):
        for body in ('-old\n+new', '@@\n context\n\n+new', '@@\n-old\n+new\n*** End of File\n\n  ',
                     '@@\n-old\n+new\n*** End of File\n\n@@ next\n context'):
            patch = '*** Begin Patch\n*** Update File: a.js\n' + body + '\n*** End Patch'
            with self.subTest(body=body):
                self.assertEqual([('a.js', 'a.js')], adapter.patch_paths(patch))

    def test_failed_patch_and_unrelated_tools_do_not_validate(self):
        for response in ({'success': False}, {'isError': True}, 'apply_patch verification failed: fixture'):
            with mock.patch.object(adapter, 'run_validator') as run:
                self.assertEqual({'continue': True}, adapter.dispatch(self.event('bad', tool_response=response)))
                run.assert_not_called()
        self.assertEqual({'continue': True}, adapter.dispatch({'tool_name': 'Bash'}))

    def test_nested_cwd_uses_project_ancestor(self):
        path = self.file('force-app/main/default/lwc/example/example.js')
        event = self.event('*** Add File: example.js\n+text')
        event['cwd'] = str(self.component)
        with mock.patch.object(adapter, 'run_validator', return_value={'continue': True}) as run:
            adapter.dispatch(event)
        self.assertEqual(path, run.call_args.args[0])
        self.assertEqual(self.component, run.call_args.args[1])

    def test_invalid_cwd_and_non_salesforce_project(self):
        for cwd in (None, 'relative', str(self.root / 'absent')):
            event = self.event('*** Add File: a.js\n+text'); event['cwd'] = cwd
            with self.subTest(cwd=cwd), self.assertRaises((ValueError, OSError)):
                adapter.dispatch(event)
        (self.root / 'sfdx-project.json').unlink()
        self.assertEqual({'continue': True}, adapter.dispatch(self.event('*** Add File: lwc/a.js\n+text')))

    def test_one_file_interface_and_packaged_validator_resolution(self):
        package = Path(self.temp.name) / 'package'
        script = package / 'scripts/codex-local-validate.py'
        script.parent.mkdir(parents=True)
        script.write_text('import json,sys,os\nassert len(sys.argv)==2\nassert sys.stdin.read()==""\n'
                          'print(json.dumps({"continue":True,"output":sys.argv[1]+"|"+os.getcwd()}))\n')
        path = self.file('force-app/main/default/lwc/example/example.js')
        with mock.patch.object(adapter, 'ROOT', package):
            result = adapter.run_validator(path, self.root, 2)
        self.assertEqual(str(path) + '|' + str(self.root), result['output'])

    def test_validator_failures_bad_output_and_timeout_remain_advisory(self):
        path = self.file('force-app/main/default/lwc/example/example.js')
        event = self.event('*** Add File: ' + str(path) + '\n+text')
        for failure in (ValueError('bad output'), subprocess.TimeoutExpired('validator', 1), OSError('missing')):
            with self.subTest(failure=failure), mock.patch.object(adapter, 'run_validator', side_effect=failure), \
                    mock.patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), \
                    contextlib.redirect_stdout(io.StringIO()) as stream:
                self.assertEqual(0, adapter.main())
            output = json.loads(stream.getvalue())
            self.assertIn('unavailable', output['hookSpecificOutput']['additionalContext'])
            self.assertNotIn('permissionDecision', output['hookSpecificOutput'])

    def test_oversized_patch_and_file_count_skip_validation(self):
        patches = [
            '*** Begin Patch\n*** Add File: a.js\n+' + 'x' * adapter.MAX_PATCH_CHARS + '\n*** End Patch',
            '*** Begin Patch\n' + '\n'.join(
                '*** Add File: a' + str(i) + '.js\n+fixture'
                for i in range(adapter.MAX_PATCH_FILES + 1)) + '\n*** End Patch',
        ]
        for patch in patches:
            with self.subTest(length=len(patch)), mock.patch.object(adapter, 'run_validator') as run:
                event = self.event(''); event['tool_input']['command'] = patch
                with self.assertRaises(ValueError):
                    adapter.dispatch(event)
                run.assert_not_called()

    def test_parsing_time_counts_against_validation_budget(self):
        self.file('force-app/main/default/lwc/example/example.js')
        original = adapter.patch_paths
        clock = [0.0]
        def delayed_parse(patch):
            result = original(patch)
            clock[0] = adapter.BUDGET + 1
            return result
        with mock.patch.object(adapter.time, 'monotonic', side_effect=lambda: clock[0]), \
                mock.patch.object(adapter, 'patch_paths', side_effect=delayed_parse), \
                mock.patch.object(adapter, 'run_validator') as run:
            with self.assertRaises(TimeoutError):
                adapter.dispatch(self.event('*** Add File: force-app/main/default/lwc/example/example.js\n+text'))
            run.assert_not_called()

    def test_serialization_failure_returns_actionable_advisory(self):
        import shlex
        event = self.event('*** Add File: a.js\n+text')
        package = Path(self.temp.name) / 'installed package'
        with mock.patch.object(adapter, 'dispatch', return_value={'output': object()}), \
                mock.patch.object(adapter, 'ROOT', package), \
                mock.patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), \
                contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(0, adapter.main())
        output = json.loads(stream.getvalue())['hookSpecificOutput']
        self.assertEqual('PostToolUse', output['hookEventName'])
        self.assertNotIn('permissionDecision', output)
        message = output['additionalContext']
        self.assertIn('TypeError', message)
        command = message.split('Run: ', 1)[1].split(' (replace FILE', 1)[0]
        self.assertEqual([sys.executable, str(package / 'scripts/codex-local-validate.py'), 'FILE'],
                         shlex.split(command))

    def test_packaged_dependency_import_failure_returns_advisory(self):
        package = Path(self.temp.name) / 'incomplete package'
        (package / 'scripts').mkdir(parents=True)
        (package / 'scripts/codex-local-validate.py').write_bytes(
            (ROOT / 'scripts/codex-local-validate.py').read_bytes())
        path = self.file('force-app/main/default/lwc/example/example.html')
        event = self.event('*** Add File: ' + str(path) + '\n+text')
        with mock.patch.object(adapter, 'ROOT', package), \
                mock.patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), \
                contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(0, adapter.main())
        output = json.loads(stream.getvalue())
        self.assertIn('unavailable (ValueError)', output['hookSpecificOutput']['additionalContext'])
        self.assertNotIn('permissionDecision', output['hookSpecificOutput'])

    def test_aggregate_deadline(self):
        self.file('force-app/main/default/lwc/example/example.js')
        with mock.patch.object(adapter.time, 'monotonic', side_effect=[0, adapter.BUDGET + 1]), \
                mock.patch.object(adapter, 'run_validator') as run:
            with self.assertRaises(TimeoutError):
                adapter.dispatch(self.event('*** Add File: force-app/main/default/lwc/example/example.js\n+text'))
            run.assert_not_called()

    def test_real_bundled_core_findings_without_external_tools_or_file_changes(self):
        local_spec = importlib.util.spec_from_file_location('lwc_local_runner', ROOT / 'scripts/codex-local-validate.py')
        local = importlib.util.module_from_spec(local_spec)
        local_spec.loader.exec_module(local)
        path = self.file('force-app/main/default/lwc/example/example.html')
        path.write_text('<template><div if:true={count > 5}>fixture</div></template>')
        before = path.read_bytes()
        with mock.patch.object(subprocess, 'run', side_effect=AssertionError('external tooling')), \
                mock.patch.object(subprocess, 'Popen', side_effect=AssertionError('external tooling')):
            result = local.validate(path)
        self.assertIs(True, result['continue'])
        self.assertIn('Bundled SLDS score:', result['output'])
        self.assertIn('Comparison in if:true', result['output'])
        self.assertIn('were not run', result['output'])
        self.assertEqual(before, path.read_bytes())

    def test_real_subprocess_bad_advisories_and_timeout(self):
        package = Path(self.temp.name) / 'package'
        script = package / 'scripts/codex-local-validate.py'
        script.parent.mkdir(parents=True)
        path = self.file('force-app/main/default/lwc/example/example.js')
        for body in ('print("not json")', 'print("[]")', 'print(\'{"continue":false}\')',
                     'print(\'{"continue":true,"output":42}\')', 'raise SystemExit(1)'):
            script.write_text(body)
            with self.subTest(body=body), mock.patch.object(adapter, 'ROOT', package), \
                    self.assertRaises((ValueError, json.JSONDecodeError)):
                adapter.run_validator(path, self.root, 2)
        script.write_text('import time\ntime.sleep(5)')
        with mock.patch.object(adapter, 'ROOT', package), self.assertRaises(subprocess.TimeoutExpired):
            adapter.run_validator(path, self.root, .1)

    def test_native_hook_and_claude_contract(self):
        native = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())
        claude = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())
        self.assertEqual(claude['version'], native['version'])
        self.assertEqual('./skills/', native['skills'])
        hook = json.loads((ROOT / 'hooks/codex-hooks.json').read_text())['hooks']['PostToolUse'][0]
        self.assertEqual('apply_patch|Write|Edit', hook['matcher'])
        self.assertEqual(10, hook['hooks'][0]['timeout'])
        self.assertIn('${PLUGIN_ROOT}', hook['hooks'][0]['command'])
        legacy = claude['hooks']['PostToolUse'][0]['hooks'][0]['command']
        self.assertIn('${CLAUDE_PLUGIN_ROOT}', legacy)


if __name__ == '__main__':
    unittest.main()
