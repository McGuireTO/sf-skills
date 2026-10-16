#!/usr/bin/env python3
"""Run bundled Python LWC checks without launching optional external analyzers."""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/experience-lwc-generate/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location('lwc_local_' + name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate(path):
    result = load('validate_slds').SLDSValidator(str(path)).validate()
    issues = list(result.get('issues', []))
    if path.suffix.lower() == '.html':
        template = load('template_validator').LWCTemplateValidator(str(path)).validate()
        issues.extend(template.get('issues', []))
    lines = ['Bundled SLDS score: ' + str(result.get('score', 0)) + '/' + str(result.get('max_score', 140))]
    lines.extend(str(issue.get('severity', 'INFO')) + ' line ' + str(issue.get('line', 0)) +
                 ': ' + str(issue.get('message', '')) for issue in issues[:20])
    if not issues:
        lines.append('No findings from the bundled Python checks.')
    elif len(issues) > 20:
        lines.append(str(len(issues) - 20) + ' additional findings omitted.')
    lines.append('Optional SLDS Linter and Code Analyzer were not run by this automatic hook.')
    return {'continue': True, 'output': '\n'.join(lines)}


if __name__ == '__main__':
    print(json.dumps(validate(Path(sys.argv[1]))))
