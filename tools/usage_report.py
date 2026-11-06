#!/usr/bin/env python3
"""Read pinned native JSONL metadata and emit a privacy-safe usage report.

No network, native process, configuration, tracing, or credentials are used.
"""
import argparse
from collections import defaultdict
from datetime import datetime
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

RUNTIME = '0.167.0'
SOURCE_COMMIT = '086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a'
KEYS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
        'output_tokens', 'reasoning_output_tokens', 'total_tokens')
CAMEL_KEYS = ('inputTokens', 'cachedInputTokens', 'cacheWriteInputTokens',
              'outputTokens', 'reasoningOutputTokens', 'totalTokens')
CATEGORIES = {'common-upgrade', 'fixture', 'evaluation', 'probe',
              'shared-b-preflight', 'arm', 'activation', 'indexing', 'administration'}
IGNORED_NATIVE = {'response_item', 'world_state', 'turn_context',
                  'inter_agent_communication_metadata'}
RETRY_ENVELOPE = re.compile(
    rb'^\{"timestamp":"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)"'
    rb'(,"ordinal":(0|[1-9][0-9]*),"type":"(token_usage_record|event_msg)"[^\n]*)\n$')
LIMITS = [
    'Native persistence is a version-pinned internal format, not a stable public API.',
    'Null upstream usage, skipped writes, hidden WebSocket retries and background or speculative requests can be unobservable.',
    'Reconciliation proves consistency of observed records, not universal provider billing completeness.',
    'The same separate recovery probe must verify two live compactions and exact-thread restart before measured arms start.',
]


class Invalid(Exception):
    """Public errors carry fixed codes, never input values or exception text."""


def identity(value):
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise Invalid('missing_response_identity')
    return value


def hashed(value):
    return hashlib.sha256(value.encode()).hexdigest()


def timestamp(value):
    if not isinstance(value, str) or not value.endswith('Z'):
        raise Invalid('invalid_timestamp')
    try:
        return datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError:
        raise Invalid('invalid_timestamp') from None


def fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or set(value) - set(required) - set(optional):
        raise Invalid('unsupported_manifest_schema')


def label(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,47}', value):
        raise Invalid('invalid_public_label')
    return value


def zero():
    return dict.fromkeys(KEYS, 0)


def add(left, right):
    return {k: left[k] + right[k] for k in KEYS}


def subtract(left, right):
    return {k: left[k] - right[k] for k in KEYS}


def usage(value):
    if value is None:
        raise Invalid('missing_usage')
    if not isinstance(value, dict) or set(value) != set(KEYS):
        raise Invalid('unsupported_usage_schema')
    if any(type(value[k]) is not int or value[k] < 0 for k in KEYS):
        raise Invalid('invalid_usage_counter')
    if value['total_tokens'] != value['input_tokens'] + value['output_tokens']:
        raise Invalid('invalid_category_totals')
    if (value['cached_input_tokens'] + value['cache_write_input_tokens'] > value['input_tokens']
            or value['reasoning_output_tokens'] > value['output_tokens']):
        raise Invalid('invalid_category_subset')
    return dict(value)


def record_payload(payload):
    required = {'thread_id', 'session_id', 'turn_id', 'root_turn_id', 'response_id',
                'usage', 'turn_token_usage', 'thread_token_usage'}
    if not isinstance(payload, dict) or set(payload) != required:
        raise Invalid('unsupported_native_schema')
    for key in ('thread_id', 'session_id', 'turn_id', 'root_turn_id', 'response_id'):
        identity(payload[key])
    for key in ('usage', 'turn_token_usage', 'thread_token_usage'):
        usage(payload[key])


