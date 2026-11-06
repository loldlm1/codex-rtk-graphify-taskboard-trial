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
  JSONL with one canonical owner per file. Include completed descendants,
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

The pinned writer can leave a truncated JSONL row and retry the same queued item
after reopening. The reader accepts a narrowly verified partial-write retry: an
immediately following complete row, the same next ordinal after the preceding
valid row, a strictly later native timestamp, and an exact serialized byte prefix
after the timestamp. The fragment must contain a complete native timestamp,
ordinal and supported record type. The next ordinal, if present, must advance once.
The full retry must be a valid usage record or `item_completed` event with owning
thread/turn identities; the pending item's ordinal never replaces a provider
response ID. A fragment may end before its payload because the pinned writer
retains that exact queued item at that ordinal until a successful write. Both
timestamps must stay in the same declared phase and window membership. Only the
complete valid record contributes identities or counters. The full source digest
still includes every byte. Each accepted pair appears in its source's
`partial_write_recoveries` with line numbers, ordinal, type and both row digests.
Unmatched, incomplete/ambiguous envelopes, changed, intervening, repeated malformed,
unsupported or cross-boundary fragments remain incomplete; source objects reject
duplicate JSON keys.
This does not recover omitted records or infer provider response identities.

A forked child may contain copied parent metadata/context after its initial own
metadata. Exclusion requires an explicit integer `subagent_history_start_ordinal`,
own metadata at ordinal zero, `forked_from_id` equal to its distinct actual parent,
and contiguous ordinals through the stated boundary. Copied metadata at ordinal
one must match a separately ingested canonical parent source. Earlier context
counters, completion and abort markers do not belong to the child. Inherited usage
records must match an independently present original parent record; they add zero.
Unknown/malformed history, inherited accounting types without supported ownership
proof, missing boundaries/parents and foreign metadata remain incomplete. The
source's `inherited_history` reports the boundary, excluded row count and parent
hash. A generic first-metadata-wins rule is insufficient.

## Explicit active-root window closure

The default remains a strict closed run: `closed: true` requires actual completion
of every observed owning turn, including started turns without usage rows. A
completed turn without model usage does not require a synthetic usage row.
`task_started` and its `turn_started` alias require a valid nonempty string
`turn_id`; missing, null or malformed identities are incomplete. Missing/null
`turn_context.turn_id` remains supported by the pinned optional context schema.
`closed: false` without the opt-in below is always incomplete. A completed provider
response is not completion of its owning turn.

When the original coordinator must finish its assessment and report during its own
still-active terminal turn, that run may use `closed: false` with one additional
`window_closure` object. This certifies only the exclusive accounting window; the
report explicitly gives `kind: root-response-boundary`, `accounting_window: closed`
and `root_turn_completion: unclaimed`. It never inserts a turn-completion event.

| Field | Required value |
| --- | --- |
| `kind` | `root-response-boundary` |
| `source_id` | Logical ID of the canonical native root full-history prefix |
| `turn_id`, `response_id` | Actual owning root turn and last completed provider response in that prefix |
| `response_ordinal` | Actual ordinal of that standalone native usage record |
| `source_bytes` | Exact byte length of the retained immutable prefix |
| `last_ordinal` | Actual ordinal of its final complete native row |
| `cutoff` | Same UTC instant as the non-null exclusive `window.end` |

The source's existing `sha256` binds every retained byte. This mode additionally
requires newline-terminated rows and an uninterrupted ordinal sequence from zero,
with only the already verified partial-write retries allowed. Include an ordinary
cumulative snapshot after the anchor record. The anchor must be inside the window,
in one closed non-administrative phase, and belong to the run's actual root/session
and terminal owning turn. All declared phases must be closed. Every row in that root
prefix must precede the cutoff, and no additional source may introduce a later or
otherwise omitted root response. Embedded-only, earlier, foreign or missing anchors
and mismatched byte/ordinal provenance are incomplete.

Every other root turn and every child turn, including a started owning turn with no
usage row, still requires actual completion. A later invalid start leaves the root
boundary unverified. The full earlier history, source and
spawn inventory, phases, ordinary/ledger counters, compaction bindings, completion
counters and omission indicators receive the same checks. Any issue keeps allocation
null; neither billing completeness nor live compaction/restart readiness is promoted.

Capture this boundary locally before later administrative responses:

1. Finish descendants, assessment and report-evidence work. Fix the exclusive cutoff
   and close its phases; classify subsequent administrative publication outside it.
2. Copy the original root source's complete byte prefix, retaining every row from
   ordinal zero through an ordinary snapshot after its actual last provider record.
   Use a new immutable filename in a private directory (mode 0700), with the raw
   prefix and manifest readable only by their owner (mode 0600).
   Do not normalize, filter, fabricate identities or append completion. Flush and
   durably retain the copy before hashing it; retain the unchanged original privately.
   Never copy a snapshot into another Codex home or commit it to Git.
3. Verify the copy equals that exact prefix of the original. Keep private provenance
   with original/prefix digests, prefix byte length and final ordinal. Inventory all
   children and explicit sources; retain their actual completed source histories.
4. Bind the exact prefix digest, byte count, ordinals, actual response/turn identities
   and cutoff in the private manifest, then run the public CLI. Complete and check the
   assessment/report during the owning root turn; later publication uses the fixed
   inputs. Additional assessment work belongs before the freeze and requires an
   updated snapshot/window. No background watcher or later unverified publisher
   supplies certification.

An immutable completed-turn snapshot remains preferable when same-turn certification
is unnecessary. Keep real IDs, source paths, snapshots and manifests private.

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
[Writer recovery](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/rollout/src/recorder.rs#L1828)
keeps pending items and advances ordinals only after successful writes; reopening
terminates partial rows, and serialization supplies a fresh timestamp on retry.
[Fork history metadata](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/protocol/src/protocol.rs#L3485)
defines the first own-history ordinal;
[thread creation](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/thread-store/src/local/create_thread.rs#L61)
passes that boundary to the recorder. These facts justify only the checked
conditions above, not general corruption recovery or universal completeness.
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
