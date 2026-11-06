#!/usr/bin/env python3
"""Isolated code-only Graphify activation and source-freshness guard (stdlib)."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

VERSION = '0.9.103'
TOOLS = {'query_graph', 'get_node', 'get_neighbors', 'get_community', 'god_nodes', 'graph_stats', 'shortest_path'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args]).decode().strip()


def snapshot(root):
    root = Path(root).resolve()
    if Path(git(root, 'rev-parse', '--show-toplevel')).resolve() != root:
        raise ValueError('Expected an exact Git worktree root')
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-co', '--exclude-standard', '-z'])
    files = {}
    for name in sorted(set(names.decode().split('\0')) - {''}):
        path = root / name
        if path.is_symlink():
            raise ValueError('Source symlinks are outside the trial coverage: ' + name)
        if path.is_dir():
            raise ValueError('Submodules are outside the trial coverage: ' + name)
        files[name] = digest(path) if path.exists() else None
    branch = git(root, 'rev-parse', '--abbrev-ref', 'HEAD')
    return {'root': str(root), 'head': git(root, 'rev-parse', 'HEAD'),
            'branch': branch if branch != 'HEAD' else None,
            'git_dir': git(root, 'rev-parse', '--absolute-git-dir'), 'files': files}


def check(root, record):
    if record['source'] != snapshot(root):
        raise ValueError('STALE_GRAPH: source identity changed; rebuild required')
    if 'graph' in record and digest(record['graph']) != record['graph_sha256']:
        raise ValueError('STALE_GRAPH: graph bytes changed; rebuild required')
    return record


def state_dir(root, state):
    root = Path(root).resolve()
    state = Path(state).resolve()
    if state == root or root in state.parents:
        raise ValueError('Graph state must be outside the source worktree')
    return state / hashlib.sha256(str(root).encode()).hexdigest()


def environment(state):
    # Explicit allowlist: no API keys, provider URLs, auth, proxy or inherited
    # Graphify settings enter extraction/server processes. HOME is not copied.
    env = {'PATH': os.defpath, 'LANG': 'C.UTF-8', 'GRAPHIFY_BACKEND': 'none',
           'GRAPHIFY_QUERY_LOG_DISABLE': '1', 'GRAPHIFY_NO_TIPS': '1',
           'GRAPHIFY_NO_CTA': '1', 'GRAPHIFY_MAX_CONTEXTS': '1',
           'GRAPHIFY_MAX_WORKERS': '2', 'GRAPHIFY_ALLOW_LOCAL_PROVIDERS': '0'}
    for key, subdir in [('TMPDIR', 'tmp'), ('XDG_CACHE_HOME', 'cache'), ('XDG_CONFIG_HOME', 'config')]:
        path = Path(state) / subdir
        path.mkdir(parents=True, exist_ok=True)
        env[key] = str(path)
    return env


def tool_identity(prefix):
    interpreter = Path(prefix).resolve() / 'bin/python'
    program = '''import hashlib,importlib.metadata as m,json,pathlib
import graphify
root=pathlib.Path(graphify.__file__).parent
files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
print(json.dumps({'version':m.version('graphifyy'),'source_sha256':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),'dependencies':sorted((d.metadata['Name'].lower(),d.version) for d in m.distributions())},sort_keys=True))'''
    result = json.loads(subprocess.check_output([str(interpreter), '-c', program], text=True))
    if result['version'] != VERSION:
        raise ValueError('Unexpected Graphify version; use the approved lock')
    return result


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    os.replace(temporary, path)


def build(root, state, prefix):
    root = Path(root).resolve()
    owned = state_dir(root, state)
    owned.mkdir(parents=True, exist_ok=True)
    source = snapshot(root)
    identity = tool_identity(prefix)
    with tempfile.TemporaryDirectory(prefix='extract-', dir=owned) as staging:
        command = [str(Path(prefix).resolve() / 'bin/graphify'), 'extract', str(root),
                   '--out', staging, '--code-only', '--no-dedup', '--max-workers', '2']
        result = subprocess.run(command, cwd=root, env=environment(owned), text=True, capture_output=True)
        (owned / 'build.log').write_text(result.stdout + result.stderr)
        result.check_returncode()
        fresh = Path(staging) / 'graphify-out/graph.json'
        if snapshot(root) != source:
            raise ValueError('Source changed during extraction; rebuild required')
        data = json.loads(fresh.read_text())
        if not data.get('nodes'):
            raise ValueError('Graph has no nodes')
        graph = owned / 'graph.json'
        # Only the newly generated graph crosses the generation boundary;
        # semantic layers, caches, memories and sidecars are never retained.
        os.replace(fresh, graph)
        record = {'schema': 1, 'source': source, 'tool': identity,
                  'policy': {'code_only': True, 'dedup': False, 'backend': 'none', 'workers': 2},
                  'graph': str(graph), 'graph_sha256': digest(graph)}
        atomic_json(owned / 'current.json', record)
    return record


def load(root, state):
    path = state_dir(root, state) / 'current.json'
    return check(root, json.loads(path.read_text()))


def request_error(message, root, record):
    if message.get('method') not in ('tools/call', 'resources/read'):
        return None
    try:
        check(root, record)
        if message['method'] == 'resources/read':
            raise ValueError('Resources are excluded from this code-only trial; use source query tools')
        params = message.get('params', {})
        if params.get('name') not in TOOLS:
            raise ValueError('Tool is outside the local source-query scope')
        selected = params.get('arguments', {}).get('project_path')
        if selected and Path(selected).resolve() != Path(root).resolve():
            raise ValueError('WRONG_WORKTREE: use the server configured for that exact worktree')
    except (ValueError, OSError) as exc:
        return {'jsonrpc': '2.0', 'id': message.get('id'), 'result': {
            'isError': True, 'content': [{'type': 'text', 'text': str(exc)}]}}
    return None


def serve(root, state, prefix):
    root = Path(root).resolve()
    record = load(root, state)
    if tool_identity(prefix) != record['tool']:
        raise ValueError('Tool contents changed; reprovision or rebuild required')
    env = environment(state_dir(root, state))
    env['GRAPHIFY_OUT'] = str(Path(record['graph']).parent)
    child = subprocess.Popen([str(Path(prefix).resolve() / 'bin/graphify-mcp'), record['graph'], '--transport', 'stdio'],
                             cwd=root, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    lock = threading.Lock()

    def emit(value):
        with lock:
            sys.stdout.write(json.dumps(value) + '\n')
            sys.stdout.flush()

    def responses():
        for line in child.stdout:
            message = json.loads(line)
            result = message.get('result', {})
            if 'tools' in result:
                result['tools'] = [tool for tool in result['tools'] if tool['name'] in TOOLS]
            if 'resources' in result:
                result['resources'] = []
            emit(message)

    reader = threading.Thread(target=responses, daemon=True)
    reader.start()
    try:
        for line in sys.stdin:
            message = json.loads(line)
            # Read the current atomic build record for each request. Upstream
            # reloads changed graph bytes; this independent check proves source
            # freshness, including edits not represented by built_at_commit.
            try:
                record = load(root, state)
                error = request_error(message, root, record)
            except (ValueError, OSError) as exc:
                error = {'jsonrpc': '2.0', 'id': message.get('id'), 'result': {
                    'isError': True, 'content': [{'type': 'text', 'text': str(exc)}]}}
            if error and 'id' in message:
                emit(error)
            else:
                child.stdin.write(line)
                child.stdin.flush()
    finally:
        child.stdin.close()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.terminate()
            child.wait(timeout=5)
        reader.join(timeout=2)
    if child.returncode:
        raise RuntimeError('Graphify server exited with status ' + str(child.returncode))


def configuration(root, state, prefix):
    load(root, state)
    return {'command': sys.executable, 'args': [str(Path(__file__).resolve()), 'serve', '--root', str(Path(root).resolve()),
            '--state', str(Path(state).resolve()), '--prefix', str(Path(prefix).resolve())],
            'cwd': str(Path(root).resolve()), 'startup_timeout_sec': 60, 'tool_timeout_sec': 60}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'status', 'config', 'serve'])
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--prefix', required=True, type=Path, help='Locked Graphify venv; never auto-installs')
    args = parser.parse_args()
    try:
        if args.action == 'serve':
            serve(args.root, args.state, args.prefix)
            return
        value = build(args.root, args.state, args.prefix) if args.action == 'build' else (
            configuration(args.root, args.state, args.prefix) if args.action == 'config' else load(args.root, args.state))
        print(json.dumps(value, sort_keys=True))
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == '__main__':
    main()
