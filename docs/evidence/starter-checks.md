# Starter v1 preparation checks

This records agent implementation and local verification of the runnable starter.
The maintainer defined scope and approvals. Agents wrote the application and its
tests; independent review and immutable publication are coordinator-owned next
steps. This is preparation, not a measured feature implementation or savings
result. The shared execution record is [starter-v1.md](../work/starter-v1.md).

## Environment and dependencies

Preparation used Linux, Node.js **24.6.0**, npm **11.5.1**, and Google Chrome
**155.0.8059.39**. The existing environment supplies Node, npm, and Chrome;
`package-lock.json` pins the application development dependencies. There are no
runtime npm dependencies, framework, remote fonts, external data, server, or CI.

| Direct development dependency | Locked version | Purpose |
| --- | --- | --- |
| Vite | 8.3.6 | Development server and production build |
| TypeScript | 7.0.2 | Strict application, test and configuration checks |
| Vitest / @vitest/coverage-v8 | 5.1.0 / 5.1.0 | Unit/DOM tests and all-source coverage |
| jsdom | 29.1.1 | DOM boundary test environment compatible with Node 24.6 |
| @playwright/test | 1.65.0 | Real installed-Chrome browser journeys |
| @types/node | 24.19.2 | Node tooling declarations compatible with TypeScript's DOM types |

Registry metadata and maintained primary documentation informed these choices:
[Vite getting started](https://vite.dev/guide/),
[Vitest coverage](https://vitest.dev/guide/coverage.html),
[Playwright Chrome channel](https://playwright.dev/docs/browsers), and
[Playwright web server configuration](https://playwright.dev/docs/test-webserver).
The newest jsdom at preparation required a newer Node minor; 29.1.1 supports the
selected runtime. An initial old Node declaration pin conflicted with TypeScript's
URLPattern declaration; the final locked version resolves that tooling setup
failure. Neither setup issue is counted as behavioral RED evidence.

## TDD evidence

The sole cycle was `ecc:tdd-workflow`, explicitly replacing delegated Matt TDD.
Additional RED/GREEN/refactor checkpoint commits were not selected.

| Behavior | Executed RED | Executed GREEN and guarantee |
| --- | --- | --- |
| Task validation, immutable CRUD, storage recovery and DOM operations | `npm test`: **19 failed / 19**, against minimal exported no-behavior seams; actual assertions observed missing tasks/controls, unimplemented operations and absent storage behavior | Same command: **19 passed / 19**, with task create/edit/delete/status changes, reload, empty board, invalid/blocked storage, literal user text, validation and focus checked |
| Real application journeys | `npm run test:browser`: **4 failed / 4**, with empty application/missing task controls | Same suite: **4 passed / 4**, using real installed Chrome and isolated contexts |
| Duplicate task titles retain the moved card's focus | `npm test -- tests/unit/app.test.ts`: **1 failed, 4 passed**; expected `task-second`, received `task-first` | Identity-based focus restoration; the added case passes in the full suite |
| Actual entry point | Added `tests/unit/main.test.ts` imports the real entry and observes a mounted six-task board | Full suite: **21 passed / 21**, across four test files |

The DOM and Chrome boundaries exercise public outcomes, not internal function
shape. Browser checks also caught a decorative arrow entering a button's
accessible name; the arrow is now hidden from assistive technology. An ambiguous
test query was narrowed to the labeled textbox, without weakening its Tab/focus
assertion. Common select construction and text-only DOM rendering keep the
implementation small; tests remained green after focus/refactoring changes.

## Actual final checks

| Command/check | Result |
| --- | --- |
| `npm ci` | PASS; installs from lockfile, audit reports 0 vulnerabilities |
| `npm run typecheck` | PASS; strict checks, unused-code checks; no skipped library checks |
| `npm run build` | PASS; Vite production assets generated |
| `npm test` / `npm run test:coverage` | PASS; 21 tests in 4 files |
| `npm run test:browser` | PASS; 4 real Chrome journeys |
| `npm run verify` | PASS; typecheck, build, coverage and browser checks in one command |
| `npm audit --audit-level=high` | PASS; 0 vulnerabilities in the locked dependency tree |
| `git diff --check` | PASS |
| Lint | Not configured; no separate lint claim |
| Security review | Task text uses `textContent`/`value`; static template only; malformed storage validated; HTML-like text cannot create elements; no credentials or external requests in application source |

V8 coverage explicitly includes **every `src/**/*.ts` file**, including the entry
point; no source exclusions. Measured totals were **100% statements (164/164),
100% branches (48/48), 100% functions (33/33), and 100% lines (142/142)** across four
files. Thresholds remain 80% for all four metrics. These percentages describe
the executed JavaScript/TypeScript paths, not proof of every possible input or
rendered CSS state. CSS and layout are checked in Chrome and inspected directly.

The browser journeys verify Enter to submit and delete, Tab to Details, editing
and canceling, status changes, focus after rerender/removal, persistence through
reload, literal HTML-like input, validation, empty-board persistence, malformed
task data and blocked storage. Screenshots at **1440×1000** and **390×844** show the
actual responsive layout; mobile also checks a long task title. Both sizes have
no horizontal document overflow. The generated files are `desktop.png` and
`mobile.png` under the layout test's ignored `test-results/` directory. The
coordinator retains review copies; raw paths and private execution logs are not
published in source.

## Future-task boundary and limitations

`npm run test:feature` is separate from starter verification and intentionally
fails all five future acceptance cases on the missing `Status view` control.
The contract, exact prompt, rubric, values, preference storage format, checks,
and exclusions are frozen in
[saved-status-filter-v1.md](../tasks/saved-status-filter-v1.md). There is no filter
control, filtering logic, or filter persistence in application source.

Browser evidence covers installed Chrome on this Linux environment, with isolated
test contexts and no everyday user profile. Firefox, WebKit, assistive technology,
other operating systems, and production deployment were not exercised. Task data
is local to a browser origin and can be lost when that browser's storage is cleared;
this is not a synchronized or multi-user service. No final target merge, release,
deployment, immutable starter tag, paired quality result, or token saving is
claimed by these local checks.
