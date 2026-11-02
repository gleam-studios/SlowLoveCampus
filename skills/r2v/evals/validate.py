#!/usr/bin/env python3
"""Read-only structural checks for this R2V package (Python standard library only).

This deliberately validates the two scalar frontmatter fields used by this package,
not general YAML or all Agent Skills implementations. Semantic checks, native loading
and media generation are outside this tool's scope. It never installs or calls tools.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse


def validate(root: Path) -> dict:
    checks = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    required = [
        'SKILL.md', 'README.md', 'references/asset-selection.md',
        'references/reference-composition.md', 'references/generation-strategy.md',
        'references/production-brief.md', 'evals/cases.json',
        'evals/walkthrough.md', 'evals/sources.md', 'evals/validate.py',
    ]
    missing = [p for p in required if not (root / p).is_file()]
    check('required_files', not missing, 'missing=' + ', '.join(missing))
    if missing:
        return {'scope': 'structural_only', 'passed': False, 'checks': checks}

    files = sorted(p for p in root.rglob('*') if p.is_file())
    symlinks = [p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_symlink()]
    check('no_symlinks', not symlinks, ', '.join(symlinks))
    texts = {}
    bad_utf8 = []
    bad_newlines = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        try:
            raw = path.read_bytes()
            texts[rel] = raw.decode('utf-8')
            if raw.startswith(b'\xef\xbb\xbf') or b'\r\n' in raw:
                bad_newlines.append(rel)
        except UnicodeDecodeError:
            bad_utf8.append(rel)
    check('utf8_files', not bad_utf8, ', '.join(bad_utf8))
    check('no_bom_and_lf', not bad_newlines, ', '.join(bad_newlines))

    skill = texts.get('SKILL.md', '')
    fm = re.match(r'\A---\n(.*?)\n---\n', skill, flags=re.S)
    check('frontmatter_delimiters', fm is not None, 'YAML block at file start')
    meta = {}
    parse_errors = []
    if fm:
        for line in fm.group(1).splitlines():
            if ':' not in line:
                parse_errors.append(line)
                continue
            key, value = line.split(':', 1)
            key, value = key.strip(), value.strip()
            if key in meta:
                parse_errors.append('duplicate key: ' + key)
            if value.startswith('"'):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    parse_errors.append('invalid quoted scalar: ' + key)
            meta[key] = value
    check('frontmatter_scalar_parse', not parse_errors, '; '.join(parse_errors))
    check('frontmatter_fields', set(meta) == {'name', 'description'}, ', '.join(meta))
    name = meta.get('name', '')
    desc = meta.get('description', '')
    check('skill_name', isinstance(name, str) and bool(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name)) and len(name) <= 64, str(name))
    check('directory_matches_name', name == root.name, root.name)
    check('description_length', isinstance(desc, str) and 1 <= len(desc) <= 1024, str(len(desc)) if isinstance(desc, str) else 'not string')
    check('main_under_500_lines', len(skill.splitlines()) < 500, str(len(skill.splitlines())))

    broken_links = []
    private_paths = []
    for rel, text in texts.items():
        if not rel.endswith('.md'):
            continue
        # All Markdown links in this package use simple link targets.
        for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', text):
            target = target.split(' "', 1)[0]
            if urlparse(target).scheme or target.startswith('#'):
                continue
            target = unquote(target.split('#', 1)[0])
            resolved = (root / rel).parent.joinpath(target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                broken_links.append(f'{rel}: outside package: {target}')
                continue
            if not resolved.is_file():
                broken_links.append(f'{rel}: {target}')
        if re.search(r'/(?:Users|home)/[^\s]+|[A-Za-z]:\\Users\\', text):
            private_paths.append(rel)
    check('local_markdown_links', not broken_links, '; '.join(broken_links))
    check('no_private_machine_paths', not private_paths, ', '.join(private_paths))
    linked_refs = ['references/' + p.name for p in (root / 'references').glob('*.md')]
    unlinked = [p for p in linked_refs if f']({p})' not in skill]
    check('all_reference_files_linked', not unlinked, ', '.join(unlinked))

    runtime_files = ['SKILL.md'] + sorted(linked_refs)
    model_hits = [p for p in runtime_files if re.search(r'(?i)seedance|\bveo\b|minimax|runninghub|\bH3\b|kling', texts.get(p, ''))]
    check('model_neutral_runtime', not model_hits, ', '.join(model_hits))
    check('no_model_directory', not (root / 'models').exists(), 'capabilities are task inputs')
    extra_code = [p.relative_to(root).as_posix() for p in files if p.suffix in {'.py', '.sh', '.js', '.ts'} and p != root / 'evals/validate.py']
    check('maintenance_code_only', not extra_code, ', '.join(extra_code))
    check('no_execution_permissions_declared', 'allowed-tools' not in meta, 'no tool grants')

    try:
        fixture = json.loads(texts.get('evals/cases.json', ''))
        cases = fixture.get('cases', [])
        check('cases_json', isinstance(cases, list) and bool(cases), str(len(cases)))
    except (ValueError, TypeError, AttributeError) as exc:
        fixture, cases = {}, []
        check('cases_json', False, str(exc))
    ids = [c.get('id') for c in cases if isinstance(c, dict)]
    check('unique_case_ids', len(ids) == len(cases) == len(set(ids)), str(len(ids)))
    case_errors = []
    for c in cases:
        if not isinstance(c, dict):
            case_errors.append('non-object case')
            continue
        for key in ['id', 'title', 'category', 'evidence_type', 'input', 'expected_decisions', 'failure_signals', 'read_sections']:
            if not c.get(key):
                case_errors.append(f"{c.get('id')}: {key}")
        for key in ['brief', 'assets_and_observations', 'capabilities']:
            if not c.get('input', {}).get(key):
                case_errors.append(f"{c.get('id')}: input.{key}")
    check('case_structure', not case_errors, '; '.join(case_errors))
    walkthrough = texts.get('evals/walkthrough.md', '')
    missing_reviews = [cid for cid in ids if f'## {cid} ·' not in walkthrough]
    check('walkthrough_coverage', not missing_reviews, ', '.join(missing_reviews))
    honest_scope = fixture.get('independent_agent_run') is False and fixture.get('media_generation_run') is False
    check('evaluation_scope_declared', honest_scope, 'author desktop walkthrough only')
    sources = texts.get('evals/sources.md', '')
    check('source_records_present', all(s in sources for s in ['U01', 'P01', 'S01', 'S02', 'S03']), 'user experience, case provenance and primary sources')

    manifests = [
        {'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size,
         'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in files if p != root / 'evals/validation.json'
    ]
    return {
        'tool': 'r2v-local-structural-check', 'scope': 'structural_only',
        'passed': all(c['passed'] for c in checks),
        'check_count': len(checks), 'case_count': len(cases),
        'semantic_checks_automated': False, 'native_client_tested': False,
        'independent_agent_tested': False, 'media_generation_tested': False,
        'checks': checks, 'manifest_excludes': ['evals/validation.json'],
        'manifest': manifests,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Print JSON report to stdout.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    try:
        result = validate(root)
    except (OSError, ValueError) as exc:
        if args.json:
            print(json.dumps({'passed': False, 'scope': 'structural_only', 'error': str(exc)}, ensure_ascii=False))
        else:
            print(f'Validation error: {exc}', file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for c in result['checks']:
            print(('PASS' if c['passed'] else 'FAIL') + ' ' + c['name'] + ': ' + c['detail'])
        print(f"Structural result: {'PASS' if result['passed'] else 'FAIL'}; cases: {result.get('case_count', 0)}")
        print('No semantic, native-client, independent-agent or media-generation test was performed.')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
