"""Independent adversarial checks: real SQLite state and local HTTP requests.

Run with: python -m unittest discover -s tests -p test_security_review.py -v
Fixtures are fictional. No external service or network endpoint is used.
"""
import concurrent.futures
import csv
import http.client
import io
import json
import os
import socket
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from commonstead import database
from commonstead.server import COOKIE, MAX_BODY, Server
from commonstead.service import APIError, CSV_HEADERS, Service

PASSWORD = 'Fictional review password 2026!'


def registration(slug):
    return {'organization': slug, 'slug': slug, 'name': 'Fictional Reviewer',
            'email': f'owner@{slug}.example', 'password': PASSWORD}


class ServiceSecurityReview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'review.sqlite3'
        self.service = Service(self.path)
        self.alpha, self.alpha_token = self.service.register(registration('alpha'))
        self.beta, self.beta_token = self.service.register(registration('beta'))
        self.a = self.service.authenticate(self.alpha_token)
        self.b = self.service.authenticate(self.beta_token)

    def denied(self, status, operation, *args):
        with self.assertRaises(APIError) as caught:
            operation(*args)
        self.assertEqual(status, caught.exception.status)
        return caught.exception

    def invite_user(self, role='member', email='reviewer@alpha.example'):
        invite = self.service.invite(self.a, {'email': email, 'role': role})
        result, token = self.service.accept_invitation(
            {'token': invite['token'], 'name': 'Invited Reviewer', 'password': PASSWORD})
        return result, token, self.service.authenticate(token)

    def test_tenant_ids_cannot_be_injected_or_related(self):
        foreign_account = self.service.create_record(self.b, 'accounts', {'name': 'Beta secret'})['item']
        for operation, args in (
            (self.service.get_record, (self.a, 'accounts', foreign_account['id'])),
            (self.service.update_record, (self.a, 'accounts', foreign_account['id'], {'name': 'Intrusion'})),
            (self.service.delete_record, (self.a, 'accounts', foreign_account['id'])),
            (self.service.create_record, (self.a, 'contacts', {'last_name': 'Tester', 'account_id': foreign_account['id']})),
            (self.service.create_record, (self.a, 'accounts', {'name': 'Intrusion', 'owner_id': self.b['id']})),
            (self.service.change_role, (self.a, self.b['id'], {'role': 'viewer'})),
        ):
            with self.subTest(operation=operation.__name__, args=args[1:]):
                self.denied(404, operation, *args)
        self.denied(400, self.service.create_record, self.a, 'accounts',
                    {'name': 'Intrusion', 'organization_id': self.b['organization_id']})
        self.assertEqual('Beta secret', self.service.get_record(self.b, 'accounts', foreign_account['id'])['item']['name'])

    def test_search_reports_exports_and_audit_are_tenant_scoped(self):
        account = self.service.create_record(self.b, 'accounts', {'name': 'BetaMarker'})['item']
        self.service.create_record(self.b, 'contacts', {'last_name': 'BetaMarker'})
        self.service.create_record(self.b, 'opportunities',
                                   {'name': 'BetaMarker', 'account_id': account['id'], 'amount_cents': 12345})
        self.assertEqual(0, self.service.records(self.a, 'accounts', {'q': 'BetaMarker'})['total'])
        self.assertEqual(0, self.service.pipeline(self.a)['totals']['pipeline_cents'])
        self.assertNotIn('BetaMarker', self.service.export_contacts(self.a))
        self.assertNotIn(account['id'], json.dumps(self.service.audit(self.a, {})))

    def test_demotion_applies_to_an_existing_session(self):
        result, token, member = self.invite_user('admin')
        self.service.change_role(self.a, member['id'], {'role': 'viewer'})
        refreshed = self.service.authenticate(token)
        self.assertEqual('viewer', refreshed['role'])
        for operation, args in (
            (self.service.create_record, (refreshed, 'accounts', {'name': 'Denied'})),
            (self.service.invite, (refreshed, {'email': 'x@alpha.example', 'role': 'member'})),
            (self.service.audit, (refreshed, {})),
            (self.service.change_role, (refreshed, member['id'], {'role': 'owner'})),
        ):
            self.denied(403, operation, *args)
        self.assertEqual([], self.service.records(refreshed, 'accounts', {})['items'])

    def test_admin_cannot_create_an_admin_or_owner(self):
        _, _, admin = self.invite_user('admin')
        for role in ('admin', 'owner'):
            self.denied(403, self.service.invite, admin, {'email': 'x@alpha.example', 'role': role})
        self.denied(403, self.service.change_role, admin, admin['id'], {'role': 'owner'})

    def test_last_owner_transition_is_serialized(self):
        _, token, member = self.invite_user()
        self.service.change_role(self.a, member['id'], {'role': 'owner'})
        owner_two = self.service.authenticate(token)
        barrier = threading.Barrier(2)

        def demote(user):
            barrier.wait(timeout=5)
            try:
                self.service.change_role(user, user['id'], {'role': 'viewer'})
                return 'changed'
            except APIError as error:
                return error.code

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(demote, (self.a, owner_two)))
        self.assertCountEqual(['changed', 'last_owner'], results)
        with self.service.db.transaction() as connection:
            count = connection.execute("SELECT count(*) FROM users WHERE organization_id=? AND role='owner'",
                                       (self.a['organization_id'],)).fetchone()[0]
        self.assertEqual(1, count)

    def test_invitation_is_single_use_even_with_simultaneous_acceptance(self):
        invitation = self.service.invite(self.a, {'email': 'race@alpha.example', 'role': 'viewer'})
        barrier = threading.Barrier(2)

        def accept(_):
            barrier.wait(timeout=5)
            try:
                result, _ = self.service.accept_invitation(
                    {'token': invitation['token'], 'name': 'Race Reviewer', 'password': PASSWORD})
                return result['user']['role']
            except APIError as error:
                return error.code

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(accept, range(2)))
        self.assertCountEqual(['viewer', 'invitation_unavailable'], results)
        self.assertEqual(1, sum(user['email'] == 'race@alpha.example' for user in self.service.members(self.a)['items']))

    def test_invitation_reissue_and_expiry_disable_old_tokens(self):
        first = self.service.invite(self.a, {'email': 'replace@alpha.example', 'role': 'admin'})
        second = self.service.invite(self.a, {'email': 'replace@alpha.example', 'role': 'viewer'})
        self.denied(404, self.service.invitation_preview, first['token'])
        self.assertEqual('viewer', self.service.invitation_preview(second['token'])['role'])
        with self.service.db.transaction(True) as connection:
            connection.execute("UPDATE invitations SET expires_at='2000-01-01T00:00:00+00:00'")
        self.denied(404, self.service.accept_invitation,
                    {'token': second['token'], 'name': 'Expired', 'password': PASSWORD})

    def test_import_rolls_back_records_and_audit_on_a_late_bad_row(self):
        header = ','.join(CSV_HEADERS) + '\n'
        payloads = (
            header + 'A,First,same@alpha.example,,,\nB,Second,same@alpha.example,,,\n',
            header + 'A,First,first@alpha.example,,,\nB,Second,second@alpha.example,,,Missing account\n',
            header + 'A,First,first@alpha.example,,,\nB,,second@alpha.example,,,\n',
        )
        initial_audit = self.service.audit(self.a, {})['total']
        for raw in payloads:
            with self.subTest(csv=raw):
                self.denied(400, self.service.import_contacts, self.a, {'csv': raw})
                self.assertEqual(0, self.service.records(self.a, 'contacts', {})['total'])
                self.assertEqual(initial_audit, self.service.audit(self.a, {})['total'])

    def test_csv_formula_values_are_escaped_in_each_exported_column(self):
        account = self.service.create_record(self.a, 'accounts', {'name': '=1+1'})['item']
        self.service.create_record(self.a, 'contacts', {
            'first_name': '=1+1', 'last_name': '+SUM(1,1)', 'email': '=formula@alpha.example',
            'phone': '-1+2', 'title': '@SUM(1,1)', 'account_id': account['id']})
        rows = list(csv.reader(io.StringIO(self.service.export_contacts(self.a))))
        self.assertEqual(list(CSV_HEADERS), rows[0])
        self.assertTrue(all(cell.startswith("'") for cell in rows[1]), rows[1])

    def test_money_and_dates_reject_ambiguous_or_out_of_range_inputs(self):
        account = self.service.create_record(self.a, 'accounts', {'name': 'Bounds'})['item']
        for amount in (True, False, 1.25, -1, 9_000_000_000_001, '100', None):
            self.denied(400, self.service.create_record, self.a, 'opportunities',
                        {'name': 'Bounds', 'account_id': account['id'], 'amount_cents': amount})
        for value in ('2026-02-29', '2026-1-01', '20260101', '2026-W01-1', '0000-01-01', '2026-01-01Z'):
            self.denied(400, self.service.create_record, self.a, 'activities', {'subject': 'Bounds', 'due_date': value})
        valid = self.service.create_record(self.a, 'opportunities',
                                          {'name': 'Valid', 'account_id': account['id'],
                                           'amount_cents': 9_000_000_000_000, 'expected_close': '2028-02-29'})
        self.assertEqual(9_000_000_000_000, valid['item']['amount_cents'])

    def test_opportunity_account_move_cannot_invalidate_linked_activity(self):
        first = self.service.create_record(self.a, 'accounts', {'name': 'First account'})['item']
        second = self.service.create_record(self.a, 'accounts', {'name': 'Second account'})['item']
        opportunity = self.service.create_record(self.a, 'opportunities',
                                                 {'name': 'Linked deal', 'account_id': first['id']})['item']
        activity = self.service.create_record(self.a, 'activities',
                                              {'subject': 'Linked task', 'account_id': first['id'],
                                               'opportunity_id': opportunity['id']})['item']
        self.denied(409, self.service.update_record, self.a, 'opportunities', opportunity['id'],
                    {'account_id': second['id']})
        self.assertEqual(first['id'], self.service.get_record(self.a, 'opportunities', opportunity['id'])['item']['account_id'])
        self.assertEqual(first['id'], self.service.get_record(self.a, 'activities', activity['id'])['item']['account_id'])

    def test_schema_failure_rolls_back_all_tables_and_version(self):
        path = Path(self.temp.name) / 'failed.sqlite3'
        with patch.object(database, 'SCHEMA', database.SCHEMA + '; INVALID SQL HERE;'):
            with self.assertRaises(sqlite3.Error):
                database.Database(path)
        connection = sqlite3.connect(path)
        try:
            self.assertEqual(0, connection.execute('PRAGMA user_version').fetchone()[0])
            self.assertEqual([], connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
        finally:
            connection.close()

    @unittest.skipUnless(os.name == 'posix', 'POSIX mode-bit test')
    def test_database_and_journal_files_are_private_without_cli_umask(self):
        path = Path(self.temp.name) / 'permissions.sqlite3'
        previous_umask = os.umask(0o022)
        try:
            db = database.Database(path)
            with db.transaction(True) as connection:
                connection.execute("INSERT INTO organizations VALUES ('mode-test','Mode test','mode-test','2026-10-12')")
                for file in Path(self.temp.name).glob('permissions.sqlite3*'):
                    self.assertEqual(0, file.stat().st_mode & 0o077, str(file))
        finally:
            os.umask(previous_umask)


class HTTPSecurityReview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = Server(('127.0.0.1', 0), Path(self.temp.name) / 'http.sqlite3')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_port
        self.host = f'127.0.0.1:{self.port}'
        self.cookie = None
        self.csrf = None
        status, headers, result = self.request('POST', '/api/register', registration('http-alpha'))
        self.assertEqual(201, status)
        self.cookie = headers['Set-Cookie'].split(';', 1)[0]
        self.csrf = result['csrf_token']
        self.user_id = result['user']['id']

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    def request(self, method, path, data=None, headers=None, raw=None, auth=True):
        outgoing = {'Content-Type': 'application/json'}
        if auth and self.cookie:
            outgoing['Cookie'] = self.cookie
        if auth and self.csrf:
            outgoing['X-CSRF-Token'] = self.csrf
        outgoing.update(headers or {})
        body = raw if raw is not None else json.dumps(data).encode() if data is not None else None
        client = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        try:
            client.request(method, path, body, outgoing)
            response = client.getresponse()
            payload = response.read()
            content_type = response.getheader('Content-Type', '')
            result = json.loads(payload) if payload and 'application/json' in content_type else payload
            return response.status, dict(response.getheaders()), result
        finally:
            client.close()

    def wire(self, lines, body=b''):
        raw = ('\r\n'.join(lines) + '\r\n\r\n').encode('latin-1') + body
        with socket.create_connection(('127.0.0.1', self.port), timeout=5) as connection:
            connection.sendall(raw)
            connection.shutdown(socket.SHUT_WR)
            chunks = []
            while True:
                chunk = connection.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
        response = b''.join(chunks)
        return int(response.split(b' ', 2)[1]), response

    def test_auth_cookie_security_and_logout_revocation(self):
        status, headers, result = self.request('POST', '/api/login',
                                               {'organization': 'http-alpha', 'email': 'owner@http-alpha.example', 'password': PASSWORD})
        self.assertEqual(200, status)
        self.assertIn('HttpOnly', headers['Set-Cookie'])
        self.assertIn('SameSite=Strict', headers['Set-Cookie'])
        self.assertNotIn('password_hash', json.dumps(result))
        self.assertEqual(200, self.request('POST', '/api/logout', {})[0])
        self.assertEqual(401, self.request('GET', '/api/members')[0])

    def test_origin_host_variants_fail_closed(self):
        for origin in ('null', 'https://' + self.host, 'http://attacker.example', 'http://' + self.host + '.attacker.example'):
            status, _, _ = self.request('POST', '/api/records/accounts', {'name': 'Denied'}, {'Origin': origin})
            self.assertEqual(403, status, origin)
        for host in ('attacker.example', f'127.0.0.1:{self.port + 1}', 'localhost@attacker.example', 'localhost/evil'):
            status, _, _ = self.request('GET', '/api/session', headers={'Host': host})
            self.assertIn(status, (400, 403), host)
        self.assertEqual(403, self.request('POST', '/api/records/accounts', {'name': 'Denied'}, {'Sec-Fetch-Site': 'cross-site'})[0])
        self.assertEqual(201, self.request('POST', '/api/records/accounts', {'name': 'Allowed'}, {'Origin': 'http://' + self.host})[0])

    def test_duplicate_host_and_origin_headers_are_rejected(self):
        status, _ = self.wire(['GET /api/session HTTP/1.1', f'Host: {self.host}', 'Host: attacker.example'])
        self.assertEqual(400, status)
        status, _ = self.wire(['POST /api/login HTTP/1.1', f'Host: {self.host}',
                               f'Origin: http://{self.host}', 'Origin: http://attacker.example',
                               'Content-Type: application/json', 'Content-Length: 2'], b'{}')
        self.assertEqual(403, status)

    def test_non_ascii_csrf_is_a_client_error(self):
        status, _, _ = self.request('POST', '/api/records/accounts', {'name': 'Denied'}, {'X-CSRF-Token': '\xe9'})
        self.assertEqual(403, status)

    def test_malformed_json_and_wrong_media_type_are_rejected(self):
        for raw in (b'{"name":"first","name":"second"}', b'{"name":NaN}', b'{"name":"\\ud800"}', b'[]', b'{'):
            self.assertEqual(400, self.request('POST', '/api/records/accounts', raw=raw)[0], raw)
        self.assertEqual(415, self.request('POST', '/api/records/accounts', {'name': 'Denied'}, {'Content-Type': 'text/plain'})[0])

    def test_ambiguous_framing_and_incomplete_bodies_are_rejected(self):
        prefix = ['POST /api/login HTTP/1.1', f'Host: {self.host}', 'Content-Type: application/json']
        variants = (
            ['Content-Length: 2', 'Content-Length: 2'],
            ['Content-Length: 2', 'Transfer-Encoding: chunked'],
            ['Content-Length: 2', 'Transfer-Encoding:'],
            ['Content-Length: 2', 'Transfer-Encoding:', 'Transfer-Encoding: chunked'],
            ['Content-Length: 3'],
            ['Content-Length: -1'],
        )
        for framing in variants:
            with self.subTest(framing=framing):
                status, response = self.wire(prefix + framing, b'{}')
                self.assertEqual(400, status, response)
                if any('Transfer-Encoding:' in value for value in framing):
                    self.assertIn(b'invalid_body', response)
        status, _ = self.wire(prefix + [f'Content-Length: {MAX_BODY + 1}'])
        self.assertEqual(413, status)

    def test_invitation_acceptance_replaces_only_the_browser_session_identity(self):
        service = self.server.service
        _, beta_token = service.register(registration('http-beta'))
        beta = service.authenticate(beta_token)
        invite = service.invite(beta, {'email': 'guest@http-beta.example', 'role': 'viewer'})
        status, headers, result = self.request('POST', '/api/invitations/accept',
                                               {'token': invite['token'], 'name': 'Guest', 'password': PASSWORD})
        self.assertEqual(201, status)
        self.assertEqual('http-beta', result['organization']['slug'])
        self.assertEqual('viewer', result['user']['role'])
        self.assertNotEqual(self.cookie, headers['Set-Cookie'].split(';', 1)[0])
        self.cookie = headers['Set-Cookie'].split(';', 1)[0]
        self.csrf = result['csrf_token']
        self.assertEqual(403, self.request('POST', '/api/records/accounts', {'name': 'Denied'})[0])

    def test_in_flight_write_cannot_use_a_role_revoked_before_its_transaction(self):
        service = self.server.service
        owner = service.authenticate(self.cookie.split('=', 1)[1])
        invite = service.invite(owner, {'email': 'admin@http-alpha.example', 'role': 'admin'})
        _, admin_token = service.accept_invitation({'token': invite['token'], 'name': 'Admin', 'password': PASSWORD})
        admin = service.authenticate(admin_token)
        checked = threading.Event()
        continue_request = threading.Event()
        original_authenticate = service.authenticate

        def delayed_authenticate(token):
            user = original_authenticate(token)
            if token == admin_token:
                checked.set()
                if not continue_request.wait(timeout=5):
                    raise AssertionError('Review request did not resume')
            return user

        with patch.object(service, 'authenticate', delayed_authenticate):
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pending = pool.submit(self.request, 'POST', '/api/records/accounts', {'name': 'Revoked write'},
                                      {'Cookie': f'{COOKIE}={admin_token}', 'X-CSRF-Token': admin['csrf_token']})
                try:
                    self.assertTrue(checked.wait(timeout=5))
                    service.change_role(owner, admin['id'], {'role': 'viewer'})
                finally:
                    continue_request.set()
                status, _, _ = pending.result(timeout=5)
        self.assertEqual(403, status)

    def test_static_traversal_does_not_expose_database_or_source(self):
        for path in ('/../database.py', '/%2e%2e/database.py', '/%2e%2e/%2e%2e/http.sqlite3', '/api/records/accounts?limit=1&limit=2'):
            self.assertIn(self.request('GET', path)[0], (400, 404), path)


if __name__ == '__main__':
    unittest.main()
