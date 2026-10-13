"""Tenant-scoped CRM operations; each mutation and audit event share a transaction."""
import csv
import hashlib
import hmac
import io
import json
import re
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone

from .database import Database

ITERATIONS = 600_000
SESSION_HOURS = 12
STAGES = ('prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost')
CSV_HEADERS = ('first_name', 'last_name', 'email', 'phone', 'title', 'account_name')
FIELDS = {
    'accounts': ('name', 'website', 'industry', 'owner_id', 'notes'),
    'contacts': ('first_name', 'last_name', 'email', 'phone', 'title', 'account_id', 'owner_id', 'notes'),
    'leads': ('first_name', 'last_name', 'email', 'company', 'status', 'owner_id', 'notes'),
    'opportunities': ('name', 'account_id', 'amount_cents', 'currency', 'stage', 'expected_close', 'owner_id', 'notes'),
    'activities': ('subject', 'kind', 'status', 'due_date', 'assigned_to', 'account_id', 'opportunity_id', 'notes'),
}
REQUIRED = {'accounts': ('name',), 'contacts': ('last_name',), 'leads': ('last_name',),
            'opportunities': ('name', 'account_id'), 'activities': ('subject',)}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def future(**kwargs):
    return (datetime.now(timezone.utc) + timedelta(**kwargs)).isoformat(timespec='seconds')


def identifier():
    return str(uuid.uuid4())


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


class APIError(Exception):
    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details

    def body(self):
        result = {'error': {'code': self.code, 'message': self.message}}
        if self.details is not None:
            result['error']['details'] = self.details
        return result


def invalid(message, details=None):
    raise APIError(400, 'validation_error', message, details)


def object_fields(data, fields, required=()):
    if not isinstance(data, dict):
        invalid('A JSON object is required.')
    unknown = set(data) - set(fields)
    if unknown:
        invalid('Unknown fields.', {'fields': sorted(unknown)})
    for field in required:
        if field not in data:
            invalid(f'{field} is required.')


def text_value(value, field, required=False, maximum=250):
    if not isinstance(value, str):
        invalid(f'{field} must be text.')
    value = value.strip()
    if len(value) > maximum or (required and not value):
        invalid(f'{field} must contain {"1" if required else "0"} to {maximum} characters.')
    if '\x00' in value or any(ord(char) < 32 and char not in '\n\r\t' for char in value):
        invalid(f'{field} contains unsupported control characters.')
    return value


def email_value(value, required=False):
    value = text_value(value, 'email', required, 254).lower()
    if value and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
        invalid('Enter a valid email address.')
    return value


def password_hash(password):
    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        invalid('Password must contain 12 to 128 characters.')
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt}${digest.hex()}'


def verify_password(password, encoded):
    if not isinstance(password, str) or len(password) > 128:
        return False
    algorithm, iterations, salt, digest = encoded.split('$')
    calculated = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(iterations))
    return algorithm == 'pbkdf2_sha256' and hmac.compare_digest(calculated.hex(), digest)


def public_user(user):
    return {key: user[key] for key in ('id', 'name', 'email', 'role')}


def record_dict(row):
    return {key: row[key] for key in row.keys() if key != 'organization_id'}


