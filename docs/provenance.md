# Source provenance and dependency record

Record date: **2026-10-12**.

## Independent implementation boundary

Commonstead is an independent open-source project. Public Salesforce product descriptions and documented user outcomes inform the capability research; they do not supply implementation code or establish API compatibility. The implementation, naming, screen design, CSS and synthetic fixtures are written for this repository. The root `LICENSE` governs original project contributions.

No Salesforce proprietary source, private customer data, confidential documentation, logos, illustrations or other proprietary assets are incorporated. No Salesforce account, private environment or access-control bypass is required for the delivered local workflow. Product names in the research matrix identify the subject of research and do not imply endorsement or affiliation. Salesforce behavior that has not been observed in public documentation or authorized testing remains an inference or an open question.

Research links are references, not vendored dependencies. No upstream code from Django, Frappe, ERPNext, SuiteCRM, Keycloak, Celery, Temporal, Ollama or llama.cpp is copied into the original implementation. Their current published licenses and adoption decisions are recorded in [foundations.md](foundations.md). Incorporating any of them later requires a new dependency entry with a pinned version and its actual license/notice files.

## First-release runtime inventory

| Component | Relationship | License/source | Version policy |
| --- | --- | --- | --- |
| Commonstead source, static UI, tests, synthetic demo fixtures | Original repository files | Root `LICENSE` | Record release tag and commit in release notes. |
| CPython and standard library | Required installed runtime; not copied into the application source | [PSF License Version 2 and incorporated-software notices](https://docs.python.org/3.12/license.html) | Python 3.12 or later; actual tested interpreter versions belong in CI/release evidence. |
| SQLite | Runtime library used through Python sqlite3 | [Public-domain dedication](https://www.sqlite.org/copyright.html) | Supplied by the installed Python/platform; inspect `sqlite3.sqlite_version` for an actual deployment. |
| Browser | External HTML/CSS/JavaScript runtime | Vendor-dependent; not redistributed by this source repository | Tested browser and version must be recorded when UI checks run. |
| pip-installed Python packages | None required by core runtime | Not applicable | Recheck when package metadata changes. |
| npm packages, downloaded fonts or JavaScript CDNs | None required by core runtime | Not applicable | Static resources are served locally. |
| AI runtime, model weights, email/SMS/payment SDKs | Not used by the first release | Not applicable; future licenses are unreviewed | No model weights are included and no paid account is required. |

The operating system, browser, Python distribution and optional container tooling have their own dependencies and notices. "No application package dependencies" does not mean an entire computer or container image has no third-party software. If a Python/OS container is distributed, preserve that image's licenses, record its immutable digest, and inventory its packages. Development tools and CI actions are separate from application runtime dependencies and must be recorded in their configuration; their presence does not establish a completed supply-chain audit.

## Research register

All entries below were consulted on **2026-10-12**. The portfolio research has its own product-specific source URLs and evidence labels. These references cover architecture decisions only.

| Topic | Primary sources | Evidence use |
| --- | --- | --- |
| Python runtime/HTTP | [License](https://docs.python.org/3.12/license.html), [HTTP server documentation](https://docs.python.org/3.12/library/http.server.html) | Runtime notices and explicit production limitation. |
| Django | [Overview](https://www.djangoproject.com/start/overview/), [license](https://github.com/django/django/blob/main/LICENSE), [deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) | Framework evaluation and next-release operations gates. |
| Frappe ecosystem | [Framework docs](https://docs.frappe.io/framework/user/en/introduction), [framework repository](https://github.com/frappe/frappe), [license/trademark policy](https://docs.frappe.io/legal/others/license-and-trademark), [ERPNext license](https://github.com/frappe/erpnext/blob/develop/license.txt), [CRM repository](https://github.com/frappe/crm) | Component boundaries, capability candidates and separate software/branding terms. |
| SuiteCRM | [User guide](https://docs.suitecrm.com/user/), [licensing](https://docs.suitecrm.com/admin/licensing/) | Mature CRM alternative; no code imported. |
| Keycloak | [Documentation](https://www.keycloak.org/documentation), [repository](https://github.com/keycloak/keycloak) | Identity-provider candidate and Apache-2.0 notice. |
| Database engines | [SQLite use cases](https://www.sqlite.org/whentouse.html), [SQLite copyright](https://www.sqlite.org/copyright.html), [PostgreSQL license](https://www.postgresql.org/about/licence/), [row security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) | Local storage tradeoffs and planned database defense in depth. |
| Async infrastructure | [Celery repository](https://github.com/celery/celery), [Celery license](https://github.com/celery/celery/blob/main/LICENSE), [Temporal server](https://github.com/temporalio/temporal) | Queue/workflow candidates; no integration implemented. |
| Local AI | [Ollama repository](https://github.com/ollama/ollama), [Ollama FAQ](https://docs.ollama.com/faq), [llama.cpp repository](https://github.com/ggml-org/llama.cpp) | Optional runtime candidates, MIT notices and variable hardware needs; not model-license approval. |

## Rules for subsequent contributions

For each added package, asset, dataset, adapter or model, record its upstream URL, exact version/commit/digest, license identifier and file, modification status, required notices, and destination paths. Preserve copyright notices. An open-source code license does not automatically cover trademarks, hosted services, sample datasets, documentation or model weights.

Keep synthetic demo data unmistakably fictional. Never use live contact lists, mailbox exports, credentials, access tokens, private URLs or production database files as fixtures. Public release review must inspect the staged files and Git history for secrets and private data as well as dependency license conflicts; a statement in this document is not evidence that those checks passed. Record the actual scan/check results in release evidence, and leave unresolved licensing items blocked until reviewed.