def session_metadata(payload):
    if not isinstance(payload, dict):
        raise Invalid('unsupported_native_schema')
    identity(payload.get('id'))
    return {k: payload.get(k) for k in ('id', 'session_id', 'parent_thread_id', 'cli_version')}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def validate_manifest(manifest):
    fields(manifest, ('schema_version', 'runtime_version', 'window', 'runs'))
    if type(manifest['schema_version']) is not int or manifest['schema_version'] != 1 or manifest['runtime_version'] != RUNTIME:
        raise Invalid('unsupported_manifest_schema')
    window = manifest['window']
    fields(window, ('start', 'end', 'end_policy'))
    if window['end_policy'] != 'assessment-report-evidence-freeze':
        raise Invalid('invalid_window_policy')
    start = timestamp(window['start'])
    end = timestamp(window['end']) if window['end'] is not None else None
    if end is not None and end <= start:
        raise Invalid('invalid_phase_boundary')
    if not isinstance(manifest['runs'], list) or not manifest['runs']:
        raise Invalid('missing_run_inventory')
    ids = set()
    all_threads = set()
    for run in manifest['runs']:
        fields(run, ('id', 'root_thread_id', 'session_id', 'closed',
                     'expected_threads', 'sources', 'phases'), ('window_closure',))
        if label(run['id']) in ids:
            raise Invalid('duplicate_run')
        ids.add(run['id'])
        identity(run['root_thread_id']); identity(run['session_id'])
        if type(run['closed']) is not bool:
            raise Invalid('unsupported_manifest_schema')
        if 'window_closure' in run:
            closure = run['window_closure']
            fields(closure, ('kind', 'source_id', 'turn_id', 'response_id', 'response_ordinal',
                             'source_bytes', 'last_ordinal', 'cutoff'))
            if (closure['kind'] != 'root-response-boundary' or run['closed'] or end is None
                    or timestamp(closure['cutoff']) != end):
                raise Invalid('invalid_window_closure')
            label(closure['source_id'])
            identity(closure['turn_id']); identity(closure['response_id'])
            if (any(type(closure[k]) is not int or closure[k] < 0 for k in
                    ('response_ordinal', 'source_bytes', 'last_ordinal'))
                    or closure['source_bytes'] == 0
                    or closure['last_ordinal'] < closure['response_ordinal']):
                raise Invalid('invalid_window_closure')
        if not isinstance(run['expected_threads'], list) or not run['expected_threads']:
            raise Invalid('missing_run_inventory')
        parents = {}
        for thread in run['expected_threads']:
            fields(thread, ('thread_id', 'parent_thread_id'))
            tid = identity(thread['thread_id'])
            if tid in parents or tid in all_threads:
                raise Invalid('duplicate_thread_inventory')
            parents[tid] = thread['parent_thread_id']
            if thread['parent_thread_id'] is not None:
                identity(thread['parent_thread_id'])
        all_threads.update(parents)
        root = run['root_thread_id']
        if root not in parents or parents[root] is not None:
            raise Invalid('invalid_lineage_inventory')
        for tid in parents:
            visited = set()
            current = tid
            while current != root:
                if current in visited or current not in parents:
                    raise Invalid('invalid_lineage_inventory')
                visited.add(current)
                current = parents[current]
        if not isinstance(run['sources'], list) or not run['sources']:
            raise Invalid('missing_sources')
        source_ids = set()
        for source in run['sources']:
            fields(source, ('id', 'kind', 'path', 'sha256'))
            if label(source['id']) in source_ids:
                raise Invalid('duplicate_source')
            source_ids.add(source['id'])
            if source['kind'] not in ('native', 'notifications'):
                raise Invalid('unsupported_source_kind')
            if not isinstance(source['path'], str) or not isinstance(source['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', source['sha256']):
                raise Invalid('invalid_source_descriptor')
        if not isinstance(run['phases'], list) or not run['phases']:
            raise Invalid('missing_phase_boundaries')
        intervals = []
        phase_ids = set()
        for phase in run['phases']:
            fields(phase, ('id', 'category', 'start', 'end'), ('workload', 'arm'))
            if label(phase['id']) in phase_ids or phase['category'] not in CATEGORIES:
                raise Invalid('invalid_phase_policy')
            phase_ids.add(phase['id'])
            arm_phase = phase['category'] in ('arm', 'activation', 'indexing')
            if arm_phase:
                if phase.get('workload') not in ('web', 'canvas') or phase.get('arm') not in ('A', 'B'):
                    raise Invalid('invalid_phase_policy')
                if phase['category'] != 'arm' and phase['arm'] != 'B':
                    raise Invalid('invalid_phase_policy')
            elif 'workload' in phase or 'arm' in phase:
                raise Invalid('invalid_phase_policy')
            begin = timestamp(phase['start'])
            finish = timestamp(phase['end']) if phase['end'] is not None else None
            if finish is not None and finish <= begin:
                raise Invalid('invalid_phase_boundary')
            intervals.append((begin, finish))
        intervals.sort(key=lambda pair: pair[0])
        if any(a[1] is None or a[1] > b[0] for a, b in zip(intervals, intervals[1:])):
            raise Invalid('overlapping_phases')
    return start, end


class Reporter:
    def __init__(self, manifest_directory):
        self.manifest_directory = manifest_directory
        self.issues = set()
        self.records = {}
        self.duplicates = 0
        self.observed = zero()
        self.outside = zero()
        self.phase_totals = defaultdict(zero)
        self.arm_totals = {f'{w}-{a}': zero() for w in ('web', 'canvas') for a in ('A', 'B')}
        self.shared = zero()
        self.runs = []

    def issue(self, code, source='manifest'):
        self.issues.add((code, source))

    def accept_record(self, payload, when, source, embedded=False):
        try:
            record_payload(payload)
            rid = payload['response_id']
            if rid in self.records:
                previous = self.records[rid]
                if previous['payload'] != payload or (not embedded and not previous['embedded'] and previous['timestamp'] != when):
                    self.issue('conflicting_duplicate', source)
                else:
                    self.duplicates += 1
                    if previous['embedded'] and not embedded:
                        previous.update(timestamp=when, source=source, embedded=False)
                return
            self.records[rid] = {'payload': payload, 'timestamp': when, 'source': source, 'embedded': embedded}
        except Invalid as error:
            self.issue(str(error), source)

    def verified_retry(self, partial, raw, event, state, data):
        """Only the pinned writer's same-ordinal, immediate exact-prefix retry."""
        left = RETRY_ENVELOPE.fullmatch(partial)
        right = RETRY_ENVELOPE.fullmatch(raw)
        if not left or not right or state['owner'] is None or state['owner']['cli_version'] != RUNTIME:
            return False
        ordinal = int(left[3])
        if (left[3] != right[3] or state['ordinal'] != ordinal - 1
                or not right[2].startswith(left[2]) or len(left[2]) >= len(right[2])
                or (state['boundary'] is not None and ordinal < state['boundary'])):
            return False
        payload = event.get('payload')
        if not isinstance(payload, dict) or payload.get('thread_id') != state['owner']['id']:
            return False
        try:
            identity(payload.get('turn_id'))
            if left[4] == b'token_usage_record':
                record_payload(payload)
            elif payload.get('type') != 'item_completed' or not isinstance(payload.get('item'), dict):
                return False
        except Invalid:
            return False
        earlier = timestamp(left[1].decode('ascii'))
        later = timestamp(right[1].decode('ascii'))
        if earlier >= later:
            return False
        def allocation(when):
            phases = tuple(p['id'] for p in data['phases'] if when >= timestamp(p['start'])
                           and (p['end'] is None or when < timestamp(p['end'])))
            start, end = data['window']
            return phases, when >= start and (end is None or when < end)
        before = allocation(earlier)
        return len(before[0]) == 1 and before == allocation(later)

    def native_row(self, event, raw, data, sid, state):
        kind = event.get('type')
        payload = event.get('payload')
        if state['recovery_next'] is not None:
            expected = state['recovery_next']
            state['recovery_next'] = None
            if type(event.get('ordinal')) is not int or event['ordinal'] != expected:
                raise Invalid('invalid_retry_ordinal')
        if state['owner'] is None:
            if kind != 'session_meta':
                raise Invalid('missing_session_metadata')
            owner = session_metadata(payload)
            state['owner'] = owner
            if 'subagent_history_start_ordinal' in payload:
                boundary = payload['subagent_history_start_ordinal']
                parent = owner['parent_thread_id']
                if (type(boundary) is not int or boundary < 2 or event.get('ordinal') != 0
                        or not isinstance(parent, str) or not parent or parent == owner['id']
                        or payload.get('forked_from_id') != parent or owner['cli_version'] != RUNTIME):
                    raise Invalid('invalid_fork_history_boundary')
                state['boundary'] = boundary
        elif state['boundary'] is not None:
            ordinal = event.get('ordinal')
            if type(ordinal) is not int or ordinal != state['ordinal'] + 1:
                raise Invalid('invalid_fork_history_boundary')
            if ordinal < state['boundary']:
                state['inherited_rows'] += 1
                if kind == 'session_meta':
                    candidate = session_metadata(payload)
                    if ordinal != 1 or candidate['id'] != state['owner']['parent_thread_id']:
                        raise Invalid('invalid_inherited_metadata')
                    data['inherited_metadata'].append((candidate, sid))
                    state['inherited_meta_seen'] = True
                elif kind == 'token_usage_record':
                    record_payload(payload)
                    data['inherited_records'].append((payload, state['owner']['parent_thread_id'], sid))
                elif kind == 'event_msg':
                    self.native_event(payload, timestamp(event.get('timestamp')), data, sid, inherited=True)
                elif kind not in IGNORED_NATIVE:
                    raise Invalid('unsupported_inherited_accounting')
                state['ordinal'] = ordinal
                return
            state['boundary_reached'] = True
        ordinal = event.get('ordinal')
        state['ordinal'] = ordinal if type(ordinal) is int else None
        if data['closure'] is not None and isinstance(payload, dict):
            owning = kind in ('token_usage_record', 'turn_context') or (
                kind == 'event_msg' and payload.get('type') in ('task_started', 'turn_started', 'task_complete'))
            if owning and payload.get('turn_id') is not None:
                turn = identity(payload['turn_id'])
                data['owning_turns'][sid].add(turn)
                state['last_owning_turn'] = turn
        if kind in IGNORED_NATIVE:
            return
        when = timestamp(event.get('timestamp'))
        if kind == 'session_meta':
            candidate = session_metadata(payload)
            tid = candidate['id']
            if tid in data['metadata'] and data['metadata'][tid] != candidate:
                self.issue('conflicting_session_metadata', sid)
            data['metadata'][tid] = candidate
            data['source_threads'].add(tid)
        elif kind == 'token_usage_record':
            record_payload(payload)
            if any(payload[key] != state['owner'][meta_key] for key, meta_key in
                   (('thread_id', 'id'), ('session_id', 'session_id'))):
                self.issue('record_ownership', sid)
            self.accept_record(payload, when, sid)
        elif kind == 'compacted':
            if not isinstance(payload, dict):
                raise Invalid('unsupported_native_schema')
            latest = payload.get('latest_token_usage_record')
            if latest is not None:
                self.accept_record(latest, when, sid, embedded=True)
            data['checkpoints'].append({
                'source': sid,
                'compaction_response_id': payload.get('compaction_response_id'),
                'window_id': payload.get('window_id'),
                'replacement_history_present': isinstance(payload.get('replacement_history'), list) and bool(payload['replacement_history']),
                'binding_sha256': hashed(json.dumps(payload, sort_keys=True, separators=(',', ':'))),
                'checkpoint_sha256': hashlib.sha256(raw).hexdigest()})
        elif kind == 'event_msg':
            self.native_event(payload, when, data, sid)
        else:
            raise Invalid('unsupported_native_schema')

    def read_source(self, source, data):
        sid = source['id']
        digest = hashlib.sha256()
        state = dict(owner=None, ordinal=None, boundary=None, inherited_rows=0,
                     inherited_meta_seen=False, boundary_reached=False, recovery_next=None)
        pending = None
        recoveries = []
        prefix = data['closure'] is not None and data['closure']['source_id'] == sid
        state.update(byte_count=0, responses={}, ordinary_positions=[], latest_timestamp=None,
                     last_owning_turn=None)
        try:
            path = Path(source['path'])
            if not path.is_absolute():
                path = self.manifest_directory / path
            with path.open('rb') as stream:
                for line, raw in enumerate(stream, 1):
                    digest.update(raw)
                    state['byte_count'] += len(raw)
                    if prefix and not raw.endswith(b'\n'):
                        self.issue('invalid_window_snapshot', sid)
                    try:
                        event = json.loads(raw, object_pairs_hook=unique_object)
                        if not isinstance(event, dict):
                            raise Invalid('unsupported_native_schema')
                        if source['kind'] == 'notifications':
                            self.notification(event, data, sid)
                            continue
                        recovered = False
                        if pending is not None:
                            partial, partial_line = pending
                            pending = None
                            if self.verified_retry(partial, raw, event, state, data):
                                recovered = True
                                recoveries.append({'partial_line': partial_line, 'retry_line': line,
                                    'ordinal': event['ordinal'], 'type': event['type'],
                                    'partial_sha256': hashlib.sha256(partial).hexdigest(),
                                    'retry_sha256': hashlib.sha256(raw).hexdigest()})
                            else:
                                self.issue('malformed_source', sid)
                        if prefix:
                            expected = 0 if state['ordinal'] is None else state['ordinal'] + 1
                            if type(event.get('ordinal')) is not int or event['ordinal'] != expected:
                                self.issue('invalid_window_snapshot', sid)
                            when = timestamp(event.get('timestamp'))
                            latest = state['latest_timestamp']
                            state['latest_timestamp'] = max(latest, when) if latest else when
                        self.native_row(event, raw, data, sid, state)
                        if prefix and event.get('type') == 'token_usage_record':
                            state['responses'].setdefault(event['payload']['response_id'],
                                (event['payload'], event['ordinal'], timestamp(event['timestamp'])))
                        if (prefix and event.get('type') == 'event_msg'
                                and event['payload'].get('type') == 'token_count'
                                and event['payload'].get('info') is not None):
                            state['ordinary_positions'].append((event['ordinal'], timestamp(event['timestamp'])))
                        if recovered:
                            state['recovery_next'] = event['ordinal'] + 1
                    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError):
                        if source['kind'] == 'native' and pending is None:
                            pending = raw, line
                        else:
                            pending = None
                            self.issue('malformed_source', sid)
                    except Invalid as error:
                        self.issue(str(error), sid)
        except OSError:
            self.issue('unreadable_source', sid)
            return
        if digest.hexdigest() != source['sha256']:
            self.issue('source_digest_mismatch', sid)
        if pending is not None:
            self.issue('malformed_source', sid)
        if source['kind'] == 'native' and not data['source_threads']:
            self.issue('missing_session_metadata', sid)
        summary = {'id': sid, 'kind': source['kind'], 'sha256': digest.hexdigest()}
        if recoveries:
            summary['partial_write_recoveries'] = recoveries
        if state['boundary'] is not None:
            if not state['boundary_reached'] or not state['inherited_meta_seen']:
                self.issue('invalid_fork_history_boundary', sid)
            summary['inherited_history'] = {'start_ordinal': state['boundary'],
                'excluded_rows': state['inherited_rows'],
                'parent_thread_id_hash': hashed(state['owner']['parent_thread_id'])}
        data['sources'].append(summary)
        if prefix:
            data['source_states'][sid] = state

    def native_event(self, payload, when, data, sid, inherited=False):
        if not isinstance(payload, dict):
            raise Invalid('unsupported_native_schema')
        kind = payload.get('type', '')
        if not isinstance(kind, str):
            raise Invalid('unsupported_native_schema')
        if inherited:
            if kind in ('raw_response_completed', 'response_completed'):
                raise Invalid('unsupported_inherited_accounting')
            if kind not in ('token_count', 'task_complete', 'context_compacted', 'error', 'warning',
                            'turn_aborted', 'stream_error', 'task_started', 'turn_started',
                            'thread_settings_applied', 'item_started', 'item_completed'):
                raise Invalid('unsupported_native_schema')
            if kind == 'token_count' and payload.get('info') is not None:
                info = payload['info']
                if not isinstance(info, dict):
                    raise Invalid('unsupported_native_schema')
                usage(info.get('total_token_usage'))
            return
        if kind == 'token_count':
            info = payload.get('info')
            if info is not None:
                if not isinstance(info, dict):
                    raise Invalid('unsupported_native_schema')
                data['ordinary'].append((when, usage(info.get('total_token_usage')), sid))
        elif kind == 'task_complete':
            data['completed'].add(payload.get('turn_id'))
            if payload.get('error') is not None:
                self.issue('known_omission_indicator', sid)
        elif kind in ('raw_response_completed', 'response_completed'):
            data['completions'].append((payload, sid, False))
        elif kind == 'context_compacted':
            data['compaction_markers'].add(sid)
        elif kind in ('error', 'warning', 'turn_aborted', 'stream_error') or any(word in kind for word in ('background', 'speculative', 'usage_record')):
            self.issue('known_omission_indicator', sid)
        elif kind not in ('task_started', 'turn_started', 'thread_settings_applied',
                          'item_started', 'item_completed'):
            raise Invalid('unsupported_native_schema')

    def notification(self, event, data, sid):
        if event.get('error') is not None:
            self.issue('known_omission_indicator', sid)
        method = event.get('method', '')
        params = event.get('params', {})
        if not isinstance(method, str) or not isinstance(params, dict):
            raise Invalid('unsupported_notification_schema')
        if method in ('item/started', 'item/completed'):
            item = params.get('item', {})
            if not isinstance(item, dict):
                raise Invalid('unsupported_notification_schema')
            if item.get('type') == 'subAgentActivity' and item.get('kind') == 'started':
                data['started'].add((identity(params.get('threadId')), identity(item.get('agentThreadId'))))
        elif method == 'thread/tokenUsage/updated':
            token_usage = params.get('tokenUsage')
            if not isinstance(token_usage, dict) or not isinstance(token_usage.get('total'), dict):
                raise Invalid('unsupported_notification_schema')
            total = token_usage['total']
            if set(total) != set(CAMEL_KEYS):
                raise Invalid('unsupported_notification_schema')
            counters = usage({key: total[name] for key, name in zip(KEYS, CAMEL_KEYS)})
            data['notification_totals'].append((identity(params.get('threadId')), counters))
        elif method == 'turn/completed':
            turn = params.get('turn')
            if not isinstance(turn, dict):
                raise Invalid('unsupported_notification_schema')
            if turn.get('status') in ('failed', 'interrupted') or turn.get('error') is not None:
                self.issue('known_omission_indicator', sid)
        elif method in ('error', 'turn/aborted') or 'background' in method or 'speculative' in method:
            self.issue('known_omission_indicator', sid)
        elif method in ('thread/rawResponse/completed', 'response/completed'):
            data['completions'].append((params, sid, True))

    def window_boundary(self, run, start, end, data, source_threads, records):
        """Certify a closed window, without claiming the active root turn ended."""
        closure = data['closure']
        if closure is None:
            return None
        sid = closure['source_id']
        state = data['source_states'].get(sid)
        anchor = self.records.get(closure['response_id'])
        if state is None or anchor is None or anchor['embedded']:
            self.issue('invalid_window_anchor', run['id'])
            return None
        responses = list(state['responses'].values())
        phases = [p for p in run['phases'] if anchor['timestamp'] >= timestamp(p['start'])
                  and p['end'] is not None and anchor['timestamp'] < timestamp(p['end'])]
        root_ids = {r['payload']['response_id'] for r in records
                    if r['payload']['thread_id'] == run['root_thread_id']}
        source_ids = {p['response_id'] for p, _, _ in responses}
        if (source_threads.get(sid) != run['root_thread_id']
                or not responses or responses[-1][0] != anchor['payload']
                or responses[-1][1] != closure['response_ordinal']
                or responses[-1][2] != anchor['timestamp']
                or anchor['payload']['thread_id'] != run['root_thread_id']
                or anchor['payload']['session_id'] != run['session_id']
                or state['last_owning_turn'] != closure['turn_id']
                or anchor['payload']['turn_id'] != closure['turn_id']
                or anchor['payload']['root_turn_id'] != closure['turn_id']
                or root_ids != source_ids or not start <= anchor['timestamp'] < end
                or len(phases) != 1 or phases[0]['category'] == 'administration'
                or any(p['end'] is None for p in run['phases'])
                or state['latest_timestamp'] is None or state['latest_timestamp'] >= end
                or not any(ordinal > closure['response_ordinal'] and when >= anchor['timestamp']
                           for ordinal, when in state['ordinary_positions'])):
            self.issue('invalid_window_anchor', run['id'])
            return None
        if (state['byte_count'] != closure['source_bytes']
                or state['ordinal'] != closure['last_ordinal']):
            self.issue('invalid_window_snapshot', sid)
            return None
        source = next(s for s in data['sources'] if s['id'] == sid)
        return {'kind': closure['kind'], 'accounting_window': 'closed',
                'root_turn_completion': 'unclaimed',
                'response_id_hash': hashed(closure['response_id']),
                'turn_id_hash': hashed(closure['turn_id']), 'source_id': sid,
                'source_sha256': source['sha256'], 'source_bytes': state['byte_count'],
                'response_ordinal': closure['response_ordinal'], 'last_ordinal': state['ordinal'],
                'cutoff': closure['cutoff']}

    def run(self, run, start, end):
        data = {'metadata': {}, 'ordinary': [], 'completed': set(), 'completions': [],
                'started': set(), 'checkpoints': [], 'sources': [], 'notification_totals': [],
                'compaction_markers': set(), 'inherited_metadata': [], 'inherited_records': [],
                'phases': run['phases'], 'window': (start, end),
                'closure': run.get('window_closure'), 'source_states': {}, 'owning_turns': defaultdict(set)}
        ordinary_by_thread = {}
        source_threads = {}
        completed_by_thread = defaultdict(set)
        owning_by_thread = defaultdict(set)
        before = set(self.records)
        for source in run['sources']:
            # Ordinary counters belong to the source's session metadata, including
            # replayed snapshots after restart; keep each source's final snapshot.
            local = dict(data, ordinary=[], completed=set(), source_threads=set())
            self.read_source(source, local)
            if source['kind'] == 'native':
                if len(local['source_threads']) != 1:
                    self.issue('ambiguous_source_metadata', source['id'])
                    continue
                tid = next(iter(local['source_threads']))
                source_threads[source['id']] = tid
                completed_by_thread[tid].update(local['completed'])
                owning_by_thread[tid].update(data['owning_turns'][source['id']])
                if local['ordinary']:
                    latest = max(local['ordinary'], key=lambda x: x[0])
                    previous = ordinary_by_thread.get(tid)
                    if previous and latest[0] == previous[0] and latest[1] != previous[1]:
                        self.issue('conflicting_ordinary_snapshot', source['id'])
                    if previous is None or latest[0] > previous[0]:
                        ordinary_by_thread[tid] = latest
        parents = {t['thread_id']: t['parent_thread_id'] for t in run['expected_threads']}
        for inherited, sid in data['inherited_metadata']:
            tid = inherited['id']
            if tid not in source_threads.values() or data['metadata'].get(tid) != inherited:
                self.issue('invalid_inherited_metadata', sid)
        for inherited, parent, sid in data['inherited_records']:
            original = self.records.get(inherited['response_id'])
            if (inherited['thread_id'] != parent or original is None or original['embedded']
                    or original['payload'] != inherited or source_threads.get(original['source']) != parent):
                self.issue('inherited_usage_mismatch', sid)
        for tid, parent in parents.items():
            meta = data['metadata'].get(tid)
            if meta is None:
                self.issue('missing_descendant' if parent else 'missing_session_metadata', run['id'])
            elif meta != {'id': tid, 'session_id': run['session_id'], 'parent_thread_id': parent, 'cli_version': RUNTIME}:
                self.issue('session_lineage_mismatch', run['id'])
        if set(data['metadata']) - parents.keys():
            self.issue('unknown_thread', run['id'])
        for parent, child in data['started']:
            if child not in parents:
                self.issue('missing_descendant', run['id'])
            elif parents[child] != parent:
                self.issue('session_lineage_mismatch', run['id'])
        for child, parent in parents.items():
            if parent is not None and (parent, child) not in data['started']:
                self.issue('missing_descendant_start', run['id'])
        run_record_ids = self.records.keys() - before
        records = [self.records[rid] for rid in run_record_ids]
        boundary = self.window_boundary(run, start, end, data, source_threads, records)
        root_turns = {r['payload']['turn_id'] for r in records if r['payload']['thread_id'] == run['root_thread_id']}
        grouped = defaultdict(list)
        for entry in records:
            rec = entry['payload']
            if entry['embedded']:
                self.issue('missing_original_response_timestamp', run['id'])
            if rec['thread_id'] not in parents:
                self.issue('unknown_thread', run['id'])
            if rec['session_id'] != run['session_id']:
                self.issue('session_lineage_mismatch', run['id'])
            if rec['root_turn_id'] not in root_turns or (rec['thread_id'] == run['root_thread_id'] and rec['root_turn_id'] != rec['turn_id']):
                self.issue('root_turn_lineage', run['id'])
            grouped[rec['thread_id']].append(entry)
            when = entry['timestamp']
            in_window = when >= start and (end is None or when < end)
            self.observed = add(self.observed, rec['usage']) if in_window else self.observed
            self.outside = add(self.outside, rec['usage']) if not in_window else self.outside
            matches = [p for p in run['phases'] if when >= timestamp(p['start'])
                       and (p['end'] is None or when < timestamp(p['end']))]
            if len(matches) != 1:
                if in_window:
                    self.issue('unassigned_response_phase', run['id'])
                continue
            phase = matches[0]
            if (phase['category'] == 'administration') == in_window:
                self.issue('administration_window_policy', run['id'])
            if in_window:
                key = (run['id'], phase['id'], phase['category'])
                self.phase_totals[key] = add(self.phase_totals[key], rec['usage'])
                if phase['category'] in ('arm', 'activation', 'indexing'):
                    arm = phase['workload'] + '-' + phase['arm']
                    self.arm_totals[arm] = add(self.arm_totals[arm], rec['usage'])
                elif phase['category'] == 'shared-b-preflight':
                    self.shared = add(self.shared, rec['usage'])
        threads = []
        ordinary_total = zero()
        ledger_total = zero()
        compaction_total = zero()
        compaction_ids = set()
        checkpoints = []
        checkpoint_bindings = {}
        window_bindings = {}
        checkpoint_threads = set()
        for checkpoint in data['checkpoints']:
            rid = checkpoint.get('compaction_response_id')
            window = checkpoint.get('window_id')
            if not isinstance(rid, str) or rid not in run_record_ids or not isinstance(window, str) or not window or not checkpoint['replacement_history_present']:
                self.issue('incomplete_compaction_checkpoint', run['id'])
                continue
            tid = source_threads.get(checkpoint['source'])
            rec = self.records[rid]['payload']
            if tid not in parents or rec['thread_id'] != tid or rec['session_id'] != run['session_id']:
                self.issue('compaction_checkpoint_ownership', checkpoint['source'])
                continue
            binding = (tid, window, checkpoint['binding_sha256'])
            if ((rid in checkpoint_bindings and checkpoint_bindings[rid] != binding)
                    or (window in window_bindings and window_bindings[window] != rid)):
                self.issue('conflicting_compaction_checkpoint', checkpoint['source'])
                continue
            checkpoint_threads.add(tid)
            if rid in checkpoint_bindings:
                continue
            checkpoint_bindings[rid] = binding
            window_bindings[window] = rid
            compaction_total = add(compaction_total, rec['usage'])
            compaction_ids.add(rid)
            checkpoints.append({'response_id_hash': hashed(rid), 'window_id_hash': hashed(window),
                                'checkpoint_sha256': checkpoint['checkpoint_sha256']})
        for sid in data['compaction_markers']:
            if source_threads.get(sid) not in checkpoint_threads:
                self.issue('missing_compaction_checkpoint', sid)
        for tid in parents:
            current = zero()
            turns = defaultdict(zero)
            ordinary_prefix = zero()
            prefixes = {tuple(zero().values())}
            entries = sorted(grouped[tid], key=lambda e: (e['payload']['thread_token_usage']['total_tokens'], e['timestamp']))
            if not entries:
                self.issue('missing_usage', run['id'])
            for entry in entries:
                rec = entry['payload']; current = add(current, rec['usage'])
                turns[rec['turn_id']] = add(turns[rec['turn_id']], rec['usage'])
                if rec['response_id'] not in compaction_ids:
                    ordinary_prefix = add(ordinary_prefix, rec['usage'])
                prefixes.add(tuple(current.values()))
                prefixes.add(tuple(ordinary_prefix.values()))
                if current != rec['thread_token_usage'] or turns[rec['turn_id']] != rec['turn_token_usage']:
                    self.issue('ledger_reconciliation', run['id'])
            snapshot = ordinary_by_thread.get(tid)
            if snapshot is None:
                self.issue('missing_ordinary_cumulative', run['id'])
            else:
                ordinary = snapshot[1]
                ordinary_total = add(ordinary_total, ordinary)
                delta = subtract(current, ordinary)
                thread_compaction = zero()
                for rid in compaction_ids:
                    if self.records[rid]['payload']['thread_id'] == tid:
                        thread_compaction = add(thread_compaction, self.records[rid]['payload']['usage'])
                if delta != zero() and delta != thread_compaction:
                    self.issue('ordinary_reconciliation', run['id'])
            if (run['closed'] or data['closure'] is not None) and any(
                    turn not in completed_by_thread[tid]
                    and not (boundary is not None and tid == run['root_thread_id']
                             and turn == data['closure']['turn_id']) for turn in turns.keys() | owning_by_thread[tid]):
                self.issue('missing_turn_completion', run['id'])
            for notification_tid, counters in data['notification_totals']:
                if notification_tid == tid and tuple(counters.values()) not in prefixes:
                    self.issue('notification_reconciliation', run['id'])
            ledger_total = add(ledger_total, current)
            threads.append({'thread_id_hash': hashed(tid), 'parent_thread_id_hash': hashed(parents[tid]) if parents[tid] else None,
                            'response_count': len(entries), 'ledger_usage': current})
        if any(tid not in parents for tid, _ in data['notification_totals']):
            self.issue('unknown_thread', run['id'])
        for completion, sid, notification in data['completions']:
            try:
                if notification:
                    required = {'threadId', 'turnId', 'responseId', 'usage'}
                    optional = {'usageMetadata'}
                    owners = {'thread_id': completion.get('threadId'), 'turn_id': completion.get('turnId')}
                else:
                    required = {'type', 'response_id', 'usage'}
                    optional = {'thread_id', 'turn_id', 'session_id', 'root_turn_id', 'usage_metadata'}
                    owners = {key: completion[key] for key in optional - {'usage_metadata'} if key in completion}
                    owners['thread_id'] = source_threads.get(sid)
                    if 'thread_id' in completion and completion['thread_id'] != owners['thread_id']:
                        raise Invalid('completion_ownership')
                if not required <= completion.keys() or set(completion) - required - optional:
                    raise Invalid('unsupported_completion_schema')
                rid = completion.get('responseId' if notification else 'response_id')
                counters = completion['usage']
                if not isinstance(rid, str) or counters is None or rid not in run_record_ids:
                    raise Invalid('unaccounted_completion')
                if notification:
                    if not isinstance(counters, dict) or set(counters) != set(CAMEL_KEYS):
                        raise Invalid('unsupported_usage_schema')
                    counters = {key: counters[name] for key, name in zip(KEYS, CAMEL_KEYS)}
                rec = self.records[rid]['payload']
                if any(rec[key] != owner for key, owner in owners.items()):
                    raise Invalid('completion_ownership')
                if usage(counters) != rec['usage']:
                    raise Invalid('completion_reconciliation')
            except Invalid as error:
                self.issue(str(error), sid)
        if not run['closed'] and boundary is None:
            self.issue('open_run', run['id'])
        self.runs.append({'id': run['id'], 'sources': data['sources'], 'threads': threads,
                          'ledger_usage': ledger_total, 'ordinary_usage': ordinary_total,
                          'ordinary_compaction_delta': subtract(ledger_total, ordinary_total),
                          'checkpoints': checkpoints})
        if data['closure'] is not None:
            self.runs[-1]['window_closure'] = boundary or {
                'kind': data['closure']['kind'], 'accounting_window': 'unverified',
                'root_turn_completion': 'unclaimed',
                'evidence_status': 'incomplete'}

    def report(self):
        allocated = {arm: {k: str(Fraction(v) + (Fraction(self.shared[k], 2) if arm.endswith('-B') else 0))
                           for k, v in totals.items()} for arm, totals in self.arm_totals.items()}
        return {'schema_version': 1, 'runtime_version': RUNTIME, 'native_source_commit': SOURCE_COMMIT,
                'evidence_status': 'incomplete' if self.issues else 'reconciled',
                'billing_completeness': 'not-proven',
                'measurement_readiness': 'pending-live-compaction-restart-validation',
                'issues': [{'code': code, 'source': source} for code, source in sorted(self.issues)],
                'unique_responses': len(self.records), 'duplicate_records': self.duplicates,
                'window_observed_usage': self.observed, 'outside_window_usage': self.outside,
                'raw_arm_usage': self.arm_totals, 'shared_b_preflight_usage': self.shared,
                'allocated_arm_usage': None if self.issues else allocated,
                'phases': [{'run': r, 'id': p, 'category': c, 'usage': v}
                           for (r, p, c), v in sorted(self.phase_totals.items())],
                'responses': [{'response_id_hash': hashed(p['response_id']),
                               'thread_id_hash': hashed(p['thread_id']),
                               'turn_id_hash': hashed(p['turn_id']),
                               'root_turn_id_hash': hashed(p['root_turn_id']),
                               'session_id_hash': hashed(p['session_id']),
                               'usage': p['usage']}
                              for p in (entry['payload'] for _, entry in sorted(self.records.items()))],
                'runs': self.runs, 'limitations': LIMITS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    args = parser.parse_args()
    reporter = Reporter(Path(args.manifest).absolute().parent)
    try:
        with Path(args.manifest).open() as stream:
            manifest = json.load(stream)
        start, end = validate_manifest(manifest)
        if end is None:
            reporter.issue('open_measurement_window')
        phases = [p for run in manifest['runs'] for p in run['phases']]
        for workload in ('web', 'canvas'):
            categories = {p['category'] for p in phases if p.get('workload') == workload and p.get('arm') == 'B'}
            if 'arm' in categories and (not {'activation', 'indexing'} <= categories
                                       or not any(p['category'] == 'shared-b-preflight' for p in phases)):
                reporter.issue('missing_b_first_use_phases')
        for run in manifest['runs']:
            reporter.run(run, start, end)
    except Invalid as error:
        reporter.issue(str(error))
    except (OSError, ValueError, TypeError, KeyError):
        reporter.issue('unreadable_or_malformed_manifest')
    report = reporter.report()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2 if reporter.issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
