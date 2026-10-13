"""Business and HTTP integration checks against real isolated SQLite databases."""
import csv
import http.client
import io
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from commonstead.database import Database, SCHEMA_VERSION
from commonstead.server import COOKIE, MAX_BODY, Server
from commonstead.service import APIError, CSV_HEADERS, Service, token_hash

PASSWORD = 'test-only-password-42'


class BusinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'crm.sqlite3'
        self.service = Service(self.path)
        self.a_session, self.a_token = self.service.register({'organization': 'North', 'name': 'Alice', 'email': 'same@example.test', 'password': PASSWORD})
        self.b_session, self.b_token = self.service.register({'organization': 'South', 'name': 'Bob', 'email': 'same@example.test', 'password': PASSWORD})
        self.a = self.service.authenticate(self.a_token)
        self.b = self.service.authenticate(self.b_token)

    def fail_api(self, status, function, *args):
        with self.assertRaises(APIError) as caught:
            function(*args)
        self.assertEqual(status, caught.exception.status, caught.exception.message)
        return caught.exception

    def create(self, user, entity, **fields):
        return self.service.create_record(user, entity, fields)['item']

    def invite_user(self, role='member', email='teammate@example.test'):
        invitation = self.service.invite(self.a, {'email': email, 'role': role})
        session, token = self.service.accept_invitation({'token': invitation['token'], 'name': role.title(), 'password': PASSWORD})
        return self.service.authenticate(token), invitation

    def csv_text(self, *rows):
        output = io.StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow(CSV_HEADERS)
        writer.writerows(rows)
        return output.getvalue()

    def test_organization_scoped_login_and_session_secrets(self):
        session, token = self.service.login({'organization': 'south', 'email': 'SAME@example.test', 'password': PASSWORD})
        self.assertEqual(self.b['id'], session['user']['id'])
        with self.service.db.transaction() as db:
            stored = db.execute('SELECT token_hash FROM sessions WHERE token_hash=?', (token_hash(token),)).fetchone()[0]
            password = db.execute('SELECT password_hash FROM users WHERE id=?', (self.b['id'],)).fetchone()[0]
        self.assertNotEqual(stored, token)
        self.assertTrue(password.startswith('pbkdf2_sha256$600000$'))
        self.assertNotIn(PASSWORD, password)
        self.fail_api(401, self.service.login, {'organization': 'missing', 'email': 'same@example.test', 'password': PASSWORD})

    def test_login_throttle_persists_across_reopen(self):
        for _ in range(5):
            self.fail_api(401, self.service.login, {'organization': 'north', 'email': 'same@example.test', 'password': 'incorrect'}, 'test-ip')
        reopened = Service(self.path)
        self.fail_api(429, reopened.login, {'organization': 'north', 'email': 'same@example.test', 'password': PASSWORD}, 'test-ip')

    def test_tenant_list_direct_mutation_search_report_export_and_audit(self):
        account = self.create(self.b, 'accounts', name='South secret')
        self.create(self.b, 'contacts', last_name='Hidden', email='hidden@example.test', account_id=account['id'])
        self.create(self.b, 'leads', last_name='South lead')
        opportunity = self.create(self.b, 'opportunities', name='Secret deal', account_id=account['id'], amount_cents=123450)
        activity = self.create(self.b, 'activities', subject='Secret call', opportunity_id=opportunity['id'], due_date='2000-01-01')
        for entity in ('accounts', 'contacts', 'leads', 'opportunities', 'activities'):
            self.assertEqual(0, self.service.records(self.a, entity, {})['total'])
            self.assertEqual([], self.service.records(self.a, entity, {'q': 'secret'})['items'])
        self.fail_api(404, self.service.get_record, self.a, 'accounts', account['id'])
        self.fail_api(404, self.service.update_record, self.a, 'accounts', account['id'], {'name': 'stolen'})
        self.fail_api(404, self.service.delete_record, self.a, 'activities', activity['id'])
        self.assertTrue(all(value == 0 for value in self.service.pipeline(self.a)['totals'].values()))
        self.assertEqual([list(CSV_HEADERS)], list(csv.reader(io.StringIO(self.service.export_contacts(self.a)))))
        audit = self.service.audit(self.a, {})['items']
        self.assertTrue(all(item['actor_name'] == 'Alice' for item in audit))
        self.assertNotIn('South', json.dumps(audit))

    def test_tenant_foreign_keys_and_assignment_cannot_cross_organizations(self):
        account = self.create(self.b, 'accounts', name='Foreign')
        opportunity = self.create(self.b, 'opportunities', name='Foreign', account_id=account['id'])
        for entity, data in (
            ('contacts', {'last_name': 'Test', 'account_id': account['id']}),
            ('opportunities', {'name': 'Test', 'account_id': account['id']}),
            ('activities', {'subject': 'Test', 'opportunity_id': opportunity['id']}),
            ('activities', {'subject': 'Test', 'assigned_to': self.b['id']}),
            ('accounts', {'name': 'Test', 'owner_id': self.b['id']}),
        ):
            self.fail_api(404, self.service.create_record, self.a, entity, data)
        self.assertEqual([self.a['id']], [row['id'] for row in self.service.members(self.a)['items']])
        self.fail_api(404, self.service.change_role, self.a, self.b['id'], {'role': 'viewer'})

    def test_complete_invitation_crm_pipeline_workflow(self):
        member, invitation = self.invite_user()
        account = self.create(self.a, 'accounts', name='Customer', industry='Engineering')
        self.assertEqual(1, self.service.import_contacts(member, {'csv': self.csv_text(('Jo', 'Smith', 'jo@example.test', '555', 'Manager', 'Customer'))})['imported'])
        lead = self.create(member, 'leads', first_name='Pat', last_name='Jones', status='qualified')
        opportunity = self.create(member, 'opportunities', name='First sale', account_id=account['id'], amount_cents=125000, expected_close='2030-02-20', owner_id=self.a['id'])
        activity = self.create(member, 'activities', subject='Call buyer', assigned_to=self.a['id'], account_id=account['id'], opportunity_id=opportunity['id'], due_date='2000-01-01')
        self.service.update_record(member, 'opportunities', opportunity['id'], {'stage': 'proposal'})
        report = self.service.pipeline(member)
        self.assertEqual(125000, report['totals']['pipeline_cents'])
        self.assertEqual(1, report['totals']['overdue_activities'])
        self.service.update_record(member, 'opportunities', opportunity['id'], {'stage': 'closed_won'})
        self.service.update_record(member, 'activities', activity['id'], {'status': 'done'})
        report = self.service.pipeline(member)
        self.assertEqual(0, report['totals']['pipeline_cents'])
        self.assertEqual(125000, report['totals']['won_cents'])
        self.assertEqual(0, report['totals']['open_activities'])
        self.assertEqual(1, report['totals']['contacts'])
        self.assertEqual(1, report['totals']['leads'])

    def test_role_permissions_escalation_and_last_owner(self):
        member, _ = self.invite_user()
        viewer, _ = self.invite_user('viewer', 'viewer@example.test')
        admin, _ = self.invite_user('admin', 'admin@example.test')
        account = self.create(member, 'accounts', name='Allowed')
        self.assertEqual(1, self.service.records(viewer, 'accounts', {})['total'])
        for role_user in (viewer, member):
            self.fail_api(403, self.service.delete_record, role_user, 'accounts', account['id'])
            self.fail_api(403, self.service.invite, role_user, {'email': 'new@example.test', 'role': 'viewer'})
            self.fail_api(403, self.service.audit, role_user, {})
            self.fail_api(403, self.service.change_role, role_user, role_user['id'], {'role': 'owner'})
        self.fail_api(403, self.service.create_record, viewer, 'accounts', {'name': 'Denied'})
        self.fail_api(403, self.service.update_record, viewer, 'accounts', account['id'], {'name': 'Denied'})
        self.fail_api(403, self.service.import_contacts, viewer, {'csv': self.csv_text(('', 'Denied', '', '', '', ''))})
        self.fail_api(403, self.service.invite, admin, {'email': 'new@example.test', 'role': 'admin'})
        self.fail_api(403, self.service.invite, self.a, {'email': 'new@example.test', 'role': 'owner'})
        self.fail_api(409, self.service.change_role, self.a, self.a['id'], {'role': 'member'})
        self.service.change_role(self.a, member['id'], {'role': 'owner'})
        self.service.change_role(self.a, self.a['id'], {'role': 'member'})
        refreshed = self.service.authenticate(self.a_token)
        self.assertEqual('member', refreshed['role'])
        self.service.delete_record(admin, 'accounts', account['id'])

    def test_invitation_expiry_single_use_and_reissue(self):
        member, used = self.invite_user()
        self.fail_api(404, self.service.invitation_preview, used['token'])
        self.fail_api(404, self.service.accept_invitation, {'token': used['token'], 'name': 'Replay', 'password': PASSWORD})
        first = self.service.invite(self.a, {'email': 'other@example.test', 'role': 'viewer'})
        second = self.service.invite(self.a, {'email': 'other@example.test', 'role': 'member'})
        self.fail_api(404, self.service.invitation_preview, first['token'])
        preview = self.service.invitation_preview(second['token'])
        self.assertEqual('north', preview['organization']['slug'])
        with self.service.db.transaction(True) as db:
            token = db.execute('SELECT token_hash FROM invitations WHERE token_hash=?', (token_hash(second['token']),)).fetchone()[0]
            self.assertNotEqual(second['token'], token)
            db.execute("UPDATE invitations SET expires_at='2000-01-01T00:00:00+00:00' WHERE token_hash=?", (token,))
        self.fail_api(404, self.service.invitation_preview, second['token'])

    def test_strict_validation_and_referenced_delete_rollback(self):
        account = self.create(self.a, 'accounts', name='Required customer')
        opportunity = self.create(self.a, 'opportunities', name='Valid', account_id=account['id'])
        for change in ({'amount_cents': True}, {'amount_cents': -1}, {'amount_cents': 1.2}, {'currency': 'EUR'},
                       {'stage': 'won'}, {'expected_close': '2025-02-30'}, {'name': []}, {'organization_id': self.b['organization_id']}):
            self.fail_api(400, self.service.update_record, self.a, 'opportunities', opportunity['id'], change)
        before = self.service.audit(self.a, {})['total']
        self.fail_api(409, self.service.delete_record, self.a, 'accounts', account['id'])
        self.assertEqual(before, self.service.audit(self.a, {})['total'])
        self.assertEqual(account['id'], self.service.get_record(self.a, 'accounts', account['id'])['item']['id'])
        self.fail_api(400, self.service.create_record, self.a, 'contacts', {'last_name': ''})
        self.fail_api(400, self.service.create_record, self.a, 'accounts', {'name': 'x', 'extra': 'unknown'})

    def test_import_is_atomic_tenant_scoped_and_duplicate_safe(self):
        self.create(self.b, 'accounts', name='Only South')
        before = self.service.audit(self.a, {})['total']
        bad = self.csv_text(('', 'Valid', 'valid@example.test', '', '', ''), ('', 'Foreign', 'other@example.test', '', '', 'Only South'))
        self.fail_api(400, self.service.import_contacts, self.a, {'csv': bad})
        self.assertEqual(0, self.service.records(self.a, 'contacts', {})['total'])
        self.assertEqual(before, self.service.audit(self.a, {})['total'])
        duplicate = self.csv_text(('', 'One', 'one@example.test', '', '', ''), ('', 'Two', 'ONE@example.test', '', '', ''))
        self.fail_api(400, self.service.import_contacts, self.a, {'csv': duplicate})
        self.create(self.a, 'contacts', last_name='Existing', email='one@example.test')
        self.fail_api(400, self.service.import_contacts, self.a, {'csv': self.csv_text(('', 'One', 'one@example.test', '', '', ''))})
        self.fail_api(400, self.service.import_contacts, self.a, {'csv': 'last_name,email\nSmith,a@example.test\n'})
        oversized = self.csv_text(*[('', 'Contact', '', '', '', '') for _ in range(1001)])
        self.fail_api(400, self.service.import_contacts, self.a, {'csv': oversized})

    def test_export_formula_sanitization_and_search_pagination(self):
        self.create(self.a, 'contacts', first_name='=1+1', last_name='100% real', phone='+123', title='@SUM(A1)')
        self.create(self.a, 'contacts', last_name='100 other')
        rows = list(csv.reader(io.StringIO(self.service.export_contacts(self.a))))
        dangerous = next(row for row in rows[1:] if row[1] == '100% real')
        self.assertEqual("'=1+1", dangerous[0])
        self.assertEqual("'+123", dangerous[3])
        self.assertEqual("'@SUM(A1)", dangerous[4])
        self.assertEqual(1, self.service.records(self.a, 'contacts', {'q': '%'})['total'])
        page = self.service.records(self.a, 'contacts', {'limit': '1', 'offset': '1'})
        self.assertEqual(2, page['total'])
        self.assertEqual(1, len(page['items']))
        self.fail_api(400, self.service.records, self.a, 'contacts', {'limit': '201'})

    def test_persistence_migrations_foreign_constraints_and_audit_secrets(self):
        account = self.create(self.a, 'accounts', name='Persistent')
        reopened = Service(self.path)
        user = reopened.authenticate(self.a_token)
        self.assertEqual('Persistent', reopened.get_record(user, 'accounts', account['id'])['item']['name'])
        Database(self.path)
        with reopened.db.transaction() as db:
            self.assertEqual(SCHEMA_VERSION, db.execute('PRAGMA user_version').fetchone()[0])
            self.assertEqual(1, db.execute('PRAGMA foreign_keys').fetchone()[0])
        with self.assertRaises(sqlite3.IntegrityError):
            with reopened.db.transaction(True) as db:
                db.execute('UPDATE accounts SET owner_id=? WHERE id=?', (self.b['id'], account['id']))
        self.assertEqual(self.a['id'], reopened.get_record(user, 'accounts', account['id'])['item']['owner_id'])
        raw_audit = json.dumps(reopened.audit(user, {}))
        self.assertNotIn(PASSWORD, raw_audit)
        self.assertNotIn(self.a_token, raw_audit)
        self.assertNotIn(self.a_session['csrf_token'], raw_audit)
        self.service.logout(self.a)
        self.assertIsNone(self.service.authenticate(self.a_token))


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.server = Server(('127.0.0.1', 0), Path(cls.temp.name) / 'http.sqlite3')
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.temp.cleanup()

    def request(self, method, path, data=None, headers=None, raw=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        all_headers = {'Content-Type': 'application/json'}
        all_headers.update(headers or {})
        body = raw if raw is not None else json.dumps(data).encode() if data is not None else None
        connection.request(method, path, body=body, headers=all_headers)
        response = connection.getresponse()
        raw_body = response.read()
        result = (response.status, dict(response.getheaders()), json.loads(raw_body) if raw_body and response.getheader('Content-Type', '').startswith('application/json') else raw_body)
        connection.close()
        return result

    def register(self):
        name = self._testMethodName
        status, headers, body = self.request('POST', '/api/register', {'organization': name.replace('_', '-'), 'name': 'HTTP Owner', 'email': 'owner@example.test', 'password': PASSWORD}, {'Origin': f'http://127.0.0.1:{self.server.server_port}'})
        self.assertEqual(201, status, body)
        return {'Cookie': headers['Set-Cookie'].split(';', 1)[0], 'X-CSRF-Token': body['csrf_token']}, headers, body

    def test_http_cookie_csrf_origin_and_host_boundaries(self):
        auth, headers, session = self.register()
        self.assertIn('HttpOnly', headers['Set-Cookie'])
        self.assertIn('SameSite=Strict', headers['Set-Cookie'])
        self.assertIn('Max-Age=43200', headers['Set-Cookie'])
        status, _, body = self.request('GET', '/api/session', headers=auth)
        self.assertTrue(body['authenticated'])
        for headers, expected in (
            ({'Cookie': auth['Cookie']}, 403),
            ({**auth, 'X-CSRF-Token': 'wrong'}, 403),
            ({**auth, 'Origin': 'https://evil.example'}, 403),
            ({**auth, 'Sec-Fetch-Site': 'cross-site'}, 403),
            ({**auth, 'Host': 'evil.example'}, 403),
        ):
            self.assertEqual(expected, self.request('POST', '/api/records/accounts', {'name': 'Blocked'}, headers)[0])
        self.assertEqual(0, self.request('GET', '/api/records/accounts', headers=auth)[2]['total'])
        status, _, account = self.request('POST', '/api/records/accounts', {'name': 'HTTP success'}, auth)
        self.assertEqual(201, status)
        self.assertEqual(200, self.request('PATCH', '/api/records/accounts/' + account['item']['id'], {'industry': 'Tests'}, auth)[0])
        status, headers, body = self.request('POST', '/api/logout', {}, auth)
        self.assertEqual(200, status)
        self.assertIn('Max-Age=0', headers['Set-Cookie'])
        self.assertFalse(self.request('GET', '/api/session', headers=auth)[2]['authenticated'])

    def test_unauthenticated_origin_guards_and_content_validation(self):
        for endpoint in ('/api/register', '/api/login', '/api/invitations/accept'):
            self.assertEqual(403, self.request('POST', endpoint, {}, {'Origin': 'null'})[0])
            self.assertEqual(403, self.request('POST', endpoint, {}, {'Origin': 'http://evil.example'})[0])
        self.assertEqual(415, self.request('POST', '/api/login', {}, {'Content-Type': 'text/plain'})[0])
        # The server rejects the declared length before reading any oversized bytes.
        self.assertEqual(413, self.request('POST', '/api/login', raw=b'', headers={'Content-Length': str(MAX_BODY + 1)})[0])
        self.assertEqual(400, self.request('POST', '/api/login', raw=b'{"organization":"one","organization":"two"}')[0])
        self.assertEqual(400, self.request('POST', '/api/login', raw=b'{"password":NaN}')[0])
        self.assertEqual(400, self.request('POST', '/api/login', raw=b'[]')[0])
        self.assertEqual(400, self.request('POST', '/api/login', raw=b'{"password":"\\ud800"}')[0])
        self.assertEqual(401, self.request('GET', '/api/records/accounts')[0])

    def test_health_security_headers_and_static_traversal(self):
        status, headers, body = self.request('GET', '/health')
        self.assertEqual(200, status)
        self.assertEqual('0.1.0', body['version'])
        self.assertEqual(1, body['schema_version'])
        self.assertIn("script-src 'self'", headers['Content-Security-Policy'])
        self.assertNotIn('unsafe-inline', headers['Content-Security-Policy'])
        self.assertEqual('no-store', headers['Cache-Control'])
        self.assertEqual('nosniff', headers['X-Content-Type-Options'])
        self.assertEqual(404, self.request('GET', '/../../service.py')[0])
        self.assertEqual(404, self.request('GET', '/%2e%2e/%2e%2e/service.py')[0])
        self.assertEqual(403, self.request('GET', '/health', headers={'Host': f'localhost:{self.server.server_port + 1}'})[0])


if __name__ == '__main__':
    unittest.main()
