"""実験素材と制作履歴を、独立したアプリのデータへコピーする。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
from urllib.parse import quote, unquote


def _ignore(directory, names):
    return [name for name in names if name.startswith('.') or name.endswith('.env')]


def _check_tree(root: Path) -> None:
    if root.is_symlink():
        raise ValueError('移行元にシンボリックリンクは指定できない')
    for path in root.rglob('*'):
        if any(part.startswith('.') for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            raise ValueError('移行対象にシンボリックリンクが含まれている')


def _rewrite_urls(value, mappings):
    if isinstance(value, dict):
        return {key: _rewrite_urls(item, mappings) for key, item in value.items()}
    if isinstance(value, list):
        return [_rewrite_urls(item, mappings) for item in value]
    prefix = '/media/capability-lab/'
    if isinstance(value, str) and value.startswith(prefix):
        relative = unquote(value[len(prefix):])
        if Path(relative).is_absolute() or '..' in Path(relative).parts:
            return value
        for old, new in mappings:
            if relative.startswith(old + '/'):
                return '/media/library/' + quote(new + relative[len(old):], safe='/')
    return value


def migrate(source: Path, destination: Path) -> dict:
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_dir():
        raise ValueError('移行元のデータディレクトリが存在しない')
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError('移行先は存在しないディレクトリか空のディレクトリを指定してね')
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError('移行元と移行先を入れ子にはできない')

    lab = source / 'capability-lab'
    manifest = lab / 'results.json'
    entries = json.loads(manifest.read_text()).get('experiments', []) if manifest.exists() else []
    items, copies, mappings, ids = [], [], [], set()
    for item in entries:
        if not item.get('raw'):
            continue
        identity = item['id']
        if not isinstance(identity, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', identity) or identity in ids:
            raise ValueError('素材IDが不正、または重複している')
        ids.add(identity)
        relative = Path(item['raw'])
        folder = lab / relative.parent
        if relative.is_absolute() or '..' in relative.parts or any(p.startswith('.') for p in relative.parts):
            raise ValueError('素材の参照先が不正')
        if not folder.resolve().is_relative_to(lab.resolve()) or not (folder / 'raw.png').is_file():
            raise ValueError('素材の元画像が存在しない、または参照範囲外')
        _check_tree(folder)
        items.append({'id': identity, 'title': item['title'], 'notes': item.get('notes', ''), 'folder': 'library/' + identity})
        copies.append((folder, destination / 'library' / identity))
        mappings.append((relative.parent.as_posix(), identity))
    history = source / 'chat-studio'
    if history.exists():
        _check_tree(history)

    # 完了印を最後に作る。途中で失敗した移行先を次の実行で上書きしない。
    destination.mkdir(parents=True, exist_ok=True)
    for old, new in copies:
        shutil.copytree(old, new, ignore=_ignore)
    chats = 0
    if history.exists():
        target = destination / 'chat-studio'
        shutil.copytree(history, target, ignore=_ignore)
        for path in target.glob('*/chat.json'):
            value = _rewrite_urls(json.loads(path.read_text()), mappings)
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
            chats += 1
    index = destination / 'library/index.json'
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text(json.dumps({'items': items}, ensure_ascii=False, indent=2) + '\n')
    return {'materials': len(items), 'chats': chats, 'destination': str(destination)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(migrate(args.source, args.destination), ensure_ascii=False))


if __name__ == '__main__':
    main()
