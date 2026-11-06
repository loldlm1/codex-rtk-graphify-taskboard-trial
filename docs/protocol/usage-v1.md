# Native usage protocol v1

Run the public boundary with Python 3.12 or later; it has no third-party dependencies:

```sh
python3 tools/usage_report.py --manifest examples/usage-v1/manifest.json
python3 -m unittest discover -s tests -v
```

The example is wholly synthetic: 10 input + 4 output = 14 total tokens. Cached
input 3, cache-write input 1 and reasoning output 2 are already subsets. Test
fixtures generate native-shaped records for delegation, retries, compaction,
restart replay and the fixed first-use policy.

Exit 0 means **observed evidence reconciled**. Exit 2 and `evidence_status:
incomplete` identify missing, unsupported or conflicting evidence; allocated totals
are then null. `window_observed_usage` always means observed usage, never a passing
or guaranteed complete billing total. This tool does not decide adoption. Its
`measurement_readiness` remains `pending-live-compaction-restart-validation`;
ticket 22 must supply that separate acceptance before measured arms start.

## Local manifest

Keep the real manifest private. The checked example shows every required key.
Unknown manifest fields and runtime/schema versions fail closed. Paths resolve
relative to the manifest, or may be absolute local paths. The tool reads only
explicitly listed sources, has no discovery/network/configuration/credential access,
and launches no native process. Source IDs, run IDs and phase IDs are intentional
public logical labels (`[a-z][a-z0-9-]{0,47}`); do not put private names in them.

- `schema_version` is 1; `runtime_version` is exactly `0.167.0`.
- `window` contains UTC `start`, exclusive UTC `end`, and fixed `end_policy:
  assessment-report-evidence-freeze`. A null end retains an ongoing window and
  produces an explicit incomplete result. Administrative publication/delivery is
  declared outside that window before results; it cannot replace assessment costs.
- Each `runs` entry has a unique logical `id`, actual native `root_thread_id` and
  `session_id`, `closed` boolean, full `expected_threads`, `sources` and `phases`.
  Each thread entry has `thread_id` and nullable `parent_thread_id`. Inventory is
  a rooted acyclic tree. Actual session metadata and observed subagent **started**
  events must agree; interaction targets and wait calls are not spawn evidence.
- Each source has logical `id`, `kind: native` or `notifications`, local `path`,
  and exact full-file lowercase `sha256`. Capture the digest at a durable boundary;
  changes during ingestion fail closed. Native sources are plaintext canonical
  JSONL with one session metadata identity per file. Include completed descendants,
  archived sources and earlier snapshots needed for full cumulative reconciliation.
  Required compressed/encrypted/unknown metadata is unsupported; do not decrypt it.
- A phase has logical `id`, fixed `category`, UTC `start` and exclusive UTC `end`
  (nullable only for ongoing work). Intervals cannot overlap; every response inside
  the window must belong to exactly one phase. Arm phases also require `workload:
  web|canvas` and `arm: A|B`. Other categories reject those fields.

Allowed categories are `arm`, `activation`, `indexing`, `shared-b-preflight`,
`common-upgrade`, `fixture`, `evaluation`, `probe`, `administration`.

Declare actual root preparation boundaries now, leaving the ongoing common phase
open rather than asserting a closed run. Before B-only provisioning begins, close
common preparation at a durable boundary and start `shared-b-preflight`. Before each
native arm starts, declare its phase boundaries and explicit source/thread inventory;
close them only after its workers/reviews/recovery finish. B activation and initial
indexing belong to that B workload. Finish workers around phase transitions so their
costs cannot cross into another activity unnoticed. Preserve preparation records from
the original execution anchor onward; the original anchor/registry remains local.
The closed ordinary validation sample is only a selected sample, not the complete
trial measurement window. Before final reporting, close evaluation at the assessment
and report-evidence freeze and classify later administration outside the window.

Full source ledgers are reconciled even when the window starts partway through a
long-lived coordinator thread. Records outside the selected window are shown
separately; they are not charged to its arms. UTC response timestamps determine
phase membership, including descendant/retry/recovery responses. Replayed standalone
records must preserve original timestamps; a checkpoint alone cannot establish the
original response time and therefore yields incomplete phase evidence.

## Accounting and fixed allocation

Actual provider response IDs are the deduplication key in this selected evidence
scope. Ownership includes thread, turn, root-turn and session. Identical replays and
embedded latest-record snapshots add zero. Conflicting ownership, counters or
standalone timestamps fail completeness. Distinct retry response IDs count separately;
no identity is synthesized from a timestamp, turn, line number or retry count.

