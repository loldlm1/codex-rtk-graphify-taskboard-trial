# Neutral task-board quality review

Judgments frozen before treatment mapping or token totals were supplied. Only the
neutral `cedar/` and `orchid/` application artifacts and shared rubric were used.

| Independent attribute | Cedar | Orchid |
| --- | ---: | ---: |
| Correctness | 2 | 1 |
| Scope | 2 | 2 |
| Maintainability | 2 | 2 |
| Visual clarity | 2 | 2 |
| Interaction | 2 | 2 |
| Regressions | 2 | 2 |

The preserved local four-axis scores are: Cedar correctness **2**, maintainability
**2**, visual clarity **2**, interaction **2**; Orchid correctness **1**,
maintainability **2**, visual clarity **2**, interaction **2**. No totals or pooled
score are used.

Both implementations meet the fixed functional contract in the supplied executed
evidence. Each constructs one native, explicitly labeled Status view select using
the existing three statuses with All statuses prepended in the required order
(`cedar/src/app.ts:86–100`, `orchid/src/app.ts:86–93,202–208`). Filtering operates on
a derived visible list while retaining the complete task collection; view changes
write only the preference. Missing, invalid/non-string JSON, unsupported strings,
storage-access failures and read failures fall back to `all`; write failures return
false and leave the session usable (`cedar/src/storage.ts:3–25`,
`orchid/src/storage.ts:3–6,30–46`). Preference warnings remain separate from task
write warnings and clear on a successful retry. Task storage retains its original
key/schema and separate save path (`cedar/src/storage.ts:27–46`,
`orchid/src/storage.ts:8–27`).

The one concrete deficiency is Orchid's filtered count: a one-task board displays
“1 of 1 tasks” because that branch always uses the plural
(`orchid/src/app.ts:130–132`). Cedar handles the singular (`cedar/src/app.ts:138`).
This is a minor grammatical feedback issue, accounting for Orchid's correctness
score of 1; the number, selected tasks and persistence remain correct. It creates
no ambiguous state or material quality regression.

Both preserve hidden tasks during create/edit/delete/status changes. Nonmatching
creation stays hidden, editing can move a task out of view, moved tasks reappear in
their destination view, and deletion uses visible order. View changes retain the
same focused select; status changes restore focus to the moved select or Status
view; deletion focuses a visible neighbor or relevant control. Cedar falls back
to Task title after deleting the final match; Orchid chooses Status view when
hidden tasks remain. Both satisfy the focus contract
(`cedar/src/app.ts:136–205`, `orchid/src/app.ts:128–199`). The original all-board
empty state remains distinct from “No tasks in this view.” Both safely render
task content with textContent/value and retain the existing small modules.
Package manifests and task-domain source match between artifacts; no excluded
framework, service or unrelated feature was found.

Frozen acceptance suites are byte-identical. They cover exact matching, reload,
unchanged task data, malformed preferences, filtered CRUD, empty results, real
keyboard selection/focus, mobile overflow and preference read/write failures
(`cedar/tests/acceptance/saved-status-filter.spec.ts:17–118`). Added unit tests
exercise meaningful DOM/storage boundaries, failure recovery and visible-neighbor
focus; Orchid additionally separates preference-storage tests. Starter browser
and unit suites match between artifacts and preserve CRUD, validation,
cancellation, literal text, blocked storage and duplicate-title focus coverage.

All five supplied PNGs were viewed: Cedar `screenshots/1.png` and `2.png`; Orchid
`screenshots/1.png`, `2.png` and `3.png`. Desktop and mobile controls, results,
status badges and focus outlines are clear without visible clipping. Cedar uses
a stacked label/select; Orchid uses an inline pair. Both are readable and usable;
neither arrangement merits a lower visual or interaction score. The screenshots
show the same three-task fixture but different selected statuses and include
scrolled/full-page captures, limiting exact pixel-for-pixel comparison.

`checks.json` reports required gates passing: Cedar 42 unit, 4 starter-browser and
5 feature-browser tests; Orchid 44, 4 and 5 respectively, with no skips. Both pass
types/build. Cedar coverage is 100% for all four metrics; Orchid is 100%
statements/functions/lines and 98.48% branches. Orchid's documented unit gap is the
final-visible-card deletion fallback with hidden tasks; frozen browser coverage
exercises it. Both exceed the frozen 80% floors. Lint is unconfigured.

No material regression was identified between neutral implementations or against
the starter behaviors represented by the frozen tests/evidence. Executed results
are the coordinator's normalized summaries, not independent reruns or raw-log
inspection. No dependencies were installed or tests rerun. The requested
`docs/validation/starter-v1.md` filename was corrected to the supplied
`docs/tasks/starter-v1.md` and `docs/evidence/starter-checks.md`; this is not a
missing-check finding. No treatment/token disclosure occurred. Browser/assistive
technology coverage beyond the supplied Chrome evidence remains unverified.
