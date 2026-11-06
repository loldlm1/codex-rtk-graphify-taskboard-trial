# Usage protocol v1 validation

Scope is the [approved shared accounting contract](../tasks/usage-v1.md), implemented
only on `protocol/v1`. This is agent implementation/test evidence. The maintainer
owns scope and approvals; root coordination owns integration/final review and tracker
updates. No application starter or measured arm was modified or launched.

ECC `tdd-workflow` supplied the sole implementation/test cycle, explicitly replacing
delegated Matt TDD. ECC `search-first` reused the existing exact-version native
research; cumulative notifications lacked response identities, internal raw flags
were not durable across cold resume, and unsafe/incomplete diagnostic traces were
unsuitable. A small stdlib reader was necessary; no dependency was added. ECC
`security-review` and `verification-loop` guidance covered local inputs, private
session material, output projection and final checks. No orchestration was nested
and no RED/GREEN/refactor checkpoint commits were created.

## Actual RED and GREEN

The runner resolved to Python 3.12 stdlib unittest; there was no package manifest,
third-party test runner, configured type checker or linter. Tests use the real CLI
in subprocesses with disposable, wholly synthetic native-shaped JSONL/manifest data.
The missing-file scaffold observation was not treated as behavioral RED. A runnable
CLI scaffold then returned an incomplete report, and known-total/diagnostic
assertions failed as intended before accounting implementation.

| Behavior | Actual RED | Actual GREEN / guarantee |
| --- | --- | --- |
| Native totals, lineage, retry/replay/checkpoints, subset categories, incomplete inputs, allocation | 9-test target failed assertions against runnable unimplemented CLI | Same target passed after implementation |
| Replayed native sources and per-thread completion ownership | Two new assertions failed | Identical source replay adds zero; one thread cannot borrow another thread's completion |
| Malformed local metadata, B first-use declarations, hashed response ownership | New output/status assertions failed; malformed token info raised an observed exception | Inputs now yield safe incomplete JSON without traceback/raw values; B policy and hashed ownership are enforced |
| Original response timestamp vs embedded checkpoints | Two assertions failed | Standalone timestamp conflicts and embedded-only original timing fail completeness |
| Manifest-relative paths and unsupported accounting schemas | Two assertions failed | Portable source resolution; unknown schemas cannot pass |
| Ordinary notifications / failed turns | Mismatched notification assertion failed | Cumulative snapshots match ledger prefixes; malformed/failed metadata is incomplete |
| Missing checkpoint / invalid replacement-history shape | Focused assertions failed against otherwise complete native evidence | Compaction markers require checkpoints; invalid history shape cannot certify persistence |
| Review fixes: checkpoint ownership/bindings and observed completions | All four new CLI tests failed intended assertions before code changes (22 failing assertions/subtests); the existing 20 passed | Markers require their own thread's checkpoint; conflicting response/window/persisted metadata and completion counters/ownership are incomplete; identical replays remain valid |

After GREEN, source/checkpoint projection was kept minimal and evidence was rerun.
The original broad omission test also lacked turn-completion evidence; that fixture
was corrected so its focused RED isolated the missing-checkpoint behavior. This
avoids claiming a failure caused merely by another missing requirement.

Final command `python3 -m unittest discover -s tests -v`: **24/24 passed**. Subtests
cover missing/null usage and identity, category arithmetic, conflicting duplicates,
unknown runtime/schema, missing descendants/starts/counters/completions, digest and
file failures, private-input exclusion, open windows/runs, phase overlap/gaps, fixed
B allocations, administration outside the window, retries/restart and compaction
snapshots. These are public ingestion/report outcomes, not private-helper or prose
tests. The synthetic policy example charges 15-token phases as 15 for A, 45 raw for
B, and `105/2` allocated B after the exact half-share; common costs remain visible
in the full window.

The independent three-case review reproduction was rerun against the fixes: all
three now return exit 2 / incomplete with null allocations and the specific
`missing_compaction_checkpoint`, `conflicting_compaction_checkpoint` or
`completion_reconciliation` issue. Additional public CLI cases retain successful
own-thread checkpoints, identical checkpoint replays, consistent repeated native
completions and pinned notification completions. Counter/ownership/schema conflicts
are rejected rather than described as billing limitations.

## Measured coverage and final checks

A task-local stdlib `sys.settrace` hook followed each CLI subprocess. Fresh hit files
for this final source were unioned and compared with AST executable statement-start
lines, excluding docstrings. Result after the review fixes: **446/491 = 90.84%** for
`tools/usage_report.py`.
This is statement-line coverage, not branch coverage. Remaining unexecuted lines
mostly reject additional malformed manifest inventories/labels/cycles/intervals,
conflicting session metadata and additional omission/source-error variants. It is not a
claim that every possible malformed input or branch was tested. Instrumentation and
raw logs remain local; no dependency or coverage framework was introduced.

