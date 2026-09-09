"""Private file transport for a Claude process owned by an Orca terminal."""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def command(schema: dict) -> list[str]:
    return [
        'claude', '--print', '--verbose', '--output-format', 'stream-json',
        '--input-format', 'stream-json', '--model', 'sonnet', '--effort', 'high',
        '--json-schema', json.dumps(schema), '--no-session-persistence',
        '--safe-mode', '--setting-sources', '', '--strict-mcp-config',
        '--mcp-config', '{"mcpServers":{}}', '--disable-slash-commands',
        '--tools', 'WebSearch,WebFetch', '--allowedTools', 'WebSearch,WebFetch',
        '--permission-mode', 'dontAsk',
    ]


def run(directory: Path) -> None:
    os.umask(0o077)
    config = json.loads((directory / 'request.json').read_text())
    child = None
    outcome = {'ok': False, 'error': 'Sonnetの実行が中断された'}

    def interrupted(_signum, _frame):
        raise InterruptedError('Sonnetの実行が中断された')

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, interrupted)
    try:
        # Keep the existing subscription login, but do not inherit API credentials.
        env = {k: v for k, v in os.environ.items()
               if not k.endswith(('API_KEY', 'AUTH_TOKEN')) and k != 'CLAUDECODE'}
        with (directory / 'events.jsonl').open('w') as output, (directory / 'stderr.txt').open('w') as error:
            child = subprocess.Popen(command(config['schema']), cwd=directory,
                                     env=env, stdin=subprocess.PIPE,
                                     stdout=output, stderr=error, start_new_session=True)
            child.stdin.write((json.dumps(config['message']) + '\n').encode())
            child.stdin.close()
            deadline = time.monotonic() + config['timeout']
            while child.poll() is None:
                if (directory / 'cancel').exists():
                    raise InterruptedError('Sonnetの実行が取り消された')
                if time.monotonic() >= deadline:
                    raise TimeoutError('Sonnetの応答が制限時間を超えた')
                time.sleep(0.1)
            outcome = {'ok': child.returncode == 0, 'exit_code': child.returncode}
            if child.returncode:
                outcome['error'] = f'Sonnetが終了コード {child.returncode} で失敗した'
    except Exception as exc:
        outcome = {'ok': False, 'error': str(exc)}
    finally:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        temporary = directory / 'done.tmp'
        temporary.write_text(json.dumps(outcome))
        temporary.replace(directory / 'done.json')


if __name__ == '__main__':
    run(Path(sys.argv[1]))
