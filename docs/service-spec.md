# Service increment specification — v0.2

Research date: **2026-10-12, America/Chicago**. Status: **planned**; this document is a specification, not implementation or test evidence. Target: a local internal support workflow using Commonstead's existing organizations, sessions, roles, accounts, contacts, audit and SQLite deployment. It is a narrow part of portfolio group S01.

## Public evidence

The following are publicly documented Salesforce outcomes, reviewed without a licensed tenant or a live behavioral test:

| Source | Documented outcome used as research input |
|---|---|
| [What's a Case?](https://help.salesforce.com/s/articleView?id=service.cases_def.htm&language=en_US) | Cases capture customer issues, support identification and recording, associate an answer, and track closure. |
| [Guidelines for Working with Cases](https://help.salesforce.com/s/articleView?id=service.cases_edit.htm&language=en_US&type=5) | Cases relate to accounts/contacts; permitted users update them, attach articles and report on ownership and status. Configuration affects behavior. |
| [Solve and Close Cases](https://help.salesforce.com/s/articleView?id=service.cases_intro_close.htm&language=en_US&type=5) | A resolved customer issue can be closed; reusable knowledge can help similar cases. |
| [Create and Edit Case Comments](https://help.salesforce.com/s/articleView?id=service.case_comments.htm&language=en_US&type=5) | Case notes persist as related comments; reading and modifying comments require permissions. |
| [Create and Edit Articles](https://help.salesforce.com/s/articleView?id=service.knowledge_article_create.htm&language=en_US&type=5) | Articles can be drafted, reviewed and published; publishing is distinct from editing. |
| [Find, Attach, and Email Articles with the Case Feed Articles Tool](https://help.salesforce.com/s/articleView?id=sf.case_interaction_using_articles.htm&language=en_US&type=5) | Users find relevant knowledge and associate an article with a case. |
| [Salesforce Knowledge Article Versions](https://help.salesforce.com/s/articleView?id=sf.knowledge_article_versions.htm&language=en_US) | Preserving the content associated with a case matters when knowledge changes. |

Everything below is an **original Commonstead design decision**. The five status values, role policy, account/contact consistency rule, immutable publication and API paths are not assertions of Salesforce compatibility. No proprietary interface, content or schema is copied.

## One complete workflow

1. An owner/admin/member creates a case against an existing tenant account, optionally selecting one of that account's contacts, and assigns a tenant user. The case starts `new`.
2. The agent changes status to `in_progress` or `waiting`, adds internal comments, and searches the tenant knowledge list.
3. An owner/admin/member creates a draft knowledge article. An owner/admin reviews and publishes it. Publication makes it eligible to link to a resolution; it does not publish anything to the internet.
4. The agent enters a resolution, optionally links a published article, then marks the case `resolved` and eventually `closed`.
5. An agent can reopen a resolved/closed case by changing status to `in_progress`; the previous resolution and article remain visible, and the status change is audited. An agent may then amend the resolution before resolving again.
6. A viewer reads the case, comments, linked article and service report but cannot mutate them. A second organization cannot see or reference any of this data.

## Records and invariants

Use opaque UUIDs and UTC timestamps as in v0.1. Unknown/wrongly typed fields and client-supplied tenant/author/timestamp values are rejected. All new tables carry `organization_id`; every related-ID foreign key includes organization ID, backed by database constraints and API checks.

| Record | Required data and original rules |
|---|---|
| Case | `subject` (1–250 trimmed characters), `description` (up to 10,000), `account_id` required, optional `contact_id`, `assigned_to` defaults to creator, `status`, `resolution` (up to 10,000), optional `article_id`, creator and created/updated timestamps. Contact must belong to the selected account. Changing an account/contact cannot leave an inconsistent pair. Assignee is an existing user in the same organization. |
| Case comment | Case ID, nonblank `body` (1–10,000 trimmed characters), author and creation time. Append-only in v0.2; no public flag, edit, deletion or notification delivery. |
| Knowledge article | Nonblank `title` (1–250) and `body` (1–20,000), `status` exactly `draft` or `published`, author and created/updated timestamps; publisher and publication time recorded on publish. Published content is immutable in v0.2. A correction creates a new draft/article; old case links keep the original content. |

Case statuses are exactly `new`, `in_progress`, `waiting`, `resolved`, `closed`. Authorized editors may select any status; no queue or SLA engine is implied. Both `resolved` and `closed` require a nonblank trimmed resolution in the merged resulting record, including on direct creation. Clearing resolution while terminal fails. An optional linked article must be a **published article from the same tenant**, checked inside the write transaction. Reopening does not erase earlier resolution text or change the linked publication silently. Reassignment, status changes, resolution changes, comments, draft changes and publication produce tenant-scoped audit events in the same transaction.

No service deletion endpoint is required in v0.2. Existing CRM account/contact deletion must return a clean reference conflict when service records depend on them. Status/detail updates must validate the complete merged result, not just the submitted fields.

## Permissions and visibility

| Action | Owner/admin | Member | Viewer |
|---|---|---|---|
| Read tenant cases, comments, draft/published articles and service report | Yes | Yes | Yes |
| Create/update/reassign/reopen cases; add comments | Yes | Yes | No |
| Create/edit draft article | Yes | Yes | No |
| Publish article | Yes | No | No |
| Change published content | No | No | No |

These are **internal tenant-wide read permissions**, consistent with v0.1. Draft status is an editorial state, not a confidentiality boundary. Lists, searches, details, comments, article links and aggregate reports all filter by the authenticated organization. Other-tenant and nonexistent record IDs both return 404; invalid related IDs return the existing API's validation/not-found convention without leaking another tenant's record. Authentication, CSRF, origin, payload limits and session-time role checks apply to all new endpoints. There is no external customer identity or portal.

## Proposed API and original UI

Reuse the v0.1 record conventions for `cases` and `articles`: authenticated list/detail/create/update under `/api/records/{entity}`. Add `GET/POST /api/cases/{id}/comments`, `POST /api/articles/{id}/publish` and `GET /api/reports/service`. Publish requires `{}` and is idempotent for an already published immutable article. Paginated lists/searches use existing bounds and response envelopes. Server errors use existing structured errors. Paths may change during implementation, but update `docs/api.md` and tests to agree.

Extend the existing original interface with Cases and Knowledge navigation, accessible labeled forms, tenant-member assignment, account-filtered contact choices, status controls, a comment timeline, visible draft/published state, and a published-article selector. Show server validation errors without discarding form input. Hide or disable mutation controls for viewers and publishing controls for members; server enforcement remains authoritative. Render all customer/article text safely as text, without inserting supplied HTML.

The service report returns every status with zero counts where appropriate, plus `total_cases`, `active_cases` (`new + in_progress + waiting`), `resolved_cases` (`resolved` only), `closed_cases` (`closed` only), `draft_articles` and `published_articles`. Counts cover all current records in the tenant, across all time, and use one consistent read snapshot. They are current-state counts, not historical resolution rates, SLA compliance, or response-time metrics.

## Acceptance and release evidence

- **Migration:** initialize a genuine v1 database using the v0.1 schema, insert CRM records and relationships, then upgrade transactionally to v2. Prove IDs, passwords/roles, CRM values, audit and relationships remain unchanged; reopening the v2 database is safe. Clean install reaches v2; an unsupported newer schema is rejected. Rollback a deliberately failed migration without advancing the version or leaving partial tables.
- **Workflow:** create an account/contact case, assign another tenant user, progress through all five statuses, add comment, draft and publish article, link it to a resolution, close, reopen, amend and resolve. Restart the process and verify persisted detail and exact report counts.
- **Invariants:** reject every invalid status, blank terminal resolution, cross-account contact, wrong-tenant account/contact/assignee/article/case, draft-article resolution link and publication by a member. Test constraints directly against SQLite as well as through the API. Changing an existing contact's account must not silently invalidate cases; either reject that CRM update with 409 while referenced or implement an explicitly tested reconciliation rule.
- **Authorization:** viewer writes fail on every mutation; all four roles can read their tenant's data; second-tenant list/search/detail/comments/links/reports cannot leak records or counts. Test revoking a role during an existing session and missing/incorrect CSRF. Draft visibility is intentionally internal and tenant-wide.
- **Publication and rendering:** published title/body cannot change; an old linked article still displays the exact content used. Duplicate publish does not duplicate publication/audit side effects. Script-like customer text is displayed inertly. Browser smoke verifies create, comment, publish, resolve and viewer behavior through the original UI.
- **Report:** use two tenants and a fixture spanning all statuses; counts reconcile exactly before and after reopen, including zero-filled states. Run existing CRM tests unchanged to catch regressions.

Record actual commands/results in the release evidence and coverage matrix. Keep S01 **partial** at product-family level even when this workflow passes. This increment excludes email/chat/voice, routing queues, SLA timers, portals, attachments, notifications, AI, full knowledge versioning and external integrations. It requires no new paid service or background-job infrastructure.
