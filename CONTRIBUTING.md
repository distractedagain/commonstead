# Contributing

Start from the [roadmap](docs/roadmap.md). Keep one deliverable workflow per change, with persistence, tenant/permission checks, failure behavior, and test evidence. Update the product matrix and coverage claims when behavior changes. Never label a stub, fixture, or mock as a verified integration.

Run the README test commands in a temporary database. Tests must use fictional `.test` addresses and synthetic entities. Add cases for another organization, another role, malformed input, and partial-failure rollback where relevant. Use original code and public behavioral documentation. Do not submit Salesforce source, copied UI/assets, private tenant exports, proprietary SDK code, or credentials.

There are no third-party runtime packages in v0.1.0. Before adding one, record its exact version, source, license and notices, maintenance/security posture, free-use constraints, and replaceability in `docs/provenance.md`. Model weights require their own license review. Preserve the MIT license and upstream obligations.

The backend separates storage, domain operations, and HTTP transport; the frontend uses standard DOM APIs with text nodes for user data. Prefer small modules and explicit behavior. Changes to schema require a numbered, transactional forward migration, backup instructions, and fixtures proving existing data survives an upgrade. Never silently reset a database or downgrade its schema.

Pull requests should describe the concrete user behavior, relevant official-source research, compatibility limits, and actual verification. Keep contribution discussions free of private personal/customer information.
