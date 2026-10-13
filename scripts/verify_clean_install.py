#!/usr/bin/env python3
"""Verify source-only installation, real HTTP and restart persistence in isolation.

Creates a temporary standard-library venv without pip, copies only the application
source and static assets, and runs its probe with isolated Python (-I). No database,
credentials, environment files or logs are retained. Requires local socket access.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv


PROBE = r'''
import http.client
import importlib.metadata
import json
from pathlib import Path
import secrets
import site
import sqlite3
import sys
import threading

source, database = map(Path, sys.argv[1:3])
assert sys.flags.isolated == 1
assert not site.ENABLE_USER_SITE
assert sys.prefix != sys.base_prefix
distributions = sorted(distribution.metadata['Name'] for distribution in importlib.metadata.distributions())
assert distributions == [], distributions
sys.path.insert(0, str(source))
import commonstead
from commonstead.server import Server
assert Path(commonstead.__file__).resolve().is_relative_to(source.resolve())

def request(server, method, path, data=None, authentication=None):
    connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=15)
    headers = {'Content-Type': 'application/json', 'Origin': f'http://127.0.0.1:{server.server_port}'}
    headers.update(authentication or {})
    try:
        connection.request(method, path, body=None if data is None else json.dumps(data), headers=headers)
        response = connection.getresponse()
        raw = response.read()
        result = json.loads(raw) if 'application/json' in response.getheader('Content-Type', '') else raw
        return response.status, dict(response.getheaders()), result
    finally:
        connection.close()

def start():
    server = Server(('127.0.0.1', 0), str(database))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread

def stop(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(timeout=10)
    assert not thread.is_alive()

password = secrets.token_urlsafe(24)
server, thread = start()
try:
    status, headers, health = request(server, 'GET', '/health')
    assert status == 200 and health['status'] == 'ok', (status, health)
    status, headers, session = request(server, 'POST', '/api/register', {
        'organization': 'Isolated Verification', 'name': 'Verification Owner',
        'email': 'verification@example.test', 'password': password})
    assert status == 201 and session['authenticated'], status
    authentication = {'Cookie': headers['Set-Cookie'].split(';', 1)[0], 'X-CSRF-Token': session['csrf_token']}
    status, _, account = request(server, 'POST', '/api/records/accounts', {'name': 'Persisted isolated account'}, authentication)
    assert status == 201, (status, account)
    account_id = account['item']['id']
    status, _, html = request(server, 'GET', '/')
    assert status == 200 and b'<html' in html.lower(), status
finally:
    stop(server, thread)

server, thread = start()
try:
    status, headers, session = request(server, 'POST', '/api/login', {
        'organization': 'isolated-verification', 'email': 'verification@example.test', 'password': password})
    assert status == 200 and session['authenticated'], status
    authentication = {'Cookie': headers['Set-Cookie'].split(';', 1)[0], 'X-CSRF-Token': session['csrf_token']}
    status, _, account = request(server, 'GET', '/api/records/accounts/' + account_id, authentication=authentication)
    assert status == 200 and account['item']['name'] == 'Persisted isolated account', (status, account)
    status, _, listing = request(server, 'GET', '/api/records/accounts', authentication=authentication)
    assert status == 200 and listing['total'] == 1, (status, listing)
finally:
    stop(server, thread)

print(json.dumps({
    'status': 'passed', 'python': sys.version.split()[0], 'sqlite': sqlite3.sqlite_version,
    'isolated_python': bool(sys.flags.isolated), 'user_site_enabled': site.ENABLE_USER_SITE,
    'third_party_distributions': distributions, 'application_version': commonstead.__version__,
    'checks': ['fresh_source_copy', 'venv_without_pip', 'health_http', 'static_html_http',
               'registration_http', 'account_create_http', 'server_restart', 'login_http',
               'persisted_account_http', 'no_third_party_distributions']
}, sort_keys=True))
'''


def main():
    project = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='commonstead-install-') as directory:
        workspace = Path(directory)
        source = workspace / 'source'
        package = source / 'commonstead'
        package.mkdir(parents=True)
        for file in sorted((project / 'commonstead').glob('*.py')):
            shutil.copy2(file, package / file.name)
        shutil.copytree(project / 'commonstead' / 'static', package / 'static',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
        environment = workspace / 'venv'
        venv.EnvBuilder(with_pip=False, system_site_packages=False).create(environment)
        interpreter = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        child_environment = {key: value for key, value in os.environ.items()
                             if not key.startswith('PYTHON') and key != 'VIRTUAL_ENV'}
        result = subprocess.run([str(interpreter), '-I', '-c', PROBE, str(source), str(workspace / 'data.sqlite3')],
                                cwd=workspace, env=child_environment, capture_output=True, text=True, timeout=90)
        if result.returncode:
            print('Clean-install verification failed:', file=sys.stderr)
            print(result.stderr.strip(), file=sys.stderr)
            return result.returncode
        report = json.loads(result.stdout)
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