class Service:
    def __init__(self, path):
        self.db = Database(path)
        # A fixed, valid dummy hash equalizes nonexistent-user password checks.
        self.dummy_hash = f'pbkdf2_sha256${ITERATIONS}$' + ('00' * 16) + '$' + ('00' * 32)

    def _audit(self, connection, user, action, entity, entity_id, details=None):
        connection.execute('INSERT INTO audit VALUES (?,?,?,?,?,?,?,?,?)',
                           (identifier(), user['organization_id'], user['id'], user['name'], action,
                            entity, entity_id, json.dumps(details or {}, sort_keys=True), now()))

    def _session(self, connection, user):
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        connection.execute('DELETE FROM sessions WHERE expires_at <= ?', (now(),))
        connection.execute('INSERT INTO sessions VALUES (?,?,?,?)',
                           (token_hash(token), user['id'], csrf, future(hours=SESSION_HOURS)))
        org = connection.execute('SELECT id,name,slug FROM organizations WHERE id=?',
                                 (user['organization_id'],)).fetchone()
        return {'authenticated': True, 'user': public_user(user), 'organization': dict(org),
                'csrf_token': csrf}, token

    def authenticate(self, token):
        if not isinstance(token, str) or not token or len(token) > 200:
            return None
        with self.db.transaction() as connection:
            row = connection.execute('''SELECT u.*,s.csrf_token,s.token_hash FROM sessions s
                JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?''',
                                     (token_hash(token), now())).fetchone()
            return dict(row) if row else None

    def session(self, user):
        if not user:
            return {'authenticated': False}
        with self.db.transaction() as connection:
            org = connection.execute('SELECT id,name,slug FROM organizations WHERE id=?',
                                     (user['organization_id'],)).fetchone()
            return {'authenticated': True, 'user': public_user(user), 'organization': dict(org),
                    'csrf_token': user['csrf_token']}

    def require(self, user, roles=None):
        if not user:
            raise APIError(401, 'authentication_required', 'Sign in to an organization first.')
        if roles and user['role'] not in roles:
            raise APIError(403, 'forbidden', 'Your organization role does not permit this action.')

    @contextmanager
    def authorized_transaction(self, user, write=False, roles=None):
        """Recheck session and role after acquiring the transaction lock.

        A request may wait for another writer that revokes its session or role.
        The authorization snapshot loaded by HTTP must not survive that change.
        """
        self.require(user)
        with self.db.transaction(write) as connection:
            current = connection.execute('SELECT * FROM users WHERE id=? AND organization_id=?',
                                         (user['id'], user['organization_id'])).fetchone()
            self.require(current, roles)
            if 'token_hash' in user and not connection.execute(
                    'SELECT 1 FROM sessions WHERE token_hash=? AND user_id=? AND expires_at>?',
                    (user['token_hash'], user['id'], now())).fetchone():
                raise APIError(401, 'authentication_required', 'Session expired. Sign in again.')
            yield connection

    def register(self, data):
        object_fields(data, ('organization', 'name', 'email', 'password', 'slug'),
                      ('organization', 'name', 'email', 'password'))
        organization = text_value(data['organization'], 'organization', True, 120)
        name = text_value(data['name'], 'name', True, 120)
        email = email_value(data['email'], True)
        slug = data.get('slug', re.sub('[^a-z0-9]+', '-', organization.lower()).strip('-'))
        slug = text_value(slug, 'slug', True, 64).lower()
        if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', slug):
            invalid('Organization slug may contain lowercase letters, numbers, and single hyphens.')
        encoded = password_hash(data['password'])
        user = {'id': identifier(), 'organization_id': identifier(), 'name': name, 'email': email, 'role': 'owner'}
        try:
            with self.db.transaction(True) as connection:
                connection.execute('INSERT INTO organizations VALUES (?,?,?,?)',
                                   (user['organization_id'], organization, slug, now()))
                connection.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?)',
                                   (user['id'], user['organization_id'], name, email, encoded, 'owner', now()))
                self._audit(connection, user, 'register', 'organization', user['organization_id'])
                return self._session(connection, user)
        except sqlite3.IntegrityError:
            raise APIError(409, 'organization_exists', 'That organization slug is already in use.') from None

    def login(self, data, address='local'):
        object_fields(data, ('organization', 'email', 'password'), ('organization', 'email', 'password'))
        slug = text_value(data['organization'], 'organization', True, 64).lower()
        email = email_value(data['email'], True)
        key = token_hash(address + '\0' + slug + '\0' + email)
        ip_key = token_hash('ip\0' + address)
        failure = False
        with self.db.transaction(True) as connection:
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(timespec='seconds')
            connection.execute('DELETE FROM login_attempts WHERE window_start < ?', (cutoff,))
            for attempt_key, maximum in ((key, 5), (ip_key, 30)):
                attempt = connection.execute('SELECT failures FROM login_attempts WHERE attempt_key=?',
                                             (attempt_key,)).fetchone()
                if attempt and attempt['failures'] >= maximum:
                    raise APIError(429, 'rate_limited', 'Too many failed sign-in attempts. Try again in 15 minutes.')
            user = connection.execute('''SELECT u.* FROM users u JOIN organizations o ON o.id=u.organization_id
                                         WHERE o.slug=? AND u.email=?''', (slug, email)).fetchone()
            valid = verify_password(data['password'], user['password_hash'] if user else self.dummy_hash)
            if not user or not valid:
                for attempt_key in (key, ip_key):
                    connection.execute('''INSERT INTO login_attempts VALUES (?,1,?)
                        ON CONFLICT(attempt_key) DO UPDATE SET failures=failures+1''', (attempt_key, now()))
                failure = True
            else:
                connection.execute('DELETE FROM login_attempts WHERE attempt_key=?', (key,))
                self._audit(connection, user, 'login', 'user', user['id'])
                result = self._session(connection, user)
        if failure:
            raise APIError(401, 'invalid_credentials', 'Organization, email, or password is incorrect.')
        return result

    def logout(self, user):
        self.require(user)
        with self.authorized_transaction(user, True) as connection:
            connection.execute('DELETE FROM sessions WHERE token_hash=?', (user['token_hash'],))
            self._audit(connection, user, 'logout', 'user', user['id'])
        return {'authenticated': False}

    def members(self, user):
        self.require(user)
        with self.db.transaction() as connection:
            rows = connection.execute('SELECT id,name,email,role FROM users WHERE organization_id=? ORDER BY name,id',
                                      (user['organization_id'],)).fetchall()
            return {'items': [dict(row) for row in rows]}

    def change_role(self, user, member_id, data):
        self.require(user, ('owner',))
        object_fields(data, ('role',), ('role',))
        if data['role'] not in ('owner', 'admin', 'member', 'viewer'):
            invalid('Unknown role.')
        with self.authorized_transaction(user, True, ('owner',)) as connection:
            member = self._foreign(connection, user, 'users', member_id)
            if member['role'] == 'owner' and data['role'] != 'owner':
                count = connection.execute("SELECT count(*) FROM users WHERE organization_id=? AND role='owner'",
                                           (user['organization_id'],)).fetchone()[0]
                if count <= 1:
                    raise APIError(409, 'last_owner', 'An organization must retain at least one owner.')
            connection.execute('UPDATE users SET role=? WHERE id=? AND organization_id=?',
                               (data['role'], member_id, user['organization_id']))
            self._audit(connection, user, 'change_role', 'user', member_id,
                        {'from': member['role'], 'to': data['role']})
            return {'item': public_user(connection.execute('SELECT * FROM users WHERE id=?', (member_id,)).fetchone())}

    def invite(self, user, data):
        self.require(user, ('owner', 'admin'))
        object_fields(data, ('email', 'role'), ('email', 'role'))
        email = email_value(data['email'], True)
        role = data['role']
        allowed = ('admin', 'member', 'viewer') if user['role'] == 'owner' else ('member', 'viewer')
        if role not in allowed:
            raise APIError(403, 'forbidden_role', 'You cannot invite a user with this role.')
        token, invitation_id, expires = secrets.token_urlsafe(32), identifier(), future(days=7)
        with self.authorized_transaction(user, True, ('owner', 'admin')) as connection:
            current_role = connection.execute('SELECT role FROM users WHERE id=?', (user['id'],)).fetchone()[0]
            if current_role == 'admin' and role == 'admin':
                raise APIError(403, 'forbidden_role', 'You cannot invite a user with this role.')
            if connection.execute('SELECT 1 FROM users WHERE organization_id=? AND email=?',
                                  (user['organization_id'], email)).fetchone():
                raise APIError(409, 'member_exists', 'This email already belongs to an organization member.')
            # Reissuing replaces outstanding invitations so old links cannot remain usable.
            connection.execute('UPDATE invitations SET used_at=? WHERE organization_id=? AND email=? AND used_at IS NULL',
                               (now(), user['organization_id'], email))
            connection.execute('INSERT INTO invitations VALUES (?,?,?,?,?,?,?,?,?)',
                               (invitation_id, user['organization_id'], email, role, token_hash(token), expires,
                                None, user['id'], now()))
            self._audit(connection, user, 'invite', 'invitation', invitation_id, {'email': email, 'role': role})
        return {'token': token, 'expires_at': expires, 'email': email, 'role': role}

    def _invitation(self, connection, token):
        if not isinstance(token, str) or not token or len(token) > 200:
            raise APIError(404, 'invitation_unavailable', 'Invitation is invalid, expired, or already used.')
        row = connection.execute('SELECT * FROM invitations WHERE token_hash=? AND used_at IS NULL AND expires_at>?',
                                 (token_hash(token), now())).fetchone()
        if not row:
            raise APIError(404, 'invitation_unavailable', 'Invitation is invalid, expired, or already used.')
        return row

    def invitation_preview(self, token):
        with self.db.transaction() as connection:
            row = self._invitation(connection, token)
            org = connection.execute('SELECT name,slug FROM organizations WHERE id=?', (row['organization_id'],)).fetchone()
            return {'email': row['email'], 'role': row['role'], 'expires_at': row['expires_at'], 'organization': dict(org)}

    def accept_invitation(self, data):
        object_fields(data, ('token', 'name', 'password'), ('token', 'name', 'password'))
        name = text_value(data['name'], 'name', True, 120)
        # Validate the token before expensive password work; validate it again in the write transaction.
        self.invitation_preview(data['token'])
        encoded = password_hash(data['password'])
        try:
            with self.db.transaction(True) as connection:
                invitation = self._invitation(connection, data['token'])
                user = {'id': identifier(), 'organization_id': invitation['organization_id'], 'name': name,
                        'email': invitation['email'], 'role': invitation['role']}
                connection.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?)',
                                   (user['id'], user['organization_id'], name, user['email'], encoded, user['role'], now()))
                connection.execute('UPDATE invitations SET used_at=? WHERE id=?', (now(), invitation['id']))
                self._audit(connection, user, 'accept_invitation', 'user', user['id'])
                return self._session(connection, user)
        except sqlite3.IntegrityError:
            raise APIError(409, 'member_exists', 'This email already belongs to an organization member.') from None

    def _entity(self, entity):
        if entity not in FIELDS:
            raise APIError(404, 'not_found', 'Resource not found.')

    def _foreign(self, connection, user, entity, record_id):
        if entity not in (*FIELDS, 'users'):
            raise ValueError('Invalid internal table name')
        if not isinstance(record_id, str):
            invalid('Related record IDs must be text.')
        row = connection.execute(f'SELECT * FROM {entity} WHERE organization_id=? AND id=?',
                                 (user['organization_id'], record_id)).fetchone()
        if not row:
            raise APIError(404, 'not_found', 'Record or related record not found in this organization.')
        return row

    def _validate_record(self, connection, user, entity, data, previous=None):
        object_fields(data, FIELDS[entity])
        if previous is None:
            values = {field: '' for field in FIELDS[entity]}
            for field in ('account_id', 'opportunity_id'):
                if field in values:
                    values[field] = None
            if 'owner_id' in values:
                values['owner_id'] = user['id']
            if entity == 'leads':
                values['status'] = 'new'
            if entity == 'opportunities':
                values.update(amount_cents=0, currency='USD', stage='prospecting')
            if entity == 'activities':
                values.update(kind='task', status='open', assigned_to=user['id'])
        else:
            values = {field: previous[field] for field in FIELDS[entity]}
        values.update(data)
        for field, value in values.items():
            if field == 'amount_cents':
                if type(value) is not int or not 0 <= value <= 9_000_000_000_000:
                    invalid('amount_cents must be a nonnegative integer up to 9000000000000.')
            elif field in ('account_id', 'opportunity_id', 'owner_id', 'assigned_to'):
                optional = field in ('account_id', 'opportunity_id') and not (entity == 'opportunities' and field == 'account_id')
                if optional and value in (None, ''):
                    values[field] = None
                    continue
                table = {'account_id': 'accounts', 'opportunity_id': 'opportunities',
                         'owner_id': 'users', 'assigned_to': 'users'}[field]
                self._foreign(connection, user, table, value)
            elif field in ('expected_close', 'due_date'):
                values[field] = text_value(value, field, maximum=10)
                if value:
                    try:
                        if date.fromisoformat(value).isoformat() != value:
                            raise ValueError()
                    except ValueError:
                        invalid(f'{field} must be a valid YYYY-MM-DD date.')
            elif field == 'email':
                values[field] = email_value(value)
            else:
                values[field] = text_value(value, field, field in REQUIRED[entity],
                                           10000 if field == 'notes' else 2048 if field == 'website' else 250)
        enums = {'leads': {'status': ('new', 'contacted', 'qualified', 'disqualified')},
                 'opportunities': {'stage': STAGES, 'currency': ('USD',)},
                 'activities': {'status': ('open', 'done'), 'kind': ('task', 'call', 'meeting')}}
        for field, choices in enums.get(entity, {}).items():
            if values[field] not in choices:
                invalid(f'{field} must be one of: {", ".join(choices)}.')
        if entity == 'activities' and values['account_id'] and values['opportunity_id']:
            opportunity = self._foreign(connection, user, 'opportunities', values['opportunity_id'])
            if opportunity['account_id'] != values['account_id']:
                invalid('Activity account must match its opportunity account.')
        return values

    def _insert_record(self, connection, user, entity, values):
        record_id, timestamp = identifier(), now()
        columns = ('id', 'organization_id', *FIELDS[entity], 'created_at', 'updated_at')
        arguments = (record_id, user['organization_id'], *[values[field] for field in FIELDS[entity]], timestamp, timestamp)
        connection.execute(f'INSERT INTO {entity} ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})', arguments)
        self._audit(connection, user, 'create', entity, record_id, {'fields': list(FIELDS[entity])})
        return record_dict(self._foreign(connection, user, entity, record_id))

    def create_record(self, user, entity, data):
        self.require(user, ('owner', 'admin', 'member'))
        self._entity(entity)
        try:
            with self.authorized_transaction(user, True, ('owner', 'admin', 'member')) as connection:
                values = self._validate_record(connection, user, entity, data)
                return {'item': self._insert_record(connection, user, entity, values)}
        except sqlite3.IntegrityError:
            raise APIError(409, 'record_conflict', 'A contact with this email already exists or a related record is unavailable.') from None

    def update_record(self, user, entity, record_id, data):
        self.require(user, ('owner', 'admin', 'member'))
        self._entity(entity)
        try:
            with self.authorized_transaction(user, True, ('owner', 'admin', 'member')) as connection:
                previous = self._foreign(connection, user, entity, record_id)
                values = self._validate_record(connection, user, entity, data, previous)
                if entity == 'opportunities' and values['account_id'] != previous['account_id']:
                    conflicting = connection.execute('''SELECT 1 FROM activities
                        WHERE organization_id=? AND opportunity_id=? AND account_id IS NOT NULL
                        AND account_id<>? LIMIT 1''',
                        (user['organization_id'], record_id, values['account_id'])).fetchone()
                    if conflicting:
                        raise APIError(409, 'activity_account_conflict',
                                       'Update or clear the account on linked activities before moving this opportunity to another account.')
                columns = (*FIELDS[entity], 'updated_at')
                connection.execute(f'UPDATE {entity} SET {",".join(field + "=?" for field in columns)} WHERE organization_id=? AND id=?',
                                   (*[values[field] for field in FIELDS[entity]], now(), user['organization_id'], record_id))
                self._audit(connection, user, 'update', entity, record_id, {'fields': sorted(data)})
                return {'item': record_dict(self._foreign(connection, user, entity, record_id))}
        except sqlite3.IntegrityError:
            raise APIError(409, 'record_conflict', 'A contact with this email already exists or a related record is unavailable.') from None

    def delete_record(self, user, entity, record_id):
        self.require(user, ('owner', 'admin'))
        self._entity(entity)
        try:
            with self.authorized_transaction(user, True, ('owner', 'admin')) as connection:
                self._foreign(connection, user, entity, record_id)
                connection.execute(f'DELETE FROM {entity} WHERE organization_id=? AND id=?', (user['organization_id'], record_id))
                self._audit(connection, user, 'delete', entity, record_id)
        except sqlite3.IntegrityError:
            raise APIError(409, 'record_referenced', 'This record is referenced by another record. Remove or update those relationships first.') from None
        return {'deleted': True}

    def pagination(self, query):
        try:
            limit, offset = int(query.get('limit', 100)), int(query.get('offset', 0))
        except (ValueError, TypeError):
            invalid('limit and offset must be integers.')
        if not 1 <= limit <= 200 or not 0 <= offset <= 1_000_000_000:
            invalid('limit must be 1–200 and offset must be nonnegative.')
        return limit, offset

    def records(self, user, entity, query):
        self.require(user)
        self._entity(entity)
        limit, offset = self.pagination(query)
        search = text_value(query.get('q', ''), 'q', maximum=250)
        where, params = 'organization_id=?', [user['organization_id']]
        if search:
            columns = [field for field in FIELDS[entity] if field not in ('owner_id', 'assigned_to', 'account_id', 'opportunity_id', 'amount_cents')]
            where += ' AND (' + ' OR '.join(f'{field} LIKE ? ESCAPE \'\\\'' for field in columns) + ')'
            escaped = search.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            params.extend(['%' + escaped + '%'] * len(columns))
        with self.db.transaction() as connection:
            total = connection.execute(f'SELECT count(*) FROM {entity} WHERE {where}', params).fetchone()[0]
            rows = connection.execute(f'SELECT * FROM {entity} WHERE {where} ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?',
                                      (*params, limit, offset)).fetchall()
            return {'items': [record_dict(row) for row in rows], 'total': total, 'limit': limit, 'offset': offset}

    def get_record(self, user, entity, record_id):
        self.require(user)
        self._entity(entity)
        with self.db.transaction() as connection:
            return {'item': record_dict(self._foreign(connection, user, entity, record_id))}

    def pipeline(self, user):
        self.require(user)
        org = user['organization_id']
        with self.db.transaction() as connection:
            rows = connection.execute('SELECT stage,count(*) count,coalesce(sum(amount_cents),0) amount_cents FROM opportunities WHERE organization_id=? GROUP BY stage', (org,)).fetchall()
            grouped = {row['stage']: dict(row) for row in rows}
            stages = [grouped.get(stage, {'stage': stage, 'count': 0, 'amount_cents': 0}) for stage in STAGES]
            totals = {'opportunity_count': sum(row['count'] for row in stages),
                      'pipeline_cents': sum(row['amount_cents'] for row in stages if not row['stage'].startswith('closed_')),
                      'won_cents': grouped.get('closed_won', {}).get('amount_cents', 0)}
            for entity in ('accounts', 'contacts', 'leads'):
                totals[entity] = connection.execute(f'SELECT count(*) FROM {entity} WHERE organization_id=?', (org,)).fetchone()[0]
            totals['open_activities'] = connection.execute("SELECT count(*) FROM activities WHERE organization_id=? AND status='open'", (org,)).fetchone()[0]
            totals['overdue_activities'] = connection.execute("SELECT count(*) FROM activities WHERE organization_id=? AND status='open' AND due_date<>'' AND due_date<?", (org, datetime.now(timezone.utc).date().isoformat())).fetchone()[0]
        return {'stages': stages, 'totals': totals}

    def import_contacts(self, user, data):
        self.require(user, ('owner', 'admin', 'member'))
        object_fields(data, ('csv',), ('csv',))
        raw = data['csv']
        if not isinstance(raw, str) or len(raw.encode('utf-8')) > 1_000_000:
            invalid('csv must be text no larger than 1 MB.')
        try:
            reader = csv.DictReader(io.StringIO(raw.lstrip('\ufeff'), newline=''), strict=True)
            if reader.fieldnames != list(CSV_HEADERS):
                invalid('CSV headers must be exactly: ' + ','.join(CSV_HEADERS))
            rows = []
            for row in reader:
                if len(rows) >= 1000:
                    invalid('Import is limited to 1000 contacts.')
                if None in row or any(value is None for value in row.values()):
                    invalid('Every CSV row must have exactly six columns.')
                rows.append(row)
        except csv.Error:
            invalid('Malformed CSV input.')
        if not rows:
            invalid('CSV must contain at least one contact.')
        try:
            with self.authorized_transaction(user, True, ('owner', 'admin', 'member')) as connection:
                seen = set()
                for line_number, row in enumerate(rows, start=2):
                    account_name = text_value(row.pop('account_name'), 'account_name', maximum=250)
                    row['account_id'] = None
                    if account_name:
                        accounts = connection.execute('SELECT id FROM accounts WHERE organization_id=? AND name=?',
                                                      (user['organization_id'], account_name)).fetchall()
                        if len(accounts) != 1:
                            invalid(f'CSV row {line_number}: account_name must match exactly one existing account; create it first.')
                        row['account_id'] = accounts[0]['id']
                    values = self._validate_record(connection, user, 'contacts', row)
                    email = values['email']
                    if email and (email in seen or connection.execute('SELECT 1 FROM contacts WHERE organization_id=? AND lower(email)=?', (user['organization_id'], email)).fetchone()):
                        invalid(f'CSV row {line_number}: duplicate contact email.')
                    seen.add(email)
                    self._insert_record(connection, user, 'contacts', values)
                self._audit(connection, user, 'import', 'contacts', '', {'imported': len(rows)})
        except sqlite3.IntegrityError:
            raise APIError(409, 'record_conflict', 'Import conflicts with an existing contact.') from None
        return {'imported': len(rows)}

    def export_contacts(self, user):
        self.require(user)
        output = io.StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow(CSV_HEADERS)
        with self.db.transaction() as connection:
            rows = connection.execute('''SELECT c.first_name,c.last_name,c.email,c.phone,c.title,coalesce(a.name,'') account_name
                FROM contacts c LEFT JOIN accounts a ON a.id=c.account_id AND a.organization_id=c.organization_id
                WHERE c.organization_id=? ORDER BY c.last_name,c.first_name,c.id''', (user['organization_id'],)).fetchall()
            for row in rows:
                # Spreadsheet software treats formula-leading cells as executable expressions.
                writer.writerow(["'" + value if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')) else value for value in row])
        return output.getvalue()

    def audit(self, user, query):
        self.require(user, ('owner', 'admin'))
        limit, offset = self.pagination(query)
        with self.authorized_transaction(user, roles=('owner', 'admin')) as connection:
            total = connection.execute('SELECT count(*) FROM audit WHERE organization_id=?', (user['organization_id'],)).fetchone()[0]
            rows = connection.execute('''SELECT id,actor_name,action,entity,entity_id,created_at,details
                FROM audit WHERE organization_id=? ORDER BY created_at DESC,rowid DESC LIMIT ? OFFSET ?''',
                                      (user['organization_id'], limit, offset)).fetchall()
            items = [dict(row) for row in rows]
            for item in items:
                item['details'] = json.loads(item['details'])
            return {'items': items, 'total': total, 'limit': limit, 'offset': offset}
