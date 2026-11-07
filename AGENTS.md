# Task-board conventions

The assigned local task contract owns scope and acceptance. Root coordination uses
Matt implement-spec; implementation and review-fix workers use ecc:tdd-workflow as
the sole test cycle, explicitly replacing delegated Matt tdd. Do not also run Matt
TDD or nest another orchestration workflow. Resolve skills from the actual installed
catalog and shared workflow references from the active Codex home.

Read the assigned contract, GLOSSARY.md, actual files/dependencies and applicable
instructions before editing. Use the actual package manager and validation commands.
Keep the application ordinary and small; add no speculative framework or machinery.
First-time project-convention setup stays explicitly selected; do not auto-run it.

Use npm and the locked dependencies. `npm run verify` checks strict TypeScript,
the Vite build, all-source V8 coverage, and the actual Chrome starter journeys.
There is no configured linter. `npm run test:feature` is separate future acceptance:
it intentionally fails on the starter until the saved-status-view task is selected.
See README.md for reproduction and docs/tasks/saved-status-filter-v1.md for the
frozen task. Keep native controls, labels, keyboard operation, responsive layout,
literal task text, and focus restoration intact. No server or external data exists.

The coordinator owns shared GitHub progress and publication. Workers must not push,
create/edit issues or PRs, change repo settings, merge a final target, release or
deploy. Scoped local task commits and integration are authorized by the assigned
task. No extra RED/GREEN/refactor checkpoint commits. Preserve unrelated work.

For meaningful executable behavior, confirm intended public-boundary RED, implement
minimally to GREEN, then refactor while GREEN. Prefer observable outcomes over prose
or private implementation details. Documentation receives direct validation. Report
actual coverage and gaps without weakening checks or inventing successful results.

Task contracts live in docs/tasks/. Execution records live in docs/work/<task-id>.md,
one per selected task specification; root coordinates the same record across workers.
The original per-scope review baseline is immutable. Before handoff, merge the current
assigned integration tip and rerun affected checks. Return actual commits, commands,
RED/GREEN, coverage, limitations and evidence to the coordinator.

Keep credentials, native configuration, trust decisions/hashes, raw sessions, caches,
private machine paths and private conversations outside Git. Public evidence uses
sanitized projections and accurate human/agent responsibilities. Hook review remains
under native controls. Do not copy upstream plugin source into this repository.

## RTK treatment policy

This selected treatment checkout uses pinned RTK 1.1.0 OSS on its process-local
PATH. Coordinator and workers read this policy from their actual checkout.
Prefix the verified commands explicitly: `rtk npm run typecheck`, `rtk npm run
build`, `rtk npm test`, `rtk npm run test:coverage`, and `rtk npm run test:browser`.
Preserve the project's scripts and arguments. There is no automatic rewrite hook.

Bare `rtk vitest` injects a JSON reporter that writes to a file in Vitest 5.1,
leaving stdout without counts or failure locations. Use `rtk npm test`; the tested
direct alternative is `rtk vitest run --reporter=default`. The specialized
Playwright filter changes its reporter to JSON and can omit warning output; keep
the npm browser script. Use unfiltered npm installation/audit commands when their
warnings matter: the RTK npm filter strips `npm WARN` and notices.

Check exit status, counts, skips and diagnostic locations. If a recovery hint
appears, use `rtk recall HASH --full`. Successful/small outputs, retention limits
and unavailable storage can leave no usable recall. A hint is not guaranteed.
Use `rtk bypass <original command>` when diagnosis needs raw output; record the
bypass and include its complete work in usage accounting. Do not treat omitted
output as a successful check. Do not activate a proxy, model route, global hook,
custom filter, provider setting or telemetry. Preserve native hook review/trust.

## Graphify treatment policy

Use the source-query server bound to the exact Git worktree and pass that same
absolute `project_path`; the private process bindings identify each server.
Keep graph state outside Git and rebuild for that exact worktree after any source,
record, commit, merge or branch change before querying. A server connection alone
does not prove freshness. Implementation and fixes use the precreated implementation
worktree; read-only Standards/Spec review uses the integrated root and its server.
Do not import other-worktree graphs, semantic layers, memories or caches.
