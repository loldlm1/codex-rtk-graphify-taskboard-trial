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


def native_line(event, ordinal):
    event = dict(timestamp=event['timestamp'], ordinal=ordinal,
                 type=event['type'], payload=event['payload'])
    if event['type'] == 'token_usage_record':
        event['payload'] = {k: event['payload'][k] for k in
                            ('thread_id', 'turn_id', 'session_id', 'root_turn_id', 'response_id',
                             'usage', 'turn_token_usage', 'thread_token_usage')}
    # Match the pinned Rust writer's envelope and compact serialization.
    event['timestamp'] = event['timestamp'].replace('Z', '.000Z')
    return json.dumps(event, separators=(',', ':')).encode() + b'\n'


def partial_retry(event, ordinal=1, cut=None):
    complete = native_line(event, ordinal)
    retry = complete.replace(b'.000Z', b'.100Z', 1)
    return complete[:cut or len(complete) - 5] + b'\n', retry


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

    def window_manifest(self, manifest):
        """Select a byte-exact full-history root prefix for an active root turn."""
        manifest['window']['end'] = '2026-01-01T00:00:20Z'
        run = manifest['runs'][0]
        run['closed'] = False
        run['phases'][0]['end'] = manifest['window']['end']
        source = run['sources'][0]
        raw = Path(source['path']).read_bytes()
        last = json.loads(raw.splitlines()[-1])
        run['window_closure'] = {
            'kind': 'root-response-boundary', 'source_id': source['id'],
            'turn_id': 'turn', 'response_id': 'response-one', 'response_ordinal': 1,
            'source_bytes': len(raw), 'last_ordinal': last.get('ordinal'),
            'cutoff': manifest['window']['end']}

    def window_rows(self, rows=None):
        rows = rows or [meta(), record('response-one'), count(usage())]
        return b''.join(native_line(event, ordinal) for ordinal, event in enumerate(rows))

    def test_root_response_window_closes_only_explicit_active_root_boundary(self):
        raw = self.window_rows()
        code, report = self.run_report({'root': raw}, self.window_manifest)
        self.assertEqual(code, 0, report)
        self.assertEqual(report['window_observed_usage'], usage())
        self.assertEqual(report['billing_completeness'], 'not-proven')
        closure = report['runs'][0]['window_closure']
        self.assertEqual(closure['kind'], 'root-response-boundary')
        self.assertEqual(closure['accounting_window'], 'closed')
        self.assertEqual(closure['root_turn_completion'], 'unclaimed')
        self.assertEqual(closure['response_id_hash'], hashlib.sha256(b'response-one').hexdigest())
        self.assertEqual(closure['source_bytes'], len(raw))
        self.assertEqual(closure['response_ordinal'], 1)
        self.assertEqual(closure['last_ordinal'], 2)
        self.assertEqual(closure['source_sha256'], hashlib.sha256(raw).hexdigest())
        for closed, issue in ((True, 'missing_turn_completion'), (False, 'open_run')):
            code, report = self.run_report({'root': raw},
                lambda m: m['runs'][0].update(closed=closed))
            self.assertEqual(code, 2, report)
            self.assertIn(issue, {x['code'] for x in report['issues']})
            self.assertIsNone(report['allocated_arm_usage'])

    def test_root_response_window_requires_other_root_turns_completed(self):
        earlier = record('earlier', turn='earlier-turn', root_turn='earlier-turn')
        current = record('response-one', cumulative=plus(usage(), usage()), second=3)
        current['payload']['turn_token_usage'] = usage()
        for complete in (False, True):
            rows = [meta(), earlier]
            if complete:
                rows.append(row('event_msg', {'type': 'task_complete', 'turn_id': 'earlier-turn'}, 2))
            rows.extend([current, count(plus(usage(), usage()))])
            def change(m):
                self.window_manifest(m)
                m['runs'][0]['window_closure']['response_ordinal'] = 3 if complete else 2
            code, report = self.run_report({'root': self.window_rows(rows)}, change)
            self.assertEqual(code, 0 if complete else 2, report)
            if not complete:
                self.assertIn('missing_turn_completion', {x['code'] for x in report['issues']})
                self.assertIsNone(report['allocated_arm_usage'])

    def test_root_response_window_requires_every_child_turn_completed(self):
        for complete in (False, True):
            child = [meta('child', 'root'), record('child-response', thread='child', turn='child-turn'), count(usage())]
            if complete:
                child.append(row('event_msg', {'type': 'task_complete', 'turn_id': 'child-turn'}, 10))
            files = {'root': self.window_rows(), 'child': child, 'events': [{
                'method': 'item/completed', 'params': {'threadId': 'root', 'item': {
                    'type': 'subAgentActivity', 'kind': 'started', 'agentThreadId': 'child'}}}]}
            def change(m):
                self.window_manifest(m)
                m['runs'][0]['expected_threads'].append({'thread_id': 'child', 'parent_thread_id': 'root'})
            code, report = self.run_report(files, change)
            self.assertEqual(code, 0 if complete else 2, report)
            if not complete:
                self.assertIn('missing_turn_completion', {x['code'] for x in report['issues']})
                self.assertIsNone(report['allocated_arm_usage'])

    def test_root_response_window_tracks_owning_turns_without_usage(self):
        for position in ('earlier-root', 'later-root', 'later-child'):
            with self.subTest(position=position):
                root = [meta(), record('response-one'), count(usage())]
                started = row('event_msg', {'type': 'task_started', 'turn_id': 'unfinished'}, 10)
                if position == 'earlier-root':
                    started['timestamp'] = meta()['timestamp']
                    root.insert(1, started)
                elif position == 'later-root': root.append(started)
                child = [meta('child', 'root'), record('child-response', thread='child', turn='child-turn'),
                         count(usage()), row('event_msg', {'type': 'task_complete', 'turn_id': 'child-turn'}, 10)]
                if position == 'later-child': child.append(started)
                files = {'root': self.window_rows(root), 'child': child, 'events': [{
                    'method': 'item/completed', 'params': {'threadId': 'root', 'item': {
                        'type': 'subAgentActivity', 'kind': 'started', 'agentThreadId': 'child'}}}]}
                def change(m):
                    self.window_manifest(m)
                    m['runs'][0]['expected_threads'].append({'thread_id': 'child', 'parent_thread_id': 'root'})
                    if position == 'earlier-root':
                        m['runs'][0]['window_closure']['response_ordinal'] = 2
                code, report = self.run_report(files, change)
                self.assertEqual(code, 2, report)
                self.assertIn('missing_turn_completion', {x['code'] for x in report['issues']})
                self.assertIsNone(report['allocated_arm_usage'])

    def test_root_response_window_rejects_missing_started_identity(self):
        for event_type in ('task_started', 'turn_started'):
            for identity_kind in ('missing', 'null'):
                with self.subTest(event_type=event_type, identity_kind=identity_kind):
                    payload = {'type': event_type}
                    if identity_kind == 'null':
                        payload['turn_id'] = None
                    rows = [meta(), record('response-one'), count(usage()),
                            row('event_msg', payload, 10)]
                    code, report = self.run_report({'root': self.window_rows(rows)}, self.window_manifest)
                    self.assertEqual(code, 2, report)
                    self.assertEqual(report['evidence_status'], 'incomplete')
                    self.assertIn('missing_response_identity', {x['code'] for x in report['issues']})
                    self.assertIsNone(report['allocated_arm_usage'])
                    self.assertEqual(report['runs'][0]['window_closure']['accounting_window'], 'unverified')

    def test_root_response_window_rejects_malformed_started_identity(self):
        for event_type in ('task_started', 'turn_started'):
            for value in ('', False, 0, [], {}, 'private-canary' * 80):
                with self.subTest(event_type=event_type, value=value):
                    rows = [meta(), record('response-one'), count(usage()),
                            row('event_msg', {'type': event_type, 'turn_id': value}, 10)]
                    code, report = self.run_report({'root': self.window_rows(rows)}, self.window_manifest)
                    self.assertEqual(code, 2, report)
                    self.assertIn('missing_response_identity', {x['code'] for x in report['issues']})
                    self.assertIsNone(report['allocated_arm_usage'])
                    self.assertNotIn('private-canary', json.dumps(report))
                    self.assertEqual(report['runs'][0]['window_closure']['accounting_window'], 'unverified')

    def test_root_response_window_rejects_child_start_without_identity(self):
        for event_type in ('task_started', 'turn_started'):
            for identity_kind in ('missing', 'null'):
                with self.subTest(event_type=event_type, identity_kind=identity_kind):
                    payload = {'type': event_type}
                    if identity_kind == 'null':
                        payload['turn_id'] = None
                    child = [meta('child', 'root'),
                             record('child-response', thread='child', turn='child-turn'), count(usage()),
                             row('event_msg', {'type': 'task_complete', 'turn_id': 'child-turn'}, 10),
                             row('event_msg', payload, 11)]
                    files = {'root': self.window_rows(), 'child': child, 'events': [{
                        'method': 'item/completed', 'params': {'threadId': 'root', 'item': {
                            'type': 'subAgentActivity', 'kind': 'started', 'agentThreadId': 'child'}}}]}
                    def change(m):
                        self.window_manifest(m)
                        m['runs'][0]['expected_threads'].append({'thread_id': 'child', 'parent_thread_id': 'root'})
                    code, report = self.run_report(files, change)
                    self.assertEqual(code, 2, report)
                    self.assertIn('missing_response_identity', {x['code'] for x in report['issues']})
                    self.assertIsNone(report['allocated_arm_usage'])

    def test_valid_started_identity_and_optional_context_identity_remain_accepted(self):
        for event_type in ('task_started', 'turn_started'):
            for context_identity in ({}, {'turn_id': None}, {'turn_id': 'turn'}):
                for window in (False, True):
                    with self.subTest(event_type=event_type, context_identity=context_identity, window=window):
                        rows = [meta(), row('event_msg', {'type': event_type, 'turn_id': 'turn'}),
                                record('response-one'), count(usage()), row('turn_context', context_identity, 10)]
                        if not window:
                            rows.append(row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}, 11))
                        def change(m):
                            self.window_manifest(m)
                            m['runs'][0]['window_closure']['response_ordinal'] = 2
                        code, report = self.run_report({'root': self.window_rows(rows)}, change if window else None)
                        self.assertEqual(code, 0, report)
                        self.assertEqual(report['evidence_status'], 'reconciled')
                        self.assertEqual(report['window_observed_usage'], usage())
                        self.assertIsNotNone(report['allocated_arm_usage'])
                        if window:
                            self.assertEqual(report['runs'][0]['window_closure']['root_turn_completion'], 'unclaimed')

    def test_strict_closure_requires_started_turns_without_usage_completed(self):
        for event_type in ('task_started', 'turn_started'):
            for thread in ('root', 'child'):
                for complete in (False, True):
                    with self.subTest(event_type=event_type, thread=thread, complete=complete):
                        root = [meta(), record('response-one'), count(usage()),
                                row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}, 10)]
                        child = [meta('child', 'root'), record('child-response', thread='child', turn='child-turn'),
                                 count(usage()), row('event_msg', {'type': 'task_complete', 'turn_id': 'child-turn'}, 10)]
                        owning = root if thread == 'root' else child
                        owning.append(row('event_msg', {'type': event_type, 'turn_id': 'nonmodel-turn'}, 11))
                        if complete:
                            owning.append(row('event_msg', {'type': 'task_complete', 'turn_id': 'nonmodel-turn'}, 12))
                        files = {'root': root, 'child': child, 'events': [{
                            'method': 'item/completed', 'params': {'threadId': 'root', 'item': {
                                'type': 'subAgentActivity', 'kind': 'started', 'agentThreadId': 'child'}}}]}
                        def change(m):
                            m['runs'][0]['expected_threads'].append({'thread_id': 'child', 'parent_thread_id': 'root'})
                        code, report = self.run_report(files, change)
                        self.assertEqual(code, 0 if complete else 2, report)
                        self.assertEqual(report['window_observed_usage'], plus(usage(), usage()))
                        self.assertEqual(report['unique_responses'], 2)
                        if complete:
                            self.assertIsNotNone(report['allocated_arm_usage'])
                        else:
                            self.assertEqual({x['code'] for x in report['issues']}, {'missing_turn_completion'})
                            self.assertIsNone(report['allocated_arm_usage'])

    def test_strict_closure_rejects_missing_or_malformed_started_identity(self):
        for event_type in ('task_started', 'turn_started'):
            for identity_kind, value in (('missing', None), ('null', None), ('empty', ''),
                                         ('boolean', False), ('number', 0), ('array', []),
                                         ('object', {}), ('oversized', 'private-canary' * 80)):
                with self.subTest(event_type=event_type, identity_kind=identity_kind):
                    payload = {'type': event_type}
                    if identity_kind != 'missing':
                        payload['turn_id'] = value
                    rows = [meta(), record('response-one'), count(usage()),
                            row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}, 10),
                            row('event_msg', payload, 11)]
                    code, report = self.run_report({'root': rows})
                    self.assertEqual(code, 2, report)
                    self.assertIn('missing_response_identity', {x['code'] for x in report['issues']})
                    self.assertIsNone(report['allocated_arm_usage'])
                    self.assertNotIn('private-canary', json.dumps(report))

    def test_root_response_window_rejects_missing_or_mismatched_binding(self):
        changes = {'kind': 'future-kind', 'source_id': 'absent', 'turn_id': 'absent',
                   'response_id': 'absent', 'response_ordinal': 0, 'source_bytes': 1,
                   'last_ordinal': 1, 'cutoff': '2026-01-01T00:00:19Z'}
        for field, value in changes.items():
            for missing in (False, True):
                with self.subTest(field=field, missing=missing):
                    def change(m):
                        self.window_manifest(m)
                        boundary = m['runs'][0]['window_closure']
                        if missing:
                            del boundary[field]
                        else:
                            boundary[field] = value
                    code, report = self.run_report({'root': self.window_rows()}, change)
                    self.assertEqual(code, 2, report)
                    self.assertIsNone(report['allocated_arm_usage'])
        for field in ('response_ordinal', 'source_bytes', 'last_ordinal'):
            for bad in (True, -1, '1'):
                def change(m):
                    self.window_manifest(m)
                    m['runs'][0]['window_closure'][field] = bad
                code, report = self.run_report({'root': self.window_rows()}, change)
                self.assertEqual(code, 2, report)
        for mutation in ('closed-run', 'open-window', 'open-phase', 'admin', 'phase-gap', 'unknown-field'):
            def change(m):
                self.window_manifest(m)
                run = m['runs'][0]
                if mutation == 'closed-run': run['closed'] = True
                elif mutation == 'open-window': m['window']['end'] = None
                elif mutation == 'open-phase': run['phases'][0]['end'] = None
                elif mutation == 'admin': run['phases'][0]['category'] = 'administration'
                elif mutation == 'phase-gap': run['phases'][0]['start'] = '2026-01-01T00:00:02Z'
                else: run['window_closure']['private-canary'] = True
            code, report = self.run_report({'root': self.window_rows()}, change)
            self.assertEqual(code, 2, report)
            self.assertIsNone(report['allocated_arm_usage'])

    def test_root_response_window_rejects_earlier_nonroot_embedded_or_late_anchor(self):
        for bad in ('earlier', 'embedded', 'foreign-owner', 'at-cutoff', 'before-window', 'later-other-source', 'replayed-earlier'):
            with self.subTest(bad=bad):
                root = [meta(), record('response-one'), count(usage())]
                if bad in ('earlier', 'later-other-source', 'replayed-earlier'):
                    later = record('response-two', cumulative=plus(usage(), usage()), second=10)
                    root = [meta(), record('response-one'), later, count(plus(usage(), usage()), 11)]
                    if bad == 'replayed-earlier': root.insert(3, record('response-one'))
                elif bad == 'embedded':
                    root[1] = row('compacted', {'latest_token_usage_record': record('response-one')['payload'],
                        'compaction_response_id': 'response-one', 'window_id': 'window', 'replacement_history': [{}]})
                elif bad == 'foreign-owner': root[1]['payload']['thread_id'] = 'child'
                elif bad == 'at-cutoff': root[1]['timestamp'] = '2026-01-01T00:00:20Z'
                files = {'root': self.window_rows(root)}
                if bad == 'later-other-source':
                    files['root'] = self.window_rows()
                    files['later'] = self.window_rows(root)
                def change(m):
                    self.window_manifest(m)
                    if bad == 'before-window': m['window']['start'] = '2026-01-01T00:00:02Z'
                    if bad == 'replayed-earlier': m['runs'][0]['window_closure']['response_ordinal'] = 3
                code, report = self.run_report(files, change)
                self.assertEqual(code, 2, report)
                self.assertIsNone(report['allocated_arm_usage'])

    def test_root_response_window_requires_complete_ordinal_prefix_and_ordinary_snapshot(self):
        for bad in ('first-ordinal', 'gap', 'duplicate', 'missing-ordinal', 'missing-ordinary',
                    'ordinary-before-response', 'later-row', 'unterminated', 'counter-gap', 'error', 'unknown'):
            with self.subTest(bad=bad):
                rows = [meta(), record('response-one'), count(usage())]
                if bad == 'missing-ordinary': rows.pop()
                elif bad == 'ordinary-before-response': rows[2]['timestamp'] = rows[0]['timestamp']
                elif bad == 'later-row': rows.append(row('response_item', {}, 20))
                elif bad == 'counter-gap': rows[2] = count(usage(11))
                elif bad in ('error', 'unknown'):
                    rows.append(row('event_msg', {'type': 'error' if bad == 'error' else 'new-accounting-event'}, 10))
                raw = self.window_rows(rows)
                if bad == 'first-ordinal': raw = raw.replace(b'"ordinal":0', b'"ordinal":7', 1)
                elif bad == 'gap': raw = raw.replace(b'"ordinal":1', b'"ordinal":7', 1)
                elif bad == 'duplicate': raw = raw.replace(b'"ordinal":2', b'"ordinal":1', 1)
                elif bad == 'missing-ordinal': raw = raw.replace(b'"ordinal":1,', b'', 1)
                elif bad == 'unterminated': raw = raw[:-1]
                code, report = self.run_report({'root': raw}, self.window_manifest)
                self.assertEqual(code, 2, report)
                self.assertIsNone(report['allocated_arm_usage'])

    def test_root_response_window_retains_verified_retry_and_compaction_checks(self):
        partial, retry = partial_retry(record('response-one'))
        raw = (native_line(meta(), 0) + partial + retry + native_line(count(usage()), 2))
        code, report = self.run_report({'root': raw}, self.window_manifest)
        self.assertEqual(code, 0, report)
        self.assertEqual(len(report['runs'][0]['sources'][0]['partial_write_recoveries']), 1)
        compact = record('compact', cumulative=plus(usage(), usage()), second=3)
        checkpoint = row('compacted', {'compaction_response_id': 'compact', 'window_id': 'window',
            'replacement_history': [{}], 'latest_token_usage_record': compact['payload']}, 4)
        rows = [meta(), record('response-one'), compact, checkpoint, count(usage(), 5)]
        def change(m):
            self.window_manifest(m)
            m['runs'][0]['window_closure'].update(response_id='compact', response_ordinal=2)
        code, report = self.run_report({'root': self.window_rows(rows)}, change)
        self.assertEqual(code, 0, report)
        self.assertEqual(report['runs'][0]['ordinary_compaction_delta'], usage())
        rows[-1] = count(usage(11), 5)
        code, report = self.run_report({'root': self.window_rows(rows)}, change)
        self.assertEqual(code, 2, report)
        self.assertIn('ordinary_reconciliation', {x['code'] for x in report['issues']})
        self.assertIsNone(report['allocated_arm_usage'])

    def test_records_native_usage_and_subsets_once(self):
        code, report = self.run_report()
        self.assertEqual(code, 0)
        self.assertEqual(report['evidence_status'], 'reconciled')
        self.assertEqual(report['window_observed_usage'], usage())
        self.assertEqual(report['unique_responses'], 1)
        self.assertEqual(report['billing_completeness'], 'not-proven')
        self.assertEqual(report['measurement_readiness'], 'pending-live-compaction-restart-validation')
        self.assertEqual(report['runs'][0]['threads'][0]['response_count'], 1)

    def test_verified_partial_write_retries_count_complete_usage_once(self):
        first, retry = partial_retry(record('response-one'))
        item = row('event_msg', {'type': 'item_completed', 'thread_id': 'root', 'turn_id': 'turn',
                                 'item': {'type': 'CommandExecution', 'private': 'private-canary'}})
        partial_item, retry_item = partial_retry(item, 2)
        raw = (native_line(meta(), 0) + first + retry + partial_item + retry_item
               + native_line(count(usage()), 3)
               + native_line(row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}), 4))
        code, report = self.run_report({'root': raw})
        self.assertEqual(code, 0, report)
        self.assertEqual(report['unique_responses'], 1)
        self.assertEqual(report['duplicate_records'], 0)
        self.assertEqual(report['window_observed_usage'], usage())
        source = report['runs'][0]['sources'][0]
        self.assertEqual(source['sha256'], hashlib.sha256(raw).hexdigest())
        recoveries = source['partial_write_recoveries']
        self.assertEqual([(x['partial_line'], x['retry_line'], x['ordinal'], x['type']) for x in recoveries],
                         [(2, 3, 1, 'token_usage_record'), (4, 5, 2, 'event_msg')])
        self.assertEqual(recoveries[0]['partial_sha256'], hashlib.sha256(first).hexdigest())
        self.assertEqual(recoveries[0]['retry_sha256'], hashlib.sha256(retry).hexdigest())
        self.assertNotIn('private-canary', json.dumps(report))

    def test_exact_response_item_retry_is_audited_and_adds_no_usage(self):
        for item_type in ('reasoning', 'custom_tool_call'):
            for short in (False, True):
                with self.subTest(item_type=item_type, short=short):
                    event = row('response_item', {'type': item_type, 'private': 'private-canary',
                                                 'usage': usage(999)})
                    partial, retry = partial_retry(event)
                    if short:
                        partial = partial[:partial.index(b'"payload":') + 3] + b'\n'
                    raw = native_line(meta(), 0) + partial + retry
                    raw += native_line(record('response-one', second=2), 2)
                    raw += native_line(count(usage()), 3)
                    raw += native_line(row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}), 4)
                    code, report = self.run_report({'root': raw})
                    self.assertEqual(code, 0, report)
                    self.assertEqual(report['unique_responses'], 1)
                    self.assertEqual(report['window_observed_usage'], usage())
                    source = report['runs'][0]['sources'][0]
                    self.assertEqual(source['sha256'], hashlib.sha256(raw).hexdigest())
                    recovery = source['partial_write_recoveries'][0]
                    self.assertEqual((recovery['partial_line'], recovery['retry_line'], recovery['ordinal'], recovery['type']),
                                     (2, 3, 1, 'response_item'))
                    self.assertEqual(recovery['partial_sha256'], hashlib.sha256(partial).hexdigest())
                    self.assertEqual(recovery['retry_sha256'], hashlib.sha256(retry).hexdigest())
                    self.assertNotIn('private-canary', json.dumps(report))

    def test_response_item_retry_preserves_exact_envelope_and_boundary_requirements(self):
        for bad in ('ordinal', 'type', 'prefix', 'timestamp', 'intervening', 'multiple-partials',
                    'incomplete-type', 'previous-ordinal', 'next-ordinal', 'phase', 'window', 'other-ignored-type'):
            with self.subTest(bad=bad):
                event = row('response_item', {'type': 'reasoning', 'private': 'private-canary'})
                partial, retry = partial_retry(event)
                if bad == 'ordinal': retry = retry.replace(b'"ordinal":1', b'"ordinal":2')
                elif bad == 'type': retry = retry.replace(b'"type":"response_item"', b'"type":"world_state"')
                elif bad == 'prefix': retry = retry.replace(b'private-canary', b'changed-canary')
                elif bad == 'timestamp': retry = retry.replace(b'.100Z', b'.000Z')
                elif bad == 'intervening': retry = native_line(row('response_item', {}), 1) + retry
                elif bad == 'multiple-partials': retry = partial + retry
                elif bad == 'incomplete-type': partial = partial[:partial.index(b'response_item') + 4] + b'\n'
                elif bad == 'other-ignored-type':
                    partial = partial.replace(b'response_item', b'world_state')
                    retry = retry.replace(b'response_item', b'world_state')
                raw = native_line(meta(), 5 if bad == 'previous-ordinal' else 0) + partial + retry
                raw += native_line(record('response-one', second=2), 9 if bad == 'next-ordinal' else 2)
                raw += native_line(count(usage()), 3)
                raw += native_line(row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}), 4)
                def change(m):
                    if bad == 'window': m['window']['start'] = '2026-01-01T00:00:01.050Z'
                    elif bad == 'phase':
                        phase = m['runs'][0]['phases'][0]
                        phase['end'] = '2026-01-01T00:00:01.050Z'
                        m['runs'][0]['phases'].append(dict(phase, id='next', start=phase['end'], end='2026-01-01T00:01:00Z'))
                code, report = self.run_report({'root': raw}, change)
                self.assertEqual(code, 2, report)
                self.assertIn('invalid_retry_ordinal' if bad == 'next-ordinal' else 'malformed_source',
                              {x['code'] for x in report['issues']})
                self.assertIsNone(report['allocated_arm_usage'])

    def test_partial_recovery_rejects_unmatched_changed_and_ambiguous_rows(self):
        first, retry = partial_retry(record('response-one'))
        cases = {
            'ordinal': (first, retry.replace(b'"ordinal":1', b'"ordinal":2')),
            'type': (first, retry.replace(b'"type":"token_usage_record"', b'"type":"compacted"')),
            'owner': (first, retry.replace(b'"thread_id":"root"', b'"thread_id":"other"')),
            'counter': (first, retry.replace(b'"input_tokens":10', b'"input_tokens":11')),
            'timestamp': (first, retry.replace(b'.100Z', b'.000Z')),
            'unknown-malformed': (b'{"private":"private-canary"\n', retry),
            'short-prefix': (first[:50] + b'\n', retry),
            'unmatched': (first, b''),
            'intervening': (first, native_line(row('response_item', {}), 1) + retry),
            'multiple-partials': (first, first + retry),
            'non-prefix': (first[:-2] + b'!\n', retry),
            'invalid-retry': (first, retry[:-2] + b'!\n'),
            'prior-ordinal': (first, retry),
        }
        for name, (partial, complete) in cases.items():
            with self.subTest(name=name):
                owner = native_line(meta(), 5 if name == 'prior-ordinal' else 0)
                raw = owner + partial + complete + native_line(count(usage()), 2)
                raw += native_line(row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}), 3)
                code, report = self.run_report({'root': raw})
                self.assertEqual(code, 2, report)
                self.assertIn('malformed_source', {x['code'] for x in report['issues']})
                self.assertIsNone(report['allocated_arm_usage'])

    def test_partial_recovery_requires_unambiguous_envelope_and_full_retry(self):
        for bad in ('incomplete-ordinal', 'incomplete-type', 'event-without-owner', 'event-foreign-owner', 'duplicate-json-key'):
            with self.subTest(bad=bad):
                event = record('response-one')
                if bad.startswith('event-'):
                    event = row('event_msg', {'type': 'item_completed', 'item': {}})
                    if bad == 'event-foreign-owner':
                        event['payload'].update(thread_id='other', turn_id='turn')
                partial, retry = partial_retry(event)
                if bad == 'incomplete-ordinal':
                    partial = partial[:partial.index(b'"ordinal":') + len(b'"ordinal":')] + b'\n'
                elif bad == 'incomplete-type':
                    partial = partial[:partial.index(b'"type":"') + len(b'"type":"token_')] + b'\n'
                elif bad == 'duplicate-json-key':
                    retry = retry[:-2] + b',"type":"response_item"}\n'
                raw = native_line(meta(), 0) + partial + retry + native_line(count(usage()), 2)
                raw += native_line(row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}), 3)
                code, report = self.run_report({'root': raw})
                self.assertEqual(code, 2, report)
                self.assertIn('malformed_source', {x['code'] for x in report['issues']})

    def test_same_ordinal_known_type_retry_recovers_short_native_header(self):
        item = row('event_msg', {'type': 'item_completed', 'thread_id': 'root', 'turn_id': 'turn', 'item': {}})
        for event in (item, record('response-one')):
            with self.subTest(kind=event['type']):
                partial, retry = partial_retry(event)
                partial = partial[:partial.index(b'"payload":') + 3] + b'\n'
                rows = native_line(meta(), 0) + partial + retry
                total = usage()
                next_ordinal = 2
                if event['type'] == 'event_msg':
                    rows += native_line(record('response-one', second=2), next_ordinal)
                    next_ordinal += 1
                rows += native_line(count(total), next_ordinal)
                rows += native_line(row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}), next_ordinal+1)
                code, report = self.run_report({'root': rows})
                self.assertEqual(code, 0, report)
                self.assertEqual(report['window_observed_usage'], total)
                self.assertEqual(len(report['runs'][0]['sources'][0]['partial_write_recoveries']), 1)

    def test_recovery_requires_following_ordinal_and_explained_cumulative_totals(self):
        for bad in ('next-ordinal', 'missing-next-ordinal', 'ledger-gap', 'ordinary-gap'):
            partial, retry = partial_retry(record('response-one'))
            following = count(usage(20) if bad == 'ordinary-gap' else usage())
            if bad == 'ledger-gap':
                event = record('response-one', cumulative=usage(20))
                partial, retry = partial_retry(event)
            next_row = native_line(following, 9 if bad == 'next-ordinal' else 2)
            if bad == 'missing-next-ordinal':
                next_row = next_row.replace(b'"ordinal":2,', b'')
            raw = native_line(meta(), 0) + partial + retry + next_row
            raw += native_line(row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}), 3)
            code, report = self.run_report({'root': raw})
            self.assertEqual(code, 2, report)
            expected = {'next-ordinal': 'invalid_retry_ordinal', 'missing-next-ordinal': 'invalid_retry_ordinal',
                        'ledger-gap': 'ledger_reconciliation', 'ordinary-gap': 'ordinary_reconciliation'}[bad]
            self.assertIn(expected, {x['code'] for x in report['issues']})
            self.assertIsNone(report['allocated_arm_usage'])

    def test_partial_recovery_cannot_cross_phase_or_window_boundaries(self):
        first, retry = partial_retry(record('response-one'))
        raw = native_line(meta(), 0) + first + retry + native_line(count(usage()), 2)
        raw += native_line(row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}), 3)
        for boundary in ('phase', 'window'):
            def change(m):
                if boundary == 'window':
                    m['window']['start'] = '2026-01-01T00:00:01.050Z'
                else:
                    phase = m['runs'][0]['phases'][0]
                    phase['end'] = '2026-01-01T00:00:01.050Z'
                    m['runs'][0]['phases'].append(dict(phase, id='next', start=phase['end'], end='2026-01-01T00:01:00Z'))
            code, report = self.run_report({'root': raw}, change)
            self.assertEqual(code, 2, report)
            self.assertIn('malformed_source', {x['code'] for x in report['issues']})

    def test_recovered_rows_still_require_source_hash_and_valid_counters(self):
        for bad in ('hash', 'counters', 'source-owner'):
            event = record('response-one')
            if bad == 'counters':
                event['payload']['usage']['total_tokens'] = 99
            if bad == 'source-owner':
                event['payload']['thread_id'] = 'child'
            first, retry = partial_retry(event)
            raw = native_line(meta(), 0) + first + retry + native_line(count(usage()), 2)
            raw += native_line(row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}), 3)
            def change(m):
                if bad == 'hash':
                    m['runs'][0]['sources'][0]['sha256'] = '0' * 64
            code, report = self.run_report({'root': raw}, change)
            self.assertEqual(code, 2, report)
            self.assertIn({'hash': 'source_digest_mismatch', 'counters': 'invalid_category_totals',
                           'source-owner': 'record_ownership'}[bad], {x['code'] for x in report['issues']})

    def fork_files(self):
        own = meta('child', 'root')
        own['payload'].update(forked_from_id='root', subagent_history_start_ordinal=4)
        inherited = [meta(), count(usage(999)), row('event_msg', {'type': 'turn_aborted'})]
        rows = [own] + inherited + [record('child-response', 'child', 'child-turn'),
                                   count(usage()), row('event_msg', {'type': 'task_complete', 'turn_id': 'child-turn'})]
        files = {'root': [meta(), record('response-one'), count(usage()),
                          row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})],
                 'child': rows,
                 'events': [{'method': 'item/started', 'params': {'threadId': 'root',
                    'item': {'type': 'subAgentActivity', 'kind': 'started', 'agentThreadId': 'child'}}}]}
        return files

    def run_fork(self, files, change=None):
        files = copy.deepcopy(files)
        if isinstance(files['child'], list):
            files['child'] = b''.join(native_line(r, i) for i, r in enumerate(files['child']))
        def manifest(m):
            m['runs'][0]['expected_threads'].append({'thread_id': 'child', 'parent_thread_id': 'root'})
            if change:
                change(m)
        return self.run_report(files, manifest)

    def test_explicit_fork_boundary_keeps_canonical_child_owner(self):
        code, report = self.run_fork(self.fork_files())
        self.assertEqual(code, 0, report)
        self.assertEqual(report['unique_responses'], 2)
        self.assertEqual(report['window_observed_usage'], plus(usage(), usage()))
        self.assertEqual(report['runs'][0]['ordinary_compaction_delta'], dict.fromkeys(KEYS, 0))
        child = report['runs'][0]['sources'][1]['inherited_history']
        self.assertEqual(child['start_ordinal'], 4)
        self.assertEqual(child['excluded_rows'], 3)
        self.assertEqual(child['parent_thread_id_hash'], hashlib.sha256(b'root').hexdigest())

    def test_fork_boundary_rejects_missing_invalid_or_foreign_metadata(self):
        for bad in ('missing', 'null', 'bool', 'negative', 'no-parent', 'wrong-fork', 'foreign', 'conflict', 'after-boundary', 'never-reached', 'missing-ordinal', 'gap'):
            with self.subTest(bad=bad):
                files = self.fork_files(); rows = files['child']; own = rows[0]['payload']
                if bad == 'missing': own.pop('subagent_history_start_ordinal')
                elif bad in ('null', 'bool', 'negative'): own['subagent_history_start_ordinal'] = {'null':None, 'bool':True, 'negative':-1}[bad]
                elif bad == 'no-parent': own['parent_thread_id'] = None
                elif bad == 'wrong-fork': own['forked_from_id'] = 'other'
                elif bad == 'foreign': rows[1]['payload']['id'] = 'other'
                elif bad == 'conflict': rows[1]['payload']['cli_version'] = 'other'
                elif bad == 'after-boundary': rows[4] = meta()
                elif bad == 'never-reached': own['subagent_history_start_ordinal'] = 100
                elif bad == 'missing-ordinal': files['child'] = ''.join(json.dumps(r)+'\n' for r in rows).encode()
                elif bad == 'gap': files['child'] = b''.join(native_line(r, i if i < 2 else i+1) for i,r in enumerate(rows))
                code, report = self.run_fork(files)
                self.assertEqual(code, 2, report)
                self.assertIsNone(report['allocated_arm_usage'])

    def test_inherited_usage_requires_matching_original_parent_record(self):
        for bad in (False, True):
            files = self.fork_files()
            files['child'][2] = record('response-one')
            if bad:
                files['child'][2]['payload']['usage'] = usage(20)
            code, report = self.run_fork(files)
            self.assertEqual(code, 2 if bad else 0, report)
            self.assertEqual(report['unique_responses'], 2)
            if bad:
                self.assertIn('inherited_usage_mismatch', {x['code'] for x in report['issues']})

    def test_fork_history_does_not_hide_unknown_or_missing_parent_evidence(self):
        for bad in ('unknown', 'malformed', 'checkpoint', 'missing-parent', 'foreign-usage'):
            files = self.fork_files()
            if bad == 'unknown': files['child'][2] = row('new_accounting', {})
            elif bad == 'checkpoint': files['child'][2] = row('compacted', {})
            elif bad == 'missing-parent': files.pop('root')
            elif bad == 'foreign-usage': files['child'][2] = record('unseen-parent-response')
            elif bad == 'malformed':
                files['child'] = b''.join(native_line(r, i) if i != 2 else b'{"private":"private-canary"\n'
                                          for i, r in enumerate(files['child']))
            code, report = self.run_fork(files)
            self.assertEqual(code, 2, report)
            self.assertIsNone(report['allocated_arm_usage'])

    def native_start_files(self, event_type='item_completed'):
        start = row('event_msg', {'type': event_type, 'thread_id': 'root',
            'turn_id': 'turn', 'item': {'type': 'SubAgentActivity', 'kind': 'started',
                'agent_thread_id': 'child', 'model': 'synthetic-model',
                'reasoning_effort': 'high', 'id': 'synthetic-call', 'agent_path': '/synthetic'}}, 2)
        return {'root': [meta(), row('event_msg', {'type': 'task_started', 'turn_id': 'turn'}),
                         start, record('response-one', second=3), count(usage()),
                         row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'})],
                'child': [meta('child', 'root'), record('child-response', 'child', 'child-turn'),
                          count(usage()), row('event_msg', {'type': 'task_complete', 'turn_id': 'child-turn'})]}

    def run_native_start(self, files, change=None):
        def manifest(m):
            m['runs'][0]['expected_threads'].append({'thread_id': 'child', 'parent_thread_id': 'root'})
            if change:
                change(m)
        return self.run_report(files, manifest)

    def test_persisted_native_starts_supply_descendant_inventory_without_notifications(self):
        for event_type in ('item_started', 'item_completed'):
            with self.subTest(event_type=event_type):
                files = self.native_start_files(event_type)
                files['root'].insert(3, copy.deepcopy(files['root'][2]))
                files['replay'] = copy.deepcopy(files['root'])
                code, report = self.run_native_start(files)
                self.assertEqual(code, 0, report)
                self.assertEqual(report['unique_responses'], 2)
                self.assertEqual(report['duplicate_records'], 1)
                self.assertEqual(report['window_observed_usage'], plus(usage(), usage()))
                self.assertEqual(report['runs'][0]['ordinary_compaction_delta'], dict.fromkeys(KEYS, 0))

    def test_native_start_rejects_missing_or_invalid_provenance_identities(self):
        for field in ('thread_id', 'turn_id', 'agent_thread_id'):
            for value in ('missing', None, '', True, [], {}, 'x' * 1025):
                with self.subTest(field=field, value=value):
                    files = self.native_start_files()
                    payload = files['root'][2]['payload']
                    target = payload['item'] if field == 'agent_thread_id' else payload
                    if value == 'missing': target.pop(field)
                    else: target[field] = value
                    code, report = self.run_native_start(files)
                    self.assertEqual(code, 2, report)
                    self.assertIn('invalid_descendant_start_identity', {x['code'] for x in report['issues']})
                    self.assertIsNone(report['allocated_arm_usage'])

    def test_native_start_rejects_foreign_parent_self_child_and_unobserved_turn(self):
        for bad in ('foreign-parent', 'self-child', 'wrong-turn', 'missing-owning-turn', 'completed-turn'):
            with self.subTest(bad=bad):
                files = self.native_start_files()
                payload = files['root'][2]['payload']
                issue = 'descendant_start_ownership'
                if bad == 'foreign-parent': payload['thread_id'] = 'foreign'
                elif bad == 'self-child': payload['item']['agent_thread_id'] = 'root'
                else:
                    issue = 'descendant_start_turn_ownership'
                    if bad == 'wrong-turn': payload['turn_id'] = 'other-turn'
                    elif bad == 'missing-owning-turn': files['root'].pop(1)
                    elif bad == 'completed-turn':
                        files['root'].insert(2, row('event_msg', {'type': 'task_complete', 'turn_id': 'turn'}))
                code, report = self.run_native_start(files)
                self.assertEqual(code, 2, report)
                self.assertIn(issue, {x['code'] for x in report['issues']})
                self.assertIsNone(report['allocated_arm_usage'])

    def test_native_activity_targets_and_notification_shapes_do_not_supply_native_births(self):
        for bad in ('wait', 'notification-case', 'missing-item', 'invalid-item'):
            with self.subTest(bad=bad):
                files = self.native_start_files()
                payload = files['root'][2]['payload']
                if bad == 'wait': payload['item']['kind'] = 'waiting'
                elif bad == 'notification-case':
                    payload['item'] = {'type': 'subAgentActivity', 'kind': 'started', 'agentThreadId': 'child'}
                elif bad == 'missing-item': payload.pop('item')
                else: payload['item'] = []
                code, report = self.run_native_start(files)
                self.assertEqual(code, 2, report)
                self.assertIn('missing_descendant_start', {x['code'] for x in report['issues']})
                self.assertIsNone(report['allocated_arm_usage'])

    def test_native_start_requires_child_source_and_declared_lineage(self):
        for bad in ('missing-source', 'missing-inventory', 'wrong-parent'):
            with self.subTest(bad=bad):
                files = self.native_start_files()
                def change(m):
                    threads = m['runs'][0]['expected_threads']
                    if bad == 'missing-inventory': threads.pop()
                    elif bad == 'wrong-parent':
                        threads.append({'thread_id': 'other', 'parent_thread_id': 'root'})
                        threads[1]['parent_thread_id'] = 'other'
                if bad == 'missing-source': files.pop('child')
                code, report = self.run_native_start(files, change)
                self.assertEqual(code, 2, report)
                self.assertIn('session_lineage_mismatch' if bad == 'wrong-parent' else 'missing_descendant',
                              {x['code'] for x in report['issues']})
                self.assertIsNone(report['allocated_arm_usage'])

    def test_inherited_native_start_cannot_replace_canonical_parent_birth(self):
        for original in (True, False):
            with self.subTest(original=original):
                files = self.fork_files()
                files.pop('events')
                start = self.native_start_files()['root'][2]
                files['child'][2] = copy.deepcopy(start)
                if original:
                    files['root'].insert(1, row('event_msg', {'type': 'task_started', 'turn_id': 'turn'}))
                    files['root'].insert(2, start)
                code, report = self.run_fork(files)
                self.assertEqual(code, 0 if original else 2, report)
                self.assertEqual(report['unique_responses'], 2)
                if not original:
                    self.assertIn('missing_descendant_start', {x['code'] for x in report['issues']})
                    self.assertIsNone(report['allocated_arm_usage'])

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
