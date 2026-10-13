# Commonstead

An independent, MIT-licensed customer workspace. **Version 0.1.0 implements a local CRM workflow. It is not a complete Salesforce replacement.** The long-term scope includes the wider portfolio; the [product matrix](docs/portfolio-matrix.csv) and [roadmap](docs/roadmap.md) preserve that scope.

Create an organization, invite teammates, configure roles, import contacts, manage accounts and leads, advance opportunities, assign activities, and export a pipeline report. These workflows use a real SQLite database and enforced organization permissions. The interface contains no simulated customers unless you deliberately load the synthetic demo.

## Run locally

Prerequisites: Python **3.12 or newer** with SQLite support and a modern browser. Core operation needs no subscription, API key, package installation, frontend build, or internet connection.

```sh
git clone https://github.com/distractedagain/commonstead.git
cd commonstead
python3 -m commonstead
```

If the repository is not yet published, extract the release archive and `cd commonstead` instead. Open <http://127.0.0.1:8765>, choose **Create workspace**, and use a password of 12–128 characters. Keep the organization sign-in ID shown in the sidebar; sign-in requires that ID, email, and password. Data persists in `data/commonstead.sqlite3`. Stop with Ctrl+C and rerun the same command to reopen it.

The application uses Python's development HTTP server and is **for trusted local evaluation**. Do not expose it to the public internet. TLS alone does not establish production readiness. See [deployment and backup](docs/deployment.md) and [security limits](SECURITY.md).

## First complete workflow

1. Create your organization. Its first user is the owner.
2. Open **Team & access**, create an invitation, and copy its single-use link. No email is sent. For local evaluation, accept the link in a separate browser profile on the same host. Invitations expire in seven days.
3. As owner, set the teammate's role. A viewer can read/export; a member can create/update; an admin can also delete and invite members/viewers. Only an owner can change roles.
4. Create an **Account**. In **Contacts → Import contacts**, paste the sample below, changing `Northstar Workshop` to the exact account name you created.
5. Create a **Lead**, update its status, and create an **Opportunity** attached to an account. Use **Edit → Stage** to progress the opportunity.
6. Create an **Activity**, assign it to a teammate, link it to the account/opportunity, and mark it done when completed.
7. Open **Overview** to view persisted totals; **Export report** downloads exact USD cents and stage counts. Admins/owners can inspect **Audit history**.

```csv
first_name,last_name,email,phone,title,account_name
Avery,Stone,avery@example.test,,Buyer,Northstar Workshop
Jordan,Reed,jordan@example.test,,Operations,Northstar Workshop
```

Imports are atomic, limited to 1,000 contacts, and reject duplicate nonblank emails, malformed rows, or missing/ambiguous account matches. Matching account names is exact and case-sensitive. Spreadsheet exports escape formula-leading cells; this can intentionally change their literal representation on reimport.

## Synthetic demo

```sh
python3 scripts/seed_demo.py --db data/demo.sqlite3
python3 -m commonstead --db data/demo.sqlite3
```

The seed script generates fictional records and prints the local demo sign-in details. No real customer data or external integration is used. Use a separate database for your own work; never publish a populated database, session cookie, invitation link, or password.

## Test and inspect

```sh
python3 -m unittest discover -s tests -v
python3 scripts/verify_clean_install.py
python3 scripts/check_release.py
node --check commonstead/static/app.js  # optional development check; Node is not a runtime requirement
```

Tests cover workflows, role enforcement, cross-tenant access, CSV atomicity, persistence, migration behavior, and real HTTP protections. Read [actual release evidence](docs/verification.md) and the [capability coverage matrix](docs/coverage.md) before relying on any claim. GitHub CI is configured; a configured workflow is not a passing remote run.

Optional local container: `docker compose up --build`. It publishes only `127.0.0.1:8765` and stores data in a named volume. Docker and base-image downloads are optional; see the evidence document for whether this path has been executed.

## Project map

- [Architecture and decisions](docs/architecture.md), [API contract](docs/api.md), [foundation evaluation](docs/foundations.md)
- [Official-source portfolio survey](docs/portfolio-survey.md), [product matrix](docs/portfolio-matrix.csv), [full roadmap](docs/roadmap.md)
- [Coverage](docs/coverage.md), [release notes](CHANGELOG.md), [verification](docs/verification.md), [review](docs/review.md)
- [Provenance and dependencies](docs/provenance.md), [contributing](CONTRIBUTING.md), [continuation instructions](docs/continuation.md)

No Salesforce source, proprietary assets, private account data, or private APIs are included. Commonstead is independently designed and is not affiliated with Salesforce or its brands. Salesforce API, metadata, Apex, SOQL, and package compatibility are not implemented. Hosting, storage, delivery services, and optional future AI inference can have operating costs; no such service is required or purchased by this release.
