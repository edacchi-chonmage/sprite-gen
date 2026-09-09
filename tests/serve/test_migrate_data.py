import json
from pathlib import Path

import pytest
from PIL import Image

from sprite_gen.serve.chat_studio import Studio
from sprite_gen.serve.migrate_data import migrate


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def source_data(tmp_path):
    root = tmp_path / 'old-assets'
    folder = root / 'capability-lab/dragon_flight'
    folder.mkdir(parents=True)
    Image.new('RGB', (4, 4), 'red').save(folder / 'raw.png')
    (folder / 'pipeline/qa').mkdir(parents=True)
    Image.new('RGB', (4, 4), 'red').save(folder / 'pipeline/qa/flight.gif')
    write_json(root / 'capability-lab/results.json', {'experiments': [
        {'id': 'dragon_flight', 'title': 'ドラゴン', 'notes': '翼を調整', 'raw': 'dragon_flight/raw.png'}]})
    write_json(root / 'chat-studio' / ('a' * 32) / 'chat.json', {
        'id': 'a' * 32, 'reference_id': 'dragon_flight', 'messages': [
            {'role': 'user', 'text': 'URL /media/capability-lab/dragon_flight/raw.png は文章内なので維持'}],
        'versions': [{'image': '/media/chat-studio/old/raw.png',
                      'references': ['/media/capability-lab/dragon_flight/raw.png']}],
        'status': 'idle'})
    write_json(root / 'chat-studio' / ('a' * 32) / 'versions/v1/generation.json',
               {'refs': ['/old/absolute/path.png']})
    (root / 'secret.env').write_text('secret')
    (folder / '.env.local').write_text('secret')
    (folder / 'secret.env').write_text('secret')
    return root


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_migrate_preserves_history_sources_and_excludes_secrets(tmp_path):
    source = source_data(tmp_path)
    before = snapshot(source)
    destination = tmp_path / 'data'
    result = migrate(source, destination)
    assert result['materials'] == result['chats'] == 1
    assert snapshot(source) == before
    assert not list(destination.rglob('*.env'))
    assert not list(destination.rglob('.env*'))
    assert not (destination / 'capability-lab').exists()
    chat = json.loads((destination / 'chat-studio' / ('a' * 32) / 'chat.json').read_text())
    assert chat['reference_id'] == 'dragon_flight'
    assert chat['versions'][0]['references'] == ['/media/library/dragon_flight/raw.png']
    assert chat['versions'][0]['image'] == '/media/chat-studio/old/raw.png'
    assert ' /media/capability-lab/' in chat['messages'][0]['text']
    report = destination / 'chat-studio' / ('a' * 32) / 'versions/v1/generation.json'
    assert json.loads(report.read_text()) == {'refs': ['/old/absolute/path.png']}
    studio = Studio(destination)
    library = studio.library()
    assert library['dragon_flight']['thumbnail'] == '/media/library/dragon_flight/raw.png'
    assert library['dragon_flight']['animation'] == '/media/library/dragon_flight/pipeline/qa/flight.gif'
    assert studio.create('dragon_flight')['reference_id'] == 'dragon_flight'


def test_nonempty_destination_is_rejected_before_any_write(tmp_path):
    source = source_data(tmp_path)
    destination = tmp_path / 'data'
    migrate(source, destination)
    before = snapshot(destination)
    with pytest.raises(ValueError, match='空'):
        migrate(source, destination)
    assert snapshot(destination) == before


def test_failed_copy_cannot_be_silently_retried(tmp_path, monkeypatch):
    source = source_data(tmp_path)
    destination = tmp_path / 'data'
    from sprite_gen.serve import migrate_data
    original = migrate_data.shutil.copytree

    def fail(old, new, **kwargs):
        Path(new).mkdir(parents=True)
        (Path(new) / 'partial').write_text('partial')
        raise OSError('copy interrupted')

    monkeypatch.setattr(migrate_data.shutil, 'copytree', fail)
    with pytest.raises(OSError):
        migrate(source, destination)
    before = snapshot(destination)
    monkeypatch.setattr(migrate_data.shutil, 'copytree', original)
    with pytest.raises(ValueError, match='空'):
        migrate(source, destination)
    assert snapshot(destination) == before


def test_external_symlink_rejected_before_destination_created(tmp_path):
    source = source_data(tmp_path)
    external = tmp_path / 'private.png'
    external.write_bytes(b'private')
    (source / 'capability-lab/dragon_flight/leak.png').symlink_to(external)
    destination = tmp_path / 'data'
    with pytest.raises(ValueError, match='リンク'):
        migrate(source, destination)
    assert not destination.exists()


def test_library_has_no_legacy_fallback_and_rejects_outside_folder(tmp_path):
    source = source_data(tmp_path)
    studio = Studio(source)
    assert studio.library() == {}
    write_json(source / 'library/index.json', {'items': [
        {'id': 'bad', 'title': 'bad', 'folder': '../outside'}]})
    with pytest.raises(ValueError):
        studio.library()