- `python3 -m py_compile tools/usage_report.py tests/test_usage_report.py`: passed.
- Runnable synthetic example through the CLI: exit 0, reconciled, 14 total tokens.
- `git diff --check`: passed.
- Repository diff, allowlisted output, private-path/session-ID/credential-pattern
  scans, source scope and documentation links were checked directly.
- Type/lint/security dependency commands: not applicable; none configured and no
  third-party dependencies. This does not claim an external vulnerability scan.
- Current `protocol/v1` was merged into the worker before handoff; affected tests
  and native sample were rerun. Root owns subsequent integration and review.

## Existing real selected-runtime sample

The [sanitized native summary](ordinary-native-sample.json) contains only hashed
identities and allowed counters, not raw sessions, IDs, machine paths, histories,
error messages or credentials. It was produced from the already accepted native
0.167.0 feature/process-restart evidence, without any new native/model/MCP call.

All nine threads reconcile every turn/thread cumulative record and all final
ordinary counters. The final sample has **108 unique responses**: 54 coordinator
and 54 across eight descendants. Input is **5,722,558**, cached input **5,521,280**,
output **55,447**, reasoning output **17,424**, cache-write input 0; total is
**5,778,005**. Subsets are not added again. Ordinary/ledger delta is zero.

A local metadata-only projection of the original pre-restart root records plus the
unchanged descendant evidence reconciles **103** responses / **5,276,955** total
tokens. Reingesting that projection alongside the existing full native sources
recognizes **49 replayed root responses**, adding zero for them; **five new actual
root responses** bring the total to 108 / 5,778,005. This reuses the real existing
restart sample; it is not a new restart experiment.

All three existing private manifests were rerun through the fixed public CLI. Their
statuses, response/duplicate counts and every usage category remain unchanged:
108 / 0 for the ordinary sample, 103 / 0 before restart and 108 / 49 after reingestion.

There are **zero live compaction checkpoints** in this sample. Synthetic compaction
coverage and ordinary native reconciliation do not establish final compaction
acceptance. The same short ticket-22 probe must prove two distinct real installed
compactions and exact-thread process-restart reconciliation. Measurement readiness
is pending that evidence, and required unresolved accounting gaps block a passing
pilot. Self-reconciliation does not prove universal billing completeness: null
upstream usage, skipped writes, hidden retries and background/speculative work can
be unobservable. The [protocol limits](usage-v1.md) remain part of every result.

No full-trial total, adoption gate, token saving, target merge, release or deployment
is claimed. The next permitted step is independent root review/integration, followed
by the already approved shared probe when its other dependencies are satisfied.

## Native writer retry and fork-history repair

