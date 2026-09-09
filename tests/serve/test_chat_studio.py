import json
from pathlib import Path
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from functools import partial

import pytest
from PIL import Image

from sprite_gen.serve.chat_studio import Studio, Handler, ThreadingHTTPServer, validate_plan, safe_file
from sprite_gen.curate.curation import load_curation, state_plan, source_frame_index


def test_chat_history_isolated_and_failure_retained(tmp_path):
    def fail(*args): raise RuntimeError('検証用の接続失敗')
    studio=Studio(tmp_path,planner=fail)
    a,b=studio.create(),studio.create()
    studio.change(a['id'],lambda c:c['messages'].append({'role':'user','text':'狼を描いて'}))
    studio.work(a['id'])
    assert studio.get(b['id'])['messages']==[]
    result=studio.get(a['id'])
    assert result['status']=='failed'
    assert '接続失敗' in result['messages'][-1]['text']
    assert not result['versions']


def test_restart_marks_running_failed_without_retry(tmp_path):
    studio=Studio(tmp_path)
    a=studio.create()
    studio.change(a['id'],lambda c:c.update(status='running'))
    restarted=Studio(tmp_path,recover=True)
    assert restarted.get(a['id'])['status']=='failed'


@pytest.mark.parametrize('reference',[{},[],42,None])
def test_bad_reference_rejected(tmp_path,reference):
    with pytest.raises(ValueError): Studio(tmp_path).create(reference)


def test_file_boundary(tmp_path):
    (tmp_path/'link').symlink_to(tmp_path.parent,target_is_directory=True)
    for name in ('../outside.png','.env.local','link/outside.png'):
        with pytest.raises(ValueError):safe_file(tmp_path,name)


def motion_fixture(tmp_path):
    source=tmp_path/'original';pipeline=source/'pipeline'
    (pipeline/'raw').mkdir(parents=True)
    req={'version':1,'kind':'sprite-gen-request','engine':'component-row',
         'character':{'id':'test','description':'fixture'},'cell':{'size':64,'safe_margin':6},
         'chroma_key':{'name':'green','hex':'#00FF00','rgb':[0,255,0]},
         'states':{'run':{'frames':2,'fps':8,'loop':True,'action':'test'}}}
    (pipeline/'sprite-request.json').write_text(json.dumps(req))
    im=Image.new('RGB',(160,64),'#00ff00')
    for x in (12,92): im.paste('brown',(x,12,x+24,52))
    im.paste('black',(100,22,104,26))
    im.save(pipeline/'raw/run.png');im.save(source/'raw.png')
    from sprite_gen.frames.extract import run
    assert run(run_dir=pipeline)==0
    return source


def test_timing_clones_export_and_next_context_preserve_holds(tmp_path):
    source=motion_fixture(tmp_path)
    original=(source/'pipeline/sprite-request.json').read_bytes()
    studio=Studio(tmp_path/'assets')
    chat=studio.create()
    folder=studio.root/chat['id']/'versions'/'first';folder.mkdir(parents=True)
    plan={'action':'timing','sequence':[0,0,0,1],'fps':8,'prompt':'最初の姿勢を保つ'}
    pipeline,kind=studio.edit_motion(plan,folder,source)
    curation=load_curation(pipeline);seq,_=state_plan(curation,kind,2)
    assert [source_frame_index(curation,kind,i,2) for i in seq]==[0,0,0,1]
    studio.render(pipeline,kind,folder)
    gif=Image.open(pipeline/'qa/run.gif')
    gif.seek(0)
    assert gif.info['duration']>=360  # Three holds at eight fps survive GIF coalescing.
    assert (source/'pipeline/sprite-request.json').read_bytes()==original
    studio.change(chat['id'],lambda c:c['versions'].append({'id':'first','image':studio.media(pipeline/'sprite-sheet-alpha.png'),'contact':studio.media(pipeline/'qa/run-contact.png')}))
    context,_=studio.context(studio.get(chat['id']),{},folder)
    assert json.loads(context)['current_motion']['playback']['run']==[0,0,0,1]


def test_bad_tween_pair_rejected_before_paid_call(tmp_path,monkeypatch):
    source=motion_fixture(tmp_path);studio=Studio(tmp_path/'assets');folder=studio.root/'copy';folder.mkdir()
    calls=[]
    monkeypatch.setattr('sprite_gen.effects.interpolate.interpolate_between',lambda *a,**k:calls.append(1))
    with pytest.raises(ValueError):studio.edit_motion({'action':'interpolate','between':[0,8]},folder,source)
    assert calls==[]


def test_http_write_origin_and_private_files(tmp_path):
    studio=Studio(tmp_path)
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,studio=studio))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    try:
        req=Request(base+'/api/chats',b'{}',headers={'Content-Type':'application/json','Origin':'https://foreign.invalid'})
        with pytest.raises(HTTPError) as e:urlopen(req)
        assert e.value.code==403
        (tmp_path/'secret.json').write_text('{"private":true}')
        with pytest.raises(HTTPError):urlopen(base+'/media/secret.json')
        req=Request(base+'/api/chats',b'{"reference_id":{}}',headers={'Content-Type':'application/json'})
        with pytest.raises(HTTPError) as e:urlopen(req)
        assert e.value.code==400
    finally:server.shutdown();server.server_close();thread.join()


def test_nonloop_wrap_rejected_before_generation(tmp_path,monkeypatch):
    source=motion_fixture(tmp_path)
    p=source/'pipeline/sprite-request.json';r=json.loads(p.read_text());r['states']['run']['loop']=False;p.write_text(json.dumps(r))
    studio=Studio(tmp_path/'assets');folder=studio.root/'copy';folder.mkdir()
    calls=[]
    monkeypatch.setattr('sprite_gen.effects.interpolate.interpolate_between',lambda *a,**k:calls.append(1))
    with pytest.raises(ValueError,match='隣接'):
        studio.edit_motion({'action':'interpolate','between':[1,0]},folder,source)
    assert calls==[]


def test_failed_processing_keeps_generated_image_visible(tmp_path):
    plan={'action':'generate','reference_id':'','analysis':'新しく描く','prompt':'wolf','frames':1,'fps':8,'cell':64,'palette':32,'kind':'idle','title':'狼'}
    studio=Studio(tmp_path,planner=lambda *a:plan)
    def generated_then_fail(plan,folder,source):
        Image.new('RGB',(64,64),'brown').save(folder/'raw.png')
        raise RuntimeError('加工に失敗')
    studio.create_pixels=generated_then_fail
    chat=studio.create();studio.work(chat['id']);result=studio.get(chat['id'])
    assert result['status']=='failed'
    assert result['versions'][0]['review_status']=='加工未完了'
    assert result['versions'][0]['image'].endswith('raw.png')


def test_overlapping_submission_rejected(tmp_path):
    studio=Studio(tmp_path);chat=studio.create()
    studio.change(chat['id'],lambda c:c.update(status='running'))
    with pytest.raises(ValueError,match='実行中'):studio.submit(chat['id'],'重複した依頼')
    assert studio.get(chat['id'])['messages']==[]
