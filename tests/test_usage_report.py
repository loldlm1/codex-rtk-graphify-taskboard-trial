"""Public CLI tests; all session-shaped inputs are synthetic."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'tools' / 'usage_report.py'
KEYS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
        'output_tokens', 'reasoning_output_tokens', 'total_tokens')


def usage(n=10):
    return dict(zip(KEYS, (n, 3, 1, 4, 2, n + 4)))


def plus(*values):
    return {k: sum(v[k] for v in values) for k in KEYS}


def row(kind, payload, second=1):
    return {'timestamp': f'2026-01-01T00:00:{second:02d}Z',
            'type': kind, 'payload': payload}


def meta(thread='root', parent=None):
    return row('session_meta', {'id': thread, 'session_id': 'root',
                              'parent_thread_id': parent, 'cli_version': '0.167.0'}, 0)


def record(response, thread='root', turn='turn', root_turn='turn',
           amount=None, cumulative=None, second=1):
    amount = amount or usage()
    return row('token_usage_record', {
        'thread_id': thread, 'session_id': 'root', 'turn_id': turn,
        'root_turn_id': root_turn, 'response_id': response, 'usage': copy.deepcopy(amount),
        'turn_token_usage': copy.deepcopy(cumulative or amount),
        'thread_token_usage': copy.deepcopy(cumulative or amount)}, second)


def count(total, second=9):
    return row('event_msg', {'type': 'token_count',
                           'info': {'total_token_usage': total}}, second)


class ReportCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def run_report(self, files=None, change=None):
        if files is None:
            files = {'root': [meta(), record('response-one'), count(usage()),
                              row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})]}
        sources = []
        for name, rows in files.items():
            path = self.directory / (name + '.jsonl')
            raw = rows if isinstance(rows, bytes) else ''.join(json.dumps(r) + '\n' for r in rows).encode()
            path.write_bytes(raw)
            sources.append({'id': name, 'path': str(path),
                            'kind': 'notifications' if name == 'events' else 'native',
                            'sha256': hashlib.sha256(raw).hexdigest()})
        manifest = {
            'schema_version': 1, 'runtime_version': '0.167.0',
            'window': {'start': '2026-01-01T00:00:00Z',
                       'end': '2026-01-01T00:01:00Z',
                       'end_policy': 'assessment-report-evidence-freeze'},
            'runs': [{'id': 'sample', 'root_thread_id': 'root', 'session_id': 'root',
                      'closed': True,
                      'expected_threads': [{'thread_id': 'root', 'parent_thread_id': None}],
                      'sources': sources,
                      'phases': [{'id': 'upgrade', 'category': 'common-upgrade',
                                  'start': '2026-01-01T00:00:00Z',
                                  'end': '2026-01-01T00:01:00Z'}]}]}
        if change:
            change(manifest)
        path = self.directory / 'manifest.json'
        path.write_text(json.dumps(manifest))
        result = subprocess.run([sys.executable, str(CLI), '--manifest', str(path)],
                                capture_output=True, text=True)
        self.assertIn(result.returncode, (0, 2), result.stderr)
        self.assertEqual(result.stderr, '')
        data = json.loads(result.stdout)
        self.assertNotIn(str(self.directory), result.stdout)
        self.assertNotIn('response-one', result.stdout)
        return result.returncode, data

    def test_records_native_usage_and_subsets_once(self):
        code, report = self.run_report()
        self.assertEqual(code, 0)
        self.assertEqual(report['evidence_status'], 'reconciled')
        self.assertEqual(report['window_observed_usage'], usage())
        self.assertEqual(report['unique_responses'], 1)
        self.assertEqual(report['billing_completeness'], 'not-proven')
        self.assertEqual(report['measurement_readiness'], 'pending-live-compaction-restart-validation')
        self.assertEqual(report['runs'][0]['threads'][0]['response_count'], 1)

    def test_descendants_retry_replay_and_embedded_compaction(self):
        first = record('response-one')
        retry = record('response-retry', cumulative=plus(usage(), usage()), second=2)
        compact = record('response-compaction', amount=usage(20),
                         cumulative=plus(usage(), usage(), usage(20)), second=3)
        checkpoint = row('compacted', {'compaction_response_id': 'response-compaction',
                         'latest_token_usage_record': compact['payload'],
                         'replacement_history': [{'private': 'never output this'}],
                         'window_id': 'window-one'}, 4)
        events = [{'method': 'item/started', 'params': {'threadId': 'root',
                   'item': {'type': 'subAgentActivity', 'kind': 'started', 'agentThreadId': 'child'}}}]
        files = {'root': [meta(), first, retry, compact, checkpoint, first,
                          count(plus(usage(), usage())),
                          row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})],
                 'child': [meta('child', 'root'), record('child-response', 'child', 'child-turn'),
                           count(usage()), row('event_msg', {'type': 'task_complete', 'turn_id': 'child-turn'})],
                 'events': events}
        def change(m):
            m['runs'][0]['expected_threads'].append({'thread_id': 'child', 'parent_thread_id': 'root'})
        code, report = self.run_report(files, change)
        self.assertEqual(code, 0, report)
        self.assertEqual(report['unique_responses'], 4)
        self.assertEqual(report['duplicate_records'], 2)
        self.assertEqual(report['window_observed_usage'], plus(usage(), usage(), usage(20), usage()))
        self.assertEqual(report['runs'][0]['ordinary_compaction_delta'], usage(20))
        self.assertEqual(len(report['runs'][0]['checkpoints']), 1)

    def test_replayed_source_and_conflicting_ordinary_snapshot(self):
        rows = [meta(), record('response-one'), count(usage()),
                row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})]
        code, report = self.run_report({'root': rows, 'replay': rows})
        self.assertEqual(code, 0, report)
        self.assertEqual(report['unique_responses'], 1)
        self.assertEqual(report['duplicate_records'], 1)
        bad = copy.deepcopy(rows)
        bad[2] = count(usage(20))
        code, report = self.run_report({'root': rows, 'replay': bad})
        self.assertEqual(code, 2, report)
        self.assertIn('conflicting_ordinary_snapshot', {x['code'] for x in report['issues']})

    def test_missing_completion_cannot_be_borrowed_from_another_thread(self):
        files = {'root': [meta(), record('response-one'), count(usage())],
                 'child': [meta('child', 'root'), record('child-response', 'child'), count(usage()),
                           row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})],
                 'events': [{'method': 'item/started', 'params': {'threadId': 'root',
                   'item': {'type': 'subAgentActivity', 'kind': 'started', 'agentThreadId': 'child'}}}]}
        def change(m):
            m['runs'][0]['expected_threads'].append({'thread_id': 'child', 'parent_thread_id': 'root'})
        code, report = self.run_report(files, change)
        self.assertEqual(code, 2, report)
        self.assertIn('missing_turn_completion', {x['code'] for x in report['issues']})

    def test_fail_closed_for_bad_native_evidence(self):
        mutations = {
            'missing_usage': lambda r: r['payload'].update(usage=None),
            'unsupported_usage_schema': lambda r: r['payload']['usage'].update(new_category=2),
            'invalid_category_totals': lambda r: r['payload']['usage'].update(total_tokens=99),
            'invalid_category_subset': lambda r: r['payload']['usage'].update(cached_input_tokens=100),
            'ledger_reconciliation': lambda r: r['payload']['thread_token_usage'].update(input_tokens=100, total_tokens=104),
            'unknown_thread': lambda r: r['payload'].update(thread_id='missing-child'),
            'root_turn_lineage': lambda r: r['payload'].update(root_turn_id='wrong-root-turn'),
            'missing_response_identity': lambda r: r['payload'].update(response_id=None),
        }
        for issue, mutate in mutations.items():
            with self.subTest(issue=issue):
                rec = record('response-one'); mutate(rec)
                code, report = self.run_report({'root': [meta(), rec, count(usage())]})
                self.assertEqual(code, 2, report)
                self.assertEqual(report['evidence_status'], 'incomplete')
                self.assertIn(issue, [x['code'] for x in report['issues']])
                self.assertIsNone(report['allocated_arm_usage'])

    def test_conflicting_duplicate_and_missing_descendant(self):
        changed = record('response-one', amount=usage(20))
        events = [{'method': 'item/completed', 'params': {'threadId': 'root',
                   'item': {'type': 'subAgentActivity', 'kind': 'started', 'agentThreadId': 'omitted'}}}]
        code, report = self.run_report({'root': [meta(), record('response-one'), changed, count(usage())],
                                        'events': events})
        self.assertEqual(code, 2)
        self.assertTrue({'conflicting_duplicate', 'missing_descendant'} <= {x['code'] for x in report['issues']})

    def test_missing_file_digest_malformed_and_unknown_runtime(self):
        changes = [lambda m: m['runs'][0]['sources'][0].update(path='/unavailable/private/session'),
                   lambda m: m['runs'][0]['sources'][0].update(sha256='0' * 64),
                   lambda m: m.update(runtime_version='0.168.0'),
                   lambda m: m.update(schema_version=2)]
        for change in changes:
            with self.subTest(change=change):
                code, report = self.run_report(change=change)
                self.assertEqual(code, 2, report)
        code, report = self.run_report({'root': [meta(), row('token_usage_record_v2', {})]})
        self.assertEqual(code, 2)
        self.assertIn('unsupported_native_schema', {x['code'] for x in report['issues']})

    def test_known_omissions_and_unaccounted_completion_fail(self):
        indicators = [row('event_msg', {'type': 'error', 'message': 'private storage failure'}),
                      row('event_msg', {'type': 'raw_response_completed', 'response_id': 'lost', 'usage': None}),
                      row('event_msg', {'type': 'background_compaction_started'}),
                      row('event_msg', {'type': 'context_compacted'})]
        for indicator in indicators:
            code, report = self.run_report({'root': [meta(), record('response-one'), count(usage()),
                row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}), indicator]})
            self.assertEqual(code, 2, report)
            self.assertNotIn('private storage failure', json.dumps(report))

    def test_missing_cumulative_and_open_window_are_incomplete(self):
        code, report = self.run_report({'root': [meta(), record('response-one')]})
        self.assertEqual(code, 2)
        self.assertIn('missing_ordinary_cumulative', {x['code'] for x in report['issues']})
        code, report = self.run_report(change=lambda m: m['window'].update(end=None))
        self.assertEqual(code, 2)
        self.assertIn('open_measurement_window', {x['code'] for x in report['issues']})

    def test_invalid_json_and_malformed_metadata_never_expose_inputs(self):
        cases = [b'not-json private-canary\n', b'\xff\n',
                 [meta(), row('event_msg', {'type': 'token_count', 'info': []})],
                 [meta(), row('event_msg', {'type': ['private-canary']})],
                 [meta(), row('token_usage_record', [])]]
        for rows in cases:
            with self.subTest(rows=type(rows).__name__):
                code, report = self.run_report({'root': rows})
                self.assertEqual(code, 2, report)
                self.assertNotIn('private-canary', json.dumps(report))

    def test_b_first_use_must_declare_activation_index_and_shared_preflight(self):
        def change(m):
            m['runs'][0]['phases'][0].update(category='arm', workload='web', arm='B')
        code, report = self.run_report(change=change)
        self.assertEqual(code, 2, report)
        self.assertIn('missing_b_first_use_phases', {x['code'] for x in report['issues']})

    def test_response_projection_preserves_hashed_ownership(self):
        code, report = self.run_report()
        self.assertEqual(code, 0)
        response = report['responses'][0]
        self.assertEqual(response['response_id_hash'], hashlib.sha256(b'response-one').hexdigest())
        self.assertEqual(response['thread_id_hash'], hashlib.sha256(b'root').hexdigest())
        self.assertEqual(response['usage'], usage())

    def test_embedded_only_response_has_unknown_original_phase_time(self):
        compact = record('response-one')
        checkpoint = row('compacted', {'compaction_response_id': 'response-one',
                         'latest_token_usage_record': compact['payload'],
                         'replacement_history': [{'synthetic': True}], 'window_id': 'window-one'}, 4)
        code, report = self.run_report({'root': [meta(), checkpoint, count(usage()),
            row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})]})
        self.assertEqual(code, 2, report)
        self.assertIn('missing_original_response_timestamp', {x['code'] for x in report['issues']})

    def test_checkpoint_requires_native_replacement_history_shape(self):
        compact = record('response-one')
        checkpoint = row('compacted', {'compaction_response_id': 'response-one',
                         'latest_token_usage_record': compact['payload'],
                         'replacement_history': 'invalid-private-canary', 'window_id': 'window-one'}, 4)
        code, report = self.run_report({'root': [meta(), compact, checkpoint, count(usage()),
            row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})]})
        self.assertEqual(code, 2, report)
        self.assertIn('incomplete_compaction_checkpoint', {x['code'] for x in report['issues']})

    def test_compaction_marker_requires_own_thread_checkpoint(self):
        root_record = record('response-one')
        child_record = record('child-response', 'child', 'child-turn')
        child_checkpoint = row('compacted', {'compaction_response_id': 'child-response',
            'window_id': 'child-window', 'replacement_history': [{'synthetic': True}],
            'latest_token_usage_record': child_record['payload']}, 4)
        files = {
            'root': [meta(), root_record, count(usage()),
                     row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}),
                     row('event_msg', {'type': 'context_compacted'}, 5)],
            'child': [meta('child', 'root'), child_record, child_checkpoint, count(usage()),
                      row('event_msg', {'type': 'task_complete', 'turn_id': 'child-turn'})],
            'events': [{'method': 'item/started', 'params': {'threadId': 'root', 'item': {
                'type': 'subAgentActivity', 'kind': 'started', 'agentThreadId': 'child'}}}]}
        def change(m):
            m['runs'][0]['expected_threads'].append({'thread_id': 'child', 'parent_thread_id': 'root'})
        code, report = self.run_report(files, change)
        self.assertEqual(code, 2, report)
        self.assertIn('missing_compaction_checkpoint', {x['code'] for x in report['issues']})
        self.assertIsNone(report['allocated_arm_usage'])
        root_checkpoint = copy.deepcopy(child_checkpoint)
        root_checkpoint['payload'].update(compaction_response_id='response-one',
            window_id='root-window', latest_token_usage_record=root_record['payload'])
        files['root'].append(root_checkpoint)
        code, report = self.run_report(files, change)
        self.assertEqual(code, 0, report)
        self.assertEqual(len(report['runs'][0]['checkpoints']), 2)
        # A checkpoint in the root file cannot borrow the child's response identity.
        files['root'][-1] = child_checkpoint
        code, report = self.run_report(files, change)
        self.assertEqual(code, 2, report)
        self.assertIn('compaction_checkpoint_ownership', {x['code'] for x in report['issues']})

    def test_checkpoint_replay_preserves_response_window_and_persisted_metadata(self):
        first = record('response-one')
        second = record('response-two', cumulative=plus(usage(), usage()), second=2)
        checkpoint = row('compacted', {'compaction_response_id': 'response-one',
            'window_id': 'window-one', 'replacement_history': [{'synthetic': True}],
            'latest_token_usage_record': first['payload']}, 4)
        native = [meta(), first, second, checkpoint, count(plus(usage(), usage())),
                  row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})]
        mutations = {
            'response-window': {'window_id': 'window-conflicting'},
            'window-response': {'compaction_response_id': 'response-two',
                                'latest_token_usage_record': second['payload']},
            'replacement-history': {'replacement_history': [{'synthetic': 'changed'}]},
            'embedded-snapshot': {'latest_token_usage_record': second['payload']},
        }
        for case, changed in mutations.items():
            with self.subTest(case=case):
                conflict = copy.deepcopy(checkpoint)
                conflict['payload'].update(changed)
                code, report = self.run_report({'root': native + [conflict]})
                self.assertEqual(code, 2, report)
                self.assertIn('conflicting_compaction_checkpoint', {x['code'] for x in report['issues']})
                self.assertIsNone(report['allocated_arm_usage'])
        # Identical persisted evidence may recur in another snapshot of this thread.
        code, report = self.run_report({'root': native, 'replay': copy.deepcopy(native)})
        self.assertEqual(code, 0, report)
        self.assertEqual(report['unique_responses'], 2)
        self.assertEqual(report['window_observed_usage'], plus(usage(), usage()))
        self.assertEqual(len(report['runs'][0]['checkpoints']), 1)

    def test_observed_completion_usage_must_match_ledger(self):
        native = [meta(), record('response-one'), count(usage()),
                  row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})]
        for kind in ('raw_response_completed', 'response_completed'):
            with self.subTest(kind=kind):
                completion = row('event_msg', {'type': kind, 'response_id': 'response-one',
                                              'usage': usage(999)})
                code, report = self.run_report({'root': native + [completion]})
                self.assertEqual(code, 2, report)
                self.assertIn('completion_reconciliation', {x['code'] for x in report['issues']})
                self.assertIsNone(report['allocated_arm_usage'])
                completion['payload']['usage'] = usage()
                code, report = self.run_report({'root': native + [completion, completion]})
                self.assertEqual(code, 0, report)
                self.assertEqual(report['window_observed_usage'], usage())
        completion = {'type': 'raw_response_completed', 'response_id': 'response-one', 'usage': usage()}
        for changed in [dict(thread_id='other'), dict(turn_id='other'), dict(session_id='other'),
                        dict(root_turn_id='other'), dict(usage={'private-canary': 1}),
                        dict(unsupported='private-canary')]:
            with self.subTest(changed=tuple(changed)):
                code, report = self.run_report({'root': native + [
                    row('event_msg', dict(completion, **changed))]})
                self.assertEqual(code, 2, report)
                self.assertIsNone(report['allocated_arm_usage'])

    def test_completion_notification_counters_schema_and_ownership(self):
        native = [meta(), record('response-one'), count(usage()),
                  row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})]
        camel = ('inputTokens', 'cachedInputTokens', 'cacheWriteInputTokens',
                 'outputTokens', 'reasoningOutputTokens', 'totalTokens')
        params = {'threadId': 'root', 'turnId': 'turn', 'responseId': 'response-one',
                  'usage': dict(zip(camel, usage().values())), 'usageMetadata': None}
        for method in ('thread/rawResponse/completed', 'response/completed'):
            code, report = self.run_report({'root': native, 'events': [{'method': method, 'params': params}]})
            self.assertEqual(code, 0, report)
            mutations = [dict(threadId='other'), dict(turnId='other'),
                         dict(usage=dict(zip(camel, usage(999).values()))),
                         dict(usage={'private-canary': 1}), dict(responseId='unknown'),
                         dict(usage=None)]
            for changed in mutations:
                with self.subTest(method=method, changed=tuple(changed)):
                    code, report = self.run_report({'root': native, 'events': [
                        {'method': method, 'params': dict(params, **changed)}]})
                    self.assertEqual(code, 2, report)
                    self.assertIsNone(report['allocated_arm_usage'])
                    self.assertNotIn('private-canary', json.dumps(report))

    def test_standalone_duplicate_timestamp_conflict_fails(self):
        code, report = self.run_report({'root': [meta(), record('response-one'),
            record('response-one', second=2), count(usage()),
            row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})]})
        self.assertEqual(code, 2, report)
        self.assertIn('conflicting_duplicate', {x['code'] for x in report['issues']})

    def test_relative_source_paths_are_relative_to_manifest(self):
        code, report = self.run_report(change=lambda m: m['runs'][0]['sources'][0].update(path='root.jsonl'))
        self.assertEqual(code, 0, report)

    def test_unknown_accounting_event_is_incomplete(self):
        code, report = self.run_report({'root': [meta(), record('response-one'), count(usage()),
              row('event_msg', {'type': 'future_usage_event'})]})
        self.assertEqual(code, 2, report)
        self.assertIn('unsupported_native_schema', {x['code'] for x in report['issues']})

    def test_notification_totals_and_failed_turns_fail_closed(self):
        camel = ('inputTokens', 'cachedInputTokens', 'cacheWriteInputTokens',
                 'outputTokens', 'reasoningOutputTokens', 'totalTokens')
        native = [meta(), record('response-one'), count(usage()),
                  row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})]
        for event in [
            {'method': 'thread/tokenUsage/updated', 'params': {'threadId': 'root',
                'tokenUsage': {'total': dict(zip(camel, usage(20).values()))}}},
            {'method': 'thread/tokenUsage/updated', 'params': {'threadId': 'root', 'tokenUsage': {}}},
            {'method': 'turn/completed', 'params': {'turn': {'status': 'failed', 'error': {'message': 'private-canary'}}}},
        ]:
            code, report = self.run_report({'root': native, 'events': [event]})
            self.assertEqual(code, 2, report)
            self.assertNotIn('private-canary', json.dumps(report))

    def test_fixed_first_use_allocation_and_common_full_window(self):
        rows = [meta()]
        total = {k: 0 for k in KEYS}
        categories = [('arm', 'web', 'A'), ('arm', 'web', 'B'), ('activation', 'web', 'B'),
                      ('indexing', 'web', 'B'), ('arm', 'canvas', 'A'), ('arm', 'canvas', 'B'),
                      ('activation', 'canvas', 'B'), ('indexing', 'canvas', 'B'),
                      ('shared-b-preflight', None, None), ('fixture', None, None),
                      ('evaluation', None, None), ('probe', None, None), ('administration', None, None)]
        for i, _ in enumerate(categories, 1):
            total = plus(total, usage(11))
            rows.append(record(f'r-{i}', amount=usage(11), cumulative=total, second=i))
        rows.append(count(total, 20))
        rows.append(row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}, 20))
        def change(m):
            m['window']['end'] = '2026-01-01T00:00:13Z'
            m['runs'][0]['phases'] = [dict(id=f'phase-{i}', category=c,
                start=f'2026-01-01T00:00:{i:02d}Z', end=f'2026-01-01T00:00:{i+1:02d}Z',
                **({'workload': w, 'arm': a} if w else {}))
                for i, (c, w, a) in enumerate(categories, 1)]
        code, report = self.run_report({'root': rows}, change)
        self.assertEqual(code, 0, report)
        self.assertEqual(report['window_observed_usage'], {k: v * 12 for k, v in usage(11).items()})
        self.assertEqual(report['outside_window_usage'], usage(11))
        self.assertEqual(report['raw_arm_usage']['web-B'], {k: v * 3 for k, v in usage(11).items()})
        self.assertEqual(report['allocated_arm_usage']['web-B']['total_tokens'], '105/2')
        self.assertEqual(report['shared_b_preflight_usage'], usage(11))
        self.assertEqual(report['allocated_arm_usage']['web-A']['total_tokens'], '15')

    def test_phase_gaps_overlap_and_invalid_allocation_are_incomplete(self):
        changes = [lambda m: m['runs'][0]['phases'][0].update(start='2026-01-01T00:00:02Z'),
                   lambda m: m['runs'][0]['phases'].append(copy.deepcopy(m['runs'][0]['phases'][0])),
                   lambda m: m['runs'][0]['phases'][0].update(category='activation', arm='A', workload='web'),
                   lambda m: m['runs'][0].update(closed=False)]
        for change in changes:
            code, report = self.run_report(change=change)
            self.assertEqual(code, 2, report)


if __name__ == '__main__':
    unittest.main()
