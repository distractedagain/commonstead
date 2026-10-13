#!/usr/bin/env python3
"""Bounded source/staged/history hygiene checks; not a comprehensive secret audit."""
import argparse
import ast
import csv
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    'github_credential': re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})'),
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'aws_access_id': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'credential_url': re.compile(r'https?://[^\s/:]+:[^\s/@]+@[^\s]+'),
    'local_private_path': re.compile(r'/Users/[^/\s]+/(?:\.codex|Documents|\.ssh)/'),
}
IGNORED = {'.git', '.venv', '__pycache__', 'data', 'work', 'dist', 'build'}
ALLOWED_BINARY = {'.png', '.jpg', '.jpeg', '.webp'}


def git(*arguments, check=True):
    return subprocess.run(['git', '-C', str(ROOT), *arguments], capture_output=True, check=check)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true', help='Inspect the Git index instead of working files')
    parser.add_argument('--history', action='store_true', help='Also scan all reachable commit text and blobs')
    args = parser.parse_args()
    errors, files, commits = [], {}, []
    if args.staged:
        for name in git('ls-files', '-z').stdout.decode().split('\0'):
            if name:
                files[name] = git('show', ':' + name).stdout
    else:
        for path in ROOT.rglob('*'):
            relative = path.relative_to(ROOT)
            if any(part in IGNORED for part in relative.parts):
                continue
            if path.is_symlink():
                errors.append(f'{relative}: symlink requires manual provenance review')
            elif path.is_file():
                files[str(relative)] = path.read_bytes()

    def scan(name, raw):
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            if Path(name).suffix.lower() not in ALLOWED_BINARY:
                errors.append(f'{name}: unexpected binary')
            return
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                errors.append(f'{name}: possible {label}; inspect locally (value suppressed)')

    for name, raw in files.items():
        if re.search(r'(?:\.sqlite(?:3)?(?:-\w+)?|\.db(?:-\w+)?|\.env(?:\..*)?|\.pem|\.key)$', name):
            errors.append(f'{name}: runtime database/credential file is not a release artifact')
        scan(name, raw)
    if args.history:
        commits = git('rev-list', '--all', check=False).stdout.decode().splitlines()
        seen = set()
        for commit in commits:
            scan('commit:' + commit, git('show', '-s', '--format=%B', commit).stdout)
            for line in git('ls-tree', '-r', commit).stdout.decode().splitlines():
                metadata, name = line.split('\t', 1)
                _, kind, blob = metadata.split()
                if kind == 'blob' and blob not in seen:
                    seen.add(blob)
                    scan(name, git('cat-file', 'blob', blob).stdout)

    runtime_imports = set()
    for path in (ROOT / 'commonstead').glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                runtime_imports.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                runtime_imports.add(node.module.split('.')[0])
    external = runtime_imports - sys.stdlib_module_names - {'commonstead'}
    if external:
        errors.append('Unrecorded runtime imports: ' + ', '.join(sorted(external)))
    for required in ('LICENSE', 'README.md', 'SECURITY.md', 'CONTRIBUTING.md', 'CHANGELOG.md',
                     'docs/provenance.md', 'docs/coverage.md', 'docs/verification.md', 'docs/continuation.md'):
        if required not in files:
            errors.append(f'Missing required release file: {required}')
    matrix = ROOT / 'docs' / 'portfolio-matrix.csv'
    rows = list(csv.DictReader(matrix.open(newline='')))
    ids = [row['id'] for row in rows]
    if len(ids) != len(set(ids)):
        errors.append('Duplicate portfolio IDs')
    allowed = {'researched','planned','in progress','partial','verified','blocked'}
    for row in rows:
        if row['implementation_status'] not in allowed:
            errors.append(f"Unknown capability status for {row['id']}")
    print(json.dumps({'status':'failed' if errors else 'passed', 'files_scanned':len(files),
                      'history_commits_scanned':len(commits), 'portfolio_rows':len(rows),
                      'third_party_runtime_imports':sorted(external), 'findings':errors,
                      'limits':'Pattern scan and import inventory only; manual provenance/license review is still required.'}, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
