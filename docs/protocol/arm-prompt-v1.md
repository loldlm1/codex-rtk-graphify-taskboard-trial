# Frozen native arm prompt v1

Render the text below once per arm. Substitute only the table fields and owned
absolute paths; preserve all remaining text. Record the rendered text/hash before
the first model turn. Attach the actual discovered qualified
`mattpocock-skills:implement-spec` skill entry, without copying its source. The
runtime settings and treatment policy are those of measurement-v1.md. This is a
prompt contract, not a claim that an arm has started.

| Field | Web A / Web B | Canvas B / Canvas A |
| --- | --- | --- |
| WORKLOAD | web | canvas |
| ARM | A / B | B / A |
| TASK | docs/tasks/saved-status-filter-v1.md | docs/tasks/pause-resume-restart-v1.md |
| STARTER | 01dbac8f5a60a1a5a5be89238971fd13badb3b56 | a4031c0da42d95f97d3b2e0fed4bdbcd76dd3087 |
| ORIGINAL_BASELINE | 14ae1c0462e42df8eaff2848e7786811cefc06e8 | 223ce7462ebbb7cda1961e62f2860a2c3f0dcc65 |
| ISSUE | 23 / 24 | 26 / 25 |

ROOT, WORKER_ROOT, CODEX_HOME, RECORD and GRAPH_STATE are new arm-owned absolute
paths. ROOT and every worker worktree must be bound to the right graph server in
B before native threads use it. A has no graph state/server or RTK activation.
RECORD is the project's one concise `docs/work/arm-v1.md` execution record.
The order is Web A, Web B, Canvas B, Canvas A; the ISSUE table maps the approved
original issue numbers and does not change that order.

```text
Execute only approved spec13 ticket ISSUE, WORKLOAD arm ARM, in ROOT. The originating
issue is https://github.com/loldlm1/.codex/issues/ISSUE and the complete fixed feature
contract is TASK. Read that task, this checkout's AGENTS.md and established checks,
the frozen common measurement/quality policy supplied by the outer coordinator,
and the active CODEX_HOME/workflow/{execute,recover}.md. Do not read another arm's
solution, added tests, review, generated context or transcript. No other feature,
extra experiment, new dependency, stack migration, hook/model/configuration change or
automatic-compaction threshold change is selected.

Use only fresh arm-owned application dependencies and generated caches. Workers
may use their own arm's node_modules tree; never point this arm at a preflight or
another arm's tree. Vite/Vitest default result/module caches live under node_modules
and are not isolated by XDG alone. Preserve the frozen starter scripts/arguments.

Use the selected installed Matt implement-spec coordinator and the installed hybrid
contract. Explicitly replace every delegated Matt tdd call with actual installed
ecc:tdd-workflow as the sole implementation/test cycle. Do not also run Matt TDD,
nest ECC orchestrators, invoke user-only setup/planning stages or make RED/GREEN
checkpoint commits. Use the existing package manager, lockfile and approved seams;
demonstrate meaningful intended RED, smallest complete GREEN and refactor while
green. Preserve all existing acceptance/coverage thresholds and do not weaken tests.

Record immutable ORIGINAL_BASELINE and exact STARTER separately in RECORD; neither
is replaced by a moving HEAD or merge-base. The feature review fixed point is exact
STARTER. Start isolated worker branches/worktrees from the current arm integration
tip within WORKER_ROOT. Every implementation, review and fix worker MUST use fresh
fork_turns none, inherited gpt-6.1-sol model and explicit reasoning_effort xhigh.
Root keeps ultra/default and native concurrency2. Delegate only actual bounded
implementation/review/fix tasks required by this ticket; no arbitrary fanout. Include
the task/record/baseline, actual worktree, sole ECC cycle and authorization in every
handoff. Do not reset unrelated work or rewrite history. Merge current integration
into a worker before handoff, integrate and rerun affected checks.

Arm A uses the accepted updated common stack without the experimental tools. Arm B
uses the same stack plus the already verified project RTK explicit-prefix policy
and dedicated exact-worktree local Graphify MCP. Follow the actual checkout policy;
verify effective RTK config/blocked telemetry and actual root/worker calls. B must
rebuild its fresh code-only/no-dedup/backendnone graph after any source/record/branch/
merge identity change before querying it; use only the server bound to the exact
queried worktree, with generated state outside source. Source queries do not replace
tests, browser interaction or visual inspection. No automatic rewrite hook, proxy,
model route, hosted service, semantic enrichment or LLM deduplication is authorized.

Complete the feature's frozen build, type, unit, browser, future-feature acceptance
and all-application-source coverage commands and direct desktop/mobile interactions.
Use relevant installed ECC verification/e2e/security guidance proportionately. Report
actual RED/GREEN, counts, screenshots, coverage and gaps; lint is unconfigured.
Run actual installed Matt code-review with separate fresh Standards and Spec axes,
respecting native capacity; fix concrete findings using the same sole ECC cycle,
and repeat affected checks. Required missing evidence blocks completion.

Maintain the same concise committed RECORD at integration/verification/recovery
boundaries, retaining scope, immutable baselines, completed commits/actual checks,
authorization, tool/graph identity, blockers and one next action. Finish workers
around boundaries. Preserve actual native usage for all root/descendant responses,
reviews, retries, compactions and recovery; the outer coordinator owns full source
closure, phase classification and publication. No filler or extra readiness probe.

Routine local task commits/integration in this arm are authorized. Outer root owns
GitHub writes and publication. Do not final-merge a trial solution or target branch,
release, deploy, modify auth/trust/hooks or consume another arm's work. Return the
clean branch, exact commits, actual checks/evidence, unresolved gaps and next action.
Do not declare savings or adoption; independent comparative assessment follows all
four frozen implementations.
```
