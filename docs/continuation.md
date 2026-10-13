# Durable project state and continuation

Snapshot: 2026-10-12. Project: Commonstead. GitHub destination: `https://github.com/distractedagain/commonstead`. Original user authorization covers creation/publication to the user's GitHub account; paid services and new charges are prohibited. No automation or unattended/background work has been scheduled.

## Completed locally

0.1.0 CRM workflow, original MIT implementation, shared tenant/role/persistence foundation, browser UI,36 passing workflow/security tests, isolated clean installation and bounded benchmark, synthetic seed data, API/architecture/deployment docs, and a95-group official-source portfolio inventory with every65-entry Help index mapped. See `verification.md` for exact limitations. Do not call this a complete Salesforce replacement.

First-release design decisions: Python standard library + SQLite + vanilla DOM; trusted local evaluation only; one organization per user account with organization-scoped email; four roles; fixed CRM fields/stages; USD cents; manual invitation sharing; no paid API. No public-HTTP production claim. Do not silently add a cloud provider or identity service.

## Exact next steps

1. Read README, architecture, coverage, verification, roadmap and this state file. Run `git status --short`, inspect the current tag/remote commit and available Actions results before assuming publication succeeded.
2. Run `python3 -m unittest discover -s tests -v` and `python3 scripts/verify_clean_install.py` after any code/migration change. Use a scratch database, never the user's live customer data.
3. Finish/verify0.1.0 publication and CI if the publication record still says pending. Inspect staged files and reachable history with `python3 scripts/check_release.py --staged --history`, plus manual diff/license review. No secrets or runtime database belong in Git.
4. Next bounded expansion: see `service-spec.md` for an original case→assignment→comment→knowledge-backed resolution workflow. Add a transactional schema1→2 migration preserving existing organizations, sessions, roles and CRM data; prove rollback and tenant relationships. Implement browser outcomes and tests before claiming any support capability verified.
5. Strengthen shared platform in dependency order: maintained framework/identity boundary, tested backup/restore and migration tooling, custom object/field model and policy tests, then outbox/jobs/workflow semantics. Broader case channels/SLA timers/portals depend on these services; do not mock them as complete.
6. Continue through the whole roadmap: marketing; commerce/revenue; data/integration/analytics; collaboration; industry packs; application development and local-AI options. Every discovered family and alias remains in scope. Refresh pending acquisitions and mutable official docs at each relevant increment.

## Required evidence on each release

Update coverage and portfolio-family status separately. A narrow scenario may be verified while its family is partial. Record source URLs/date, unknown internal behavior, permissions, persistence, failure semantics, current test results, previous-version migration and clean-install evidence, actual performance method, integration access limits, dependency versions/licenses and remote commit/CI result. Use only researched/planned/in progress/partial/verified/blocked statuses.

This file is a handoff, not a claim that work continues after the active run ends. Current unfinished scope includes most of the researched portfolio and production platform operations.
