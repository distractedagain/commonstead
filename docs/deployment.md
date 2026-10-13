# Local deployment and data operations

## Direct Python

Run from the source directory using Python3.12+ with SQLite support:

```sh
python3 -m commonstead --db data/commonstead.sqlite3 --host 127.0.0.1 --port 8765
```

The default is loopback-only. Access via `http://127.0.0.1:8765`. CLI flags configure database, host, port and Secure cookies; no environment secret is required. The repository never contains your runtime database. POSIX database/WAL/SHM creation is restricted to the OS user; protecting the parent directory and machine remains your responsibility.

## Optional Docker Compose

```sh
docker compose up --build
docker compose stop
docker compose start
```

Compose binds the host port to127.0.0.1, runs uid10001 with capabilities dropped, and persists `/data` in the `commonstead-data` volume. The root filesystem is read-only; `/data` is writable. Downloading the Python base image requires internet and disk space. The image tag is intentionally unpinned in this initial configuration; review and record its digest before adopting a deployment. No cloud resources are provisioned.

`docker compose down` removes the containers/network but preserves the volume. **Adding `--volumes` deletes the database volume**; use it only for disposable test installations. The CI job uses it solely on its ephemeral fixture volume.

## Back up and restore

For this first release, stop the server before taking a filesystem backup, then copy the **whole data directory**, including any SQLite sidecars, to a private backup destination. Do not copy only the main file while another writer is active. Restart the server after the copy. Test restoration to a separate directory and launch a separate server pointing to that copy. A SQLite online backup tool may be added later; none is currently bundled.

For a Docker deployment, stop the service and back up the named volume with trusted local tooling. Store backups privately; they contain customer records, password hashes and token hashes. Backups are not automatically encrypted, scheduled, uploaded, or retention-managed.

Schema version1 initializes transactionally and startup is idempotent. A newer unsupported schema is refused. There is no prior-release data migration claim. Future schema changes require tested incremental migrations and backup instructions; do not edit `PRAGMA user_version` to bypass a version refusal.

## Operational boundaries

This is a single-host, local-evaluation configuration. `http.server` is a development server; no worker cap, distributed jobs, reverse proxy, email delivery, public identity service, TLS certificates, monitoring, HA, or public rate-limit layer is provisioned. Do not interpret `--host 0.0.0.0` or `--secure-cookies` as production deployment features. In Docker the wildcard bind is internal to the container and the host publishing stays loopback-only.

Use separate browser profiles for the owner and invited users during local tests. Invitation URLs using127.0.0.1 refer to the recipient's own machine; they are not remotely routable invitations. A maintained production framework and an explicitly reviewed hosting configuration are prerequisites for an actual remote team deployment.

Core software is free under MIT. You still supply computing hardware, disk, electricity and backups. Optional future cloud hosting, email/SMS, payment processors, AI models/inference, data licenses, or commercial connectors may have separate costs and license terms. No paid service was provisioned for this release.
