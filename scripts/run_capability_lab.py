#!/usr/bin/env python3
"""Images 2.5 capability experiments, independent of Dotter's rig pipeline."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
from PIL import Image
from sprite_gen.gen import generate_image

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'assets/capability-lab'
CLI = ROOT / '.venv/bin/sprite-gen'
LOCK = threading.Lock()
MODEL = 'gpt-image-2.5-sunburst'
STYLE = 'Match the attached adopted sprite exactly: tiny head, long slim adult proportions, narrow dark violet suit, red tie, same face and hair, same pixel clusters and shading. The standing body is 46 logical pixels tall and the head excluding neck is only 5 logical pixels tall. Do not enlarge the head, widen the torso, shorten the legs, or add facial detail. No antialiasing, blur or painterly rendering. Change only the pose.'
SPECS = [
 dict(id='human_idle',title='人物・待機',category='人物64×64',kind='idle',frames=4,fps=4,loop=True,cell=64,action='Unarmed idle breathing cycle, subtle chest and shoulder motion with slight delayed hands. Feet remain planted. Four distinct poses inhale, hold, exhale, rest. Same right facing as reference, no weapon.'),
 dict(id='human_attack',title='人物・高速の抜き撃ち',category='人物64×64',kind='attack',frames=4,fps=20,loop=False,cell=64,action='A very fast unarmed idle to pistol shot, then recoil, then gun lowered. Frame 1: neutral empty hands. Frame 2: pistol fully extended and already firing, small hard-edged muzzle flash physically touching the barrel. Frame 3: recoil. Frame 4: recovery. No long windup. Keep pistol attached to the grip, accurate anatomy.'),
 dict(id='human_run',title='人物・走り再試行',category='人物64×64',kind='run',frames=8,fps=16,loop=True,cell=64,action='Natural rightward running in place. Exactly one full stride: right contact, compression, passing, flight, left contact, compression, passing, flight. Opposite arm/leg swings, fists, bent elbows. Same tiny head and long thin legs as reference. No gun. Legs account for about half standing height.'),
 dict(id='human_jump',title='人物・ジャンプ',category='人物64×64',kind='jump',frames=6,fps=10,loop=False,cell=64,action='Right-facing jump in place without a gun: crouch with planted feet, push off, rising with bent knees, apex with knees tucked, falling with feet extended, landing crouch. Natural torso and arm motion. Preserve vertical jump arc.'),
 dict(id='human_views',title='人物・4方向の描き分け',category='人物64×64',kind='turnaround',frames=4,fps=2,loop=False,cell=64,action='Four static unarmed standing views of the same man, in this order: front, right profile, back, left profile. Same head size, body proportions, outfit and palette in every view. These are four camera directions, not walking phases.'),
 dict(id='wolf_base',title='動物・狼の基準絵',category='動物32×32',cell=32,base=True,prompt='A single right-facing grey wolf standing on four legs, full body including ears and tail, no scenery. Genuine 32x32 logical pixel art, large uniform square pixel blocks, exactly 16 grey brown cream colors, readable dark outline, anatomically believable quadruped. Render enlarged with nearest-neighbor square pixels, no antialiasing, no gradients. Center one whole wolf with ample padding on perfectly flat pure green #00FF00. Not a sheet. No shadow, no text.'),
 dict(id='dragon_base',title='大型モンスター・ドラゴンの基準絵',category='モンスター128×128',cell=128,base=True,prompt='A single magnificent dark crimson western dragon hovering, facing right in side three-quarter view, full body including both wings, four limbs, tail and horns. Genuine detailed 128x128 logical pixel art with exactly 32 colors, crisp pixel clusters, dark outlines, carefully shaded burgundy scales and muted golden wing membrane, classic 16-bit battle monster aesthetic. Natural anatomy, two large wings half raised. Center with ample padding on perfectly flat pure green #00FF00. No landscape, no shadows, no labels, no blur, no antialiasing. Not a sprite sheet.'),
 dict(id='city',title='背景・スクランブル交差点から109',category='背景・32色',scene=True,prompt='A wide 16:10 pixel art background showing Shibuya scramble crossing from pedestrian eye height, looking toward the cylindrical SHIBUYA 109 building. Recognizable crossing stripes, dense commercial facades, 109 sign, restrained pedestrians, late afternoon light. Meticulous genuine pixel art with deliberate clusters and exactly 32 muted colors, no antialiasing, no photographic texture. Composition across the entire canvas, no frame or UI. Aim for a 1280x800 logical pixel canvas. One scene, not a sheet.'),
 dict(id='wolf_run',title='動物・狼の走り',category='動物32×32',kind='run',frames=6,fps=12,loop=True,cell=32,depends='wolf_base',action='One full rightward wolf gallop in place, six consecutive distinct phases. Four legs coordinate naturally: gathered hindlegs, rear push off, extended flight, front contact, compression, gathered flight. Preserve exactly the reference wolf, snout, ears, markings, colors and size. Tail follows with delay. No human limbs or extra legs.'),
 dict(id='dragon_flight',title='大型モンスター・羽ばたき',category='モンスター128×128',kind='flight',frames=6,fps=8,loop=True,cell=128,depends='dragon_base',action='One seamless wingbeat cycle while hovering in place, facing right. Six distinct wing phases: high upstroke, wings partly up, powerful downstroke, wings low, recovery, lifting. Both wings connect anatomically to shoulders, no duplicated wings; tail and feet lag gently. Preserve reference dragon scale, horns, face, colors and fine pixel detail.'),
 dict(id='city_ruins',title='背景・同じ構図の荒廃版',category='背景・32色',scene=True,depends='city',prompt='Edit the attached Shibuya pixel art scene into its abandoned ruined version. Preserve the exact camera angle, crossing stripe layout, road perspective, cylindrical 109 building position and other building silhouettes. Broken windows, faded signs, weeds through pavement, abandoned cars, scattered rubble, muted cloudy daylight. No people. Keep deliberate pixel clusters and a coherent 32-color palette. Do not change the composition or invent a different street. One full scene, no UI.'),
]

def update(s, **fields):
 with LOCK:
  path=LAB/'results.json'; data=json.loads(path.read_text())
  item=next(v for v in data['experiments'] if v['id']==s['id']);item.update(fields)
  temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2));temp.replace(path)

def command(args, log):
 with log.open('a') as f:
  result=subprocess.run([str(CLI),*map(str,args)],cwd=ROOT,stdout=f,stderr=f)
 if result.returncode:raise RuntimeError(f'{args[0]} が失敗。{log.relative_to(LAB)} を参照')

def process(s, folder, source):
 kind=s.get('kind','idle');frames=s.get('frames',1);cell=s['cell']
 request={'cell':{'width':cell,'height':cell,'safe_margin':max(3,cell//12)},'states':{kind:{'frames':frames,'fps':s.get('fps',4),'loop':s.get('loop',False),'action':s.get('action','Keep the accepted base pose.')}},'fit':{'pixel_unfake':True,'logical_height':cell,'palette_size':s.get('palette',16 if cell==32 else 32),'align_x':'foot-centroid','align_y':'bottom','ground_frames':False,'outline':False},'style':STYLE if s['id'].startswith('human') else 'Match the attached reference identity, anatomy, silhouette, colors and pixel density exactly. Only change the pose. Uniform crisp pixel grid, no antialiasing.'}
 config=folder/'request.json';config.write_text(json.dumps(request,indent=2))
 pipeline=folder/'pipeline';command(['prepare','--out-dir',pipeline,'--character-id',s['id'],'--base-image',source,'--request',config,'--chroma-key','#00FF00'],folder/'prepare.log')
 return pipeline,kind

def run(s):
 folder=LAB/s['id'];folder.mkdir(parents=True,exist_ok=True)
 if (folder/'raw.png').exists():
  print(s['id'],'既存の生成画像を保持してスキップ',flush=True)
  return
 try:
  update(s,status='生成中',notes='Images 2.5で生成している')
  source=None
  if s['id'].startswith('human'):source=ROOT/'assets/inputs/adopted-green-x8.png'
  elif s.get('depends'):
   parent=LAB/s['depends'];source=parent/'raw.png'
  refs=[]
  if source:
   shutil.copyfile(source,folder/'input.png');source=folder/'input.png';refs=[source]
   update(s,reference=f"{s['id']}/input.png")
  if s.get('kind'):
   pipeline,kind=process(s,folder,source)
   refs=[pipeline/'base-source.png',pipeline/'references/layout-guides'/f'{kind}.png']
   prompt=(pipeline/'prompts'/f'{kind}.txt').read_text()
  else:prompt=s['prompt']
  (folder/'prompt.txt').write_text(prompt)
  result=generate_image('openai',prompt,folder/'raw.png',refs=refs,model=MODEL)
  (folder/'generation.json').write_text(json.dumps(result.to_dict(),ensure_ascii=False,indent=2))
  update(s,status='加工中',raw=f"{s['id']}/raw.png",notes='生成画像を保存済み。加工して比較する')
  image=Image.open(folder/'raw.png'); metrics={'api_size':list(image.size),'model':MODEL,'usage':result.extra.get('usage'),'seconds':round(result.elapsed_seconds,1)}
  if s.get('scene'):
   image.convert('RGB').quantize(colors=32,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGB').save(folder/'processed.png')
   metrics['output_size']=list(image.size);metrics['colors']=len(Image.open(folder/'processed.png').getcolors(maxcolors=10000000))
   update(s,processed=f"{s['id']}/processed.png")
  else:
   if s.get('base'):pipeline,kind=process(s,folder,folder/'raw.png')
   shutil.copyfile(folder/'raw.png',pipeline/'raw'/f'{kind}.png')
   command(['extract','--run-dir',pipeline],folder/'extract.log');command(['preview','--run-dir',pipeline],folder/'preview.log');command(['compose-atlas','--run-dir',pipeline],folder/'compose.log')
   manifest=json.loads((pipeline/'frames/frames-manifest.json').read_text());metrics['extraction_ok']=manifest.get('ok');metrics['warnings']=manifest.get('warnings',[])
   update(s,contact=f"{s['id']}/pipeline/qa/{kind}-contact.png",animation=f"{s['id']}/pipeline/qa/{kind}.gif" if s.get('frames',1)>1 and s['id']!='human_views' else None)
   if s.get('base'):
    frame=Image.open(pipeline/'frames'/kind/'frame-0.png').convert('RGBA');scale=max(1,512//s['cell']);frame=frame.resize((frame.width*scale,frame.height*scale),Image.Resampling.NEAREST);bg=Image.new('RGBA',frame.size,'#00FF00');bg.alpha_composite(frame);bg.convert('RGB').save(folder/'reference.png');update(s,processed=f"{s['id']}/reference.png")
  update(s,status='目視評価待ち',metrics=metrics,notes='生成と加工が完了。絵と動きの品質はこれから判定する。')
 except BaseException as exc:
  update(s,status='失敗',notes=str(exc));print(s['id'],str(exc),flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['initial','dependent'],required=True);args=parser.parse_args();LAB.mkdir(parents=True,exist_ok=True)
 if not (LAB/'results.json').exists():(LAB/'results.json').write_text(json.dumps({'experiments':[{k:s[k] for k in ['id','title','category']}|{'status':'待機中','notes':'未実行'} for s in SPECS]},ensure_ascii=False,indent=2))
 chosen=[s for s in SPECS if bool(s.get('depends'))==(args.stage=='dependent')]
 with ThreadPoolExecutor(max_workers=6) as pool:
  for f in as_completed([pool.submit(run,s) for s in chosen]):f.result()
 print('実験処理終了',flush=True)
