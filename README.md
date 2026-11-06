# Small Hours

A small, local task board for the work ahead. Create a task, add details, change its
status, edit it, or clear it from the board. Tasks stay in this browser on this
origin. There is no account or server; use fictional, non-sensitive task content.

The fixed statuses are **To do**, **In progress**, and **Done**. A new browser starts
with six fictional tasks. Deleting every task keeps an empty board after reload.
Unavailable browser storage leaves the board usable for the session and displays
a warning. User text is rendered as text, including text that looks like HTML.

Use **Status view** to show all tasks or just one status. The selection is saved
separately from task data and restored after reload. Missing, invalid, or unreadable
preferences use All statuses. If the preference cannot be saved, the selected view
still works in the current tab and a warning explains the reload limitation.
Hidden tasks stay on the board; changing the view never changes their status.

## Run locally

Use Node.js 24 and npm 11. The preparation environment was Node 24.6.0 / npm 11.5.1.

```sh
npm ci
npm run dev
```

Open the local address printed by Vite. `npm run build` creates `dist/`;
`npm run preview` serves that build locally.

## Checks

```sh
npm run typecheck
npm run build
npm test
npm run test:coverage
npm run test:browser
npm run verify
npm run test:feature
```

The browser suite uses Playwright's `chrome` channel and a new isolated browser
context per test. Install Google Chrome separately if it is not available.
Playwright does not connect to your everyday browser profile. Port 4173 must be
free. No linter is configured; TypeScript's strict and unused-code checks run in
`typecheck`. No CI or deployment is included.

Vitest exercises the task, storage, DOM, and entry-point boundaries. V8 coverage
includes every `src/**/*.ts` file, with 80% minimum statements, branches, functions,
and lines. CSS and browser rendering are assessed through the actual browser
journeys and screenshots, rather than assigned a JavaScript coverage percentage.

The saved status view contract is frozen in
[saved-status-filter-v1.md](docs/tasks/saved-status-filter-v1.md).
`npm run test:feature` runs its independent acceptance suite, including filtering,
preference recovery, filtered task operations, keyboard focus, and mobile layout.
Run it alongside `npm run verify`, which retains the starter checks.

## Structure and provenance

- `src/tasks.ts`: task validation and immutable task operations.
- `src/storage.ts`: browser persistence and safe recovery.
- `src/app.ts`: native, labeled DOM controls and focus management.
- `src/main.ts`, `src/styles.css`: application entry and responsive presentation.
- `tests/unit/`, `tests/browser/`: starter checks.
- `tests/acceptance/`: frozen saved status view behavior, separately runnable.

This starter was built through a maintainer-directed Codex workflow: the human
defined scope and approvals; agents implemented, tested, and reviewed the code.
Native account and trust approvals remain human actions. Preparation evidence is
recorded in [starter-checks.md](docs/evidence/starter-checks.md); the coordinator
owns [the execution record](docs/work/starter-v1.md).

The repository's [public method overview](https://github.com/loldlm1/codex-rtk-graphify-taskboard-trial/blob/main/README.md)
explains the wider validation purpose. This application branch contains the
runnable starter and its next task; shared reporting support lives separately.
No measured result, release, deployment, or final merge is claimed here.
