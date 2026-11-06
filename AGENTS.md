# Public workflow-trial fixture conventions

The assigned local task contract owns scope and acceptance. Root coordination uses
Matt implement-spec; implementation and review-fix workers use ecc:tdd-workflow as
the sole test cycle, explicitly replacing delegated Matt tdd. Do not also run Matt
TDD or nest another orchestration workflow. Resolve skills from the actual installed
catalog and shared workflow references from the active Codex home.

Read the assigned contract, GLOSSARY.md, actual files/dependencies and applicable
instructions before editing. Use the actual package manager and validation commands.
Keep the application ordinary and small; add no speculative framework or machinery.
First-time project-convention setup stays explicitly selected; do not auto-run it.

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
