"""Run a visual/research planning turn through Orca and subscription Claude Sonnet."""
from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable


_ROOT = Path(__file__).resolve().parents[2]


def _orca(executable: str, *args: str) -> dict:
    result = subprocess.run([executable, *args, '--json'], cwd=_ROOT,
                            capture_output=True, text=True, timeout=30)
    try:
        payload = json.loads(result.stdout)
    except ValueError as exc:
        raise RuntimeError('Orcaから正常な応答を取得できなかった') from exc
    if result.returncode or not payload.get('ok'):
        code = payload.get('error', {}).get('code', 'unknown')
        raise RuntimeError(f'Orcaへの接続に失敗した（{code}）')
    return payload['result']


def _message(prompt: str, images: list[Path]) -> dict:
    content = [{'type': 'text', 'text': prompt}]
    for path in images:
        mime = mimetypes.guess_type(path.name)[0]
        if mime not in {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}:
            raise ValueError('参照画像はPNG・JPEG・GIF・WebPを指定してね')
        content.append({'type': 'image', 'source': {
            'type': 'base64', 'media_type': mime,
            'data': base64.b64encode(path.read_bytes()).decode('ascii'),
        }})
    return {'type': 'user', 'message': {'role': 'user', 'content': content}}


def _event(event: dict, on_event: Callable[[str], None]) -> None:
    if event.get('type') == 'system' and event.get('subtype') == 'init':
        on_event(f"使用モデル：{event.get('model', 'Sonnet（実名未取得）')}")
    if event.get('type') == 'assistant':
        for item in event.get('message', {}).get('content', []):
            if item.get('type') == 'tool_use':
                if item.get('name') == 'WebSearch':
                    on_event('参考情報を検索している：' + str(item.get('input', {}).get('query', ''))[:200])
                elif item.get('name') == 'WebFetch':
                    on_event('参考ページの内容を確認している：' + str(item.get('input', {}).get('url', ''))[:200])


def _structured(result: dict | None) -> dict:
    if not result:
        raise RuntimeError('Sonnetから最終回答を取得できなかった')
    if result.get('is_error') or result.get('subtype') not in (None, 'success'):
        raise RuntimeError('Sonnetが計画の作成に失敗した')
    value = result.get('structured_output')
    if value is None:
        try:
            value = json.loads(result.get('result', ''))
        except ValueError as exc:
            raise RuntimeError('Sonnetの回答が指定したJSON形式ではなかった') from exc
    if not isinstance(value, dict):
        raise RuntimeError('Sonnetの回答がJSONオブジェクトではなかった')
    return value


def run_sonnet(work_dir: Path, prompt: str, images: list[Path], schema: dict,
               on_event: Callable[[str], None], *, timeout: float = 300,
               orca_command: str = 'orca') -> dict:
    """The caller owns public artifacts; this transport stays outside served paths."""
    if timeout <= 0:
        raise ValueError('制限時間は正の値を指定してね')
    worktree = _orca(orca_command, 'worktree', 'current')['worktree']['id']
    message = _message(prompt, images)
    with tempfile.TemporaryDirectory(prefix='sprite-sonnet-') as temporary:
        directory = Path(temporary)
        config = directory / 'request.json'
        config.write_text(json.dumps({'message': message, 'schema': schema, 'timeout': timeout}))
        config.chmod(0o600)
        terminal = None
        try:
            created = _orca(orca_command, 'terminal', 'create', '--worktree', 'id:' + worktree,
                            '--title', 'スプライトの調査・設計', '--command',
                            shlex.join([sys.executable, str(Path(__file__).with_name('sonnet_worker.py')), str(directory)]))
            terminal = created['terminal']['handle']
            on_event('OrcaからClaude Sonnetを起動した。参照画像と依頼を確認している')
            offset = 0
            buffered = ''
            final = None
            deadline = time.monotonic() + timeout + 10
            while True:
                stream = directory / 'events.jsonl'
                if stream.exists():
                    with stream.open() as reader:
                        reader.seek(offset)
                        buffered += reader.read()
                        offset = reader.tell()
                    lines = buffered.split('\n')
                    buffered = lines.pop()
                    for line in lines:
                        if not line.strip():
                            continue
                        event = json.loads(line)
                        _event(event, on_event)
                        if event.get('type') == 'result':
                            final = event
                done = directory / 'done.json'
                if done.exists():
                    outcome = json.loads(done.read_text())
                    if not outcome.get('ok'):
                        raise RuntimeError(outcome.get('error', 'Sonnetの実行に失敗した'))
                    # done is published after stdout closes; consume its last bytes once.
                    if stream.exists() and stream.stat().st_size > offset:
                        continue
                    return _structured(final)
                if time.monotonic() >= deadline:
                    raise TimeoutError('Sonnetの応答が制限時間を超えた')
                time.sleep(0.2)
        finally:
            if terminal:
                (directory / 'cancel').touch()
                deadline = time.monotonic() + 5
                while not (directory / 'done.json').exists() and time.monotonic() < deadline:
                    time.sleep(0.1)
                try:
                    _orca(orca_command, 'terminal', 'close', '--terminal', terminal)
                except Exception:
                    on_event('Orcaの作業ターミナルを閉じられなかった。実行の取消しは送信済み')
