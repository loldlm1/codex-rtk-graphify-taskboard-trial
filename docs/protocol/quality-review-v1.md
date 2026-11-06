# Application quality review v1

This supplement is fixed before the first measured implementation. It preserves
each starter's exact feature contract, acceptance tests, validation commands and
local rubric. It provides the six independent attributes required by the approved
comparison; it does not change feature behavior or replace a required check.

Record each attribute separately for both implementations of each workload. Do
not sum, average or pool the attributes or workloads. A score of 0, failed required
check, missing required evidence or meaningful quality regression prevents an
adoption result regardless of token savings. A score below 2 needs a concrete
observation and its effect. Compare the implementations directly as well as with
the starter; explain any lower candidate score before deciding whether a difference
is meaningful. A passing score alone cannot waive a concrete material defect.

| Attribute | 2 — meets scope | 1 — minor issue | 0 — material failure |
| --- | --- | --- | --- |
| Correctness | All fixed feature behaviors, edge cases and required acceptance pass | Nonblocking feedback issue with correct behavior | Missing/wrong behavior, data loss, unsafe timing/reset or failed required feature check |
| Scope | Implements the selected change within the fixed exclusions and stack | Small unnecessary change with no functional or maintenance cost | Unrelated feature, excluded service/framework or material change to the task/constraints |
| Maintainability | Small changes follow existing modules with meaningful public-boundary tests | Local naming or duplication issue | Tangled lifecycle/state, speculative machinery, unsafe rendering, production test coupling or weakened checks |
| Visual clarity | Relevant state/results and controls remain clear at both fixed sizes | Small spacing/typography issue without ambiguity | Ambiguous state/results, unreadable or clipped content, hidden controls or broken layout |
| Interaction | Fixed keyboard, focus, pointer/touch and follow-up actions work predictably | Small extra navigation cost without blocking use | Lost focus, keyboard trap, unreachable action, stuck input or unusable touch controls |
| Regressions | Starter operations, persistence/gameplay, rendering and required checks remain intact | Small nonblocking presentation inconsistency | Broken existing operation, lost data, gameplay/render/input defect or failed required starter check |

The task-board local rubric directly scores correctness, maintainability, visual
clarity and interaction. Preserve those four scores; add distinct Scope and
Regressions observations/scores using this table. The Breakwater local rubric
combines correctness with scope and separately scores gameplay/regressions.
Preserve all five local scores, and record correctness and scope independently in
this six-attribute comparison. Apply relevant observations to each affected
attribute without creating a combined total.

For the task board inspect 1440×1000 and 390×844, with the same fictional task
data, native status selection, reload, filtered operations, empty states and
keyboard/focus. For Breakwater inspect 1280×1000 and 390×844, with keyboard and
pointer/touch, pause rendering, safe resume, repeated restart and terminal
recovery. Keep actual desktop/mobile screenshots and executed check results.
Coverage must include every application TypeScript file with the frozen 80%
floor for statements, branches, functions and lines. Unconfigured lint is reported
as unconfigured, not as a passing check.

Each arm's own implementation/Standards/Spec review and fixes belong to that
arm's usage. The independent comparative application review belongs to common
evaluation. For that comparison conceal arm labels and token totals where
practical: provide neutral artifact labels, the same starter/contracts and
validation evidence, and no other arm's implementation to an active implementer.
Record any unavoidable disclosure. Preserve the private label mapping until
quality observations are frozen. The final report may then reveal labels and
apply the separately fixed first-use accounting and per-workload 10% gate.

No measured result, quality score or saving is asserted by this document.
