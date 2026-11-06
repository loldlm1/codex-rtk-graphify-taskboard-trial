"""Behavior tests for source identity, independent from Graphify extraction."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('graphify_local', Path(__file__).parents[1] / 'tools/graphify_local.py')
local = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(local)


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        self.root.mkdir()
        self.git('init', '-q')
        (self.root / 'app.ts').write_text('export function original() { return 1; }\n')
        self.git('add', '.')
        self.git('-c', 'user.name=Trial', '-c', 'user.email=trial@example.invalid', 'commit', '-qm', 'starter')
        self.record = {'source': local.snapshot(self.root)}

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True).strip()


class FreshnessTests(FixtureCase):
    def test_unchanged_source_passes(self):
        self.assertEqual(local.check(self.root, self.record), self.record)

    def test_uncommitted_edit_is_stale_even_at_same_head(self):
        (self.root / 'app.ts').write_text('export function changed() { return 2; }\n')
        with self.assertRaisesRegex(ValueError, 'STALE_GRAPH'):
            local.check(self.root, self.record)

    def test_untracked_source_is_stale(self):
        (self.root / 'new.ts').write_text('export function added() {}\n')
        with self.assertRaisesRegex(ValueError, 'STALE_GRAPH'):
            local.check(self.root, self.record)

    def test_deleted_source_is_stale(self):
        (self.root / 'app.ts').unlink()
        with self.assertRaisesRegex(ValueError, 'STALE_GRAPH'):
            local.check(self.root, self.record)

    def test_same_commit_branch_switch_is_stale(self):
        self.git('switch', '-qc', 'another')
        with self.assertRaisesRegex(ValueError, 'STALE_GRAPH'):
            local.check(self.root, self.record)

    def test_other_worktree_rejected(self):
        other = Path(self.tmp.name) / 'other'
        self.git('worktree', 'add', '-q', '--detach', str(other), 'HEAD')
        with self.assertRaisesRegex(ValueError, 'STALE_GRAPH'):
            local.check(other, self.record)

    def test_ignored_cache_does_not_invalidate(self):
        (self.root / '.git/info/exclude').write_text('cache/\n')
        (self.root / 'cache').mkdir()
        (self.root / 'cache' / 'data').write_text('not source')
        self.assertEqual(local.check(self.root, self.record), self.record)

    def test_graph_tampering_is_stale(self):
        graph = Path(self.tmp.name) / 'graph.json'
        graph.write_text('{"nodes": []}')
        self.record.update(graph=str(graph), graph_sha256=local.digest(graph))
        local.check(self.root, self.record)
        graph.write_text('{"nodes": ["foreign"]}')
        with self.assertRaisesRegex(ValueError, 'graph bytes changed'):
            local.check(self.root, self.record)

    def test_nested_root_is_rejected(self):
        nested = self.root / 'nested'
        nested.mkdir()
        with self.assertRaisesRegex(ValueError, 'exact Git worktree root'):
            local.snapshot(nested)

    def test_source_symlinks_are_outside_coverage(self):
        (self.root / 'external.ts').symlink_to('/etc/hostname')
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            local.snapshot(self.root)

    def test_state_cannot_pollute_source_tree(self):
        for path in (self.root, self.root / 'generated'):
            with self.assertRaisesRegex(ValueError, 'outside'):
                local.state_dir(self.root, path)

    def test_each_worktree_gets_distinct_state(self):
        other = Path(self.tmp.name) / 'other'
        self.git('worktree', 'add', '-q', '--detach', str(other), 'HEAD')
        state = Path(self.tmp.name) / 'state'
        self.assertNotEqual(local.state_dir(self.root, state), local.state_dir(other, state))

    def test_provider_keys_and_unrelated_settings_are_absent(self):
        from unittest.mock import patch
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'synthetic-secret', 'GRAPHIFY_API_KEY': 'synthetic-secret',
                                      'GRAPHIFY_OUT': '/foreign', 'GRAPHIFY_BACKEND': 'openai'}):
            env = local.environment(Path(self.tmp.name) / 'env')
        self.assertNotIn('OPENAI_API_KEY', env)
        self.assertNotIn('GRAPHIFY_API_KEY', env)
        self.assertNotIn('GRAPHIFY_OUT', env)
        self.assertEqual(env['GRAPHIFY_BACKEND'], 'none')
        self.assertEqual(env['GRAPHIFY_MAX_WORKERS'], '2')
        self.assertEqual(env['GRAPHIFY_QUERY_LOG_DISABLE'], '1')

    def request(self, name='get_node', selected=None):
        args = {'label': 'original'}
        if selected is not None:
            args['project_path'] = str(selected)
        return {'jsonrpc': '2.0', 'id': 19, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}

    def test_guard_permits_fresh_source_query(self):
        self.assertIsNone(local.request_error(self.request(selected=self.root), self.root, self.record))

    def test_guard_rejects_foreign_worktree_with_mcp_error(self):
        result = local.request_error(self.request(selected=Path(self.tmp.name) / 'foreign'), self.root, self.record)
        self.assertEqual(result['id'], 19)
        self.assertTrue(result['result']['isError'])
        self.assertIn('WRONG_WORKTREE', result['result']['content'][0]['text'])

    def test_guard_rejects_stale_source_query(self):
        (self.root / 'app.ts').write_text('export function changed() {}')
        result = local.request_error(self.request(), self.root, self.record)
        self.assertTrue(result['result']['isError'])
        self.assertIn('STALE_GRAPH', result['result']['content'][0]['text'])

    def test_hosted_pr_tools_and_memory_resources_are_excluded(self):
        result = local.request_error(self.request(name='list_prs'), self.root, self.record)
        self.assertTrue(result['result']['isError'])
        result = local.request_error({'id': 2, 'method': 'resources/read'}, self.root, self.record)
        self.assertTrue(result['result']['isError'])

    def test_protocol_inventory_does_not_query_source(self):
        self.assertIsNone(local.request_error({'id': 1, 'method': 'tools/list'}, self.root, self.record))


# Opt in to the pinned external runtime; ordinary identity tests need only Python/Git.
import os
import queue
import threading


@unittest.skipUnless(os.environ.get('GRAPHIFY_TEST_PREFIX'), 'set GRAPHIFY_TEST_PREFIX to a provisioned locked venv')
class RuntimeTests(FixtureCase):
    def setUp(self):
        super().setUp()
        self.prefix = Path(os.environ['GRAPHIFY_TEST_PREFIX'])
        self.state = Path(self.tmp.name) / 'graphs'
        self.record = local.build(self.root, self.state, self.prefix)

    def client(self):
        config = local.configuration(self.root, self.state, self.prefix)
        error_log = tempfile.TemporaryFile(mode='w+')
        self.addCleanup(error_log.close)
        process = subprocess.Popen([config['command'], *config['args']], cwd=self.root,
                                   env=local.environment(self.state), stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=error_log, text=True)
        messages = queue.Queue()

        def read():
            for line in process.stdout:
                messages.put(json.loads(line))

        reader = threading.Thread(target=read, daemon=True)
        reader.start()

        def cleanup():
            process.stdin.close()
            process.wait(timeout=10)
            reader.join(timeout=2)
            process.stdout.close()
            self.assertEqual(process.returncode, 0)

        self.addCleanup(cleanup)
        seq = 0

        def call(method, params):
            nonlocal seq
            seq += 1
            process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': seq, 'method': method, 'params': params}) + '\n')
            process.stdin.flush()
            response = messages.get(timeout=30)
            self.assertEqual(response.get('id'), seq)
            self.assertNotIn('error', response)
            return response['result']

        call('initialize', {'protocolVersion': '2025-11-25', 'capabilities': {},
                            'clientInfo': {'name': 'graphify-runtime-test', 'version': '1'}})
        process.stdin.write(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) + '\n')
        process.stdin.flush()
        return call

    def test_actual_code_only_build_and_query(self):
        (self.root / 'README.md').write_text('This document must never be semantically indexed.\n')
        record = local.build(self.root, self.state, self.prefix)
        graph = json.loads(Path(record['graph']).read_text())
        self.assertTrue(graph['nodes'])
        self.assertTrue(all(n.get('_origin') == 'ast' for n in graph['nodes']))
        self.assertFalse(any(n.get('source_file') == 'README.md' for n in graph['nodes']))
        call = self.client()
        tools = call('tools/list', {})
        self.assertEqual({t['name'] for t in tools['tools']}, local.TOOLS)
        result = call('tools/call', {'name': 'get_node', 'arguments': {'label': 'original', 'project_path': str(self.root)}})
        self.assertFalse(result.get('isError'))
        self.assertIn('app.ts L1', result['content'][0]['text'])
        resources = call('resources/list', {})
        self.assertEqual(resources['resources'], [])

    def test_same_server_refuses_edit_then_uses_rebuilt_graph(self):
        call = self.client()
        (self.root / 'app.ts').write_text('export function replacement() { return 2; }\n')
        params = {'name': 'get_node', 'arguments': {'label': 'replacement', 'project_path': str(self.root)}}
        stale = call('tools/call', params)
        self.assertTrue(stale['isError'])
        self.assertIn('STALE_GRAPH', stale['content'][0]['text'])
        local.build(self.root, self.state, self.prefix)
        fresh = call('tools/call', params)
        self.assertFalse(fresh.get('isError'))
        self.assertIn('replacement()', fresh['content'][0]['text'])
        self.assertIn('app.ts L1', fresh['content'][0]['text'])

    def test_relocated_configuration_and_missing_state(self):
        cfg = local.configuration(self.root, self.state, self.prefix)
        self.assertEqual(cfg['cwd'], str(self.root))
        self.assertIn(str(self.prefix.resolve()), cfg['args'])
        self.assertIn(str(self.state.resolve()), cfg['args'])
        with self.assertRaises(FileNotFoundError):
            local.load(self.root, Path(self.tmp.name) / 'unactivated')
