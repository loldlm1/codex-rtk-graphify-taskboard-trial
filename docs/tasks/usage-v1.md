# Shared native usage protocol v1

## What to build

A selected-runtime usage report accounts for coordinator and descendants, diagnoses missing evidence, and applies the pilot's fixed first-use cost policy through one public ingestion/reporting boundary.

## Acceptance criteria

- [ ] Reuse suitable existing reporting capabilities where available; add only the minimum executable support needed for complete, reproducible accounting.
- [ ] Test sanitized native events with known totals for descendants, retries, distinct responses, compaction usage, embedded duplicates, and replayed records after restart.
- [ ] Attribute actual thread/response identities and lineage, deduplicate each response once, and reconcile per-response sums against cumulative totals.
- [ ] Verify selected-runtime category semantics so cached input and reasoning are reported without being added twice.
- [ ] Missing descendants or usage, conflicting duplicates, unsupported schemas, and failed reconciliation produce explicit incomplete results rather than passing totals.
- [ ] Each B arm includes its own activation and initial indexing; one-time shared B-only provisioning/tool-preflight model usage is split equally across the two B workloads, with raw and allocated totals visible.
- [ ] Common upgrade validation, fixture construction, comparative evaluation, and the separate recovery probe remain outside each per-arm gate but inside complete-trial reporting; retain preparation evidence captured from #14 onward.
- [ ] Verify ordinary native delegated usage on the accepted runtime. Use the same short recovery probe in #22 for final live compaction/restart reconciliation, avoiding an extra probe; do not launch measured arms until that validation passes.

Canonical executable measurement support belongs on `protocol/v1`, not the
application starter branch. It is shared by both workload repositories.
