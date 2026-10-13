"""Versioned, transactional SQLite storage. SQL parameters carry all user data."""
from contextlib import contextmanager
from pathlib import Path
import os
import sqlite3

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE organizations (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
);
CREATE TABLE users (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL REFERENCES organizations(id),
 name TEXT NOT NULL, email TEXT NOT NULL, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('owner','admin','member','viewer')), created_at TEXT NOT NULL,
 UNIQUE(organization_id,email), UNIQUE(organization_id,id)
);
CREATE TABLE sessions (
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 csrf_token TEXT NOT NULL, expires_at TEXT NOT NULL
);
CREATE TABLE invitations (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL REFERENCES organizations(id),
 email TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','member','viewer')),
 token_hash TEXT NOT NULL UNIQUE, expires_at TEXT NOT NULL, used_at TEXT,
 created_by TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);
CREATE TABLE login_attempts (attempt_key TEXT PRIMARY KEY, failures INTEGER NOT NULL, window_start TEXT NOT NULL);
CREATE TABLE accounts (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL REFERENCES organizations(id),
 name TEXT NOT NULL, website TEXT NOT NULL DEFAULT '', industry TEXT NOT NULL DEFAULT '',
 owner_id TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(organization_id,id), FOREIGN KEY(organization_id,owner_id) REFERENCES users(organization_id,id)
);
CREATE TABLE contacts (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL REFERENCES organizations(id),
 first_name TEXT NOT NULL DEFAULT '', last_name TEXT NOT NULL, email TEXT NOT NULL DEFAULT '',
 phone TEXT NOT NULL DEFAULT '', title TEXT NOT NULL DEFAULT '', account_id TEXT, owner_id TEXT NOT NULL,
 notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(organization_id,id), FOREIGN KEY(organization_id,owner_id) REFERENCES users(organization_id,id),
 FOREIGN KEY(organization_id,account_id) REFERENCES accounts(organization_id,id)
);
CREATE UNIQUE INDEX contacts_email_unique ON contacts(organization_id,lower(email)) WHERE email <> '';
CREATE TABLE leads (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL REFERENCES organizations(id),
 first_name TEXT NOT NULL DEFAULT '', last_name TEXT NOT NULL, email TEXT NOT NULL DEFAULT '',
 company TEXT NOT NULL DEFAULT '', status TEXT NOT NULL CHECK(status IN ('new','contacted','qualified','disqualified')),
 owner_id TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(organization_id,id), FOREIGN KEY(organization_id,owner_id) REFERENCES users(organization_id,id)
);
CREATE TABLE opportunities (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL REFERENCES organizations(id), name TEXT NOT NULL,
 account_id TEXT NOT NULL, amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0),
 currency TEXT NOT NULL CHECK(currency='USD'),
 stage TEXT NOT NULL CHECK(stage IN ('prospecting','qualification','proposal','negotiation','closed_won','closed_lost')),
 expected_close TEXT NOT NULL DEFAULT '', owner_id TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(organization_id,id),
 FOREIGN KEY(organization_id,account_id) REFERENCES accounts(organization_id,id),
 FOREIGN KEY(organization_id,owner_id) REFERENCES users(organization_id,id)
);
CREATE TABLE activities (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL REFERENCES organizations(id), subject TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('task','call','meeting')), status TEXT NOT NULL CHECK(status IN ('open','done')),
 due_date TEXT NOT NULL DEFAULT '', assigned_to TEXT NOT NULL, account_id TEXT, opportunity_id TEXT,
 notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 FOREIGN KEY(organization_id,account_id) REFERENCES accounts(organization_id,id),
 FOREIGN KEY(organization_id,opportunity_id) REFERENCES opportunities(organization_id,id),
 FOREIGN KEY(organization_id,assigned_to) REFERENCES users(organization_id,id)
);
CREATE TABLE audit (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL REFERENCES organizations(id), actor_id TEXT REFERENCES users(id),
 actor_name TEXT NOT NULL, action TEXT NOT NULL, entity TEXT NOT NULL, entity_id TEXT NOT NULL,
 details TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX accounts_tenant ON accounts(organization_id,created_at);
CREATE INDEX contacts_tenant ON contacts(organization_id,created_at);
CREATE INDEX leads_tenant ON leads(organization_id,created_at);
CREATE INDEX opportunities_tenant ON opportunities(organization_id,stage);
CREATE INDEX activities_tenant ON activities(organization_id,status,due_date);
CREATE INDEX audit_tenant ON audit(organization_id,created_at);
"""


class Database:
    def __init__(self, path):
        self.path = str(Path(path).expanduser().resolve())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
        except FileExistsError:
            pass
        os.chmod(self.path, 0o600)
        for suffix in ('-wal', '-shm', '-journal'):
            sidecar = Path(self.path + suffix)
            if sidecar.exists():
                os.chmod(sidecar, 0o600)
        connection = self.connect()
        try:
            connection.execute('PRAGMA journal_mode=WAL')
            connection.execute('BEGIN IMMEDIATE')
            try:
                version = connection.execute('PRAGMA user_version').fetchone()[0]
                if version > SCHEMA_VERSION:
                    raise RuntimeError('Database was created by a newer Commonstead release.')
                if version == 0:
                    # executescript implicitly commits: use separate execute calls instead.
                    for statement in SCHEMA.split(';'):
                        if statement.strip():
                            connection.execute(statement)
                    connection.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        finally:
            connection.close()

    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA busy_timeout=10000')
        return connection

    @contextmanager
    def transaction(self, write=False):
        connection = self.connect()
        try:
            connection.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