Actual preflight files exposed two supported-runtime ingestion gaps: truncated
writes followed by the writer's same-ordinal retry, and child files containing
inherited parent context before their explicit own-history boundary. The pinned
[writer](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/rollout/src/recorder.rs#L1828)
retains unwritten queued items and their ordinal, reopens and terminates the partial
line, then serializes the same item with a fresh timestamp. The
[boundary definition](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/protocol/src/protocol.rs#L3485)
separates inherited model context from the child's own projected history. The
[reader contract](usage-v1.md) records the exact accepted conditions and audit fields.

ECC TDD remained the sole implementation cycle; no checkpoint commits were made.
The existing 24 tests passed while new public CLI assertions produced four intended
failures for missing retry/fork handling and source ownership. A second RED exposed
five ambiguous-prefix/owner/duplicate-key cases. The pinned queue/ordinal proof then
justified accepting a complete known envelope truncated before its payload: the
actual short-header positive and ordinal-neighborhood negative produced three
further intended failures before the final fix. Every corresponding target was
rerun to GREEN. Final `python3 -m unittest discover -s tests -v`: **35/35 passed**.
The 11 added tests include parameterized changed ordinals/types/owners/counters,
missing/foreign fork metadata, missing canonical parents, unknown/malformed inherited
rows, unmatched/nonadjacent retries, incomplete envelopes, duplicate keys, phase and
window crossings, source hashes, and unexplained cumulative differences. Only full
valid response records supply provider identities and counters. The original three
independent false-success reproductions also remain **3/3 PASS**.

Fresh statement-line coverage after the final repair: **568/617 = 92.06%**, measured
with the same task-local stdlib subprocess trace and AST method. Branch coverage is
unmeasured. Remaining lines mostly cover additional malformed manifest, notification,
metadata and omission variants. Compilation, the 14-token example, whitespace,
changed-file privacy/output projection and scoped source review passed. There is no
configured third-party build, type checker, linter or security scanner; no dependency
or runtime/configuration/trace change was introduced.

The public CLI read unchanged, fully hashed native sources and actual notification
files for two closed native preflight trees. One reconciled **7 responses / 211,391
tokens**, the other **9 responses / 265,831 tokens**, each with its actual root and
child, zero ordinary/ledger delta, and zero issues. The original ordinary and restart
manifests remain **108 / 0 duplicates / 5,778,005 tokens**, **103 / 0 / 5,276,955**
before restart, and **108 / 49 / 5,778,005** after replay.

Focused parser/counter audits of their two outer coordinator workers recovered all
five observed adjacent partial-write retry pairs from the full unchanged files.
Their actual parent/session lineage was retained. Per-turn/thread accumulation and
final ordinary counters match: **68 responses / 7,649,442 tokens** and **76 responses
/ 10,207,101 tokens**. These are selected-source audits; the ongoing preparation
root and recursive inventory still require the coordinator's complete open-run
report. No outer worker was relabeled as a root, source was normalized, partial row
was charged separately, or missing provider identity was synthesized. Raw files,
private manifests, digests and detailed evidence remain outside Git. Universal
billing completeness and the same two-compaction/process-restart live gate remain
unproven; no full-trial total or readiness acceptance is claimed.

## Active-root response-boundary window

A separately selected opt-in closes an exclusive accounting window while its actual
root turn remains active. The [manifest contract and capture recipe](usage-v1.md#explicit-active-root-window-closure)
retain strict default run closure. The optional run `window_closure` requires
`closed: false`, an actual standalone terminal root provider response/turn, its
ordinal, a full-history prefix's exact byte count/final ordinal and existing digest,
and the exclusive cutoff. Output explicitly states `accounting_window: closed`,
`kind: root-response-boundary` and `root_turn_completion: unclaimed`. Every other
owning root/child turn still requires real completion; counters, omissions,
compaction checks, fixed allocation and billing/readiness limits remain mandatory.

ECC TDD supplied the sole implementation cycle with no checkpoint commits. Eight
new public CLI test methods cover the positive boundary and parameterized strict
negatives. The initial 42-test usage target had four intended assertion failures
because the new contract was unsupported. A further focused RED had three failures
for started owning turns without usage; those turns are now completion-checked.
An explicit output-field RED failed on the missing window status. Final review
then produced an actual false-pass RED for an older response replayed after a newer
one. First-seen distinct response order prevents that replay from moving the old
identity forward. Each affected target was rerun to GREEN. Strict mode, other root
turns, unfinished workers, unknown/missing bindings, embedded/foreign/earlier anchors,
open windows/phases, ordinal/byte gaps, later records, counter differences and error
indicators remain incomplete with null allocation. Verified retries and explained
compaction differences still reconcile through the opt-in.

The already completed native-21 root/child sample supplies a real boundary check
without a new native launch or probe. The unchanged full sources reconcile nine
responses / **265,831 total tokens**. A privately retained, byte-exact full-history
root prefix ends at ordinal 49, after the real last provider record at ordinal 48
and before the actual final turn-completion event at ordinal 50. The prefix is
242,360 bytes. Strict mode rejects it solely for missing turn completion; explicit
window mode reconciles the same nine responses and every usage category, with zero
ordinary/ledger difference. Original sources remain unchanged. The private original
and prefix digests, byte/ordinal proof, manifests and reports stay outside Git; the
raw snapshot and manifest use owner-only access in a private directory.

Final validation: **64/64 tests passed**, including all **43** public usage CLI
tests and **21** existing Graphify tests, with the three provisioned local runtime
tests enabled. The original independent false-success reproductions remain **3/3
PASS**. Existing ordinary / pre-restart / replay samples retain respectively
108 / 103 / 108 responses and 5,778,005 / 5,276,955 / 5,778,005 tokens; 49 replay
records still add zero. Compilation, the 14-token strict example, whitespace and
changed-file input/output privacy review pass. Type checking, lint and external
security scanners remain unconfigured; no dependency or runtime/configuration was
added. Fresh statement-line coverage is **631/677 = 93.21%**, measured by a
new stdlib subprocess trace and AST executable statement-start lines excluding
docstrings. Branch coverage is unmeasured. The 46 unexecuted statement lines are
existing additional malformed inventory/label/metadata, notification and omission
variants; this does not claim exhaustive branch or corruption coverage.

This selected closed sample does not certify the active preparation coordinator or
the full trial. Universal billing completeness remains unproven; final live
compaction/restart readiness still belongs to the single selected probe. The
coordinator must finish/check assessment and report in its owning turn, freeze
immutable inputs before later administration, and obtain independent review before
integration. No watcher, later unverified publisher, measured arm, final target
merge, release or deployment was introduced.

### Owning-start identity correction

Independent review reproduced four false successes when a later `task_started` or
`turn_started` omitted `turn_id` or supplied null. The focused CLI RED confirmed
all four, plus four child-start variants. Twelve malformed-identity variants also
confirmed that the earlier root boundary must not remain certified. In the opt-in
path every start now requires the existing valid-string identity check; a later
invalid start leaves the root boundary unverified. A further strict-mode CLI RED
confirmed four unfinished-start false successes and sixteen malformed/missing/null
identity false successes. Owning-turn tracking and required start identity checks
now apply in both modes; completed nonmodel turns need no synthetic usage. The
pinned optional `turn_context.turn_id` contract is preserved, with absent/null and
valid context IDs and both valid start-event spellings checked in strict and
opt-in modes.

The same targets passed after the fix. Final verification passed **70/70 tests**:
all previous 64 plus six new public CLI methods. The independent original four
reproductions and earlier three false-success regressions passed. Fresh CLI
statement-line coverage measured **634/680 = 93.24%** from 245 CLI processes;
46 statement lines remain uncovered and branch coverage remains unmeasured. The
retained native-21 full, strict-prefix and opt-in-prefix reports remain exactly
unchanged: nine responses / 265,831 tokens, all six deltas zero, strict prefix
rejected only for missing completion, and opt-in root completion unclaimed. No new
native probe or runtime/configuration change was made. Independent re-review is
required before integration.


## Retained native starts and ignored response-item retries

Retained native sources exposed descendant births that had no accompanying live
notification stream. Native `SubAgentActivity` started items are now bound directly
to their canonical source owner and observed current, uncompleted owning turn.
Missing/malformed parent, turn or child identities and foreign ownership fail
closed. Inherited parent starts, waiting/activity targets and notification-shaped
native items cannot establish this owner's children. Existing notification mode,
child-source/lineage checks, counters, closure and allocation remain unchanged.

ECC TDD supplied the sole implementation cycle with no checkpoint commits. The
focused native-start target produced 30 intended failing assertions across five
methods, then passed after the fix; a sixth method checks rejected activity targets.
Two exact ignored `response_item` write retries exposed the same pinned envelope
recovery gap. Their two-method target produced five intended failures, then passed.
Only this already ignored type was added to recovery; exact byte-prefix, adjacent
same-ordinal retry, later timestamp, pinned writer, following ordinal and identical
phase/window checks remain required. Its payload supplies no identities or counters
and is neither inspected nor decrypted. Changed, incomplete, intervening, repeated,
wrong-type/ordinal/timestamp and cross-boundary fragments remain incomplete.

Two fresh private manifests omit only the notification-source entries from the
existing closed native preflight trees. Their full native files and digests remain
unchanged. Against the original collector each returns exit 2 solely for missing
descendant starts; against the fix both return exit 0 with zero issues: **7 responses
/ 211,391 tokens** and **9 responses / 265,831 tokens**. Every usage category and
ordinary/ledger reconciliation is preserved. The larger unchanged source checkpoint
also loses its missing-start and malformed-source errors while retaining all 2,615
observed responses. All three root retry pairs and the original five outer retry
pairs are audited. That checkpoint still reports incomplete for unfinished-turn
and ordinary-reconciliation evidence; this is no complete-window acceptance claim.
No source row, notification, completion or provider identity was synthesized.

Final `GRAPHIFY_TEST_PREFIX=<provisioned-local-prefix> python3 -m unittest discover
-s tests -v` passed **78/78**, with all three real Graphify runtime tests enabled
and zero skips: the previous 70 tests plus eight new public CLI methods. Fresh
stdlib subprocess tracing measured **654/696 = 93.97%** executable statement-start
lines in `tools/usage_report.py` from 298 CLI processes, excluding docstrings.
Branch coverage remains unmeasured. The 42 uncovered statements cover existing
additional malformed manifest, metadata, notification and omission variants.
Compilation, the 14-token example, whitespace, documentation links, scoped diff
and output/privacy checks passed. No new dependency or configured build/type/lint
command applies. Raw manifests, unchanged native files, source/retry proofs and
trace logs remain private. Root coordination still owns independent review,
integration, integrity-hash refresh and revalidation of the same original recovery
proof; no new native probe or measured arm was launched by this fix.
