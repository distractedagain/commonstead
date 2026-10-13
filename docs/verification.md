# Release verification

Research/release date: **2026-10-12 America/Chicago**. Runtime timestamps may be October13 UTC. This document records actual executions, not expected results.

## Local test results

- CPython3.15.0, SQLite3.54.0, macOS15.8.1/Darwin24.6.0, x86_64.
- `python3 -m unittest discover -s tests -v`: **36 tests passed in25.495seconds** after the final backend fixes. These comprise14 business/HTTP tests and22 independent adversarial tests. The parent integration run also passed; timings vary per run.
- `python3 scripts/verify_clean_install.py`: **passed**. Copied only source/static files to a fresh directory, created a venv with no pip/system packages, ran isolated Python (`-I`, user site disabled), verified an empty third-party distribution list, tested real HTTP health/static/register/create, stopped/restarted the server, signed in and recovered the persisted account.
- Synthetic seed: **passed**. Three accounts/contacts/opportunities, one lead/activity, generated password login, exact report totals, safe repeat refusal. No fixed runtime credential is shipped.
- `node --check commonstead/static/app.js`: **passed**. Node is development-only, not a runtime dependency.

The restricted execution sandbox initially refused loopback sockets. Those invocations did not test HTTP; reruns with authorized local socket access produced the results above. No tests were skipped to obtain a passing result. See [independent findings and fixes](review.md).

## Browser evidence

Manual interaction in the Codex in-app browser on the local host used only fictional `.test` identities and a separate scratch SQLite database outside the source repository. The browser provider did not expose a precise engine/version in its metadata; broad cross-browser support is unverified.

Observed through the rendered interface: organization creation; owner sign-in; account creation; two-contact CSV import; lead creation and qualification; opportunity creation with exact `$24,000.50` and advancement from qualification to proposal; invitation creation and redemption; member session; owner role update to viewer; activity assignment to the teammate; and dashboard totals (one account, two contacts, one lead, one opportunity, one open activity,2,400,050 pipeline cents). Dashboard rounds displayed dollars and labels this; its data/API retain exact cents. Captured browser error/warning logs were empty for this run.

This is manual functional/visual evidence, not an automated browser regression or accessibility audit. Native labeled inputs, tables, dialogs, keyboard focus and reduced-motion CSS are present; assistive-technology coverage and cross-browser testing remain open.

## Bounded performance measurement

Command: `python3 scripts/benchmark.py`. Same local environment. One temporary tenant,250 accounts,250 opportunities,500 imported contacts. Standard timer `time.perf_counter_ns`; one untimed warm-up before30 samples per read operation; p95 uses nearest rank. The OS cache was not flushed.

| Operation | Samples | Median | p95 / one-shot result |
|---|---|---|---|
| List100 accounts | 30 | 2.030ms | p95 2.550ms |
| Pipeline report | 30 | 1.810ms | p95 1.972ms |
| Atomic500-contact CSV import | 1 | Not applicable | 148.212ms wall time |
| Registration with600,000 PBKDF2 iterations | 1 | Not applicable | 253.875ms wall time |

These measure direct service calls on one machine, including database access. They exclude HTTP latency, browser rendering and concurrent users. They establish no throughput, capacity, scalability or production performance guarantee.

## Publication and CI

Destination: `distractedagain/commonstead`. Authentication has been verified with the authorized GitHub account. Publication, exact remote commit, tag/release and available CI results will be recorded after those operations complete. No success is implied by workflow configuration.

The local machine has no available Docker CLI/daemon, so container execution is not locally verified. The configured public-repository CI uses standard `ubuntu-latest` runners, without paid larger runners, caches or uploaded Actions artifacts. [GitHub's current billing documentation](https://docs.github.com/en/billing/concepts/product-billing/github-actions) says public repositories using standard hosted runners have free compute. No service purchase or cloud deployment is requested by CI.

## Release review boundary

`scripts/check_release.py` performs bounded pattern scans for credentials/private paths, rejects runtime data/credential files, checks original source imports against the standard library, and supports staged/history inspection. It is a hygiene check, not a comprehensive secret detector or license audit. Manual inspection must confirm intended source/docs/tests, original assets, fictional data and no vendored proprietary code. The [provenance record](provenance.md) lists runtime/platform obligations and unadopted OSS foundations.
