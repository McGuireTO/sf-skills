#!/usr/bin/env python3
"""Bounded startup rendering and disclosure/context precedence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import codex_startup as startup
import codex_hooks as hooks


class StartupTests(unittest.TestCase):
    def test_off_and_compaction_skip_cosmetic_renderer(self):
        for mode,source in [('off','startup'),('plain','compact')]:
            with mock.patch.object(startup.context,'_ui_mode',return_value=mode), \
                 mock.patch.object(startup,'run_renderer') as run:
                self.assertEqual({'continue':True},startup.presentation({'source':source}))
                run.assert_not_called()

    def test_delegates_to_installed_shared_welcome_with_a_budget(self):
        with mock.patch.object(startup.context,'_ui_mode',return_value='plain'), \
             mock.patch.object(startup,'run_renderer',return_value=
                subprocess.CompletedProcess([],0,'real shared welcome\n','')) as run:
            self.assertEqual('real shared welcome',startup.presentation({})['systemMessage'])
        self.assertEqual([sys.executable,str(ROOT/'scripts/codex_command_surface.py'),'startup'],run.call_args.args[0])
        self.assertNotIn('timeout',run.call_args.kwargs)

    def test_errors_timeout_and_oversized_output_degrade_honestly(self):
        for response in [subprocess.CompletedProcess([],1,'',''),
                         subprocess.CompletedProcess([],0,'',''),
                         subprocess.CompletedProcess([],0,'x'*16001,''),
                         subprocess.TimeoutExpired('welcome',4),OSError('missing')]:
            with self.subTest(kind=type(response).__name__), \
                 mock.patch.object(startup.context,'_ui_mode',return_value='plain'), \
                 mock.patch.object(startup,'run_renderer',**(
                    {'side_effect':response} if isinstance(response,Exception) else {'return_value':response})):
                output=startup.presentation({})
                self.assertTrue(output['continue'])
                self.assertIn('startup details unavailable',output['systemMessage'])
                self.assertNotIn('x'*100,output['systemMessage'])

    @unittest.skipUnless(os.name == 'posix', 'POSIX process-group cleanup')
    def test_timeout_kills_probe_children(self):
        with tempfile.TemporaryDirectory() as raw:
            marker=Path(raw)/'leaked-child'
            child="import time,pathlib;time.sleep(.4);pathlib.Path("+repr(str(marker))+").write_text('leaked')"
            parent="import subprocess,sys,time;subprocess.Popen([sys.executable,'-c',sys.argv[1]]);time.sleep(20)"
            with self.assertRaises(subprocess.TimeoutExpired):
                startup.run_renderer([sys.executable,'-c',parent,child],timeout=.15)
            import time
            time.sleep(.5)
            self.assertFalse(marker.exists(),'renderer probe child survived timeout')

    @unittest.skipUnless(os.name == 'posix', 'POSIX process-group cleanup')
    def test_killpg_error_still_reaps_renderer(self):
        with mock.patch.object(startup.os, 'killpg', side_effect=PermissionError('denied')):
            with self.assertRaises(subprocess.TimeoutExpired):
                startup.run_renderer([sys.executable, '-c', 'import time;time.sleep(20)'], timeout=.05)

    def test_actual_no_project_renderer_never_probes_org(self):
        with tempfile.TemporaryDirectory() as raw:
            fake=Path(raw)/'sf';sentinel=Path(raw)/'sf-executed'
            fake.write_text('#!/bin/sh\ntouch "'+str(sentinel)+'"\nexit 99\n');fake.chmod(0o755)
            env=dict(os.environ,PATH=raw+os.pathsep+os.environ['PATH'],DO_NOT_TRACK='true',
                     SF_DISABLE_TELEMETRY='true',SF_PLUGIN_UI_MODE='plain',PYTHONDONTWRITEBYTECODE='1')
            code="import sys,json;sys.path.insert(0,sys.argv[1]);import codex_startup;print(json.dumps(codex_startup.presentation({})))"
            result=subprocess.run([sys.executable,'-c',code,str(ROOT/'scripts')],cwd=raw,env=env,
                                  text=True,capture_output=True,timeout=8,check=True)
            text=json.loads(result.stdout)['systemMessage']
            self.assertIn('no Salesforce project here',text)
            self.assertNotIn('/salesforce-development:',text)
            self.assertFalse(sentinel.exists())

    def test_resume_reuses_the_sessions_rendered_surface(self):
        with tempfile.TemporaryDirectory() as raw, \
             mock.patch.object(startup,'_CACHE_DIR',Path(raw)/'codex-startup'), \
             mock.patch.object(startup.context,'_ui_mode',return_value='plain'):
            with mock.patch.object(startup,'run_renderer',return_value=
                    subprocess.CompletedProcess([],0,'first banner\n','')) as run:
                self.assertEqual('first banner',startup.presentation(
                    {'source':'startup','session_id':'cache-a'})['systemMessage'])
                self.assertEqual('first banner',startup.presentation(
                    {'source':'resume','session_id':'cache-a'})['systemMessage'])
                run.assert_called_once()
            with mock.patch.object(startup,'run_renderer',return_value=
                    subprocess.CompletedProcess([],0,'fresh banner\n','')) as run:
                self.assertEqual('fresh banner',startup.presentation(
                    {'source':'resume','session_id':'cache-b'})['systemMessage'])
                self.assertEqual('fresh banner',startup.presentation(
                    {'source':'startup','session_id':'cache-a'})['systemMessage'])
                self.assertEqual(2,run.call_count)

    def test_resume_reuses_a_surface_with_box_drawing_characters(self):
        banner='\u250c\u2500 Salesforce \u2500\u2510\n\u2514\u2500\u2500\u2500\u2518'
        with tempfile.TemporaryDirectory() as raw, \
             mock.patch.object(startup,'_CACHE_DIR',Path(raw)/'codex-startup'), \
             mock.patch.object(startup.context,'_ui_mode',return_value='plain'):
            with mock.patch.object(startup,'run_renderer',return_value=
                    subprocess.CompletedProcess([],0,banner+'\n','')) as run:
                self.assertEqual(banner,startup.presentation(
                    {'source':'startup','session_id':'cache-u'})['systemMessage'])
                self.assertEqual(banner,startup.presentation(
                    {'source':'resume','session_id':'cache-u'})['systemMessage'])
                run.assert_called_once()

    def test_session_start_matcher_skips_clear(self):
        config=json.loads((ROOT/'hooks/codex-hooks.json').read_text())
        self.assertEqual('startup|resume|compact',config['hooks']['SessionStart'][0]['matcher'])

    def test_actual_project_renderer_runs_no_cli_or_git_probe(self):
        with tempfile.TemporaryDirectory() as raw:
            bindir=Path(raw)/'bin';bindir.mkdir();sentinel=Path(raw)/'probe-executed'
            for name in ('sf','sfdx','git'):
                fake=bindir/name
                fake.write_text('#!/bin/sh\necho "$0" >> "'+str(sentinel)+'"\nexit 99\n');fake.chmod(0o755)
            # The installed-plugin summary may read the local Codex inventory.
            (bindir/'codex').write_text('#!/bin/sh\nexit 1\n');(bindir/'codex').chmod(0o755)
            project=Path(raw)/'project';(project/'.sf').mkdir(parents=True)
            (project/'sfdx-project.json').write_text(json.dumps(
                {'name':'demo','packageDirectories':[{'path':'force-app','default':True}]}))
            (project/'.sf/config.json').write_text(json.dumps({'target-org':'local-alias'}))
            env=dict(os.environ,PATH=str(bindir)+os.pathsep+'/usr/bin:/bin',HOME=raw,DO_NOT_TRACK='true',
                     SF_DISABLE_TELEMETRY='true',SF_PLUGIN_UI_MODE='full',NO_COLOR='1',PYTHONDONTWRITEBYTECODE='1')
            result=subprocess.run([sys.executable,str(ROOT/'scripts/codex_command_surface.py'),'startup'],
                                  cwd=project,env=env,text=True,capture_output=True,timeout=8,check=True)
            self.assertIn('org: local-alias',result.stdout)
            self.assertIn('the Salesforce status workflow',result.stdout)
            self.assertNotIn('/salesforce-development:',result.stdout)
            self.assertFalse(sentinel.exists(),sentinel.read_text() if sentinel.exists() else '')

    def test_disclosure_before_banner_and_primary_context_not_overwritten(self):
        with tempfile.TemporaryDirectory() as raw:
            project=Path(raw);(project/'sfdx-project.json').write_text('{}')
            old=Path.cwd()
            try:
                with mock.patch.object(hooks,'invoke',return_value={'systemMessage':'DISCLOSURE'}), \
                     mock.patch.object(startup,'presentation',return_value={'systemMessage':'BANNER'}), \
                     mock.patch.object(hooks.context,'_record_welcomed') as welcomed, \
                     mock.patch.object(hooks.context,'_record_entered') as entered:
                    output=hooks.dispatch('SessionStart',{'cwd':str(project),'session_id':'startup-test'})
                self.assertEqual('DISCLOSURE\nBANNER',output['systemMessage'])
                welcomed.assert_called_once_with('codex:startup-test')
                entered.assert_called_once_with('codex:startup-test')
                self.assertIn('skills first',output['hookSpecificOutput']['additionalContext'])
                context=output['hookSpecificOutput']['additionalContext']
                self.assertIn(str(hooks.ROOT),context)
                self.assertIn('SF_AGENT_CLIENT=codex',context)
                self.assertIn('${CLAUDE_PLUGIN_ROOT}',context)
                self.assertIn('do not persist',context)
                self.assertIn('other plugins',context)
                self.assertIn('unavailable child skill',context)
                self.assertIn('fresh Codex session',context)
                self.assertIn('does not establish activation',context)
            finally:os.chdir(old)


if __name__=='__main__':unittest.main()
