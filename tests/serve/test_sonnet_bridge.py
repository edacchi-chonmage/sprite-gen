import base64
import json
from pathlib import Path
import shlex
import sys

import pytest

from sprite_gen.serve import sonnet_bridge as bridge
from sprite_gen.serve import sonnet_worker as worker


def test_image_input_contains_actual_bytes(tmp_path):
    image = tmp_path / 'reference.png'
    image.write_bytes(b'original pixels')
    message = bridge._message('この絵を参照', [image])
    source = message['message']['content'][1]['source']
    assert base64.b64decode(source['data']) == image.read_bytes()
    assert source['media_type'] == 'image/png'


def test_orca_transport_cleanup_and_structured_output(monkeypatch, tmp_path):
    calls = []
    directories = []
    events = []

    def orca(executable, *args):
        calls.append(args)
        if args[:2] == ('worktree', 'current'):
            return {'worktree': {'id': 'repo::/checkout'}}
        if args[:2] == ('terminal', 'create'):
            directory = Path(shlex.split(args[-1])[-1])
            directories.append(directory)
            assert directory.stat().st_mode & 0o777 == 0o700
            assert (directory / 'request.json').stat().st_mode & 0o777 == 0o600
            assert directory.parent != tmp_path
            records = [
                {'type': 'system', 'subtype': 'init', 'model': 'claude-sonnet-test'},
                {'type': 'assistant', 'message': {'content': [
                    {'type': 'tool_use', 'name': 'WebSearch', 'input': {'query': '走る姿勢'}}]}},
                {'type': 'result', 'subtype': 'success', 'structured_output': {'plan': '走る'}, 'result': 'ignored'},
            ]
            (directory / 'events.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in records))
            (directory / 'done.json').write_text('{"ok":true}')
            return {'terminal': {'handle': 'owned-terminal'}}
        assert args == ('terminal', 'close', '--terminal', 'owned-terminal')
        return {}

    monkeypatch.setattr(bridge, '_orca', orca)
    result = bridge.run_sonnet(tmp_path, '依頼', [], {}, events.append)
    assert result == {'plan': '走る'}
    assert any('claude-sonnet-test' in e for e in events)
    assert any('走る姿勢' in e for e in events)
    assert calls[-1][1] == 'close'
    assert not directories[0].exists()


@pytest.mark.parametrize('result', [None, {'is_error': True}, {'subtype': 'error_max_turns'}, {'result': 'not json'}, {'structured_output': []}])
def test_invalid_or_failed_model_results_are_not_success(result):
    with pytest.raises(RuntimeError):
        bridge._structured(result)


def test_worker_timeout_kills_and_reaps_child(monkeypatch, tmp_path):
    request = {'schema': {}, 'message': {}, 'timeout': 0.01}
    (tmp_path / 'request.json').write_text(json.dumps(request))
    monkeypatch.setattr(worker, 'command', lambda _: [sys.executable, '-c', 'import sys,time; sys.stdin.read(); time.sleep(30)'])
    original_popen = worker.subprocess.Popen
    children = []

    def capture(*args, **kwargs):
        child = original_popen(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(worker.subprocess, 'Popen', capture)
    # Avoid changing pytest's process-wide signal handlers or umask.
    monkeypatch.setattr(worker.signal, 'signal', lambda *args: None)
    monkeypatch.setattr(worker.os, 'umask', lambda *args: None)
    worker.run(tmp_path)
    done = json.loads((tmp_path / 'done.json').read_text())
    assert done['ok'] is False
    assert '制限時間' in done['error']
    assert children[0].poll() is not None


def test_worker_limits_tools_and_preserves_subscription_auth_mode():
    command = worker.command({})
    assert command[command.index('--model') + 1] == 'sonnet'
    assert command[command.index('--tools') + 1] == 'WebSearch,WebFetch'
    assert command[command.index('--allowedTools') + 1] == 'WebSearch,WebFetch'
    assert '--safe-mode' in command
    assert '--bare' not in command
    assert '--dangerously-skip-permissions' not in command
