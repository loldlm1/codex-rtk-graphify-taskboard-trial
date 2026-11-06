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

After GREEN, source/checkpoint projection was kept minimal and evidence was rerun.
The original broad omission test also lacked turn-completion evidence; that fixture
was corrected so its focused RED isolated the missing-checkpoint behavior. This
avoids claiming a failure caused merely by another missing requirement.

Final command `python3 -m unittest discover -s tests -v`: **20/20 passed**. Subtests
cover missing/null usage and identity, category arithmetic, conflicting duplicates,
unknown runtime/schema, missing descendants/starts/counters/completions, digest and
file failures, private-input exclusion, open windows/runs, phase overlap/gaps, fixed
B allocations, administration outside the window, retries/restart and compaction
snapshots. These are public ingestion/report outcomes, not private-helper or prose
tests. The synthetic policy example charges 15-token phases as 15 for A, 45 raw for
B, and `105/2` allocated B after the exact half-share; common costs remain visible
in the full window.

## Measured coverage and final checks

A task-local stdlib `sys.settrace` hook followed each CLI subprocess. Fresh hit files
for this final source were unioned and compared with AST executable statement-start
lines, excluding docstrings. Result: **398/447 = 89.04%** for `tools/usage_report.py`.
This is statement-line coverage, not branch coverage. Remaining unexecuted lines
mostly reject additional malformed manifest inventories/labels/cycles/intervals,
conflicting metadata and optional completion notification variants. It is not a
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
