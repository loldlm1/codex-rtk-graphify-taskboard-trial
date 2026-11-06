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
