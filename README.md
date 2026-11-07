# Task-board workflow trial

This public, reusable repository tests a Codex workflow coordinated by Matt Pocock's
skills, with ECC as its sole TDD provider. The comparison uses the validated updated
hybrid without experimental activation and the same hybrid with RTK command filtering
and Graphify Labs' free local MCP.

The maintainer defines and approves scope. Codex agents prepare, implement, test and
review the fixtures. Native account sign-in and hook approvals remain human actions;
agent-built does not mean those approvals were automated.

The measured task adds saved status filters to an existing task board.
The application starter is preserved on `starter/v1` and immutable `starter-v1.0.0`.
Measured solution branches and draft PRs remain separate and unmerged.
Shared measurement code lives on the task-board repository's `protocol/v1` branch,
separate from the application starter trees.

The initial pilot has exactly four implementations across the two repositories.
Adoption requires at least 10% fewer allocated complete-run tokens on **each**
workload and no meaningful output-quality regression. A pooled average cannot
rescue a failing workload. Both first-use token gates failed; permanent tool
integration is deferred while the validated Matt/ECC update remains deliverable.
See the [pilot results](docs/results/pilot-v1.md), [public counters and evidence](docs/results/pilot-v1/)
and [reuse/upgrade guide](docs/results/reuse-v1.md).

Accepted common stack profile: `51ed50320fff77610a9030e0846fbe6f532c39ba6c766466ffb0f1026b4d2f97`.
Source, prompts/configuration, acceptance, checks, aggregate usage, application
artifacts and limitations are versioned. Private sessions, credentials, native
trust/configuration and generated caches remain private. Routine future upgrades
start with proportional compatibility/recovery checks; full comparisons need a
material reason, and tasks rotate when contamination or relevance requires it.

Current phase: all four implementations and neutral quality reviews are complete;
final selected-scope review and report-evidence freeze are in progress. Retained
solutions are linked from the report. Trial PRs remain unmerged; user acceptance
and final plugin-update merge authorization are separate.

The shared [native usage protocol](docs/protocol/usage-v1.md) provides a standard-library
CLI, synthetic runnable example, strict incomplete results and fixed first-use
allocation on `protocol/v1`. Ordinary native delegation/restart and the separate
live compaction/restart probe have reconciled. The collector retains its static
pending-readiness label; [accepted native recovery proof](docs/protocol/recovery-proof-v1.json)
supplies that operational prerequisite separately. [Validation evidence](docs/protocol/usage-v1-validation.md)
records parser limits; universal provider billing completeness remains unproven.

The isolated [Graphify local preflight](docs/protocol/graphify-local-v1.md) records
the official pinned runtime, hash-locked provisioning, per-worktree freshness guard
and actual native coordinator/worker query evidence. It does not activate tooling
for a normal checkout or establish a measured savings result.

The [short recovery protocol](docs/protocol/recovery-v1.md) requires two installed
manual compactions, exact-thread process restart, real resumed RTK/MCP behavior
and strict compaction/replay reconciliation. The
[four-run measurement contract](docs/protocol/measurement-v1.md) fixes runtime,
fresh-worker policy, isolation, counterbalanced order, quality checks and first-use
allocation before any measured outcome.
