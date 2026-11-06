# Graphify free local preflight, v1

Ticket [#21](https://github.com/loldlm1/.codex/issues/21) uses the official
[Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) package,
`graphifyy[mcp]==0.9.103`. This is isolated pilot tooling. No normal installation,
plugin, hook, trust setting, hosted Graphify service, or application feature changes.

## Pin and provenance

The maintained release on 2026-11-06 is
[`v0.9.103`](https://github.com/Graphify-Labs/graphify/releases/tag/v0.9.103), peeled
commit `16218bfc80d4ca2799734d045039f7ed1a5fa9fb`. [PyPI metadata](https://pypi.org/pypi/graphifyy/0.9.103/json)
records upload 2026-11-05 and the wheel SHA256
`7948c030f8b04153d88bc1ee23a485ddaa0c2d6aaa03a748c177e3c217bcfe34`.
All 97 installed Python source files matched that commit. The complete resolved
59-distribution closure is [hash locked](graphify-requirements.lock); it includes
MCP 2.3.0 and the package's mandatory parsers. Optional model SDK, database,
watch/media, hosted integration, and Graphify skill installation extras are absent.
The installed Graphify package-content fingerprint is
`24479aad442819e220500475ce2c2195bcbede8d174133bd61d6472931fc5748`.

The [upstream extraction source](https://github.com/Graphify-Labs/graphify/blob/16218bfc80d4ca2799734d045039f7ed1a5fa9fb/graphify/cli.py)
shows that `--code-only` skips semantic work but preserves existing semantic data,
even with `--force`. The [backend source](https://github.com/Graphify-Labs/graphify/blob/16218bfc80d4ca2799734d045039f7ed1a5fa9fb/graphify/llm.py)
provides `GRAPHIFY_BACKEND=none`. The [stdio server source](https://github.com/Graphify-Labs/graphify/blob/16218bfc80d4ca2799734d045039f7ed1a5fa9fb/graphify/serve.py)
reloads graph files by mtime/size; that mechanism does not compare live source.

The pinned [NOTICE](https://github.com/Graphify-Labs/graphify/blob/16218bfc80d4ca2799734d045039f7ed1a5fa9fb/NOTICE) identifies Apache-2.0 with earlier MIT portions retained in
[LICENSE-MIT](https://github.com/Graphify-Labs/graphify/blob/16218bfc80d4ca2799734d045039f7ed1a5fa9fb/LICENSE-MIT).
The pinned README's Privacy section describes offline, key-free code extraction;
the separate Cloud section advertises a hosted trial. Inspection of the installed
97 Python modules and the selected CLI extraction/stdio call paths found no
Graphify sign-in, license validation, subscription quota or machine-activation
gate on local code extraction/querying. That is a source-based conclusion for
this pin and path, supported by fresh-prefix operation, not a promise of unlimited
capacity or future product terms. Normal safeguards remain: the upstream
[graph loader](https://github.com/Graphify-Labs/graphify/blob/16218bfc80d4ca2799734d045039f7ed1a5fa9fb/graphify/security.py)
defaults to a 512-MiB JSON cap; traversal depth is capped at six; this activation
retains one project context and two extraction workers. No cap was raised. Without
the optional Leiden package this pin uses NetworkX Louvain communities. Rendering's
5,000-node aggregate-view default is separate from code-query licensing and was
not exercised here. Source coverage, memory and ordinary machine resources still
bound usefulness; large-corpus performance was not measured.

## Provision and activate only a selected B worktree

Use Python 3.12 and a task-owned prefix. The preflight used Python 3.12.8 on Linux
x86_64. `uv` is provisioning tooling; it is not required by the MCP launcher.
No Graphify account, subscription, vendor activation, API key, or model is needed.

```bash
uv venv "$graphify_prefix"
UV_CACHE_DIR="$trial_state/provision-cache" uv pip sync --no-cache --require-hashes \
  --python "$graphify_prefix/bin/python" \
  "$protocol_root/docs/protocol/graphify-requirements.lock" \
  --index-url https://pypi.org/simple
python "$protocol_root/tools/graphify_local.py" build \
  --root "$trial_root" --state "$trial_state" --prefix "$graphify_prefix"
python "$protocol_root/tools/graphify_local.py" config \
  --root "$trial_root" --state "$trial_state" --prefix "$graphify_prefix"
```

Set all variables to absolute paths. `trial_root` must be the exact Git worktree
root, and `trial_state` must be outside it. `config` prints a machine-specific
Codex MCP server stanza with absolute interpreter, launcher, prefix, root and state
paths. Apply that object only as process-local `-c mcp_servers.<name>.<key>=<JSON>`
overrides for the intended native process. It does not write configuration.
Each intended worker context needs its own exact-worktree stanza, or an explicitly
named server already configured for that worker's worktree. Always supply the same
absolute `project_path` in calls. A native child inherits available servers;
changing its cwd alone does not rebind a parent server's default graph.

Native proof used the retained authenticated, hook-reviewed Codex home in place;
auth/trust/caches/sessions were never copied into a treatment environment. Native
process state additionally isolates ECC_AGENT_DATA_HOME, CLV2_HOMUNCULUS_DIR,
TMPDIR, npm_config_cache and XDG_CACHE_HOME. Unrelated browser MCP was disabled
through process overrides. New native login or hook review remains an explicit
readiness dependency wherever required; Graphify itself requires neither.

A fresh second prefix was independently provisioned from this lock on the same
host. Its package contents and dependency versions matched, regenerated launch
paths referenced the new prefix/state, and an actual stdio query returned
`loadTasks()` at `src/storage.ts L6`. This proves relocation on the tested host;
other operating systems/Python versions remain untested. Recreate a venv instead
of copying it between machines because its entry-point shebangs contain local paths.

## Model exclusion, tool scope and resource bounds

The launcher builds into a new empty generation every time:
`graphify extract <root> --out <empty-generation> --code-only --no-dedup --max-workers 2`.
Only the new graph JSON is promoted; the temporary generation and all its sidecars
are removed. No previous semantic layer, graph, extraction cache, work memory,
reflection or learned overlay is imported. Fresh AST cache logs were 0/15 files
(web) and 0/20 (Canvas). No `--dedup-llm`, model backend, enrichment/cluster-only
command, global merge, watcher, or optional service runs.

Extraction and upstream MCP receive an explicit environment allowlist:
GRAPHIFY_BACKEND=none, GRAPHIFY_ALLOW_LOCAL_PROVIDERS=0,
GRAPHIFY_QUERY_LOG_DISABLE=1, GRAPHIFY_NO_TIPS=1, GRAPHIFY_NO_CTA=1,
GRAPHIFY_MAX_WORKERS=2, GRAPHIFY_MAX_CONTEXTS=1, task-owned TMPDIR/XDG paths,
fixed system PATH and locale. API keys, Graphify credentials, provider endpoints,
proxy settings, and unrelated inherited Graphify settings are absent. StdIO is
explicit. There is no HTTP listener or vendor request path in this activation.
The pinned graph bytes and installed source/dependency identity are checked.
These controls establish the chosen code-only path; they are not an OS network
sandbox or a general audit of every upstream command.

The launcher exposes only seven local source tools: `get_node`, `query_graph`,
`get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path`.
[Actual tool schemas](graphify-tools-v1.json) retain upstream arguments, including
`project_path`. Hosted/GitHub PR tools and graph memory/report resources are
excluded. Native proof used `get_node(label, project_path)` and
`query_graph(question, depth=1, token_budget=500, project_path)`. The token budget
is a preference: Canvas returned its complete approximately 655-token answer
with an over-budget notice. Count actual usage; no savings claim follows.

## Freshness and identity contract

`build`, `status`, `config` and every MCP source call compare an identity record:
canonical worktree root, Git directory, HEAD, branch, hashes of tracked and
untracked non-ignored files, and graph SHA256. The state directory is keyed by
canonical root. Another checkout's graph cannot satisfy that identity. Source
symlinks and submodules are rejected; ignored caches are outside this snapshot.
Keep fixture source in tracked/non-ignored files. Builds reject concurrent source
changes; operate serially while a query/build runs.

A source edit, addition, deletion, branch switch, commit, merge, graph tampering
or worktree mismatch requires a fresh rebuild. The server returns an MCP error
rather than answering against stale source. Rebuild with the same explicit root,
state and prefix, then query again. Upstream reload observes the new graph;
the independent identity check establishes why those bytes are current. Never
accept server connection, `built_at_commit`, a graph touch or reload as proof of
source freshness. Config/source checks are conservative: documentation changes
also require a rebuild even when the AST content is unchanged.

## Observed proof and limits

The exact immutable starters were web `01dbac8f5a60a1a5a5be89238971fd13badb3b56`
and Canvas `a4031c0da42d95f97d3b2e0fed4bdbcd76dd3087`. All mutation proofs used
sacrificial worktrees. Baseline graphs had 88 nodes/146 edges and 104/174,
respectively. Both answered real stdio node/search queries with verified source
locations. The native coordinator answered web `loadTasks()` at
`src/storage.ts L6`; its actual fresh child answered Canvas `GameController`
at `src/controller.ts L14`, using separate graph servers/output directories.
The child's process cwd remained web and its explicit Canvas server/project_path
selected Canvas correctly. No application implementation took place.

For each fixture, a harmless exported sentinel in an uncommitted edit was refused
as stale. Touching the old graph caused the raw upstream server to reload but did
not reveal the new source symbol. A fresh rebuild returned its exact source and
line. A branch switch at the same commit was refused until rebuilt. A separate
worktree initially lacked the symbol, used a distinct output directory, then
refused its old graph after fast-forward integration; rebuilding returned the
integrated symbol. Queries directed to another worktree were refused.

Native 0.167.0 produced four actual MCP tool calls across one coordinator and one
child. Ordinary turn-context metadata recorded gpt-6.1-sol/ultra for both, with no
spawn model/effort overrides; this preflight observation is separate from #16's
child xhigh observation. Keep measured-arm policy frozen and audit actual settings.
Native proof usage was 175,750 coordinator + 90,081 child = 265,831 tokens. This
is a native-proof subset; the complete shared-B allocation also includes outer
research/setup/test/review/retry usage and is owned by the central usage registry.
Cached input and reasoning are subsets, not extra additions. No compaction or
process-recovery probe was run here; #22 owns that single gate.

External TypeScript modules are covered. Generic HTML inline JavaScript remains
outside the frozen local-code extraction boundary. Both scans reported eight
non-code documents skipped. Graphify reported no symbols from seven web and six
Canvas code inputs (including entry/config/test files); some file nodes and
import edges still exist. AST graphs include inferred relationships and do not
replace direct source reading, behavioral tests, browser checks, or quality review.

First-use costs begin at the declared shared-B preflight boundary and split equally
between web B and Canvas B. Keep these private graphs/prefix trial states out of
measured arms. #22 and each B arm must create its own activation/configuration and
fresh graph after its accounting boundary, including worker roots and postmerge
rebuilds. A arms have no Graphify activation/index. Permanent adoption, global
configuration and hook changes remain outside this preflight.

For a genuinely new Codex home or machine, provision the accepted native/plugin
baseline using its supported installer/lifecycle, then complete native sign-in
and the required `/hooks` review in that home. Do not copy authentication, trust,
sessions or caches from this preflight. This home preparation is distinct from
Graphify's account-free provisioning. Once that separate prerequisite is satisfied,
#22 may activate freshly generated tool stanzas only for its short probe; each B
arm independently repeats activation/build after its own measurement boundary.
Changing CODEX_HOME alone does not isolate ECC/CLV2/npm/XDG process data.

Run the reusable launcher tests with the provisioned runtime explicitly selected:

```bash
GRAPHIFY_TEST_PREFIX="$graphify_prefix" python -m unittest discover -s tests -v
```

Without that variable, the 18 stdlib/Git identity tests run and the three actual
Graphify runtime tests are explicitly skipped. With the locked runtime, all 21
Graphify tests pass; the existing usage tests are part of full protocol validation.
Statement-line coverage of the launcher is 145/165 (87.88%); branches, upstream
package internals, other operating systems and large-corpus scaling were not
measured. Uncovered lines are chiefly uncommon failure/shutdown paths and the
CLI build/status/config dispatch; those commands also have independent fixture
proofs outside the instrumented unit suite.
