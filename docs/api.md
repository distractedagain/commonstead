# Commonstead API 0.1.0

Base URL: `http://127.0.0.1:8765`. This is an original local JSON API. It is not the Salesforce API. All timestamps are UTC ISO strings, IDs are opaque UUID strings, dates are `YYYY-MM-DD`, and amounts are integer USD cents.

## Transport and sessions

Mutations (`POST`, `PATCH`, `DELETE`) require `Content-Type: application/json`, a single valid `Content-Length`, and a JSON object. Send `{}` for DELETE/logout. Request bodies are capped at 1 MiB; duplicate JSON keys, nonfinite numbers, ambiguous framing, and unsupported controls/types are rejected. No cross-origin API is enabled. Host must match a local/configured host and the server port. Browser Origin must exactly match scheme/Host; command-line clients may omit Origin.

Sign-in returns an HttpOnly, SameSite=Strict opaque session cookie and a JSON `csrf_token`. Send the cookie on authenticated requests and `X-CSRF-Token` on authenticated mutations. If an authenticated browser registers, signs in again, or accepts another invitation, those mutations also require its current CSRF token. `--secure-cookies` adds Secure and requires an HTTPS origin. The server is not production-ready even behind TLS.

Session envelope:

```json
{"authenticated":true,"user":{"id":"uuid","name":"Avery","email":"avery@example.test","role":"owner"},"organization":{"id":"uuid","name":"Example","slug":"example"},"csrf_token":"opaque-value"}
```

Unauthenticated `GET /api/session` returns `{"authenticated":false}`. Errors use `{"error":{"code":"validation_error","message":"Explanation","details":{}}}`; `details` is optional. Common statuses: 400 input, 401 sign-in required, 403 permission/CSRF/origin, 404 missing or other-tenant record, 409 conflict/reference/last owner, 413 body size, 415 media type, 429 login throttle. Failed sign-ins are bounded per organization/email/address and per address in a 15-minute window.

## Identity and administration

| Method/path | Body or result |
|---|---|
| `GET /health` | `status`, `version`, `schema_version`; no customer records |
| `GET /api/session` | Current session envelope |
| `POST /api/register` | `{organization,name,email,password,slug?}` → 201 session; creates organization and owner atomically |
| `POST /api/login` | `{organization: "slug",email,password}` → session |
| `POST /api/logout` | `{}` → revokes current session and expires browser cookie |
| `GET /api/members` | `{items:[{id,name,email,role}]}` within organization |
| `PATCH /api/members/{id}` | `{role}` → `{item:{...}}`; owner only, retains at least one owner |
| `POST /api/invitations` | `{email,role}` → 201 `{token,email,role,expires_at}`; token shown once |
| `GET /api/invitations/preview?token=...` | `{email,role,expires_at,organization:{name,slug}}`; valid bearer token required |
| `POST /api/invitations/accept` | `{token,name,password}` → 201 session; creates invited user; consumes token |
| `GET /api/audit?limit=25&offset=0` | Paginated tenant audit; owner/admin only |

Passwords are 12–128 characters on creation. Names/organization names are 1–120 characters. Slugs are 1–64 characters using lowercase ASCII letters, digits, and single internal hyphens. A normalized organization name generates the default slug; collisions are 409. Email is normalized to lowercase and unique per organization. No email is sent or ownership verified. An owner can invite admin/member/viewer; admin can invite member/viewer. Only a later owner-authorized role change can grant owner.

## CRM resources

`{entity}` is exactly one of `accounts`, `contacts`, `leads`, `opportunities`, `activities`.

| Method/path | Semantics |
|---|---|
| `GET /api/records/{entity}?q=text&limit=25&offset=0` | `{items,total,limit,offset}`; literal text search, default100/max200, offset≥0 |
| `GET /api/records/{entity}/{id}` | `{item:{...}}`; other-tenant and nonexistent IDs both404 |
| `POST /api/records/{entity}` | Direct field object → 201 `{item:{...}}` |
| `PATCH /api/records/{entity}/{id}` | Direct partial field object → `{item:{...}}` |
| `DELETE /api/records/{entity}/{id}` | JSON `{}` → `{deleted:true}`; owner/admin only; referenced records409 |

Records return `id`, `created_at`, `updated_at`, and the fields below. Tenant IDs are not writable. Unknown fields are rejected. Most text is limited to250 characters; website to2048, notes to10,000, email to254. Foreign IDs must belong to the session organization. All organization members can read records; member/admin/owner can create/update.

| Entity | Fields |
|---|---|
| Accounts | `name` required; `website`, `industry`, `owner_id`, `notes` |
| Contacts | `last_name` required; `first_name`, `email`, `phone`, `title`, `account_id`, `owner_id`, `notes` |
| Leads | `last_name` required; `first_name`, `email`, `company`, `status`, `owner_id`, `notes` |
| Opportunities | `name`, `account_id` required; `amount_cents`, `currency`, `stage`, `expected_close`, `owner_id`, `notes` |
| Activities | `subject` required; `kind`, `status`, `due_date`, `assigned_to`, `account_id`, `opportunity_id`, `notes` |

Defaults: owner/assignee=current user; opportunity amount=0,currency=USD,stage=prospecting; lead status=new; activity kind=task,status=open. Optional related IDs may be `null`/empty; optional dates must be empty strings to clear. If both activity account and opportunity are set, they must match.

- Lead statuses: `new`, `contacted`, `qualified`, `disqualified`.
- Opportunity stages: `prospecting`, `qualification`, `proposal`, `negotiation`, `closed_won`, `closed_lost`. Reopening is allowed; no approval or transition policy is implied.
- Activity kinds: `task`, `call`, `meeting`; statuses: `open`, `done`.
- Nonblank contact email is unique, case-insensitively, within an organization. Leads are independent; lead conversion/deduplication workflows are not implemented.
- Opportunity amount: integer0–9,000,000,000,000 cents; boolean, fractional, negative, and larger values rejected. Currency must be `USD`.

## Imports, exports and reports

`POST /api/import/contacts` accepts `{"csv":"..."}`. Exact ordered header:

```csv
first_name,last_name,email,phone,title,account_name
```

1–1,000 rows, six columns each, UTF-8/optional BOM, last name required, valid optional email, no repeated nonblank email in file or tenant. `account_name` must match exactly one existing tenant account (case-sensitive) or be blank. Whole import and audit roll back on any bad row. Result: `{"imported":2}`. The browser accepts a file or pasted contents; the server itself receives text JSON.

`GET /api/export/contacts` returns `text/csv` with the same columns, tenant-scoped. Leading formula/control characters are escaped for spreadsheets, so exported values may include a protective apostrophe. This endpoint exports all contacts; it is not a bulk streaming integration.

`GET /api/reports/pipeline` returns `stages:[{stage,count,amount_cents}]` for all six stages and `totals:{opportunity_count,pipeline_cents,won_cents,accounts,contacts,leads,open_activities,overdue_activities}`. Pipeline excludes both closed stages; won value includes only `closed_won`. Counts are for this organization, across all time. Overdue means open and due before UTC today. Dashboard CSV export is generated client-side from this response with a UTC retrieval timestamp.

No OAuth, API keys, webhooks, Salesforce sync, SOQL, background workflow execution, or third-party connectors are implemented in this release.
