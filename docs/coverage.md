# Implemented capability evidence

Snapshot: 2026-10-12, release0.1.0. **Verified** here means the bounded acceptance scenario passed in the recorded local environment. It does not mean vendor parity, production readiness, broad security assurance, or a whole Salesforce product is complete. Source-family research is in `portfolio-matrix.csv`; exact executed results are in `verification.md`.

| Capability and bounded acceptance | Status | Implementation | Test evidence |
|---|---|---|---|
| Create organization and owner, scoped login, persistent expiring session | verified | `service.py: register/login/authenticate`; `database.py`; auth UI | `BusinessTests.test_organization_scoped_login_and_session_secrets`; clean installation; browser signup/login |
| Issue, redeem, reissue, expire one-use invitations; no email delivery claim | verified | `service.py: invite/accept_invitation`; Team UI | `test_complete_invitation_crm_pipeline_workflow`, `test_invitation_expiry_single_use_and_reissue`, simultaneous-redemption reviewer test; browser invitation |
| Configure four roles, prevent escalation and last-owner loss; existing sessions honor changes | verified | `change_role`, `authorized_transaction`; Team UI | Role/escalation tests, two-owner concurrency test, in-flight authorization regression; browser role update |
| Create/update accounts, contacts and leads; persist across reopen | verified | Generic CRM service/HTTP routes and forms | Business workflow, strict validation and persistence tests; browser account/contact/lead |
| Atomic contact CSV import with relationships and duplicates; safe export | verified | `import_contacts`, `export_contacts`; import dialog | Atomicity, formula escaping and late-row rollback tests; browser two-contact import |
| Advance opportunity stages and preserve exact USD cents | verified | Opportunity validation and form | Workflow, money/date validation and relationship consistency tests; browser qualification→proposal |
| Assign/complete activities, validate related account/opportunity and tenant user | verified | Activity schema/validation and UI | Business workflow, foreign-key isolation, opportunity-account move regression; browser assignment |
| Reconcile stage sums, open pipeline, won amount and overdue activity counts | verified | `pipeline`; dashboard/CSV report | Workflow and tenant report isolation; browser values reconciled to saved opportunity |
| Search/paginate records and reject cross-tenant direct IDs/writes/related IDs | verified | `records`, `_foreign`, composite foreign keys | Tenant suite, escaped search/pagination and injected-tenant tests |
| Record transactional tenant audit with restricted read access | verified | `_audit`, `audit`; audit UI | Tenant audit, failed-import rollback and secret exclusion tests |
| Fresh schema initialization, reopen and unsupported-version refusal | verified | `Database`; schema version1 | Persistence and failed-DDL rollback tests; clean isolated installation |
| HTTP sessions, CSRF/Origin/Host, JSON/framing and static allowlist | verified | `server.py` | Real loopback integration and adversarial HTTP tests; scoped to enumerated attacks |
| Browser UI for the first workflow | verified | `static/index.html`, `app.js`, `styles.css` | Manual Codex in-app-browser interaction; see verification scenarios. No automated browser regression suite/accessibility certification |
| Single-host source-only installation without third-party packages | verified | Python package and static assets | `scripts/verify_clean_install.py` in fresh pip-free isolated venv |
| Container startup and Python3.12–3.14 CI | planned | Dockerfile, Compose, GitHub Actions | Configuration exists; remote results must be added after execution |
| Lead conversion, forecasts/quotas, custom fields/objects and record-level sharing | planned | Full-family roadmap; no stub advertised | No implementation/test claim |
| Email delivery, external APIs, webhooks, jobs, files and general workflow automation | planned | Foundation/roadmap decisions | No live integration configured or claimed |
| Support, marketing, commerce/revenue, analytics/data, collaboration, industries, application development and AI | planned | 95-group full portfolio matrix and roadmap | Public-source research; no implementation claim in0.1.0 |

Initial platform and Sales Cloud families are **partial** at portfolio level because their published feature scope far exceeds these scenarios. Future upgrades from a previous application schema need separate migration tests; version1 initialization does not prove an upgrade path.
