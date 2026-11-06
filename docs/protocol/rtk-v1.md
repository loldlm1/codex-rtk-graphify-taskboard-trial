# RTK command-filter preflight v1

Ticket [20](https://github.com/loldlm1/.codex/issues/20) tested RTK 1.1.0 OSS on
Linux x86_64 against the two immutable `starter-v1.0.0` fixtures. This is B-only
provisioning/preflight, not a measured implementation or an adoption result.
The plugin-only installation remains independent. Neither future feature was
implemented and neither immutable starter was edited.

## Selected executable

The maintained stable [1.1.0 release](https://github.com/rtk-ai/rtk/releases/tag/v1.1.0)
was published 2026-10-25 from commit
`753a3b0e939f2e4490fc24e3a1984010f40a103c`. The selected official artifact is
`rtk-oss-x86_64-unknown-linux-musl.tar.gz`; its archive SHA-256 is
`4dec94a64035e08189ae82fd5408fe4ae9ae27a665fc07e3e3ec3c4c2d8e8a3e`.
The extracted `rtk` executable reports `rtk 1.1.0`, SHA-256
`0b80810970ce2c79c92deaa474bbcf6f1cf01ac93baab0e273ee6cb4ef950d10`.

The [release README](https://github.com/rtk-ai/rtk/blob/v1.1.0/README.md#editions)
distinguishes OSS command filters from the compression engine and the separately
shipped provider proxy. Download only this OSS archive, compare its digest with
the pinned value and release checksums, inspect/extract `rtk` and `LICENSE` into
a task-owned shared prefix, and verify the executable digest/version. No remote
installer, provider proxy, service or model routing is required. Only this platform
was tested; another binary/platform needs its own fidelity check.

## Fresh treatment activation

Executable availability does not activate a project. For each B run, create new
owned config, tracking/recall, cache, npm-cache and temporary directories. Copy
[the config](../../examples/rtk-v1/config.toml) into that run's
`XDG_CONFIG_HOME/rtk/config.toml`. Launch its native process with the pinned tool
prefix on `PATH`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME`, `TMPDIR`,
`npm_config_cache`, and `RTK_TELEMETRY_DISABLED=1` set only for that process.
`RTK_DB_PATH` and `RTK_RECALL_DB` may explicitly name separate owned databases.
Give workers the same run's environment and verify their actual command workdir.
Do not copy preflight databases, recall entries, sessions or caches into an arm.

Add [the project policy](../../examples/rtk-v1/AGENTS.fragment.md) outside any
managed instruction section in the selected treatment checkout, preserving existing
instructions. Recreate it for each worktree. A has neither this policy nor RTK
activation. Existing native runtime/plugin/model/effort/agent limits and the accepted
ECC SessionStart hook remain unchanged. Keep the established isolated
`ECC_AGENT_DATA_HOME` and `CLV2_HOMUNCULUS_DIR`; `CODEX_HOME` alone is insufficient.

The [upstream Codex integration](https://github.com/rtk-ai/rtk/blob/v1.1.0/hooks/codex/README.md)
can install a native `PreToolUse` rewrite hook. This pilot deliberately selects
supported project awareness and explicit prefixes instead. **No automatic rewrite
hook is installed or claimed.** Native hook review and trust remain untouched;
future hook activation would require native review. Do not run global `rtk init`.

## Actual fidelity results

[The public projection](../../examples/rtk-v1/preflight.json) records every command
comparison, exits and log digests. Disposable copies came from web
`01dbac8f5a60a1a5a5be89238971fd13badb3b56` and Canvas
`a4031c0da42d95f97d3b2e0fed4bdbcd76dd3087`. Node 24.6.0/npm 11.5.1 used the locked
packages; Vitest 5.1.0, TypeScript 7.0.2, Vite 8.3.6 and Playwright 1.65.0 ran
actual commands, including real Chrome journeys.

Each starter's raw and `rtk npm` forms of `npm run typecheck`, `npm run build`,
`npm test`, `npm run test:coverage` and `npm run test:browser` returned 0. Web
retained 21 unit/4 browser passes; Canvas retained 16 unit/3 browser passes.
Coverage was unchanged: web 100% across all four metrics; Canvas 98.88%
statements, 94.66% branches, 100% functions and 99.32% lines.

A disposable unit assertion deliberately expected a wrong document title. Raw and
wrapped runs both returned 1, retaining the failure location, assertion, warning,
original passing counts and one skipped test. Correcting only that assertion made
the same command return 0 (web 22 passes/1 skip, Canvas 17 passes/1 skip).
Vitest itself suppresses that warning on successful runs in both forms. A missing
side-effect import produced the same nonzero compiler/build exits and named
`src/main.ts`/the missing import. Restoring it returned both builds to 0.
A disposable browser assertion also failed in both forms, preserving the failing
source location, warning, original passing count and one skip. No application
behavior changed during these checks.

Two reporter adaptations were tested rather than assumed equivalent:

- Bare `rtk vitest run` injects `--reporter=json`. Vitest 5.1 writes that JSON to
  `.vitest/json/output.json`; RTK falls back to a report-path-only output. Exits
  agree, but counts/failure locations/warnings are missing. This route is excluded.
  `rtk npm test` and `rtk vitest run --reporter=default` preserve the tested signals.
- `rtk playwright test` injects `--reporter=json`; raw/wrapped counts, exits and
  failing locations agree, but standalone warning output can be elided. Keep
  `rtk npm run test:browser` for the measured runs. The specialized route remains
  diagnostic evidence, not the selected command policy.

The [npm filter](https://github.com/rtk-ai/rtk/blob/v1.1.0/src/cmds/js/npm_cmd.rs)
also intentionally strips `npm WARN` and notices. Dependency installation/audit
warnings need a raw command; the passing fixture scripts above are the verified
filtering boundary, not a universal fidelity claim.

## Recovery and actual native use

Raw bypass returned the complete failing test diagnostics with exit 1. A retained
failure was listed and recovered with `rtk recall HASH --full`, including the
warning and assertion. A browser-failure hint also identified retained raw output.
RTK can store a failure while its size guard emits raw output without a hint;
`rtk recall --list` demonstrated that case. Retention is not promised for success,
small output, capped/evicted entries or failed storage.

The same failing invocation with `RTK_RECALL_DB` beneath a regular file, and with
`RTK_RECALL=0`, preserved exit 1 and useful failure diagnostics and emitted no
misleading recall hint. Storage failure can be silent. When no usable recovery
exists, rerun `rtk bypass <original command>` and count that work. This exercised
actual unavailable storage rather than assuming all output was retained.

One bounded native 0.167.0 coordinator and its actual child read their respective
web/Canvas `AGENTS.md` policies. The coordinator executed `rtk npm run typecheck`
(exit 0); the child executed `rtk npm test -- --run tests/unit/input.test.ts` with
the Canvas command workdir (3 passes, exit 0). The coordinator's explicit raw
bypass emitted its expected marker (exit 0). The child inherits its native thread
cwd from the parent, so the actual Canvas workdir and policy read were verified
from its command arguments/output. The trusted ECC SessionStart hook ran; no RTK
hook or trust mutation occurred. This proves explicit use, not automatic rewriting.

All research, provisioning, diagnosis/retries, native coordinator/child and fallback
work belongs to `shared-b-preflight`, split equally between the two B runs under
[usage v1](usage-v1.md). Native sources and lineage remain private and are supplied
to the coordinator for complete reconciliation. No local RTK savings dashboard is
used as the adoption gate. One ENOSPC dependency-install attempt was retried after
owned cleanup; both locked installs then passed. Identical nonroot lock packages
allowed the sacrificial Canvas copy to reuse the owned web dependency tree to save
disk. Measured arms still create their own fresh activation/accounting state.

Ticket 22 owns the single two-compaction/process-restart validation. This preflight
performed no compaction or restart and does not claim that gate, measured savings,
or permanent rollout. Public configuration is validated directly; no tests assert
this prose and no upstream or application executable source is added here.
