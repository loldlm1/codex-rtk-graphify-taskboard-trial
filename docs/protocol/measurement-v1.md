# Four-run measurement contract v1

This contract is fixed before any measured implementation or result. The
[immutable starters](starters-v1.json), their task documents, acceptance tests,
scripts and local rubrics remain authoritative. The
[six-attribute supplement](quality-review-v1.md) adds separate comparison axes
without changing either feature. The maintainer defines scope and approvals;
Codex agents implement, test and review the selected work.

## Source and runtime

Both arms use accepted common profile
`51ed50320fff77610a9030e0846fbe6f532c39ba6c766466ffb0f1026b4d2f97`:
native Codex **0.167.0**, Matt **1.3.2** at
`4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`, ECC **2.2.3** at
`b38be6a7f6350964d59328b52f0624e1d1d552d1`, root **gpt-6.1-sol / ultra /
default**, native concurrency **2**. Every implementation, review and fix worker
gets `fork_turns: none`, the inherited same model and explicit reasoning effort
`xhigh`. Verify actual native contexts and spawn arguments; a stated policy alone
does not prove the settings. Preserve the accepted ECC SessionStart definition and
native trust controls. ECC `tdd-workflow` is the sole implementation/test cycle,
explicitly replacing Matt's delegated `tdd`; Matt coordinates and owns the separate
Standards and Spec review axes. Respect the actual concurrency cap.

Use Node **24.6.0**, npm **11.5.1**, Python **3.12.8**, Google Chrome
**155.0.8059.39**, and the accepted `npx -y chrome-devtools-mcp@1.10.1` transport
with its fixed isolated/headless/system-Chrome/no-usage-statistics/no-performance-crux
flags. Recreate its owned npm cache and verify the complete runtime/dependency
fingerprint; do not silently substitute a different launcher or dependency tree.
The pinned application lockfiles determine their remaining dependencies.

Candidate B adds only the accepted [RTK policy](rtk-v1.md) and
[local Graphify policy](graphify-local-v1.md): RTK **1.1.0 OSS** executable SHA256
`0b80810970ce2c79c92deaa474bbcf6f1cf01ac93baab0e273ee6cb4ef950d10`;
Graphify **0.9.103** package-content SHA256
`24479aad442819e220500475ce2c2195bcbede8d174133bd61d6472931fc5748` and its
checked-in exact dependency lock. No automatic RTK rewrite hook, API proxy,
model route, hosted Graphify, semantic enrichment or LLM deduplication is selected.
Require actual `rtk config` success/effective settings and blocked telemetry before
wrapped commands. Require fresh code-only Graphify builds, backend none, and the
exact-worktree guard. Record actual root/worker tool calls and source answers.

## Order and isolation

Run exactly four implementations, sequentially, counterbalanced across workloads:

1. Web A, accepted common baseline.
2. Web B, same baseline plus the accepted tool treatment.
3. Canvas B, same baseline plus the accepted tool treatment.
4. Canvas A, accepted common baseline.

An operational exception must be recorded before the affected run, with its reason;
ordering does not create a code dependency. Do not repeat runs automatically or
change the order, prompts, checks or allocation in response to an observed result.

Start each arm from its workload's exact immutable starter commit, on its own
branch/worktree, fresh native root session, Codex home/configuration, accounting
stores, ECC/CLV2 state, npm/temp/XDG caches and generated graph state. Native
authentication and exact hook review remain native human actions when required;
never copy account material, trust hashes, sessions, caches or keys between homes.
No arm reads another arm's solution, tests added by that arm, review findings,
generated graph/context, recall store or transcript. Common immutable source,
approved task/check/rubric pointers and verified installed executables are reusable.

A has no RTK treatment policy/activation or Graphify graph/server. B recreates its
RTK config/databases and initial graph for that workload. Each B worker gets a
server bound to its actual worktree, or reads the integrated worktree with that
worktree's correct server. An inherited root-bound server cannot answer a foreign
worktree. Rebuild after source, record, branch or integration changes; test actual
freshness and source identity, not registration alone. Do not reuse preflight or
other-arm indexes, memories or caches. Preserve the stack, native model/effort/cap,
browser, hook and test settings across A and B.

Pass each root only its own frozen task document and starter/check/rubric pointers,
the common hybrid instructions, original workload baseline and scoped authorization.
Render and hash the [fixed arm prompt](arm-prompt-v1.md) before its first turn;
only its declared identity/path substitutions vary.
Keep the one concise arm record through compaction/restart. No exploratory feature,
ablation, extra implementation or near-limit context-filling run is selected.

## Checks, accounting and assessment

Freeze commands and thresholds from each starter: build, typecheck, unit and browser
checks, all-application-source coverage with **80%** floors in all four categories,
and its intentionally RED future-feature acceptance becoming GREEN. Lint is
unconfigured. Record actual RED/GREEN, counts, coverage/gaps, browser interactions
and desktop/mobile screenshots. Required missing evidence keeps the arm incomplete.
Do not weaken tests or replace application behavior with graph/source checks.

Apply [usage v1](usage-v1.md) unchanged. Each arm owns its implementation, separate
Standards/Spec review, fixes, retries, compactions and recovery. B additionally owns
its own activation and initial indexing; common B-only provisioning/preflight is
split exactly half to each B. Raw and exact-rational allocated totals both remain
visible. Common upgrade, fixtures, this single recovery probe and comparative
evaluation are separate full-window categories, outside the per-arm gate.

Declare phase/thread/source boundaries before work. Close workers around transitions;
freeze complete canonical source hashes, actual lineage/turns, response identities,
ordinary/compaction counters and replay evidence. Close evaluation at the assessment
and report-evidence freeze; later publication is administration outside the window.
An active-turn snapshot cannot be relabelled a closed run to hide missing tails.
Unsupported, conflicting or missing required evidence stays incomplete. The selected
ledger cannot prove universal upstream billing completeness, even when reconciled.

Independent comparative assessment uses neutral artifact labels and conceals arm
labels/token totals where practical until quality observations are frozen. Preserve
each local rubric and each of the six separate quality attributes; disclose any
unavoidable label exposure. Each workload independently needs at least **10% lower
first-use allocated total tokens** for B and no meaningful quality regression.
Never pool workloads, average quality axes or let savings waive a defect.

Readiness also requires acceptance of the same short
[recovery probe](recovery-v1.md); parser success alone does not establish it. No
measured outcome, saving, adoption, final target merge, release or deployment is
asserted by this contract.
