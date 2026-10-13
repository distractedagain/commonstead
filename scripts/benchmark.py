#!/usr/bin/env python3
"""Measure synthetic, single-process service calls against temporary local SQLite.

No HTTP, concurrency, network, production capacity or performance guarantee is
implied. Fixtures and the database are temporary; output is JSON only.
"""
import csv
import io
import json
import math
import platform
from pathlib import Path
import secrets
import sqlite3
import statistics
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from commonstead import __version__
from commonstead.service import CSV_HEADERS, Service

ACCOUNT_COUNT = 250
SAMPLES = 30
IMPORT_ROWS = 500


def milliseconds(operation):
    start = time.perf_counter_ns()
    result = operation()
    return (time.perf_counter_ns() - start) / 1_000_000, result


def repeated(operation):
    samples = [milliseconds(operation)[0] for _ in range(SAMPLES)]
    ordered = sorted(samples)
    return {'samples': SAMPLES, 'median_ms': round(statistics.median(samples), 3),
            'p95_ms': round(ordered[math.ceil(0.95 * len(ordered)) - 1], 3),
            'min_ms': round(ordered[0], 3), 'max_ms': round(ordered[-1], 3)}


def main():
    with tempfile.TemporaryDirectory(prefix='commonstead-benchmark-') as directory:
        service = Service(Path(directory) / 'benchmark.sqlite3')
        registration_ms, (_, token) = milliseconds(lambda: service.register({
            'organization': 'Synthetic Benchmark', 'name': 'Synthetic Owner',
            'email': 'synthetic@example.test', 'password': secrets.token_urlsafe(24)}))
        user = service.authenticate(token)
        fixture_start = time.perf_counter_ns()
        for index in range(ACCOUNT_COUNT):
            account = service.create_record(user, 'accounts', {
                'name': f'Synthetic Account {index:03d}', 'industry': 'Synthetic',
                'notes': 'Generated benchmark fixture; not a real organization.'})['item']
            service.create_record(user, 'opportunities', {
                'name': f'Synthetic Opportunity {index:03d}', 'account_id': account['id'],
                'amount_cents': 100000 + index * 1000, 'stage': ('prospecting', 'proposal', 'closed_won')[index % 3]})
        fixture_ms = (time.perf_counter_ns() - fixture_start) / 1_000_000
        # An untimed warm-up is explicit; operating-system cache is not flushed.
        service.records(user, 'accounts', {'limit': '100'})
        service.pipeline(user)
        account_list = repeated(lambda: service.records(user, 'accounts', {'limit': '100'}))
        pipeline_report = repeated(lambda: service.pipeline(user))
        output = io.StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow(CSV_HEADERS)
        for index in range(IMPORT_ROWS):
            writer.writerow(('Synthetic', f'Contact {index:03d}', f'contact{index:03d}@example.test',
                             '', 'Synthetic contact', f'Synthetic Account {index % ACCOUNT_COUNT:03d}'))
        import_ms, imported = milliseconds(lambda: service.import_contacts(user, {'csv': output.getvalue()}))
        assert imported['imported'] == IMPORT_ROWS
        totals = service.pipeline(user)['totals']
        assert (totals['accounts'], totals['contacts'], totals['opportunity_count']) == (ACCOUNT_COUNT, IMPORT_ROWS, ACCOUNT_COUNT)
        report = {
            'application_version': __version__,
            'scope': 'Synthetic single-process service calls with temporary local SQLite; no HTTP, concurrent load, or production-capacity claim.',
            'environment': {'python': platform.python_version(), 'implementation': platform.python_implementation(),
                            'sqlite': sqlite3.sqlite_version, 'os': platform.system(),
                            'os_release': platform.release(), 'architecture': platform.machine()},
            'fixture_counts': {'accounts': ACCOUNT_COUNT, 'opportunities': ACCOUNT_COUNT, 'imported_contacts': IMPORT_ROWS},
            'method': {'timer': 'time.perf_counter_ns wall time', 'sample_count': SAMPLES,
                       'p95': 'nearest rank, ceil(0.95*n)', 'cache': 'one untimed warm-up; OS cache not flushed',
                       'account_list_limit': 100, 'registration_pbkdf2_sha256_iterations': 600000},
            'measurements': {'registration': {'samples': 1, 'wall_ms': round(registration_ms, 3)},
                             'fixture_creation': {'samples': 1, 'wall_ms': round(fixture_ms, 3)},
                             'account_list': account_list, 'pipeline_report': pipeline_report,
                             'contact_csv_import': {'samples': 1, 'rows': IMPORT_ROWS, 'wall_ms': round(import_ms, 3)}},
        }
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
