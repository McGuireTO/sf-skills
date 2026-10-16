#!/usr/bin/env python3
"""Exercise an installed Codex package with isolated state and intercepted transport.

Usage: python3 installed_codex_lifecycle.py /absolute/installed/plugin/root
No org is contacted; only scrubbed wire projection and sender handoff are checked.
"""
import importlib, json, os, pathlib, sys, tempfile
from unittest import mock
sys.dont_write_bytecode=True
root=pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0,str(root/'scripts'))
hooks=importlib.import_module('codex_hooks')
telemetry=importlib.import_module('sf_telemetry')
assert pathlib.Path(hooks.__file__).resolve().is_relative_to(root)
assert pathlib.Path(telemetry.__file__).resolve().is_relative_to(root)
with tempfile.TemporaryDirectory(prefix='sf-installed-lifecycle-',dir='/tmp') as raw:
 project=pathlib.Path(raw)/'project'; project.mkdir(); (project/'sfdx-project.json').write_text('{}')
 os.environ.update(SF_AGENT_CLIENT='codex',CODEX_THREAD_ID='installed-fixture-thread',CODEX_SESSION_ID='outer-unrelated-session',SF_DEV_TELEMETRY_HOME=raw+'/consent',DO_NOT_TRACK='',SF_DISABLE_TELEMETRY='',CI='',CONTINUOUS_INTEGRATION='',GITHUB_ACTIONS='')
 payload={'cwd':str(project),'session_id':'installed-fixture-thread','source':'startup'}
 os.chdir(root)
 start=hooks.dispatch('SessionStart',payload)
 assert 'Telemetry Usage' in start['systemMessage']
 assert '/feedback' not in start['systemMessage']
 assert pathlib.Path.cwd()==project.resolve()
 rating=hooks.invoke(telemetry.cmd_feedback_record,{},['sf-context','feedback-record','3'])
 assert rating=={'result':'recorded'}
 assert hooks.invoke(telemetry.cmd_feedback_record,{},['sf-context','feedback-record','comments'])['reason']=='invalid_rating'
 snapshots=[]
 def handoff(path):
  rows=[json.loads(line) for line in path.read_text().splitlines()]
  snapshots.append(rows)
  return True
 with mock.patch.object(telemetry,'_spawn_sender',side_effect=handoff):
  hooks.dispatch('SessionEnd',payload)
  hooks.dispatch('SessionEnd',payload)
 assert len(snapshots)==1
 rows=snapshots[0]
 assert [r['event'] for r in rows]==['session_start','feedback','session_end']
 assert all(r['session_id']=='installed-fixture-thread' and r['harness']=='codex' for r in rows)
 pdp=[telemetry._to_pdp_event(r,org_bucket='sandbox') for r in rows]
 uip=[telemetry._to_a4d_event(r,org_bucket='sandbox',org_id='00D000000000001') for r in rows]
 assert all(pdp) and all(uip)
 wire=json.dumps([pdp,uip])
 assert 'comments' not in wire and str(project) not in wire
 os.environ['DO_NOT_TRACK']='true'
 with mock.patch.object(telemetry,'_spawn_sender') as sender:
  hooks.dispatch('SessionStart',payload)
  hooks.dispatch('SessionEnd',payload)
  assert hooks.invoke(telemetry.cmd_feedback_record,{},['sf-context','feedback-record','5'])['result']=='skipped'
  sender.assert_not_called()
 print(json.dumps({'installed_root':str(root),'events':[r['event'] for r in rows], 'sender_handoffs':len(snapshots), 'pdp_events':len(pdp), 'uip_events':len(uip), 'opt_out':'pass','network_transmission':'not attempted'}))
