#!/usr/bin/env python3
"""Compare processing resolutions/palettes without sending another paid request."""
import hashlib,json,shutil
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from run_capability_lab import LAB,process,command,update

variants=[
 {'id':'wolf_64','parent':'wolf_base','title':'同じ狼を64×64に加工','category':'解像度比較','cell':64,'palette':16},
 {'id':'wolf_128','parent':'wolf_base','title':'同じ狼を128×128に加工','category':'解像度比較','cell':128,'palette':16},
 {'id':'dragon_256','parent':'dragon_base','title':'同じドラゴンを256×256に加工','category':'解像度比較','cell':256,'palette':32},
 {'id':'human_run_16','parent':'human_run','title':'同じ走りを16色に減色','category':'色数比較','cell':64,'palette':16,'kind':'run','frames':8,'fps':16,'loop':True},
]
data=json.loads((LAB/'results.json').read_text())
for s in variants:
 if not any(e['id']==s['id']for e in data['experiments']):data['experiments'].append({k:s[k]for k in ['id','title','category']}|{'status':'加工待ち','notes':'生成画像は共通。API再生成なしで比較する。'})
(LAB/'results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
def run(s):
 folder=LAB/s['id'];folder.mkdir(exist_ok=True)
 try:
  update(s,status='加工中');src=LAB/s['parent']/'raw.png';shutil.copyfile(src,folder/'raw.png')
  pipeline,kind=process(s,folder,src);shutil.copyfile(src,pipeline/'raw'/f'{kind}.png')
  command(['extract','--run-dir',pipeline],folder/'extract.log');command(['preview','--run-dir',pipeline],folder/'preview.log');command(['compose-atlas','--run-dir',pipeline],folder/'compose.log')
  manifest=json.loads((pipeline/'frames/frames-manifest.json').read_text());fields={'raw':f"{s['id']}/raw.png",'contact':f"{s['id']}/pipeline/qa/{kind}-contact.png"}
  if s.get('frames',1)>1:fields['animation']=f"{s['id']}/pipeline/qa/{kind}.gif"
  else:
   im=Image.open(pipeline/'frames'/kind/'frame-0.png');im.resize((512,512),Image.Resampling.NEAREST).save(folder/'processed.png');fields['processed']=f"{s['id']}/processed.png"
  update(s,status='目視評価待ち',notes='API再生成なし。同じ画像を異なるサイズ・色数で加工した。',metrics={'reuse_generation_from':s['parent'],'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'cell':s['cell'],'palette':s['palette'],'extraction_ok':manifest.get('ok'),'warnings':manifest.get('warnings',[])},**fields)
 except BaseException as e:update(s,status='失敗',notes=str(e))
with ThreadPoolExecutor(max_workers=4)as pool:list(pool.map(run,variants))
