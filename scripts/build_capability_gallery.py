#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""results.json を定期取得する実験一覧ページを作成する。"""

import argparse
from pathlib import Path


HTML = r'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>スプライト制作・実験一覧</title>
<style>
:root{color-scheme:light;font-family:system-ui,-apple-system,sans-serif;color:#202b36;background:#f4f5f7}*{box-sizing:border-box}body{margin:0}header,main{max-width:1280px;margin:auto;padding:24px}h1{font-size:24px;margin:0 0 12px}p{line-height:1.7}header p{margin:5px 0;color:#596674}#connection{font-size:13px;min-height:22px}#summary{font-size:14px}#experiments{display:grid;gap:22px}.card{background:white;border:1px solid #dce1e6;border-radius:12px;padding:20px;min-width:0}.heading{display:flex;gap:12px;align-items:center;justify-content:space-between}.heading h2{font-size:19px;margin:6px 0}.category{font-size:12px;color:#596674}.status{border-radius:6px;background:#eef1f4;padding:6px 9px;font-size:13px;white-space:nowrap}.running{background:#fff0cf;color:#694800}.running:before{content:"";display:inline-block;width:8px;height:8px;background:currentColor;border-radius:50%;margin-right:7px;animation:pulse 1s infinite}.failed{background:#ffe5e5;color:#992727}.completed{background:#e0f2e9;color:#205941}@keyframes pulse{50%{opacity:.25}}.media{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:18px}figure{margin:0;min-width:0}figcaption{font-size:13px;margin-bottom:8px;color:#596674}.picture{min-height:180px;height:240px;display:flex;align-items:center;justify-content:center;border:1px solid #dce1e6;border-radius:6px;overflow:hidden;background-color:#e3e6eb;background-image:linear-gradient(45deg,#f1f2f5 25%,transparent 25%),linear-gradient(-45deg,#f1f2f5 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#f1f2f5 75%),linear-gradient(-45deg,transparent 75%,#f1f2f5 75%);background-size:20px 20px;background-position:0 0,0 10px,10px -10px,-10px 0}.picture img{display:block;width:100%;height:100%;max-width:100%;max-height:100%;object-fit:contain;image-rendering:pixelated}.empty{color:#65717e;font-size:13px}.notes{white-space:pre-wrap;overflow-wrap:anywhere;margin:16px 0 0}.metrics{font-size:12px;color:#596674;white-space:pre-wrap;overflow-wrap:anywhere;margin:12px 0 0}button{border:1px solid #c5ccd3;background:white;padding:8px 12px;border-radius:6px;color:inherit;cursor:pointer}@media(max-width:700px){header,main{padding:16px}h1{font-size:21px}.card{padding:14px}.media{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.picture{height:200px;min-height:120px}.heading h2{font-size:17px}}@media(prefers-reduced-motion:reduce){.running:before{animation:none}}
</style></head><body>
<header><h1>スプライト制作・実験一覧</h1><p>元絵・生成直後・加工後・アニメを比較する。画像を押すと原寸で開ける。</p><p>生成や加工が終わったことと、絵の品質が良いことは分けて記録する。</p><div id="summary"></div><div id="connection" role="status">結果を読み込み中…</div><button id="refresh" type="button">今すぐ更新</button></header>
<main><div id="experiments"></div></main>
<script>
const container=document.querySelector('#experiments'),connection=document.querySelector('#connection');
const labels={pending:'待機中',queued:'待機中',running:'実行中',generating:'生成中',processing:'加工中',completed:'処理完了',complete:'処理完了',done:'処理完了',failed:'失敗',error:'失敗',review:'目視確認待ち',reviewed:'目視確認済み'};
let last='',busy=false;
function el(tag,text,cls){const node=document.createElement(tag);if(text!==undefined)node.textContent=String(text);if(cls)node.className=cls;return node}
function localPath(value){if(typeof value!=='string'||!value||value.startsWith('/')||value.includes('\\'))return null;try{const u=new URL(value,location.href),base=new URL('.',location.href);if(u.origin!==base.origin||!u.pathname.startsWith(base.pathname)||decodeURIComponent(u.pathname).split('/').some(x=>x.startsWith('.')))return null;return u.href}catch{return null}}
function render(data){const experiments=Array.isArray(data.experiments)?data.experiments:[];const fragment=document.createDocumentFragment();for(const exp of experiments){const card=el('article',undefined,'card'),heading=el('div',undefined,'heading'),title=el('div');title.append(el('div',exp.category||'実験','category'),el('h2',exp.title||exp.id||'名称未設定'));const status=String(exp.status||'pending'),state=['running','generating','processing'].includes(status)?'running':['failed','error'].includes(status)?'failed':['completed','complete','done'].includes(status)?'completed':'';heading.append(title,el('span',labels[status]||status,'status '+state));card.append(heading);const media=el('div',undefined,'media');for(const [key,label]of [['reference','元絵'],['raw','生成直後'],...(exp.processed?[['processed','加工後・単体']]:[]),['contact','加工後・コマ一覧'],['animation','アニメーション']]){const fig=el('figure');fig.append(el('figcaption',label));const href=localPath(exp[key]);if(href){const a=el('a',undefined,'picture');a.href=href;a.target='_blank';a.rel='noopener';a.title='原寸で開く';const img=el('img');img.src=href;img.alt=(exp.title||exp.id||'実験')+'：'+label;img.loading='lazy';img.addEventListener('error',()=>{a.replaceChildren(el('span','画像の読み込み待ち','empty'))},{once:true});a.append(img);fig.append(a)}else{fig.append(el('div','まだありません','picture empty'))}media.append(fig)}card.append(media);const notes=Array.isArray(exp.notes)?exp.notes.join('\n'):exp.notes;card.append(el('p',notes||'結果と問題点は確認後に追記します。','notes'));if(exp.metrics){const entries=Object.entries(exp.metrics).map(([k,v])=>k+'：'+(typeof v==='object'?JSON.stringify(v):String(v)));const details=el('details');details.append(el('summary','生成・加工の詳細'),el('div',entries.join('\n'),'metrics'));card.append(details)}fragment.append(card)}container.replaceChildren(fragment);document.querySelector('#summary').textContent=experiments.length+' 件の実験';if(!experiments.length)container.append(el('p','実験の登録を待っています。'))}
async function refresh(){if(busy)return;busy=true;try{const response=await fetch('results.json',{cache:'no-store'});if(!response.ok)throw Error();const body=await response.text(),data=JSON.parse(body);if(body!==last){render(data);last=body}connection.textContent='最終確認 '+new Date().toLocaleTimeString('ja-JP')+' ・5秒ごとに自動更新'}catch{connection.textContent='結果を取得できません。5秒後に再確認します。'}finally{busy=false}}
document.querySelector('#refresh').addEventListener('click',()=>{last='';refresh()});refresh();setInterval(refresh,5000);
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1] / "assets/capability-lab", help="results.json がある実験素材のディレクトリ")
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=True)
    target = args.root / "index.html"
    target.write_text(HTML, encoding="utf-8")
    print(f"実験一覧を作成しました: {target}")


if __name__ == "__main__":
    main()
