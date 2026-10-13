# Independent engineering review — first CRM release

Review date: **2026-10-12**. Scope: original Python database/service/HTTP code, role and tenant boundaries, and a source inspection of the original JavaScript DOM construction. This review was performed separately from backend implementation. It is a bounded engineering review, not a penetration test, third-party audit, certification, or approval for internet production.

## Method and evidence

[`tests/test_security_review.py`](../tests/test_security_review.py) exercises real temporary SQLite databases and temporary loopback HTTP servers using the standard library. Test records, passwords and email addresses are fictional. No Salesforce service, customer system, email delivery service or external API is involved.

Run the independent review suite from the repository root:

```sh
python3 -m unittest discover -s tests -p test_security_review.py -v
```

Measured review environment: **CPython 3.15.0, SQLite 3.54.0, macOS 15.8.1 x86_64**. The final independent suite passed **22 tests in 16.006 seconds**, including the relationship-consistency regression added during review. That duration is test execution time, not a throughput benchmark. An earlier sandboxed attempt could not bind loopback sockets; the successful run used permitted local sockets. All five findings below have implementation fixes and the relevant regression checks pass. This result is limited to the inspected code and exercised scenarios.

## Findings and remediation

| Finding | Reproduction and impact | Implementation response | Regression evidence |
| --- | --- | --- | --- |
| Stale authorization between authentication and a write transaction | Pause an admin's HTTP request immediately after authentication; owner demotes that user to viewer; resume the write. The original code authorized from the earlier role snapshot. | `Service.authorized_transaction` rechecks the current database role and session inside the transaction. Authenticated writes and privileged audit reads use it. | `test_in_flight_write_cannot_use_a_role_revoked_before_its_transaction`, `test_demotion_applies_to_an_existing_session`: passed. |
| Invalid non-ASCII CSRF header produced an internal error | A logged-in request with a Latin-1 non-ASCII `X-CSRF-Token` reached the text-only constant-time comparison. This was a malformed-input handling problem, not an observed CSRF bypass. | Compare encoded bytes; reject mismatches with HTTP 403. | `test_non_ascii_csrf_is_a_client_error`: passed. |
| Empty Transfer-Encoding was not rejected | An empty first `Transfer-Encoding` field could evade a truthiness check, including with another transfer-encoding field following it. No successful request-smuggling exploit was established. | Reject any transfer-encoding header presence, including empty and duplicate forms. | `test_ambiguous_framing_and_incomplete_bodies_are_rejected`: passed. |
| File privacy depended on CLI startup and initialization connection was not explicitly closed | Direct database construction under a permissive umask created the database before its final chmod; journaling could begin before that privacy setting. The SQLite connection context manager alone does not close the connection. | Create the database with mode 0600 before SQLite opens it, protect existing sidecars, and explicitly close the initialization connection. | `test_database_and_journal_files_are_private_without_cli_umask`: passed; explicit close verified by source inspection. |
| Moving an opportunity could invalidate a linked activity's account relationship | Create account A, account B, an opportunity in A and an activity explicitly linked to both A and the opportunity; move the opportunity to B. The activity retained A even though activity creation rejects that mismatch. | `Service.update_record` rejects the account change with HTTP 409 while conflicting linked activities exist. The check and mutation share a transaction. | `test_opportunity_account_move_cannot_invalidate_linked_activity`: reproduced failure before fix; passed after fix, with both records unchanged. |

Reviewed source locations: `commonstead/service.py:162` (`authorized_transaction`), `commonstead/service.py:274` (invitation role recheck), `commonstead/service.py:419` (opportunity relationship protection), `commonstead/server.py:110` (framing), `commonstead/server.py:183` (CSRF comparison), and `commonstead/database.py:85` (private creation and connection closure). Line numbers may shift after subsequent edits; the named symbols identify the same review targets.

## Additional boundaries exercised

| Boundary | Concrete evidence |
| --- | --- |
| Organization isolation | Foreign-organization record reads, updates, deletes, relationship IDs, owner IDs and role changes fail; submitting an organization ID in CRM payloads fails. Search, pipeline totals, exports and audit output exclude another organization's data. |
| Role enforcement | Existing sessions observe role demotion. An admin cannot invite another admin or owner or promote themself. Two concurrent owner self-demotions retain one owner. |
| Invitation lifecycle | Two simultaneous acceptances produce exactly one user and one unavailable-token error. Reissued links and expired links fail. Accepting another organization's invitation changes the browser identity to the invited role and cannot preserve the prior owner's write permissions. |
| Atomic imports | A late duplicate email, nonexistent account or required-field error leaves both the contact table and audit count unchanged. |
| Export safety | Formula-leading strings are escaped in all six exported columns. This tests the emitted CSV; it does not certify every spreadsheet application's import settings or preserve a byte-identical raw round trip for escaped values. |
| Input and relational validation | Boolean, string, negative and excessive money amounts fail. Noncanonical or impossible dates fail; a leap-day date and the supported maximum amount succeed. |
| Database initialization | Injecting a schema failure leaves no tables and schema version zero. This establishes rollback of initial schema creation, not compatibility of future migration versions. |
| HTTP boundary | Wrong/duplicate Host, wrong/duplicate Origin, cross-site fetch metadata, duplicate JSON keys, NaN, unpaired surrogates, wrong media type, duplicate length, incomplete body, oversized declared body and transfer encoding fail. Encoded path traversal does not disclose source or database files. |
| Browser credential handling | Session cookies are HttpOnly and SameSite=Strict; logout invalidates the tested token. Secure cookies require the separate HTTPS configuration; this review did not operate a TLS proxy. |

The JavaScript helper `h()` creates text nodes for API-derived content. The reviewed client contains no `innerHTML`, `outerHTML`, `insertAdjacentHTML` or `eval` sink. The inspected download link uses a generated object URL. These are source-inspection observations; this review did not execute a browser-based stored-XSS fuzz suite or an accessibility audit.

## Remaining limits

The local HTTP server remains unsuitable for internet production. Unbounded connection/thread pressure, registration abuse, infrastructure hardening, full identity recovery/MFA, backups and disaster recovery, cross-browser behavior, large-data aggregate limits, multi-host concurrency, plugin isolation and optional integrations are outside the verified scope. See [foundations.md](foundations.md) for the migration gates. SQLite and tests do not make audit history tamper-proof against the machine administrator.

Re-run the complete repository suite and release checks after subsequent changes. Passing these cases supports the specific behaviors above; it does not establish a complete security boundary for every future feature or prove full Salesforce compatibility.
