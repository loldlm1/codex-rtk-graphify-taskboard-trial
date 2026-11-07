# Frozen comparative Canvas quality review

Judgments were frozen using only the neutral `cedar/` and `orchid/` artifacts and `quality-review-v1.md`. No treatment mapping, token totals, original arms, Git/history, private records, external sources or other reviewers' outputs were inspected. No unavoidable treatment disclosure occurred. No application files were edited and no checks were rerun.

## Independent six-attribute scores

Each score is independent; there is no total.

| Attribute | Cedar | Orchid |
| --- | --- | --- |
| Correctness | 2 | 2 |
| Scope | 2 | 2 |
| Maintainability | 2 | 2 |
| Visual clarity | 2 | 2 |
| Interaction | 2 | 1 |
| Regressions | 2 | 2 |

## Original five-axis local rubric

| Axis | Cedar | Orchid |
| --- | --- | --- |
| Correctness and scope | 2 | 2 |
| Maintainability | 2 | 2 |
| Visual clarity | 2 | 2 |
| Interaction | 2 | 1 |
| Gameplay and regressions | 2 | 2 |

## Findings and direct comparison

Both implementations meet the selected gameplay behavior. Their public controllers cancel pending work, clear held controls, preserve the round while paused, clear the timing baseline on resume, and reset the supplied state in place with `Object.assign(state, createGameState())`. Initial resumed/restarted frames use zero simulation time; subsequent motion uses elapsed time capped at 50 ms. Idempotent commands and terminal checks prevent revival through pause/resume. Disposal cancels work and clears input. See [Cedar controller](/tmp/codex-spec13/evidence/quality/canvas/cedar/src/controller.ts:26) and [Orchid controller](/tmp/codex-spec13/evidence/quality/canvas/orchid/src/controller.ts:26).

The identical frozen controller suite tests all four restart origins, complete reset/input cleanup, long-pause timing and thirty restarts with one paint per delivered frame ([acceptance](/tmp/codex-spec13/evidence/quality/canvas/cedar/tests/feature/unit/pause-restart.test.ts:28)). Added tests meaningfully use the public state, controls, paint and scheduler seams: [Cedar](/tmp/codex-spec13/evidence/quality/canvas/cedar/tests/unit/round-commands.test.ts:19), [Orchid](/tmp/codex-spec13/evidence/quality/canvas/orchid/tests/unit/round-commands.test.ts:19). Ordinary modules, dependencies and lockfiles remain consistent; no production test interface or speculative framework appears.

Both retain native buttons and polite `Round status`, change Pause to Resume, preserve focused controls, and move focus to Restart before disabling terminal Pause ([Cedar render](/tmp/codex-spec13/evidence/quality/canvas/cedar/src/render.ts:51), [Orchid render](/tmp/codex-spec13/evidence/quality/canvas/orchid/src/render.ts:44)). Browser tests cover Enter, tab order, focus outlines, terminal recovery, real Canvas pixels and mobile targets. Both CSS files require 44 px minimum button height and visible focus. All six supplied screenshots were viewed: `cedar/screenshots/1.png`–`3.png` and `orchid/screenshots/1.png`–`3.png`. Desktop/mobile paused and terminal presentations are readable, unclipped and clear. Cedar centers compact mobile buttons; Orchid fills the row. Both layouts meet the contract.

**Minor Orchid interaction deficiency:** when `createView()` throws because a 2D context is unavailable, execution reaches a catch that only updates status. Native Pause/Restart remain enabled and focusable without registered handlers ([startup](/tmp/codex-spec13/evidence/quality/canvas/orchid/src/main.ts:7), [buttons](/tmp/codex-spec13/evidence/quality/canvas/orchid/index.html:35)). They add useless keyboard stops and imply available commands in the failure state. Cedar disables both in its catch and tests that behavior ([startup](/tmp/codex-spec13/evidence/quality/canvas/cedar/src/main.ts:25), [test](/tmp/codex-spec13/evidence/quality/canvas/cedar/tests/unit/round-view.test.ts:71)). This warrants Interaction 1, but does not block a supported Canvas round or constitute a material gameplay regression. No other concrete deficiency was identified.

Both have identical physics, input, fresh-state values, starter gameplay tests and feature suites. Collision, scoring, lives, keyboard/pointer/touch steering and refresh recovery remain covered. No material regression between the neutral artifacts was found.

## Executed evidence and limits

Supplied `checks.json` summaries report typecheck/build, required starter and feature checks, direct desktop/mobile interactions and zero skipped checks passing. Cedar: 30 normal unit, 5 browser, 9 feature-controller, 3 feature-browser tests; coverage statements/branches/functions/lines **99.55/96.55/100/100%**. Orchid: **23/5/9/3** tests; coverage **98.16/94.05/100/99.44%**. Both configurations include every `src/**/*.ts` file with all four thresholds at 80%. Lint is **unconfigured**, not passed.

Execution results are supplied summaries, not independently rerun logs. There is no separate starter source snapshot here, so starter comparison relies on its frozen contract, validation documentation and preserved tests. Screenshots show different round progress; their scores/lives are not matched-state behavioral evidence. Only supplied Chrome/Linux evidence is established; physical devices, other browsers and assistive-technology usability remain unverified. The startup-error finding is source-based. These scores establish quality judgments only, before treatment or token accounting.
