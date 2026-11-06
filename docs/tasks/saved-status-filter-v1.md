# Saved status view v1 — frozen future task

This task is unimplemented in starter v1. Preparation and starter fixes do not
authorize implementing it. The same task text and acceptance apply to each
independent implementation from the frozen starter.

## Exact implementation prompt

> Implement saved status views for Small Hours. Add one clearly labeled native
> select named “Status view” with All statuses, To do, In progress, and Done, in
> that order. Show all tasks for All statuses and only matching tasks for a status.
> Preserve the selection after reload, safely falling back to All statuses when
> stored selection data is missing, malformed, unknown, or unavailable. A failed
> preference write must leave the current session usable. Keep task data separate
> from this preference. Preserve task creation, editing, deletion, status changes,
> task persistence, keyboard interaction, focus visibility, and responsive visual
> clarity. A task moved out of the chosen view disappears from that view without
> being lost. When no tasks match, show “No tasks in this view.” Keep existing
> all-board empty behavior. Use the existing stack and small module structure.
> Run the starter checks and the separate future acceptance suite. Use
> ecc:tdd-workflow as the sole implementation/test cycle, explicitly replacing
> delegated Matt tdd. Do not also run Matt TDD or nest ECC orchestration workflows.
> Report actual RED/GREEN, commands, coverage and gaps; do not weaken frozen checks.

## Fixed behavior and public seams

The task statuses remain `todo`, `in-progress`, and `done`; the All selection is
`all`. The select has accessible name `Status view` and exactly these options:

| Label | Value |
| --- | --- |
| All statuses | `all` |
| To do | `todo` |
| In progress | `in-progress` |
| Done | `done` |

Store the preference as a JSON string at `small-hours.status-view.v1`, for example
`"in-progress"`. Existing task JSON at `small-hours.tasks.v1` remains intact.
Missing, invalid JSON, non-string JSON, and unsupported strings select `all`.
Storage read failures also select `all`. Write failures must not crash or prevent
the chosen in-memory view and existing task operations. Reload may return to All
when storage cannot persist the preference; do not falsely promise persistence.

Task articles keep accessible names from their titles. The task editor keeps
`Task title`, `Details`, and `Status` controls; per-task status selects keep
`Move <task title>`. View selection must keep focus on the view control. If a task
operation removes the focused card from a view, move focus to a relevant visible
control instead of losing it to the document body. No filter libraries, accounts,
server, multi-select, search, new statuses, or unrelated product features are needed.

## Acceptance and commands

After `npm ci` with Google Chrome installed, all normal starter checks must pass:

```sh
npm run verify
```

The selected task must additionally make this independent UI suite pass:

```sh
npm run test:feature
```

The checked-in suite is [saved-status-filter.spec.ts](../../tests/acceptance/saved-status-filter.spec.ts).
It checks exact matching results for all four choices, persistence and task data
preservation, missing/malformed/unsupported storage, CRUD and status transitions
while filtered, nonmatching creation, empty matching results, real keyboard
selection/focus, mobile overflow, and preference storage read/write failures.
The starter suite keeps existing task persistence and CRUD coverage. The future
suite is intentionally RED in starter v1; ordinary starter verification is GREEN.

Coverage must include every application TypeScript file and retain the 80% floor
for statements, branches, functions, and lines. The implementation should add
focused boundary tests for new behavior. Existing and frozen acceptance checks
are not replaced by tests of internal shape or assertions about documentation.

## Fixed review rubric

Required gates are all starter and future checks passing, no lost/overwritten task
data, no uncaught interaction errors, and measured coverage meeting the floor.
Missing required evidence blocks acceptance. Review the finished app at 1440×1000
and 390×844, using keyboard as well as pointer interaction, with the same fixture
tasks. Preserve desktop/mobile screenshots and the actual check results.

Score each axis independently; do not use a total to excuse a failing axis:

| Axis | 2 — meets scope | 1 — minor issue | 0 — material failure |
| --- | --- | --- | --- |
| Correctness | All behavior gates pass; edge cases preserve data | Cosmetic feedback issue with passing behavior | Missing behavior, wrong tasks, data loss, or a failed required check |
| Maintainability | Small changes follow current modules and stack; useful boundary tests | Local naming or duplication issue | Speculative machinery, tangled state, weakened checks, or unsafe text rendering |
| Visual clarity | Selected view, status, task results and empty state are clear at both sizes; no clipping or overflow | Small spacing/typography issue without ambiguity | Ambiguous selection/results, unreadable text, hidden controls, or layout breakage |
| Interaction | Native labels, keyboard selection, Enter/Tab, visible focus and reachable follow-up actions work | Small extra navigation cost without blocking use | Keyboard trap, lost focus after removal, unreachable operation, or broken persistence feedback |

A score of 0 or any required gate failure is a material regression. Reviewers must
record concrete observations for scores below 2 and compare both implementations
against this same frozen rubric before declaring output quality preserved. The
wider comparison protocol owns the final paired decision; this document makes
no result or savings claim.
