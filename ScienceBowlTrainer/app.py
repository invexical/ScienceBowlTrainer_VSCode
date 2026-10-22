"""Science Bowl Trainer Pro — single-file Streamlit app.

Install: py -m pip install --upgrade streamlit pandas requests beautifulsoup4 pymupdf
Run: py -m streamlit run app.py

Inputs: output/questions.csv (optional), output/doe_hs_questions.csv (created by importer)
Detailed attempt logs: practice_history.json; aggregate progress: practice_progress.json
"""
import csv
import hashlib
import io
import json
import random
import re
import subprocess
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, unquote, urljoin, urlsplit

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

BASE = Path(__file__).resolve().parent

FRONTEND_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color-scheme:light dark}
*{box-sizing:border-box}body{margin:0;padding:4px;background:transparent;color:#19283b}
.player{border:1px solid #cbd5e1;border-radius:17px;background:#f8fafc;padding:20px}
.head,.optionsbar,.actions,.details,.timebox{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
.head{margin-bottom:16px}.pill{padding:7px 12px;background:#e2e8f0;border-radius:30px;font-size:12px;font-weight:800;letter-spacing:.06em}
.tag{font-size:12px;font-weight:650;border:1px solid #cbd5e1;padding:5px 9px;border-radius:7px}
.optionsbar{justify-content:flex-end;gap:13px;margin:10px 0 17px}.toggle{display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer}
select,input[type=text]{font:inherit;border:1px solid #a4b3c5;background:#fff;color:#172439;border-radius:9px;padding:10px}
select{padding:6px;max-width:220px;font-size:12px}
.display{min-height:160px;border:1px solid #dbe3ed;border-radius:13px;background:white;padding:22px;font-size:22px;line-height:1.65;font-weight:600;white-space:pre-wrap;overflow-wrap:anywhere}
.display em{font-weight:400;color:#64748b;font-size:17px}.intro{font-size:28px;font-weight:800;text-align:center;padding-top:35px;letter-spacing:.04em}
.bar{height:9px;margin:13px 0 8px;background:#dbe6f2;border-radius:20px;overflow:hidden}.fill{height:100%;background:#2563eb;width:0;transition:width .1s linear}
.details{font-size:12px;color:#64748b;margin:8px 0 15px}
button{border-radius:9px;border:1px solid #94a3b8;background:#fff;color:#16253b;padding:12px 16px;font:inherit;font-weight:650;cursor:pointer}
button:disabled{opacity:.45;cursor:not-allowed}button:hover:not(:disabled){filter:brightness(.96)}
.primary{background:#1d4ed8;color:#fff;border-color:#1d4ed8}.buzz{background:#e24a2a;color:#fff;border-color:#b91c1c;font-size:19px;flex:1;min-width:150px}
.next{background:#047857;color:white;border-color:#047857;flex:1}
.panel{padding:16px;border:1px solid #cbd5e1;border-radius:12px;background:white;margin-top:17px}
.timer{font-size:34px;font-weight:800;font-variant-numeric:tabular-nums;color:#1d4ed8}.timer.danger{color:#dc2626}
.subtitle,.hint{font-size:13px;color:#64748b}.subtitle{margin-top:5px}
input[type=text]{width:100%;margin:10px 0 12px}.choice-list{display:grid;gap:8px;margin:12px 0}
.choice{display:flex;align-items:flex-start;gap:9px;border:1px solid #dae2ef;background:#f8fafc;padding:11px;border-radius:8px;cursor:pointer}
.choice:has(input:checked){border-color:#2563eb;background:#eff6ff}
.result{background:#eff6ff;border-left:4px solid #0284c7;border-radius:6px;padding:14px;margin:9px 0;overflow-wrap:anywhere}
.message{padding:12px;border-radius:9px;margin-top:14px;background:#dbeafe;font-size:14px}.ok{background:#dcfce7;color:#166534}.bad{background:#fee2e2;color:#991b1b}
.hint{margin:12px 0 0}.tools{display:flex;gap:9px;flex-wrap:wrap;margin-top:12px}.tools a{border:1px solid #94a3b8;border-radius:9px;padding:11px 14px;color:#1d4ed8;background:#fff;text-decoration:none;font-size:14px;font-weight:650}.actions{justify-content:flex-start}.actions button{flex:0 0 auto}
[hidden]{display:none!important}
@media(max-width:580px){.player{padding:13px}.display{font-size:19px;min-height:130px}.actions button{flex:1}.optionsbar{justify-content:flex-start}}
@media(prefers-color-scheme:dark){body{color:#e2e8f0}.player{background:#111827;border-color:#374151}.display,.panel{background:#1f2937;border-color:#475569}.pill{background:#334155}.tag{border-color:#475569}.bar{background:#334155}.hint,.subtitle,.details,.display em{color:#94a3b8}select,input[type=text]{background:#0f172a;color:#e2e8f0;border-color:#64748b}button{background:#334155;color:white;border-color:#64748b}.primary{background:#1d4ed8;border-color:#1d4ed8}.buzz{background:#c24123;border-color:#a53219}.next{background:#047857;border-color:#047857}.choice{background:#111827;border-color:#475569}.choice:has(input:checked){background:#1e3a5f}.result,.message{background:#1e3a5f;color:#e0f2fe}.ok{background:#14532d;color:#bbf7d0}.bad{background:#7f1d1d;color:#fecaca}.timer{color:#93c5fd}.timer.danger{color:#fca5a5}}
</style></head><body>
<div class="player" id="player">
 <div class="head"><span id="state" class="pill">READY</span><span id="metadata" class="tag">SCIENCE BOWL</span></div>
 <div class="optionsbar">
  <label class="toggle"><input id="voice" type="checkbox"> 🔊 Voice</label>
  <select id="voiceList" aria-label="Narrator voice" hidden></select>
  <label class="toggle"><input id="showText" type="checkbox" checked> Show text</label>
  <label class="toggle"><input id="showBar" type="checkbox" checked> Progress bar</label>
 </div>
 <div class="display" id="display"><em>Press Start Reading to begin.</em></div>
 <div id="progressArea"><div class="bar"><div class="fill" id="fill"></div></div><div class="details"><span id="words"></span><span id="readTime"></span></div></div>
 <div class="actions" id="readerButtons">
  <button id="start" class="primary">▶ Start Reading</button>
  <button id="restart">↺ Restart</button>
  <button id="buzz" class="buzz" disabled>🔔 BUZZ (Space)</button>
  <button id="skip">Skip</button>
 </div>
 <div id="answerPanel" class="panel" hidden>
  <div class="timebox"><div><b id="answerLabel">Answer window</b><div class="subtitle" id="answerSubtitle"></div></div><div id="timer" class="timer">5.0s</div></div>
  <div id="choices" class="choice-list" hidden></div>
  <input type="text" id="typed" autocomplete="off" placeholder="Type your answer and press Enter" aria-label="Your answer">
  <div class="actions"><button class="primary" id="lock">Lock in answer ↵</button></div>
 </div>
 <div class="panel" id="reviewPanel" hidden>
  <strong>Official answer</strong><div class="result" id="official"></div><p id="yourResponse" class="subtitle"></p>
  <div id="gradeButtons" class="actions"><button id="right" class="primary">✅ Correct</button><button id="wrong">❌ Incorrect</button></div>
 </div>
 <div class="message" id="message" hidden></div>
  <div class="tools" id="researchTools" hidden><button id="copyQuestion" type="button">📋 Copy complete question</button><a id="googleQuestion" href="https://www.google.com/" target="_blank" rel="noopener noreferrer">🔍 Search question on Google ↗</a><span class="subtitle" id="copiedNote" aria-live="polite"></span></div>
 <div class="actions" id="nextArea" hidden><button class="next" id="next">Next question → (N)</button></div>
 <p class="hint">Space to buzz while the reader is active (click inside this player for keyboard focus). Enter to submit your answer. N for next after grading.</p>
</div>
<script>
(() => {
 'use strict';
 const $=id=>document.getElementById(id);
 const send=(type,data={})=>window.parent.postMessage({isStreamlitMessage:true,type,...data},'*');
 const notify=value=>send('streamlit:setComponentValue',{value,dataType:'json'});
 const resize=()=>send('streamlit:setFrameHeight',{height:Math.ceil(document.documentElement.scrollHeight+12)});
 const synth=window.speechSynthesis;
 const pref=(name,fallback)=>{try{let v=localStorage.getItem('sb_'+name);return v===null?fallback:v==='true';}catch(_){return fallback;}};
 const store=(name,val)=>{try{localStorage.setItem('sb_'+name,String(val));}catch(_){}};
 $('voice').checked=pref('voice',false);
 $('showText').checked=pref('showText',true);
 $('showBar').checked=pref('showBar',true);
 if(!synth){$('voice').disabled=true;$('voice').title='Speech synthesis is unavailable in this browser';}
 let preferredVoice='';try{preferredVoice=localStorage.getItem('sb_voiceName')||'';}catch(_){}
 let args=null,instance=null,wordList=[],wordStarts=[],spokenQuestion='',phase='ready';
 let introIndex=0,introToken=0,shown=0,playing=false,tickAt=0,accumMs=0;
 let voiceActive=false,utterance=null,voiceToken=0,voiceStart=0,voicePauseMs=0,voicePauseAt=0,boundaries=false;
 let answerStart=0,deadline=0,answerOrigin='',buzzPct=0,answerTime=0,submitted='',sent=false,saved=false;
 let lastShown=-1,lastFrame=0;
 const now=()=>performance.now();
 const cap=(value,min,max)=>Math.max(min,Math.min(max,value));
 const options=()=>Array.isArray(args?.options)?args.options:[];
 const limit=()=>args?.kind==='BONUS'?20:5;
 const intro=()=>[String(args?.subject||'SCIENCE'),String(args?.kind||'TOSSUP'),String(args?.format||'SHORT ANSWER')];
 const rate=()=>cap(Number(args?.words_per_second||3),0.5,15);
 const calculateWords=text=>{let tokens=[],offsets=[];for(const m of text.matchAll(/\S+/g)){tokens.push(m[0]);offsets.push(m.index);}return [tokens,offsets];};
 function populateVoices(){if(!synth)return;let list=$('voiceList');let vs=synth.getVoices();list.replaceChildren();let d=document.createElement('option');d.value='';d.textContent='Default voice';list.appendChild(d);
   for(const v of vs){let o=document.createElement('option');o.value=v.name;o.textContent=`${v.name} (${v.lang})`;list.appendChild(o);}list.value=vs.some(v=>v.name===preferredVoice)?preferredVoice:'';list.hidden=!$('voice').checked||!vs.length;resize();}
 if(synth){synth.addEventListener?.('voiceschanged',populateVoices);populateVoices();}
 function haltVoice(){voiceToken++;voiceActive=false;utterance=null;try{synth?.cancel();}catch(_){}}
 function stopActivity(){introToken++;haltVoice();playing=false;}
 function reset(){stopActivity();phase='ready';introIndex=0;shown=0;tickAt=0;accumMs=0;sent=false;saved=false;answerStart=0;deadline=0;answerTime=0;answerOrigin='';buzzPct=0;submitted='';boundaries=false;lastShown=-1;$('typed').value='';$('message').hidden=true;$('answerPanel').hidden=true;$('reviewPanel').hidden=true;$('gradeButtons').hidden=false;$('nextArea').hidden=true;
   for(const r of $('choices').querySelectorAll('input'))r.checked=false;render();}
 function makeChoices(){let box=$('choices');box.replaceChildren();let opts=options();box.hidden=!opts.length;$('typed').hidden=!!opts.length;
  for(let o of opts){let label=document.createElement('label');label.className='choice';let radio=document.createElement('input');radio.type='radio';radio.name='option';radio.value=o.letter;
   let text=document.createElement('span');text.textContent=`${o.letter}) ${o.text}`;label.append(radio,text);box.appendChild(label);}}
 function configure(data){if(!data?.instance_id)return;let isNew=instance!==data.instance_id;args=data;
  if(isNew){instance=data.instance_id;spokenQuestion=String(data.question||'').trim();let opts=options();
   // Avoid duplicating choices already printed inside the question.
   if(opts.length&&!opts.every(o=>spokenQuestion.toLowerCase().includes(String(o.text||'').toLowerCase())))spokenQuestion+='\n\n'+opts.map(o=>`${o.letter}) ${o.text}`).join('\n');
   [wordList,wordStarts]=calculateWords(spokenQuestion);makeChoices();reset();}
  if(data.saved && !saved){stopActivity();saved=true;sent=true;phase='graded';shown=wordList.length;submitted=String(data.saved.your_answer||'');
    $('message').hidden=false;$('message').className=data.saved.correct?'message ok':'message bad';
    $('message').textContent=data.saved.correct?'Correct — saved to history.':'Recorded as '+String(data.saved.status||'incorrect')+'.';}
  render();}
 function speak(text,onDone){if(!synth||!$('voice').checked)return false;
  try{haltVoice();let token=++voiceToken;let u=new SpeechSynthesisUtterance(text);utterance=u;
   u.lang='en-US';u.rate=cap(rate()/3,0.60,2.1);let choice=synth.getVoices().find(v=>v.name===$('voiceList').value);if(choice)u.voice=choice;
   u.onend=()=>{if(token!==voiceToken)return;voiceActive=false;onDone?.();};
   u.onerror=()=>{if(token!==voiceToken)return;voiceActive=false;onDone?.();};
   voiceActive=true;synth.cancel();synth.speak(u);return true;}catch(_){voiceActive=false;return false;}}
 function beginIntro(){if(phase!=='intro'||!playing)return;const stage=introIndex;if(stage>=3){startQuestion();return;}
  const token=++introToken;render();let done=false;
  const advance=()=>{if(done)return;done=true;if(token!==introToken||phase!=='intro')return;
   setTimeout(()=>{if(token!==introToken||phase!=='intro'||!playing)return;introIndex++;beginIntro();},50);};
  if(!speak(intro()[stage],advance))setTimeout(advance,50);
 }
 function startQuestion(){if(phase!=='intro')return;phase='reading';tickAt=now();accumMs=0;boundaries=false;voicePauseMs=0;voicePauseAt=0;
  if(synth&&$('voice').checked){
   haltVoice();let token=++voiceToken;let u=new SpeechSynthesisUtterance(spokenQuestion);utterance=u;u.lang='en-US';u.rate=cap(rate()/3,.60,2.1);
   let chosen=synth.getVoices().find(v=>v.name===$('voiceList').value);if(chosen)u.voice=chosen;
   u.onboundary=e=>{if(token!==voiceToken||phase!=='reading'||!playing)return;boundaries=true;let character=Math.max(0,e.charIndex||0);let index=0;while(index<wordStarts.length&&wordStarts[index]<=character)index++;shown=Math.max(shown,Math.min(index,wordList.length));render();};
   u.onend=()=>{if(token!==voiceToken||phase!=='reading')return;voiceActive=false;shown=wordList.length;beginAnswer('finished');};
   u.onerror=()=>{if(token!==voiceToken||phase!=='reading')return;voiceActive=false;accumMs=shown*1000/rate();tickAt=now();
    $('message').hidden=false;$('message').className='message';$('message').textContent='Voice playback stopped; continuing silently.';};
   try{voiceActive=true;voiceStart=now();synth.cancel();synth.speak(u);}catch(_){voiceActive=false;}
  }
  render();}
 function start(){if(phase==='ready'){phase='intro';playing=true;introIndex=0;beginIntro();}
  else if(phase==='paused_intro'){phase='intro';playing=true;beginIntro();}
  else if(phase==='paused'){phase='reading';playing=true;
   if(voiceActive&&synth?.paused){try{synth.resume();}catch(_){}if(voicePauseAt)voicePauseMs+=now()-voicePauseAt;voicePauseAt=0;}
   else if(!voiceActive)tickAt=now();}
  render();}
 function pause(){if(phase!=='reading'&&phase!=='intro')return;
  if(phase==='intro'){stopActivity();phase='paused_intro';render();return;}
  if(!voiceActive){const t=now();updateSilent(t);if(phase!=='reading')return;accumMs+=t-tickAt;}else{voicePauseAt=now();try{synth.pause();}catch(_){}}
  playing=false;phase='paused';render();}
 function updateSilent(t){if(phase!=='reading'||!playing||voiceActive)return;let elapsed=accumMs+(t-tickAt);shown=cap(Math.floor(elapsed*rate()/1000),0,wordList.length);if(shown>=wordList.length){accumMs=elapsed;beginAnswer('finished');}}
 function buzz(){if(!['reading','paused'].includes(phase))return;
  if(phase==='reading'&&!voiceActive)updateSilent(now());if(phase!=='reading'&&phase!=='paused')return;
  buzzPct=wordList.length?Math.round(shown/wordList.length*1000)/10:100;beginAnswer('buzzed');}
 function beginAnswer(origin){if(!['reading','paused'].includes(phase))return;stopActivity();phase='answer';answerOrigin=origin;
  if(origin==='finished'){shown=wordList.length;buzzPct=100;}
  answerStart=now();deadline=answerStart+limit()*1000;render();setTimeout(()=>{if(phase!=='answer')return;
  if($('typed').hidden){$('choices').querySelector('input')?.focus();}else $('typed').focus();},50);}
 function selectedAnswer(){if(!$('typed').hidden)return $('typed').value.trim();let c=$('choices').querySelector('input:checked');if(!c)return'';let opt=options().find(o=>o.letter===c.value);return`${c.value}) ${opt?.text||''}`;}
 function lock(){if(phase!=='answer')return;if(now()>=deadline){timeout();return;}submitted=selectedAnswer();answerTime=(now()-answerStart)/1000;phase='review';render();}
 function timeout(){if(phase!=='answer')return;submitted=selectedAnswer();answerTime=limit();finish(false,'timeout');}
 function skip(){if(['graded','review','answer'].includes(phase))return;stopActivity();submitted='';answerTime=0;
  buzzPct=wordList.length?Math.round(shown/wordList.length*1000)/10:0;finish(false,'skipped');}
 function finish(correct,status){if(sent||!args||!['review','answer','reading','paused','intro','ready','paused_intro'].includes(phase))return;
  stopActivity();sent=true;phase='graded';render();$('message').hidden=false;$('message').className=correct?'message ok':'message bad';
  $('message').textContent='Saving your attempt…';
  let id=(crypto?.randomUUID?.()||`${Date.now()}-${Math.random()}`);
  notify({event:'graded',event_id:id,question_id:args.question_id,instance_id:args.instance_id,
    status,correct:correct===true,your_answer:submitted,response_seconds:answerTime,buzz_percent:buzzPct,
    answered_after_read:answerOrigin==='finished'});}
 function goNext(){if(!saved||!args)return;notify({event:'next',event_id:crypto?.randomUUID?.()||String(now()),instance_id:args.instance_id,question_id:args.question_id});
  $('next').disabled=true;}
 function render(){if(!args)return;
  let label=phase==='ready'?'READY':phase==='intro'?'ANNOUNCING':phase==='paused_intro'?'PAUSED':phase==='reading'?'READING':phase==='paused'?'PAUSED':phase==='answer'?'ANSWER NOW':phase==='review'?'CHECK ANSWER':'RECORDED';
  $('state').textContent=label;$('metadata').textContent=`${args.subject} · ${args.kind} · ${args.format}`;
  let display='';
  if(!$('showText').checked) display='<em>Question text hidden — listen and buzz.</em>';
  else if(phase==='ready')display='<em>Press Start Reading to begin.</em>';
  else if(['intro','paused_intro'].includes(phase))display=`<div class="intro"></div>`;
  else if(phase==='review'||phase==='graded')display='';
  else if(shown>0)display='';
  else display='<em>Listen for the question…</em>';
  const prompt=$('display');prompt.replaceChildren();
  if(phase==='intro'||phase==='paused_intro'){
    if($('showText').checked){const x=document.createElement('div');x.className='intro';x.textContent=intro()[Math.min(2,introIndex)];prompt.appendChild(x);}
    else prompt.innerHTML=display;
  }else if($('showText').checked&&((phase==='review'||phase==='graded')||shown>0)){
    prompt.textContent=(phase==='review'||phase==='graded')?spokenQuestion:wordList.slice(0,shown).join(' ');
  }else prompt.innerHTML=display;
  $('progressArea').hidden=!$('showBar').checked;
  $('fill').style.width=`${wordList.length?100*shown/wordList.length:0}%`;
  $('words').textContent=`${shown} / ${wordList.length} words`;
  $('readTime').textContent=shown>=wordList.length?'Question read':`${Math.round((shown/Math.max(1,wordList.length))*100)}% revealed`;
  const active=['ready','intro','paused_intro','reading','paused'].includes(phase);
  $('readerButtons').hidden=!active;$('start').disabled=!active;$('start').textContent=phase==='reading'||phase==='intro'?'⏸ Pause':phase==='ready'?'▶ Start Reading':'▶ Resume';
  $('restart').disabled=!active||phase==='ready';$('buzz').disabled=!['reading','paused'].includes(phase);
  $('voice').disabled=!(phase==='ready')||!synth;$('voiceList').disabled=phase!=='ready';
  $('answerPanel').hidden=phase!=='answer';$('answerLabel').textContent=`${args.kind} — ${limit()} second answer window`;
  $('answerSubtitle').textContent=answerOrigin==='buzzed'?'Buzzed early — question stopped':'Question finished — timer started';
  $('reviewPanel').hidden=!['review','graded'].includes(phase);$('official').textContent=String(args.answer||'');
  $('yourResponse').textContent=submitted?`Your response: ${submitted}`:'No answer submitted.';
  $('gradeButtons').hidden=phase!=='review';
  $('nextArea').hidden=!saved;$('next').disabled=!saved;
   const researchReady = (phase==='answer' && shown>=wordList.length) || phase==='review' || phase==='graded';
   $('researchTools').hidden=!researchReady;
   $('googleQuestion').href='https://www.google.com/search?q='+encodeURIComponent(spokenQuestion.trim());
  if(phase==='graded'&&!saved){$('message').hidden=false;$('message').className='message';$('message').textContent='Saving your attempt…';}
  if(phase==='answer'){let remaining=Math.max(0,(deadline-now())/1000);$('timer').textContent=remaining.toFixed(1)+'s';$('timer').classList.toggle('danger',remaining<=2);}
  resize();}
 function frame(t){if(phase==='reading'&&playing){if(voiceActive){if(!boundaries&&t-voiceStart>550){let estimate=Math.floor(Math.max(0,t-voiceStart-voicePauseMs)*rate()/1000);
   shown=Math.max(shown,Math.min(Math.max(0,wordList.length-1),estimate));}}else updateSilent(t);
   if(shown!==lastShown||t-lastFrame>400){lastShown=shown;lastFrame=t;render();}}
  if(phase==='answer'){let remain=Math.max(0,(deadline-t)/1000);$('timer').textContent=remain.toFixed(1)+'s';$('timer').classList.toggle('danger',remain<=2);if(remain<=0)timeout();}
  requestAnimationFrame(frame);}
 $('start').addEventListener('click',()=>['reading','intro'].includes(phase)?pause():start());
 $('restart').addEventListener('click',reset);$('buzz').addEventListener('click',buzz);$('skip').addEventListener('click',skip);$('lock').addEventListener('click',lock);
 $('typed').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();lock();}});
 $('choices').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();lock();}});
 $('right').addEventListener('click',()=>finish(true,'correct'));$('wrong').addEventListener('click',()=>finish(false,'incorrect'));
 $('next').addEventListener('click',goNext);
  $('copyQuestion').addEventListener('click',async()=>{
    const text=spokenQuestion.trim();try{await navigator.clipboard.writeText(text);$('copiedNote').textContent='Copied!';}
    catch(_){let t=document.createElement('textarea');t.value=text;document.body.appendChild(t);t.select();let ok=document.execCommand('copy');t.remove();$('copiedNote').textContent=ok?'Copied!':'Copy not allowed; use the question bank to select text.';}
    setTimeout(()=>{$('copiedNote').textContent='';},2200);});
 $('showText').addEventListener('change',e=>{store('showText',e.target.checked);render();});
 $('showBar').addEventListener('change',e=>{store('showBar',e.target.checked);render();});
 $('voice').addEventListener('change',e=>{store('voice',e.target.checked);populateVoices();});
 $('voiceList').addEventListener('change',e=>{preferredVoice=e.target.value;try{localStorage.setItem('sb_voiceName',preferredVoice);}catch(_){}});
 document.addEventListener('keydown',e=>{
  if(e.repeat)return;
  const tag=document.activeElement?.tagName||'';
  if(['INPUT','TEXTAREA','SELECT'].includes(tag))return;
  if((e.code==='Space'||e.key===' ')&&['reading','paused'].includes(phase)){e.preventDefault();e.stopPropagation();buzz();}
  else if(e.key.toLowerCase()==='n'&&saved){e.preventDefault();goNext();}
 },true);
 window.addEventListener('message',e=>{if(e.data?.type==='streamlit:render')configure(e.data.args||{});});
 window.addEventListener('pagehide',stopActivity);
 if('ResizeObserver'in window)new ResizeObserver(resize).observe($('player'));
 send('streamlit:componentReady',{apiVersion:1});requestAnimationFrame(frame);
})();
</script></body></html>'''

# -----------------------------------------------------------------------------
# OFFICIAL DOE HIGH-SCHOOL SAMPLE-QUESTION IMPORTER
# -----------------------------------------------------------------------------
DOE_PAGE = "https://science.osti.gov/wdts/nsb/Regional-Competitions/Resources/HS-Sample-Questions"
DOE_FILE = BASE / "output" / "doe_hs_questions.csv"
DOE_REPORT = BASE / "output" / "doe_import_report.csv"
DOE_CACHE = BASE / "output" / "doe_pdf_cache"
DOE_YEAR = {1: "2009", 2: "2012", 3: "2007", 4: "2011", 5: "2011",
            6: "2012", 7: "2013", 8: "2014", 9: "2015", 10: "2016", 11: "2017"}
BANK_COLUMNS = ["id", "category", "type", "format", "number", "question", "answer",
                "choice_w", "choice_x", "choice_y", "choice_z", "year", "round",
                "set", "source_file", "source_page", "source_url", "source",
                "needs_review", "review_reasons"]


def clean_cell(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def canonical_category(name):
    raw = clean_cell(name).strip("-–—: ")
    key = raw.casefold().replace("&", "and")
    mapping = {"math": "Mathematics", "mathematics": "Mathematics",
               "earth and space": "Earth and Space", "earth space": "Earth and Space",
               "earth and space science": "Earth and Space", "earth science": "Earth and Space",
               "biology": "Biology", "chemistry": "Chemistry", "physics": "Physics",
               "energy": "Energy", "general science": "General Science"}
    return mapping.get(key, raw.title() if raw.isupper() else raw or "Unknown")


def fingerprint(q):
    return hashlib.sha256((re.sub(r"\W+", "", clean_cell(q.get("question")).casefold()) + "|"
              + canonical_category(q.get("category")) + "|" + str(q.get("type", "")).upper()).encode()).hexdigest()


def get_doe_links(html):
    from bs4 import BeautifulSoup
    doc = BeautifulSoup(html, "html.parser")
    found, used = [], set()
    for a in doc.select("a[href]"):
        url = urljoin(DOE_PAGE, a["href"])
        parsed = urlsplit(url)
        if parsed.hostname != "science.osti.gov" or not parsed.path.lower().endswith(".pdf"):
            continue
        match = re.search(r"sample-set-(\d+)", parsed.path, re.I)
        if not match or "hs-sample-questions" not in parsed.path.lower():
            continue
        if url in used:
            continue
        used.add(url)
        label = clean_cell(a.get_text(" ", strip=True))
        round_match = re.search(r"\bRound\s+(\d+)\b", label, re.I)
        found.append({"url": url, "set": int(match.group(1)),
                      "round": round_match.group(1) if round_match else "", "label": label})
    return found


QUESTION_HEADER = re.compile(
    r"^\s*(?P<number>\d{1,2})\s*[).]\s*(?P<category>[A-Za-z& /\-]+?)\s*"
    r"(?:[—–-]\s*)?(?P<format>Multiple\s+Choice|Short\s+Answer)\s*(?P<rest>.*)$", re.I)
KIND_HEADER = re.compile(r"^\s*(TOSS[\s-]*UP|BONUS)\s*$", re.I)
ANSWER_HEADER = re.compile(r"^\s*ANSWER\s*:\s*(.*)$", re.I)
CHOICE_HEADER = re.compile(r"^\s*([WXYZ])\s*[).]\s*(.*)$", re.I)
NOISE_HEADER = re.compile(
    r"^(?:ROUND\s+\d+|HIGH SCHOOL ROUND\s+\d+\s+PAGE\s+\d+|"
    r"20\d\d\s+NSB.*?PAGE\s+\d+|20\d\d\s+.*?QUESTIONS\s+PAGE\s+\d+|"
    r"\s*PAGE\s+\d+|[~_\-]{5,})$", re.I)


def clean_pdf_line(line):
    line = line.replace("\u00ad", "").replace("\u200b", "").replace("\ufeff", "")
    line = re.sub(r"[\u0000-\u0008\u000b-\u001f]", "", line)
    return clean_cell(line)


def parse_doe_pdf(data, meta):
    """Return (questions, issue_summary, page_count); no guessed answers.

    Parse printed TOSS-UP/BONUS sections, numbered questions, choices and answer
    blocks. Keep raw formula text as extracted; flag complex/suspect cases.
    """
    import fitz
    doc = fitz.open(stream=data, filetype="pdf")
    lines = []
    for page_index, page in enumerate(doc):
        raw = page.get_text("text", sort=True)
        for line in raw.splitlines():
            line = clean_pdf_line(line)
            if line and not NOISE_HEADER.fullmatch(line):
                lines.append((line, page_index + 1))
    out, problems = [], []
    current = None
    kind = None
    doc_round = meta.get("round", "")
    pdf_name = unquote(Path(urlsplit(meta["url"]).path).name)
    stem = f"doe-set{meta['set']}-" + hashlib.sha1(meta["url"].encode()).hexdigest()[:10]

    def flush():
        nonlocal current
        if current is None:
            return
        body = current["body"]
        qparts, aparts, choices = [], [], {key: "" for key in "wxyz"}
        in_answer = False
        active_choice = None
        for line in body:
            answer_match = ANSWER_HEADER.match(line)
            if answer_match:
                in_answer = True
                active_choice = None
                if answer_match.group(1).strip():
                    aparts.append(answer_match.group(1).strip())
                continue
            if in_answer:
                aparts.append(line)
                continue
            choice_match = CHOICE_HEADER.match(line)
            if choice_match and current["format"].lower().startswith("multiple"):
                active_choice = choice_match.group(1).lower()
                choices[active_choice] = choice_match.group(2).strip()
            elif active_choice:
                choices[active_choice] = clean_cell(choices[active_choice] + " " + line)
            else:
                qparts.append(line)
        text = clean_cell(" ".join(qparts))
        answer = clean_cell(" ".join(aparts))
        issues = []
        if not text or len(text) < 12:
            issues.append("Empty or unusually short question")
        if not answer:
            issues.append("Missing answer")
        if current["format"] == "Multiple Choice" and sum(bool(x) for x in choices.values()) != 4:
            issues.append("Missing multiple-choice options")
        if re.search(r"\b(?:figure|diagram|image|following graph|pictured|shown below)\b", text, re.I):
            issues.append("May reference a diagram; verify PDF")
        if text and answer:
            record = {
                "id": f"{stem}-{current['kind'].lower()}-{current['number']}",
                "category": canonical_category(current["category"]),
                "type": "Toss-up" if current["kind"] == "TOSSUP" else "Bonus",
                "format": current["format"], "number": current["number"],
                "question": text, "answer": answer, **{f"choice_{k}": v for k, v in choices.items()},
                "year": (re.search(r"(?:19|20)\d{2}", pdf_name).group(0) if re.search(r"(?:19|20)\d{2}", pdf_name) else DOE_YEAR.get(meta["set"], "Unknown")),
                "round": doc_round or "Unknown", "set": str(meta["set"]),
                "source_file": f"DOE Sample Set {meta['set']}/{pdf_name}",
                "source_page": str(current["page"]),
                "source_url": meta["url"], "source": "DOE NSB High School Sample Questions",
                "needs_review": "true" if issues else "false", "review_reasons": "; ".join(issues)
            }
            out.append(record)
        if issues:
            problems.append(f"{current['kind']} #{current['number']}: {'; '.join(issues)}")
        current = None

    for text, page in lines:
        # ROUND headings may provide missing metadata.
        rm = re.fullmatch(r"\s*ROUND\s+(\d+)\s*", text, re.I)
        if rm:
            doc_round = rm.group(1)
            continue
        # Suppress footers, page decorations and round labels.
        if NOISE_HEADER.fullmatch(text):
            continue
        km = KIND_HEADER.match(text)
        if km:
            flush()
            kind = "TOSSUP" if "TOSS" in km.group(1).upper() else "BONUS"
            continue
        hm = QUESTION_HEADER.match(text)
        if hm and (kind is not None or current is not None):
            flush()
            current = {"number": hm.group("number"), "kind": kind or "TOSSUP",
                       "category": hm.group("category"),
                       "format": "Multiple Choice" if "multiple" in hm.group("format").lower() else "Short Answer",
                       "page": page, "body": [hm.group("rest")] if hm.group("rest").strip() else []}
            continue
        if current is not None:
            current["body"].append(text)
    flush()
    page_count = len(doc)
    doc.close()
    # Older sets occasionally have header/footer variants: retain warning rather than claiming completeness.
    if not lines:
        problems.append("No extractable PDF text (scanned PDF or unsupported encoding)")
    if len(out) < 15:
        problems.append(f"Only {len(out)} answered questions detected; inspect original PDF")
    return out, problems, page_count


def download_doe_pdf(meta, cache_dir):
    import requests
    name = f"set{meta['set']:02d}_" + hashlib.sha1(meta["url"].encode()).hexdigest()[:12] + ".pdf"
    path = cache_dir / name
    if path.exists() and path.stat().st_size > 1000:
        data = path.read_bytes()
    else:
        last_err = None
        for attempt in range(3):
            try:
                resp = requests.get(meta["url"], timeout=(15, 65),
                                    headers={"User-Agent": "ScienceBowlPracticeTrainer/1.0"})
                resp.raise_for_status()
                data = resp.content
                if not data.startswith(b"%PDF"):
                    raise ValueError("URL did not return a PDF")
                temp = path.with_suffix(".part")
                temp.write_bytes(data)
                temp.replace(path)
                break
            except Exception as e:
                last_err = e
                time.sleep(1.5 * (attempt + 1))
        else:
            raise RuntimeError(f"PDF download failed: {last_err}")
    return data


def write_csv(path, records, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    with temp.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    temp.replace(path)


def import_doe_all(progress=None):
    """On-demand import; writes a separate merged supplemental bank + audit log."""
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import fitz  # raise a readable install error in UI if missing
    from bs4 import BeautifulSoup
    DOE_CACHE.mkdir(parents=True, exist_ok=True)
    html = requests.get(DOE_PAGE, timeout=(15, 40),
                        headers={"User-Agent": "Mozilla/5.0 ScienceBowlTrainer"})
    html.raise_for_status()
    links = get_doe_links(html.text)
    if not links:
        raise RuntimeError("The DOE page returned no round PDF links; source layout may have changed.")
    previous = read_csv(DOE_FILE) if DOE_FILE.exists() else []
    # Preserve successful previous imports across failures and reruns.
    existing = {str(q["id"]): q for q in previous if q.get("id")}
    report = []
    num_done = 0

    def one(meta):
        try:
            data = download_doe_pdf(meta, DOE_CACHE)
            parsed, issues, pages = parse_doe_pdf(data, meta)
            if not parsed:
                raise ValueError("No complete question/answer pairs recognized")
            return meta, parsed, issues, pages, "ok"
        except Exception as exc:
            return meta, [], [str(exc)], 0, "error"

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(one, x) for x in links]
        for future in as_completed(futures):
            meta, parsed, issues, pages, status = future.result()
            for q in parsed:
                existing[q["id"]] = q
            report.append({"set": meta["set"], "round": meta["round"],
                           "url": meta["url"], "status": status,
                           "questions": len(parsed), "pages": pages,
                           "warnings": " | ".join(issues[:15])[:2000]})
            num_done += 1
            if progress is not None:
                progress(num_done, len(links), len(existing), meta)
            if num_done % 15 == 0:
                write_csv(DOE_FILE, list(existing.values()), BANK_COLUMNS)
    write_csv(DOE_FILE, list(existing.values()), BANK_COLUMNS)
    write_csv(DOE_REPORT, sorted(report, key=lambda x: (int(x["set"]), int(x["round"] or 0))),
              ["set", "round", "url", "status", "questions", "pages", "warnings"])
    return len(links), len(existing), sum(r["status"] == "error" for r in report)

# -----------------------------------------------------------------------------
# APPLICATION STATE + DATABASE
# -----------------------------------------------------------------------------
PROGRESS_FILE = BASE / "practice_progress.json"
HISTORY_FILE = BASE / "practice_history.json"
BOOKMARK_FILE = BASE / "practice_bookmarks.json"
GENERATED_FRONTEND = BASE / ".science_bowl_player"


def read_csv(path):
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except (FileNotFoundError, OSError, csv.Error):
        return []


@st.cache_data(show_spinner=False)
def load_all_questions(paths_and_mtimes):
    # Primary user archive always wins where a question is identical.
    result, used_ids, seen_fingerprints = [], set(), set()
    for path_str, _mtime in paths_and_mtimes:
        for index, row in enumerate(read_csv(Path(path_str))):
            row = dict(row)
            if not clean_cell(row.get("question")) or not clean_cell(row.get("answer")):
                continue
            uid = clean_cell(row.get("id")) or f"{Path(path_str).stem}-row-{index}"
            if uid in used_ids:
                uid = uid + "-" + hashlib.sha1((str(index) + path_str).encode()).hexdigest()[:8]
            fp = fingerprint(row)
            if fp in seen_fingerprints:
                continue
            used_ids.add(uid)
            seen_fingerprints.add(fp)
            row["_id"] = uid
            row["category"] = canonical_category(row.get("category"))
            row.setdefault("source", "Your existing collection" if Path(path_str).name == "questions.csv" else "DOE samples")
            result.append(row)
    return result


def load_json(path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, type(default)) else default
    except (OSError, ValueError):
        return default


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def text_field(q, key, default="Unknown"):
    return clean_cell(q.get(key)) or default


def kind_of(q):
    typ = text_field(q, "type").casefold()
    return "BONUS" if "bonus" in typ else "TOSSUP"


def format_of(q):
    fmt = text_field(q, "format").casefold()
    return "MULTIPLE CHOICE" if "multiple" in fmt or any(clean_cell(q.get("choice_"+c)) for c in "wxyz") else "SHORT ANSWER"


def options_of(q):
    return [{"letter": c.upper(), "text": clean_cell(q.get("choice_"+c))}
            for c in "wxyz" if clean_cell(q.get("choice_"+c))]


def clean_history_entry(row):
    out = dict(row)
    out["category"] = canonical_category(out.get("category"))
    return out


def initialize():
    defaults = {
        "progress": load_json(PROGRESS_FILE, {}),
        "history": [clean_history_entry(r) for r in load_json(HISTORY_FILE, []) if isinstance(r, dict)],
        "bookmarks": load_json(BOOKMARK_FILE, {}),
        "queue": [], "position": 0, "session_id": uuid.uuid4().hex,
        "last_result": None, "speed": 3.0, "page": "Practice"
    }
    for name, value in defaults.items():
        if name not in st.session_state:
            st.session_state[name] = value


def create_session(selected):
    if not selected:
        st.warning("No matching questions found.")
        return
    st.session_state.queue = list(selected)
    st.session_state.position = 0
    st.session_state.session_id = uuid.uuid4().hex
    st.session_state.last_result = None
    st.session_state.pending_page = "Practice"
    st.rerun()


def practice_one(q):
    create_session([q])


def move_next():
    st.session_state.position += 1
    st.session_state.last_result = None
    st.rerun()


def mark_bookmark(q):
    id_ = q["_id"]
    if id_ in st.session_state.bookmarks:
        del st.session_state.bookmarks[id_]
    else:
        st.session_state.bookmarks[id_] = True
    save_json(BOOKMARK_FILE, st.session_state.bookmarks)


def record_attempt(event, q, pos, instance_id):
    if not isinstance(event, dict) or event.get("event") != "graded":
        return False
    if event.get("question_id") != q["_id"] or event.get("instance_id") != instance_id:
        return False
    if st.session_state.last_result and st.session_state.last_result.get("position") == pos:
        return False
    event_id = str(event.get("event_id") or "")
    if not event_id or any(h.get("event_id") == event_id for h in st.session_state.history):
        return False
    status = str(event.get("status") or "incorrect")
    if status not in {"correct", "incorrect", "timeout", "skipped"}:
        status = "incorrect"
    correct = event.get("correct") is True and status == "correct"

    def num(name, cap):
        try:
            return round(max(0, min(cap, float(event.get(name) or 0))), 2)
        except (TypeError, ValueError):
            return 0.0

    item = {
        "event_id": event_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session_id": st.session_state.session_id,
        "question_id": q["_id"],
        "category": text_field(q, "category"),
        "type": kind_of(q), "format": format_of(q),
        "year": text_field(q, "year"), "round": text_field(q, "round"),
        "question": q.get("question", ""), "official_answer": q.get("answer", ""),
        "your_answer": str(event.get("your_answer") or "")[:2000],
        "correct": correct, "status": status,
        "buzz_percent": num("buzz_percent", 100),
        "response_seconds": num("response_seconds", 1800),
        "answered_after_read": event.get("answered_after_read") is True,
        "source_file": q.get("source_file", ""),
        "source_url": q.get("source_url", "")
    }
    st.session_state.history.append(item)
    save_json(HISTORY_FILE, st.session_state.history)
    record = st.session_state.progress.setdefault(q["_id"], {"seen": 0, "correct": 0, "incorrect": 0})
    record["seen"] = int(record.get("seen", 0)) + 1
    record["correct" if correct else "incorrect"] = int(record.get("correct" if correct else "incorrect", 0)) + 1
    save_json(PROGRESS_FILE, st.session_state.progress)
    st.session_state.last_result = {**item, "position": pos}
    return True


def question_stats(question_id, history, progress):
    matching = [h for h in history if str(h.get("question_id")) == str(question_id)]
    totals = progress.get(question_id, {})
    attempts = max(int(totals.get("seen", 0)), len(matching))
    correct = max(int(totals.get("correct", 0)), sum(h.get("correct") is True for h in matching))
    buzzes = [float(h.get("buzz_percent", 0)) for h in matching if h.get("status") != "skipped"]
    return {"attempts": attempts, "correct": correct,
            "missed": max(0, attempts-correct),
            "accuracy": round(100*correct/attempts, 1) if attempts else None,
            "average_buzz": round(sum(buzzes)/len(buzzes), 1) if buzzes else None,
            "last_attempt": matching[-1].get("timestamp_utc", "") if matching else ""}


def build_analytics(questions, history, progress):
    lookup = {q["_id"]: q for q in questions}
    history_ids = defaultdict(list)
    for h in history:
        history_ids[str(h.get("question_id") or "")].append(h)
    totals = defaultdict(lambda: {"attempts": 0, "correct": 0, "buzzes": [], "times": [], "timeouts": 0, "unique": 0})
    for question_id in set(progress) | set(history_ids):
        q = lookup.get(question_id)
        events = history_ids.get(question_id, [])
        if q:
            cat = canonical_category(q.get("category"))
        elif events:
            cat = canonical_category(events[-1].get("category"))
        else:
            continue  # historical totals for unavailable question cannot be assigned a subject
        ps = progress.get(question_id) or {}
        a = max(int(ps.get("seen", 0)), len(events))
        c = max(int(ps.get("correct", 0)), sum(h.get("correct") is True for h in events))
        if not a:
            continue
        t = totals[cat]
        t["attempts"] += a
        t["correct"] += min(a, c)
        t["unique"] += 1
        for event in events:
            if event.get("status") == "timeout":
                t["timeouts"] += 1
            if event.get("status") not in {"skipped", None}:
                try:
                    t["buzzes"].append(float(event.get("buzz_percent", 0)))
                    t["times"].append(float(event.get("response_seconds", 0)))
                except (TypeError, ValueError):
                    pass
    result = []
    for category, t in totals.items():
        n=t["attempts"]
        result.append({"Subject": category, "Attempts": n, "Correct": t["correct"],
                       "Missed": n-t["correct"], "Accuracy (%)": round(t["correct"]*100/n, 1),
                       "Questions seen": t["unique"],
                       "Avg buzz (%)": round(sum(t["buzzes"])/len(t["buzzes"]), 1) if t["buzzes"] else None,
                       "Avg answer time (s)": round(sum(t["times"])/len(t["times"]), 1) if t["times"] else None,
                       "Timeouts": t["timeouts"]})
    return sorted(result, key=lambda s: (-s["Attempts"], s["Subject"]))


def history_csv(rows):
    buf = io.StringIO()
    if not rows:
        return b""
    cols = list(dict.fromkeys(k for row in rows for k in row))
    writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")


def question_google_url(question):
    return "https://www.google.com/search?q=" + quote_plus(clean_cell(question)[:1500])


def question_details(q, *, show_actions=True, show_answer=True, row_key="card", history=None):
    st.markdown(f"**{text_field(q, 'category')} · {kind_of(q)} · {format_of(q)}**")
    st.write(q.get("question", ""))
    opts = options_of(q)
    if opts:
        for o in opts:
            st.write(f"**{o['letter']})** {o['text']}")
    if show_answer:
        st.markdown("**Official answer**")
        st.success(q.get("answer") or "Answer unavailable")
    if history:
        stats = question_stats(q["_id"], history, st.session_state.progress)
        st.caption(f"Lifetime: {stats['attempts']} attempts · {stats['correct']} correct · {stats['missed']} missed · "
                   f"Average buzz: {str(stats['average_buzz'])+'%' if stats['average_buzz'] is not None else '—'}")
    if show_actions:
        c1, c2, c3 = st.columns(3)
        if c1.button("▶ Practice this", key=f"{row_key}_practice_{q['_id']}", use_container_width=True):
            practice_one(q)
        label = "★ Bookmarked" if q["_id"] in st.session_state.bookmarks else "☆ Bookmark"
        if c2.button(label, key=f"{row_key}_bookmark_{q['_id']}", use_container_width=True):
            mark_bookmark(q)
            st.rerun()
        c3.link_button("🔎 Search Google", question_google_url(q["question"]), use_container_width=True)
    info = []
    for col, name in [("year", "Year"), ("set", "Set"), ("round", "Round"),
                      ("number", "Number"), ("source_file", "Source"), ("source_page", "Page")]:
        if clean_cell(q.get(col)):
            info.append(f"{name}: {clean_cell(q[col])}")
    if info:
        st.caption(" · ".join(info))
    if q.get("source_url", "").startswith("https://science.osti.gov/"):
        st.markdown(f"[View original DOE PDF]({q['source_url']})")
    if str(q.get("needs_review", "")).lower() in ("true", "1", "yes"):
        st.warning("Extraction review: " + text_field(q, "review_reasons", "Verify against PDF"))


def is_flagged(q):
    return str(q.get("needs_review", "")).lower() in ("true", "1", "yes")

# -----------------------------------------------------------------------------
# APP UI
# -----------------------------------------------------------------------------

def prepare_reader():
    GENERATED_FRONTEND.mkdir(parents=True, exist_ok=True)
    file = GENERATED_FRONTEND / "index.html"
    if not file.exists() or file.read_text(encoding="utf-8") != FRONTEND_HTML:
        file.write_text(FRONTEND_HTML, encoding="utf-8")
    return components.declare_component("science_bowl_embedded_reader_pro_v3", path=str(GENERATED_FRONTEND))


st.set_page_config(page_title="Science Bowl Trainer Pro", page_icon="🧪", layout="wide")
reader = prepare_reader()
initialize()

primary = BASE / "output" / "questions.csv"
sources = [p for p in (primary, DOE_FILE) if p.exists()]
questions = load_all_questions(tuple((str(p), p.stat().st_mtime_ns) for p in sources)) if sources else []
lookup = {q["_id"]: q for q in questions}
# First-run convenience: open the local PDF importer when the bank is empty.
if not questions and st.session_state.page == "Practice":
    st.session_state.page = "Import local PDFs"
st.title("🧪 Science Bowl Trainer")
st.caption("Real-time buzzer · Spoken questions · Searchable question bank · Detailed missed-question review")

if "pending_page" in st.session_state:
    st.session_state.page = st.session_state.pop("pending_page")

with st.sidebar:
    pages = ["Practice", "Question bank", "History & analytics", "Import local PDFs", "Import DOE questions"]
    st.radio("Navigation", pages, key="page")
    st.divider()
    st.caption(f"**{len(questions):,} questions loaded**")
    if primary.exists():
        st.caption(f"Your collection: {len(read_csv(primary)):,} raw records")
    if DOE_FILE.exists():
        st.caption(f"DOE imported: {len(read_csv(DOE_FILE)):,} raw records")
    st.caption("Everything stays on your computer.")

attempts = sum(int(p.get("seen", 0)) for p in st.session_state.progress.values() if isinstance(p, dict))
correct_total = sum(int(p.get("correct", 0)) for p in st.session_state.progress.values() if isinstance(p, dict))
metrics = st.columns(4)
metrics[0].metric("Attempts", f"{attempts:,}")
metrics[1].metric("Correct", f"{correct_total:,}")
metrics[2].metric("Accuracy", f"{correct_total/attempts:.1%}" if attempts else "—")
metrics[3].metric("Question bank", f"{len(questions):,}")
st.divider()

if st.session_state.page == "Import local PDFs":
    st.subheader("📂 Import your local Science Bowl PDFs")
    st.write("Copy your **PDFs, DOCX, TXT or Markdown** files into the **`input`** folder, "
             "then click **Extract files into question bank**. "
             "Subfolders are supported, so you can copy your entire downloaded archive at once.")
    st.code(str(BASE / "input"), language="text")
    local_input = BASE / "input"
    local_input.mkdir(parents=True, exist_ok=True)
    local_files = [f for f in local_input.rglob("*") if f.is_file() and f.suffix.lower() in {".pdf", ".docx", ".txt", ".md"}]
    local_pdfs = sum(f.suffix.lower() == ".pdf" for f in local_files)
    col1, col2, col3 = st.columns(3)
    col1.metric("PDF files", f"{local_pdfs:,}")
    col2.metric("Other supported files", f"{len(local_files) - local_pdfs:,}")
    col3.metric("Already extracted", f"{len(read_csv(primary)):,}" if primary.exists() else "0")
    if not local_files:
        st.warning("No supported files found in `input/`. Copy your PDFs there before extracting.")
    st.caption("The extractor creates `output/questions.csv` and audit reports. "
               "It does **not** delete or reset your saved practice history or progress. "
               "But changing the input filenames or folder layout can change question IDs, "
               "so preserve the folder structure when re-importing.")
    if st.button("⚙ Extract files into question bank", type="primary", disabled=not local_files,
                 use_container_width=True):
        with st.spinner(f"Extracting questions from {len(local_files):,} files…"):
            try:
                result = subprocess.run(
                    [sys.executable, str(BASE / "extract_science_bowl.py"),
                     "--input", str(local_input), "--output", str(BASE / "output")],
                    cwd=str(BASE), capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=7200, check=False
                )
                st.session_state["local_import_log"] = (result.stdout + "\n" + result.stderr)[-24000:]
                st.session_state["local_import_success"] = result.returncode == 0
                if result.returncode == 0:
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Extraction failed. Expand the log below for details.")
            except subprocess.TimeoutExpired:
                st.error("Extraction exceeded the two-hour limit. Try smaller batches and check PDFs for corruption.")
            except Exception as exc:
                st.error(f"Could not start extractor: {type(exc).__name__}: {exc}")
    if "local_import_success" in st.session_state:
        if st.session_state.local_import_success:
            st.success("Local import finished. Open **Question bank** to browse or **Practice** to train.")
        if st.session_state.get("local_import_log"):
            with st.expander("Show last extraction log"):
                st.code(st.session_state.local_import_log, language="text")
    local_report = BASE / "output" / "file_report.csv"
    review_report = BASE / "output" / "questions_needing_review.csv"
    summary_file = BASE / "output" / "summary.json"
    if summary_file.exists():
        st.subheader("Last extraction summary")
        summary = load_json(summary_file, {})
        c1, c2, c3 = st.columns(3)
        c1.metric("Questions extracted", f"{int(summary.get('questions_extracted',0)):,}")
        c2.metric("Questions flagged for review", f"{int(summary.get('questions_needing_review',0)):,}")
        c3.metric("Files scanned", f"{int(summary.get('total_files_seen',0)):,}")
    if local_report.exists():
        audit = read_csv(local_report)
        anomalies = [r for r in audit if r.get("status") != "parsed" or clean_cell(r.get("details"))]
        if anomalies:
            st.warning(f"{len(anomalies)} files need attention or have extraction warnings. "
                       "Check the audit before assuming all questions were imported.")
            with st.expander("Files with warnings or errors"):
                st.dataframe(pd.DataFrame(anomalies), hide_index=True, use_container_width=True)
        st.download_button("Download file audit CSV", local_report.read_bytes(),
                           file_name="file_report.csv", mime="text/csv")
    if review_report.exists():
        st.download_button("Download questions needing review", review_report.read_bytes(),
                           file_name="questions_needing_review.csv", mime="text/csv")
    if primary.exists():
        st.download_button("Download local question bank CSV", primary.read_bytes(),
                           file_name="questions.csv", mime="text/csv")
    st.stop()

if st.session_state.page == "Import DOE questions":
    st.subheader("Import official DOE high-school sample sets")
    st.write("Import all round PDFs linked from the Department of Energy's **High School Sample Questions** page. "
             "The importer extracts question text, answer keys, subject, round type and options, "
             "while retaining a link to each original PDF.")
    st.link_button("Open the original DOE question index ↗", DOE_PAGE)
    st.warning("Some official sample answers are outdated, as DOE itself cautions. "
               "PDF parsing can also misread formulas, diagrams and uncommon layouts. "
               "Check the import report and source PDFs before trusting unfamiliar answers.")
    st.info("Install dependencies once in your VS Code terminal: "
            "`py -m pip install --upgrade streamlit pandas requests beautifulsoup4 pymupdf`")
    st.write("The import downloads **hundreds of PDFs**, so it can take several minutes. "
             "PDFs are cached; interrupted imports can be retried without starting from scratch. "
             "Your existing `output/questions.csv` is never changed.")
    if st.button("⬇ Import / resume all DOE sample rounds", type="primary"):
        bar = st.progress(0)
        progress_text = st.empty()
        def import_update(done, total, accumulated, meta):
            bar.progress(done/total)
            progress_text.caption(f"Processed {done}/{total} PDFs · {accumulated:,} questions · "
                                  f"Latest: Set {meta['set']}, Round {meta['round'] or '?'}")
        try:
            total_files, total_questions, failed = import_doe_all(import_update)
            st.success(f"Processed {total_files} PDF links. Imported {total_questions:,} question records; "
                       f"{failed} PDFs failed to import. See the report below.")
            st.cache_data.clear()
            st.rerun()
        except ImportError as exc:
            st.error(f"A Python dependency is missing: {exc}. Run the pip command above.")
        except Exception as exc:
            st.error(f"Import could not finish: {exc}")
    if DOE_REPORT.exists():
        st.subheader("Last import audit")
        audit = read_csv(DOE_REPORT)
        errors = [r for r in audit if r.get("status") == "error" or clean_cell(r.get("warnings"))]
        st.write(f"**{len(audit)} files checked · {len([r for r in audit if r.get('status')=='error'])} errors "
                 f"· {len(errors)} files with warnings/errors**")
        with st.expander("See file-by-file report", expanded=False):
            st.dataframe(pd.DataFrame(audit), use_container_width=True, hide_index=True)
        st.download_button("Download import audit CSV", DOE_REPORT.read_bytes(),
                           file_name="doe_import_report.csv", mime="text/csv")
    if DOE_FILE.exists():
        st.download_button("Download extracted DOE question CSV", DOE_FILE.read_bytes(),
                           file_name="doe_hs_questions.csv", mime="text/csv")
    st.stop()

if not questions:
    st.info("No questions loaded yet. Copy your PDFs into `input/`, then open **Import local PDFs** in the sidebar to extract them. You can also import the DOE sample sets separately.")
    st.stop()

if st.session_state.page == "Question bank":
    st.subheader("🔎 Search the question bank")
    search = st.text_input("Search question text, official answers, or source", placeholder="e.g. mitochondria, angular momentum, periodic table, Maxwell...")
    filter_cols = st.columns([2, 1, 1, 1])
    subjects = sorted({text_field(q,"category") for q in questions})
    sub = filter_cols[0].multiselect("Subjects", subjects, default=subjects)
    typ = filter_cols[1].selectbox("Type", ["All", "TOSSUP", "BONUS"])
    fmt = filter_cols[2].selectbox("Format", ["All", "MULTIPLE CHOICE", "SHORT ANSWER"])
    status = filter_cols[3].selectbox("Practice status", ["All", "Missed", "Not attempted", "Bookmarked", "Flagged"])
    src_choices = sorted({text_field(q, "source", "Unspecified") for q in questions})
    with st.expander("More search filters"):
        selected_sources = st.multiselect("Sources", src_choices, default=src_choices)
        all_years = sorted({text_field(q,"year") for q in questions})
        selected_years = st.multiselect("Years", all_years, default=all_years)
        search_answers = st.checkbox("Search within official answers", value=True)
    term = search.casefold().strip()
    filtered = []
    for q in questions:
        if text_field(q, "category") not in sub or text_field(q, "source", "Unspecified") not in selected_sources:
            continue
        if text_field(q,"year") not in selected_years or (typ != "All" and kind_of(q) != typ) or (fmt != "All" and format_of(q) != fmt):
            continue
        stats = st.session_state.progress.get(q["_id"], {})
        if status == "Missed" and int(stats.get("incorrect", 0)) <= 0:
            continue
        if status == "Not attempted" and int(stats.get("seen", 0)) > 0:
            continue
        if status == "Bookmarked" and q["_id"] not in st.session_state.bookmarks:
            continue
        if status == "Flagged" and not is_flagged(q):
            continue
        if term:
            columns = [q.get("question",""), q.get("source_file", ""), q.get("category", "")]
            if search_answers:
                columns.append(q.get("answer", ""))
            if term not in " ".join(columns).casefold():
                continue
        filtered.append(q)
    st.caption(f"{len(filtered):,} matching questions")
    a, b = st.columns(2)
    if a.button("▶ Practice a random 20 from results", disabled=not filtered, use_container_width=True):
        create_session(random.sample(filtered, min(20, len(filtered))))
    if b.button("★ Practice bookmarked results", disabled=not any(q["_id"] in st.session_state.bookmarks for q in filtered), use_container_width=True):
        pool = [q for q in filtered if q["_id"] in st.session_state.bookmarks]
        create_session(random.sample(pool, min(50, len(pool))))
    if filtered:
        page_size = 15
        total_pages = max(1, (len(filtered)+page_size-1)//page_size)
        current_page = st.number_input("Results page", min_value=1, max_value=total_pages, value=1)
        from_index = (int(current_page)-1)*page_size
        for i, q in enumerate(filtered[from_index:from_index+page_size], start=from_index+1):
            preview = clean_cell(q.get("question"))
            title = f"{i}. [{text_field(q, 'category')} · {kind_of(q)}] {preview[:105]}{'…' if len(preview)>105 else ''}"
            with st.expander(title):
                question_details(q, row_key="search", history=st.session_state.history)
    st.stop()

if st.session_state.page == "History & analytics":
    st.subheader("📊 Performance by subject")
    history = st.session_state.history
    stats = build_analytics(questions, history, st.session_state.progress)
    if stats:
        frame = pd.DataFrame(stats)
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.bar_chart(frame.set_index("Subject")[["Accuracy (%)"]])
        st.caption("Lifetime accuracy combines your existing progress file with detailed recorded attempts. "
                   "Buzz and response-time statistics use detailed saved attempts only.")
    else:
        st.info("Complete a few questions to populate subject statistics.")

    st.subheader("🔁 Review missed questions")
    missed_ids = set()
    for qid, record in st.session_state.progress.items():
        if isinstance(record, dict) and int(record.get("incorrect", 0)):
            missed_ids.add(qid)
    for row in history:
        if row.get("status") in {"incorrect", "timeout", "skipped"}:
            missed_ids.add(str(row.get("question_id")))
    missed_q = [lookup[id_] for id_ in missed_ids if id_ in lookup]
    missed_q.sort(key=lambda q: max((h.get("timestamp_utc", "") for h in history if h.get("question_id") == q["_id"]), default=""), reverse=True)
    if missed_q:
        cols = st.columns([3, 2, 2])
        missed_subjects = sorted({text_field(q, "category") for q in missed_q})
        review_cats = cols[0].multiselect("Missed subjects", missed_subjects, default=missed_subjects)
        latest_only = cols[1].checkbox("Still getting wrong", value=False,
                                      help="Only show questions whose latest saved attempt was incorrect, skipped or timed out")
        limit_cards = cols[2].selectbox("Show", [10, 25, 50, 100], index=1)
        missed_list = []
        for q in missed_q:
            if text_field(q,"category") not in review_cats:
                continue
            events = [h for h in history if h.get("question_id") == q["_id"]]
            if latest_only and events and events[-1].get("status") == "correct":
                continue
            missed_list.append(q)
        st.caption(f"{len(missed_list):,} missed questions match your filters")
        if st.button("▶ Review 20 missed questions", disabled=not missed_list):
            create_session(random.sample(missed_list, min(20, len(missed_list))))
        for index, q in enumerate(missed_list[:limit_cards], start=1):
            events = [e for e in history if e.get("question_id") == q["_id"]]
            stats = question_stats(q["_id"], history, st.session_state.progress)
            preview = clean_cell(q.get("question", ""))
            with st.expander(f"{index}. {text_field(q, 'category')} · {stats['missed']} missed / {stats['attempts']} attempts · {preview[:85]}…"):
                question_details(q, row_key="missed", history=history)
                if events:
                    st.markdown("**Your previous answers and performance**")
                    for h in reversed(events[-12:]):
                        when = str(h.get("timestamp_utc", "")).replace("T", " ")[:19]
                        st.write(f"**{when} UTC · {str(h.get('status','')).upper()}** — "
                                 f"Your answer: `{h.get('your_answer') or '(none)'}` · "
                                 f"Buzz: {h.get('buzz_percent', '—')}% · "
                                 f"Time: {h.get('response_seconds', '—')}s")
    else:
        st.info("No missed questions yet. Your old aggregate progress is included when question IDs still match.")

    st.subheader("📜 Full attempt history")
    if history:
        hist_subjects = sorted({canonical_category(h.get("category")) for h in history})
        hc, hs, hq = st.columns([2, 2, 2])
        filtered_cats = hc.multiselect("History subjects", hist_subjects, default=hist_subjects)
        filtered_status = hs.multiselect("Results", ["correct", "incorrect", "timeout", "skipped"],
                                          default=["correct", "incorrect", "timeout", "skipped"])
        history_search = hq.text_input("History search", placeholder="Question or your response")
        shown = [h for h in reversed(history)
                 if canonical_category(h.get("category")) in filtered_cats and h.get("status") in filtered_status and
                 (not history_search or history_search.casefold() in
                  (str(h.get("question", "")) + " " + str(h.get("your_answer", ""))).casefold())]
        st.caption(f"{len(shown)} matching attempts")
        a, b = st.columns(2)
        a.download_button("Export history CSV", history_csv(shown), "science_bowl_history.csv", "text/csv", use_container_width=True)
        b.download_button("Export history JSON", json.dumps(shown, indent=2, ensure_ascii=False),
                          "science_bowl_history.json", "application/json", use_container_width=True)
        histlimit = st.select_slider("Recent attempts to display", options=[10, 25, 50, 100, 250], value=25)
        for i, event in enumerate(shown[:histlimit]):
            q = lookup.get(str(event.get("question_id"))) or {
                **event, "_id": str(event.get("question_id")),
                "answer": event.get("official_answer", ""),
                "category": canonical_category(event.get("category")),
                "source_file": event.get("source_file", "")}
            stamp = str(event.get("timestamp_utc", ""))[:16].replace("T", " ")
            prompt_preview = clean_cell(event.get("question", ""))[:90]
            status_icon = "✅" if event.get("correct") else "❌"
            with st.expander(f"{status_icon} {stamp} · {text_field(q,'category')} · {prompt_preview}…"):
                question_details(q, row_key=f"history_{i}", history=history)
                st.markdown("**This attempt**")
                st.write(f"Your answer: **{event.get('your_answer') or '(no answer)'}**")
                st.write(f"Result: **{event.get('status', '—')}** · Buzz: **{event.get('buzz_percent', '—')}%** "
                         f"· Response time: **{event.get('response_seconds', '—')}s**")
        if len(shown) >= 2:
            ordered = list(reversed(shown))[-75:]
            recent = []
            for i in range(len(ordered)):
                seg = ordered[max(0, i-9):i+1]
                recent.append({"Attempt": i+1, "Last 10 accuracy (%)": round(100*sum(e.get("correct") is True for e in seg)/len(seg),1)})
            st.subheader("Recent accuracy trend")
            st.line_chart(pd.DataFrame(recent).set_index("Attempt"))
    else:
        st.info("Detailed history begins once you finish a question in this version.")
    st.stop()

# -----------------------------------------------------------------------------
# PRACTICE
# -----------------------------------------------------------------------------
st.subheader("🎯 Practice")
with st.expander("Choose practice settings", expanded=not bool(st.session_state.queue)):
    filter_cols = st.columns([2, 1, 1])
    cats = sorted({text_field(q,"category") for q in questions})
    years = sorted({text_field(q,"year") for q in questions})
    chosen_categories = filter_cols[0].multiselect("Subjects", cats, default=cats, key="practice_categories")
    chosen_types = filter_cols[1].multiselect("Type", ["TOSSUP", "BONUS"], default=["TOSSUP", "BONUS"])
    chosen_years = filter_cols[2].multiselect("Year", years, default=years)
    pcols = st.columns([2, 2, 1])
    practice_pool = pcols[0].selectbox("Question pool", ["All matching", "Only missed", "Never attempted", "Bookmarked"])
    count = pcols[1].slider("Session length", 1, 100, 20, step=1)
    flagged = pcols[2].checkbox("Include flagged", value=False)
    st.session_state.speed = st.slider("Reading rate (words/sec)", 1.0, 9.0, float(st.session_state.speed), 0.5)
    st.caption("Tossup: 5 seconds after reading/buzz · Bonus: 20 seconds. "
               "Voice, text visibility, and progress bar are controlled inside the player.")
    if st.button("▶ Start new randomized session", type="primary"):
        pool = []
        for q in questions:
            if (text_field(q,"category") not in chosen_categories or kind_of(q) not in chosen_types
                or text_field(q,"year") not in chosen_years or (is_flagged(q) and not flagged)):
                continue
            p = st.session_state.progress.get(q["_id"], {})
            if practice_pool == "Only missed" and not int(p.get("incorrect", 0)):
                continue
            if practice_pool == "Never attempted" and int(p.get("seen", 0)):
                continue
            if practice_pool == "Bookmarked" and q["_id"] not in st.session_state.bookmarks:
                continue
            pool.append(q)
        create_session(random.sample(pool, min(count, len(pool))))

queue = st.session_state.queue
pos = st.session_state.position
if not queue:
    st.info("Start a session using the settings above, or choose a question from the Question Bank tab.")
    st.stop()
if pos >= len(queue):
    st.success("🎉 Session complete! Go to History & analytics to review your results, or start another session.")
    st.stop()

q = queue[pos]
instance_id = f"{st.session_state.session_id}:{pos}"
saved = st.session_state.last_result
saved_here = saved if isinstance(saved, dict) and saved.get("position") == pos else None
st.progress(pos / len(queue))
st.subheader(f"Question {pos+1} of {len(queue)}")
st.caption(f"{text_field(q, 'category')} · {kind_of(q)} · {format_of(q)} · {text_field(q, 'year')}")

if saved_here:
    st.success(f"Saved: {saved_here['status']} · Buzz {saved_here['buzz_percent']}% · Answer time {saved_here['response_seconds']}s")
    if st.button("Next question →", type="primary", key=f"top_next_{instance_id}", use_container_width=True):
        move_next()

event = reader(question_id=q["_id"], instance_id=instance_id,
               question=q.get("question", ""), answer=q.get("answer", ""),
               subject=text_field(q,"category").upper(), kind=kind_of(q), format=format_of(q),
               options=options_of(q), words_per_second=float(st.session_state.speed),
               saved=saved_here, key=f"reader_{instance_id}", default=None)
if isinstance(event, dict):
    if event.get("event") == "graded" and record_attempt(event, q, pos, instance_id):
        st.rerun()
    if event.get("event") == "next" and event.get("instance_id") == instance_id and saved_here:
        move_next()

if saved_here:
    st.link_button("🔎 Search this question on Google", question_google_url(q["question"]))
    if st.button("Next question →", key=f"bottom_next_{instance_id}", use_container_width=True):
        move_next()

with st.expander("Source & question details"):
    st.write(f"File: {text_field(q, 'source_file')} · Page: {text_field(q, 'source_page')} · "
             f"Round: {text_field(q, 'round')} · Number: {text_field(q, 'number')}")
    if saved_here:
        question_details(q, row_key=f"source_{instance_id}", show_actions=False)
    if is_flagged(q):
        st.warning(text_field(q, "review_reasons", "Verify against source PDF"))
