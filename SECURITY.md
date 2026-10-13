# Security scope

Commonstead 0.1.0 is a local development release, not an audited production service. Run it on a trusted computer with a protected OS account. The HTTP adapter is Python `http.server`, which is not recommended for production by its upstream documentation. A reverse proxy does not remove its application-level limitations.

Implemented controls include organization-scoped queries and composite foreign keys; server-enforced roles; salted PBKDF2-SHA256 passwords; hashed opaque session and invitation tokens; expiring sessions and one-use invitations; JSON-only mutations; origin/Host checks; authenticated CSRF checks; CSP; parameterized SQL; transactional writes/audit; login throttling; bounded imports and request bodies; and restricted database file creation permissions. These controls have bounded tests, not a security certification.

Known limitations:

- No MFA, SSO, email verification, password recovery/change flow, account suspension, or session administration UI.
- Anyone with local access to the listening endpoint may register a separate organization. Registration is not an enterprise provisioning policy.
- A valid invitation link is a bearer credential; identity is not independently verified by email. Share it only with the intended recipient. A new invite for the same email invalidates outstanding invites.
- All tenant members can read all tenant CRM records; there is no field-level, object-level custom, or record-sharing policy. Owners/admins cannot delete a referenced record until its relationships are resolved.
- No encryption at rest beyond what the host provides, no immutable audit log, no malware scanning, no distributed rate limiting, and no denial-of-service guarantees. Audit details intentionally avoid record contents and credentials.
- No out-of-process job runner, external webhook handling, public OAuth API, compliance certification, penetration test, independent accessibility audit, or capacity guarantee.
- The host administrator can inspect/modify SQLite and application files. Tenant isolation addresses application users, not a malicious host administrator.

For a suspected vulnerability, do not post private data, tokens, or exploit credentials in a public issue. Use GitHub private vulnerability reporting if the repository owner enables it; otherwise request a private contact channel without disclosing the exploit. No monitored security mailbox or response SLA is promised.

Before remote deployment, migrate to a maintained production framework/server, review identity/session lifecycle and provisioning, add ingress rate limits and resource bounds, configure TLS and trusted origins/hosts, test backups/restoration and upgrades, and complete a deployment-specific security review. See [foundation decisions](docs/foundations.md).