Every unique record must have nonnegative integer counters with exactly the six
supported categories. Total equals input plus output. Cached and cache-write input
must fit within input; reasoning must fit within output. Recompute every turn/thread
cumulative record, then reconcile each thread's final ordinary cumulative snapshot.
Do not add `last`, restored counters, usage metadata, or embedded copies as new costs.

Pinned V2 foreground compaction can produce a ledger/ordinary difference. Preserve
that difference explicitly; allow it only when it equals the unique persisted
compaction response usage. Checkpoints need actual response/window IDs, persisted
replacement-history presence, a checkpoint digest and a matching unique ledger
record. Failed/rejected requests still contribute their observed usage; unexplained
differences remain incomplete. Markers require a valid checkpoint owned by the same
thread in this run/session. A checkpoint's source metadata must match its response's
thread/session ownership. One response binds to one window and one persisted payload;
one window binds to one response. Identical checkpoint replays add no usage or extra
checkpoint entry; conflicting window, history or embedded snapshot evidence is
incomplete. This parser does not certify successful installation,
item lifecycle, two distinct installs or exact-thread reload: those are required live
probe evidence, not consequences of parsing a checkpoint.

Observed response completions must reconcile their six counters with the matching
ledger response in the same run. Native completion events use snake-case counters
and inherit thread ownership from their source; any supplied thread, turn, root-turn
or session identity must agree. Supported completion notifications use the pinned
camel-case counters and explicit thread/turn/response identities. Null, unknown,
unsupported or contradictory completions are incomplete. Repeated consistent
completions add no usage. Arbitrary usage metadata never contributes counters.

Raw arm totals contain all `arm` usage and that B workload's `activation`/`indexing`.
B arm declarations require both first-use categories and shared preflight to be
explicitly declared, even if a phase has no model responses. For each token category:

```text
allocated web-A    = raw web-A
allocated canvas-A = raw canvas-A
allocated web-B   = raw web-B    + shared-b-preflight / 2
allocated canvas-B= raw canvas-B + shared-b-preflight / 2
```

Allocated counters are exact rational strings, so odd shared costs retain halves.
For a synthetic 15-token response in each phase, a B arm with implementation,
activation and indexing costs 45 raw + 7.5 shared = 52.5 (`105/2`) allocated; A costs
15. Common upgrade, fixture, evaluation and the separate probe remain in the full
window total and outside the per-arm gate. Never change allocation after outcomes;
never pool the two workload gates or replace first-use costs with warm reuse.

## Privacy, source limits and readiness

Only allowlisted metadata/counters survive ingestion. Output includes SHA-256
identities, logical source labels and file/checkpoint digests; it excludes raw IDs,
paths, prompts, tool arguments, source histories, error messages and arbitrary usage
metadata. Hashes are stable pseudonymous references, not a claim of irreversible
anonymization. Review output and public labels before publication. Keep raw sessions,
real manifests and private execution anchors outside Git. Do not enable diagnostic
traces, internal raw-event opt-ins, exporters, decryption or new account access.

The native format is pinned to source commit
`086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a`, tag `rust-v0.167.0`.
[Token usage records](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/protocol/src/protocol.rs#L2503),
[checkpoint persistence](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/core/src/session/mod.rs#L4631),
and [foreground compaction](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/core/src/compact_remote_v2.rs#L375)
are version-specific implementation evidence, not a stable public API contract.
Cumulative-only notifications lack per-response identity. Internal raw-event state
can disappear on a cold resume, and diagnostic traces expose request material while
omitting V2 compaction usage. None replaces persisted identity/counter evidence.

Known error/warning/stream-abort, null or unaccounted completion, background or
speculative indicators, missing children/usage/completions, changed digests, unknown
schemas and reconciliation failures produce incomplete results. The selected native
format cannot prove absence of entirely unobservable upstream null-usage responses,
skipped persistence, hidden WebSocket retries, or background/speculative requests.
A self-consistent ledger therefore never establishes universal billing completeness;
`billing_completeness` is always `not-proven`. Those limits remain visible and cannot
be waived by an attractive saving. Required unresolved accounting gaps block a passing
pilot. Keep readiness pending the same short two-compaction/process-restart probe;
do not launch an extra probe or measured arms to fill this implementation's evidence.
