# Task-board workflow trial

This public, reusable repository tests a Codex workflow coordinated by Matt Pocock's
skills, with ECC as its sole TDD provider. The comparison uses the validated updated
hybrid without experimental activation and the same hybrid with RTK command filtering
and Graphify Labs' free local MCP.

The maintainer defines and approves scope. Codex agents prepare, implement, test and
review the fixtures. Native account sign-in and hook approvals remain human actions;
agent-built does not mean those approvals were automated.

The planned measured task is saved status filters for an existing task board.
The application starter will be preserved on a dedicated branch and immutable tag.
Measured solution branches and PRs remain separate and will not be merged into it.
Shared measurement code lives on the task-board repository's `protocol/v1` branch,
separate from the application starter trees.

The initial pilot has exactly four implementations across the two repositories.
Adoption requires at least 10% fewer allocated complete-run tokens on **each**
workload and no meaningful output-quality regression. A pooled average cannot
rescue a failing workload. No outcome or savings is claimed during preparation.

Accepted common stack profile: `51ed50320fff77610a9030e0846fbe6f532c39ba6c766466ffb0f1026b4d2f97`.
Source, prompts/configuration, acceptance, checks, aggregate usage, application
artifacts and limitations will be versioned. Private sessions, credentials, native
trust/configuration and generated caches will remain private. Routine future upgrades
start with proportional compatibility/recovery checks; full comparisons need a
material reason, and tasks rotate when contamination or relevance requires it.

Current phase: bootstrap published; runnable starter and measured evidence pending.
No measured solution, release or deployment is present.

The shared [native usage protocol](docs/protocol/usage-v1.md) provides a standard-library
CLI, synthetic runnable example, strict incomplete results and fixed first-use
allocation on `protocol/v1`. Ordinary native delegation/restart has reconciled;
measurement readiness remains pending the same separate live compaction/restart
probe. [Validation evidence](docs/protocol/usage-v1-validation.md) records its limits.
