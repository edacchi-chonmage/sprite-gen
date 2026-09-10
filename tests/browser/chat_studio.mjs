import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
const {chromium}=createRequire(import.meta.url)('playwright');
const html=await readFile(new URL('../../sprite_gen/serve/chat_ui/index.html',import.meta.url));
const server=createServer((req,res)=>{res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});res.end(html)});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const appURL=`http://127.0.0.1:${server.address().port}/`;
import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true,...(process.env.SPRITE_TEST_CHROME?{executablePath:process.env.SPRITE_TEST_CHROME}:{})});
const pixel='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=';
const base={id:'a',title:'男性の走りモーション',messages:Array.from({length:12},(_,i)=>({role:i%2?'assistant':'user',text:'会話の内容を確認する。'.repeat(15)})),status:'idle',events:[],versions:[{id:'v1',title:'最初の絵',image:pixel},{id:'v2',title:'走る動き',image:pixel,animation:pixel}]};
let checks=0;
try {
for(const width of [360,390,768,1280,1440]){
 const page=await browser.newPage({viewport:{width,height:width===360?667:850}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));let a=structuredClone(base), b={...structuredClone(base),id:'b',title:'別の作品'},posts=0,delayA=false,releaseA,pollError=false;
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let body;
  if(path==='/api/library')body={items:[]};
  else if(path==='/api/chats')body={chats:[{id:'a',title:a.title},{id:'b',title:b.title}]};
  else if(path.endsWith('/messages')){posts++;a.status='running';a.phase='絵を生成している';a.events=[{text:'元絵を確認した'}];body=a;}
  else if(path==='/api/chats/a'){if(pollError){await route.fulfill({status:503,json:{error:'通信できない'}});return}if(delayA){await new Promise(r=>releaseA=r);await route.fulfill({status:500,json:{error:'古い会話の失敗'}});return}body=a}
  else if(path==='/api/chats/b')body=b;else throw Error(path);
  await route.fulfill({json:body});
 });
 await page.addInitScript(()=>localStorage.setItem('sprite-chat-id','a'));
 await page.goto(appURL);await page.waitForFunction(()=>document.querySelector('#versions')?.options.length===2);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);checks++;
 assert(await page.locator('#send').isVisible());assert(await page.locator('#text').isVisible());
 if(width<761){assert(await page.locator('#mobile-peek').isVisible());await page.locator('#mobile-peek').click()}
 assert(await page.locator('.viewer').isVisible());
 await page.locator('#canvas-in').click();assert((await page.locator('#preview-grid img').last().getAttribute('style')).includes('1.4'));
 const canvas=page.locator('#preview-grid .image-button').last();const box=await canvas.boundingBox();await page.mouse.move(box.x+30,box.y+30);await page.mouse.down();await page.mouse.move(box.x+60,box.y+30,{steps:30});await page.mouse.up();assert.equal(await page.locator('#lightbox').isVisible(),false);
 await page.locator('#canvas-fit').click();assert((await page.locator('#preview-grid img').last().getAttribute('style')).includes('scale(1)'));checks++;
 await page.locator('#versions').selectOption('v1');assert(await page.locator('#version-warning').isVisible());assert(await page.locator('#send').isDisabled());
 await page.locator('#show-latest').click();assert.equal(await page.locator('#send').isDisabled(),false);checks++;
 if(width<761)await page.locator('#tab-chat').click();
 await page.locator('#text').fill('Aの下書き');
 async function open(id){if(await page.locator('#history-toggle').isVisible()){await page.locator('#history-toggle').click();await page.locator('#history-chats button').nth(id==='a'?0:1).click()}else await page.locator('#chats button').nth(id==='a'?0:1).click();await page.waitForFunction(t=>document.querySelector('#chat-title').textContent===t,id==='a'?a.title:b.title)}
 await open('b');await page.locator('#text').fill('Bの下書き');await open('a');assert.equal(await page.locator('#text').inputValue(),'Aの下書き');await page.reload();await page.waitForFunction(()=>document.querySelector('#versions')?.options.length===2);assert.equal(await page.locator('#text').inputValue(),'Aの下書き');await open('b');assert.equal(await page.locator('#text').inputValue(),'Bの下書き');await open('a');checks++;
 await page.locator('#send').click();await page.waitForFunction(()=>document.querySelector('#send').textContent==='制作中');assert.equal(posts,1);await page.locator('#text').fill('制作中の下書き');
 if(width<761)await page.locator('#tab-preview').click();
 assert(await page.locator('#global-dot').isVisible());await page.locator('#activity-toggle').click();assert.match(await page.locator('#activity-events').innerText(),/元絵/);await page.locator('[data-close="activity-dialog"]').click();
 pollError=true;await page.waitForFunction(()=>document.querySelector('#global-phase').textContent.includes('進行状況を取得できなかった'));pollError=false;checks++;
 a.status='idle';a.versions.push({id:'v3',title:'完成版',image:pixel});await page.waitForFunction(()=>document.querySelector('#versions')?.options.length===3);assert.equal(await page.locator('#versions').inputValue(),'v3');assert.equal(await page.locator('#send').isDisabled(),false);if(width<761)await page.locator('#tab-chat').click();assert.equal(await page.locator('#text').inputValue(),'制作中の下書き');checks++;
 // 読み込み中の送信を抑止し、前の会話の遅延失敗を別会話へ表示しない。
 await open('b');delayA=true;
 if(await page.locator('#history-toggle').isVisible()){await page.locator('#history-toggle').click();await page.locator('#history-chats button').first().click();await page.waitForFunction(()=>document.querySelector('#text').disabled);await page.locator('#history-chats button').nth(1).click()}
 else {await page.locator('#chats button').first().click();await page.waitForFunction(()=>document.querySelector('#text').disabled);await page.locator('#chats button').nth(1).click()}
 await page.waitForFunction(()=>!document.querySelector('#text').disabled);releaseA();await page.waitForTimeout(100);assert.equal(await page.locator('#error').isVisible(),false);assert.equal(await page.locator('#text').inputValue(),'Bの下書き');checks++;
 assert.deepEqual(errors,[]);console.log(JSON.stringify({width,checks:'下書き・版・進捗・切替・表示を確認',errors}));await page.close();
}
// 初回の会話作成失敗と、作成直後の送信失敗でも下書きを復元する。
const page=await browser.newPage({viewport:{width:390,height:850}});let failCreate=true,created=false;
await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;
 if(path==='/api/library')return route.fulfill({json:{items:[]}});
 if(path==='/api/chats'&&route.request().method()==='GET')return route.fulfill({json:{chats:created?[{id:'a',title:base.title}]:[]}});
 if(path==='/api/chats'&&failCreate)return route.fulfill({status:503,json:{error:'会話の作成に失敗した'}});
 if(path.endsWith('/messages'))return route.fulfill({status:503,json:{error:'送信に失敗した'}});
 created=true;return route.fulfill({json:{...base,messages:[],versions:[]}});
});
await page.goto(appURL);await page.locator('#text').fill('初回の大事な下書き');await page.locator('#send').click();await page.waitForFunction(()=>document.querySelector('#error').textContent.includes('会話の作成'));
await page.reload();assert.equal(await page.locator('#text').inputValue(),'初回の大事な下書き');failCreate=false;await page.locator('#send').click();await page.waitForFunction(()=>document.querySelector('#error').textContent.includes('送信に失敗'));
await page.reload();await page.waitForFunction(()=>document.querySelector('#chat-title').textContent==='男性の走りモーション');assert.equal(await page.locator('#text').inputValue(),'初回の大事な下書き');checks+=2;await page.close();
console.log(`${checks}項目を確認`);
} finally {await browser.close();await new Promise(resolve=>server.close(resolve))}
