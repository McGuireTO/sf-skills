#!/usr/bin/env python3
"""Check delegation to shared command renderers and SFDX directory selection."""
import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import codex_command_surface as adapter


class SurfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.cwd = Path.cwd()
        self.env = mock.patch.dict(os.environ)
        self.env.start()
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self.cwd)
        self.env.stop()
        self.temp.cleanup()

    def run_surface(self, command):
        output = io.StringIO()
        with mock.patch.object(sys, 'argv', ['surface', command]), contextlib.redirect_stdout(output):
            adapter.main()
        return output.getvalue()

    def test_each_surface_uses_shared_painter_and_actual_output(self):
        for command in ('org', 'project', 'status', 'welcome'):
            with self.subTest(command=command):
                painter = mock.Mock(return_value=('model note', 'authoritative ' + command))
                with mock.patch.dict(adapter.sf_context._STATUS_FAMILY_PAINTERS,
                                     {'salesforce-development:' + command: painter}):
                    self.assertEqual(self.run_surface(command), 'authoritative ' + command + '\n')
                painter.assert_called_once_with(self.root)
                self.assertEqual(os.environ['SF_AGENT_CLIENT'], 'codex')

    def test_nested_directory_uses_nearest_sfdx_project(self):
        (self.root / 'sfdx-project.json').write_text('{}')
        child = self.root / 'nested/source'
        child.mkdir(parents=True)
        os.chdir(child)
        painter = mock.Mock(return_value=('', 'nested'))
        with mock.patch.dict(adapter.sf_context._STATUS_FAMILY_PAINTERS,
                             {'salesforce-development:project': painter}):
            self.run_surface('project')
        painter.assert_called_once_with(self.root)
        self.assertEqual(Path.cwd(), self.root)
        self.assertEqual((self.root / 'sfdx-project.json').read_text(), '{}')

    def test_actual_no_project_welcome_is_read_only_and_shared(self):
        os.environ['NO_COLOR'] = '1'
        with mock.patch.object(adapter.sf_context.subprocess, 'run', side_effect=AssertionError('CLI probe')):
            _, expected = adapter.sf_context._welcome_command_paint(self.root)
            actual = self.run_surface('welcome')
            self.assertEqual(actual, expected.replace('/salesforce-development:setup to scaffold one',
                                                     'ask to create an SFDX project') + '\n')
            self.assertNotIn('/salesforce-development:', actual)
        os.environ.pop('NO_COLOR', None)
        with mock.patch.object(adapter.sf_context.subprocess, 'run', side_effect=AssertionError('CLI probe')):
            colored = self.run_surface('welcome')
        self.assertNotIn('/salesforce-development:', colored)
        self.assertIn('the Salesforce setup workflow', colored)
        self.assertIn('to scaffold one', colored)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_codex_plain_lockup_uses_the_current_raster_without_ansi(self):
        with mock.patch.dict(os.environ, {"SF_AGENT_CLIENT": "codex", "NO_COLOR": "1"}, clear=False):
            lockup = adapter.sf_context.render_banner_block(color=False)
        self.assertIn("*oooo*", lockup)
        self.assertNotIn("███████", lockup)
        self.assertNotIn("\x1b[", lockup)

    def test_unknown_surface_is_rejected_before_dispatch(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            self.run_surface('deploy')
        self.assertEqual(raised.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
