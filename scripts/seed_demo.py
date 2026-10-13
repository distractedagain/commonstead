#!/usr/bin/env python3
"""Create fictional sample data in a development database; never sends messages."""
import argparse
import os
from pathlib import Path
import secrets
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from commonstead.service import APIError, Service


def main():
    parser = argparse.ArgumentParser(description='Seed a fictional Commonstead demo organization.')
    parser.add_argument('--db', default='data/commonstead.sqlite3')
    args = parser.parse_args()
    os.umask(0o077)
    service = Service(args.db)
    password = secrets.token_urlsafe(18)
    try:
        session, token = service.register({'organization': 'Commonstead Demo', 'slug': 'commonstead-demo',
                                          'name': 'Demo Owner', 'email': 'owner@example.test', 'password': password})
    except APIError as error:
        if error.code == 'organization_exists':
            print('Demo organization already exists; no data changed.', file=sys.stderr)
            return 1
        raise
    user = service.authenticate(token)
    for name, industry, amount, stage in (
        ('Cedar Workshop', 'Manufacturing', 2400000, 'qualification'),
        ('Harbor Studio', 'Design', 850000, 'proposal'),
        ('Meadow Cooperative', 'Agriculture', 1250000, 'closed_won'),
    ):
        account = service.create_record(user, 'accounts', {'name': name, 'industry': industry,
                                         'notes': 'Fictional sample organization.'})['item']
        service.create_record(user, 'opportunities', {'name': name + ' pilot', 'account_id': account['id'],
                               'amount_cents': amount, 'stage': stage, 'expected_close': '2030-06-30'})
        service.create_record(user, 'contacts', {'first_name': 'Sample', 'last_name': name.split()[0],
                               'email': name.split()[0].lower() + '@example.test', 'account_id': account['id'],
                               'title': 'Operations manager'})
    service.create_record(user, 'leads', {'first_name': 'Taylor', 'last_name': 'Sample', 'company': 'Fictional Labs',
                         'email': 'taylor@example.test', 'status': 'new'})
    service.create_record(user, 'activities', {'subject': 'Review fictional pilot proposals', 'kind': 'task',
                         'due_date': '2030-06-15', 'notes': 'Sample task only.'})
    service.logout(user)
    print('Fictional demo data created. Save this generated local demo password:')
    print('Organization: commonstead-demo')
    print('Email: owner@example.test')
    print('Password: ' + password)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
