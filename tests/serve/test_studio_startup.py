import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

from sprite_gen.serve import sonnet_bridge, chat_studio


def test_orca_uses_workspace_not_installed_package_path(tmp_path,monkeypatch):
    monkeypatch.setenv('SPRITE_STUDIO_WORKSPACE',str(tmp_path))
    calls=[]
    def run(args,**kwargs):
        calls.append(kwargs['cwd'])
        return SimpleNamespace(returncode=0,stdout=json.dumps({'ok':True,'result':{}}))
    monkeypatch.setattr(subprocess,'run',run)
    sonnet_bridge._orca('orca','worktree','current')
    assert calls==[tmp_path.resolve()]


def test_startup_loads_local_env_without_overriding_environment(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('SPRITE_STUDIO_WORKSPACE','before-startup')
    (tmp_path/'.env.local').write_text('STUDIO_STARTUP_TEST_FROM_FILE=value\nSTUDIO_STARTUP_TEST_EXISTING=from-file\n')
    monkeypatch.setenv('STUDIO_STARTUP_TEST_EXISTING','from-environment')
    monkeypatch.delenv('STUDIO_STARTUP_TEST_FROM_FILE',raising=False)
    monkeypatch.setattr('sys.argv',['sprite-studio'])
    captured=[]
    class Server:
        def __init__(self,address,handler):captured.append((address,handler.keywords['studio']))
        def serve_forever(self):raise KeyboardInterrupt
        def server_close(self):pass
    monkeypatch.setattr(chat_studio,'ThreadingHTTPServer',Server)
    chat_studio.main()
    import os
    assert os.environ['STUDIO_STARTUP_TEST_FROM_FILE']=='value'
    assert os.environ['STUDIO_STARTUP_TEST_EXISTING']=='from-environment'
    assert os.environ['SPRITE_STUDIO_WORKSPACE']==str(tmp_path)
    assert captured[0][1].assets==tmp_path/'data'
    monkeypatch.delenv('STUDIO_STARTUP_TEST_FROM_FILE')
