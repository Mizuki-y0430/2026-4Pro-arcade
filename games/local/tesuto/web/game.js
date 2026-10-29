"use strict";
const $ = id => document.getElementById(id);
let token='', state=null, view='menu', selectedLevel=1, busy=false, rankRequest=0;
const fonts=['system-ui,"Meiryo",sans-serif','"Yu Mincho","MS Mincho",serif','"Meiryo","Arial Rounded MT Bold",sans-serif'];
const defaults={bg_rgb:[240,239,237],accent_rgb:[183,25,41],custom_time:45,custom_lives:3,font_idx:0};
const rgbHex=rgb=>'#'+rgb.map(v=>v.toString(16).padStart(2,'0')).join('');
const hexRgb=hex=>[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));
function theme(settings){
 document.documentElement.style.setProperty('--bg',`rgb(${settings.bg_rgb.join(',')})`);
 document.documentElement.style.setProperty('--accent',`rgb(${settings.accent_rgb.join(',')})`);
 document.documentElement.style.setProperty('--font',fonts[settings.font_idx]);
}
async function request(path,data){
 const response=await fetch('/api/'+path,{method:data===undefined?'GET':'POST',headers:{'X-Mole-Token':token,'Content-Type':'application/json'},body:data===undefined?undefined:JSON.stringify(data),cache:'no-store'});
 const result=await response.json();if(!response.ok)throw new Error(result.error||'操作できませんでした。');return result;
}
function accept(next){
 if(state&&next.stamp<state.stamp)return;
 const previous=state?.phase;state=next;
 if(next.phase==='playing')view='play';
 else if(next.phase==='result'&&previous==='playing'){view='result';$('name').value='';setTimeout(()=>$('name').focus(),0);}
 draw();
}
async function action(path,data={},after){
 if(busy||!token)return;busy=true;$('notice').textContent='';draw();
 try{accept(await request(path,data));if(after)await after();}
 catch(error){$('notice').textContent=error.message;}
 finally{busy=false;draw();}
}
function show(next){view=next;draw();}
function draw(){
 if(!state)return;
 for(const id of ['menu','play','result','settings','ranking'])$(id).hidden=id!==view;
 $('menu-button').hidden=view==='menu'||view==='settings';$('menu-button').disabled=busy;
 $('menu-button').textContent=state.phase==='playing'?'中断してメニュー':'メニューへ';
 if(view!=='settings')theme(state.settings);
 $('start').disabled=busy;
 $('rules').textContent=`${state.settings.custom_time}秒 ／ ライフ${state.settings.custom_lives} ／ 不正解は−50点`;
 for(const button of $('levels').children){
  const level=Number(button.dataset.level);
  button.classList.toggle('selected',level===selectedLevel);button.setAttribute('aria-pressed',String(level===selectedLevel));
  button.querySelector('strong').textContent=state.levels[level-1][0];button.querySelector('small').textContent=state.levels[level-1][1];
  $('rank-level').options[level-1].textContent=state.levels[level-1][0];
 }
 $('time').textContent=Math.ceil(state.time_left);$('score').textContent=state.score;
 $('lives').textContent=`♥ ${state.lives}`;$('level-name').textContent=state.levels[state.level-1][0];
 $('question').textContent=state.question;$('feedback').textContent=state.feedback;
 $('feedback').dataset.tone=state.feedback.startsWith('正解！')?'correct':state.feedback.startsWith('おしい！')?'miss':'normal';
 for(let hole=0;hole<state.hole_count;hole++){
  const mole=state.moles.find(m=>m.hole===hole),button=$('mole-'+hole);
  button.hidden=!mole;button.disabled=busy||!mole||mole.hit;
  button.classList.toggle('hit',Boolean(mole?.hit));
  if(mole){const answer=button.querySelector('.answer');answer.textContent=mole.value;button.classList.toggle('word-answer',!/^[−+\-]?\d+(\.\d+)?$/.test(mole.value)||mole.value.length>5);button.setAttribute('aria-label',`穴${hole+1}：${mole.value}`);button.dataset.wave=state.wave;}
 }
 $('result-stats').textContent=`${state.levels[state.level-1][0]} ／ ${state.score}点 ／ 残り${state.time_left.toFixed(1)}秒 ／ ライフ${state.lives}`;
 $('submit').disabled=busy||state.submitted;$('submit').textContent=state.submitted?'登録しました ✓':'ランキングに登録';
 $('name').disabled=state.submitted;$('retry').disabled=busy;
}
async function menu(){await action('stop',{},()=>show('menu'));}
async function start(){await action('start',{level:selectedLevel});}
function settingsData(){return{bg_rgb:hexRgb($('bg-color').value),accent_rgb:hexRgb($('accent-color').value),custom_time:Number($('custom-time').value),custom_lives:Number($('custom-lives').value),font_idx:Number($('font').value)};}
function fillSettings(settings){
 $('bg-color').value=rgbHex(settings.bg_rgb);$('accent-color').value=rgbHex(settings.accent_rgb);
 $('custom-time').value=settings.custom_time;$('custom-lives').value=settings.custom_lives;$('font').value=settings.font_idx;theme(settings);
}
function openSettings(){if(!state||busy)return;fillSettings(state.settings);show('settings');}
async function saveSettings(){if(!$('settings-form').reportValidity())return;await action('settings',settingsData(),()=>show('menu'));}
async function loadRankings(){
 const revision=++rankRequest;
 try{
  const result=await request(`rankings?level=${$('rank-level').value}&sort=${$('rank-sort').value}`);
  if(revision!==rankRequest)return;
  $('rank-rows').replaceChildren();$('rank-empty').hidden=result.entries.length>0;
  result.entries.forEach((entry,index)=>{
   const row=document.createElement('tr');
   for(const value of [index+1,entry.name,entry.score,`${Number(entry.time_left||0).toFixed(1)}秒`,entry.lives||0]){const cell=document.createElement('td');cell.textContent=value;row.append(cell);}
   $('rank-rows').append(row);
  });
 }catch(error){$('notice').textContent=error.message;}
}
async function openRanking(){if(!state||busy)return;$('rank-level').value=selectedLevel;show('ranking');await loadRankings();}
function buildHoles(count){for(let i=0;i<count;i++){
 const hole=document.createElement('div');hole.className='hole';
 const button=document.createElement('button');button.id='mole-'+i;button.className='mole';button.hidden=true;
 const face=document.createElement('span');face.className='mole-face';face.setAttribute('aria-hidden','true');
 const answer=document.createElement('span');answer.className='answer';button.append(face,answer);
 button.addEventListener('click',()=>action('hit',{hole:i,wave:Number(button.dataset.wave)}));
 hole.append(button);$('holes').append(hole);
}}
$('start').onclick=start;$('retry').onclick=start;
$('menu-button').onclick=menu;$('result-menu').onclick=menu;$('rank-menu').onclick=menu;
$('settings-button').onclick=openSettings;$('ranking-button').onclick=openRanking;
$('name-form').onsubmit=event=>{event.preventDefault();action('submit',{name:$('name').value},async()=>{show('ranking');$('rank-level').value=state.level;await loadRankings();});};
$('settings-form').onsubmit=event=>{event.preventDefault();saveSettings();};
$('settings-form').oninput=()=>theme(settingsData());
$('reset-colors').onclick=()=>fillSettings({...settingsData(),bg_rgb:defaults.bg_rgb,accent_rgb:defaults.accent_rgb});
$('reset-settings').onclick=()=>fillSettings(defaults);
$('rank-level').onchange=loadRankings;$('rank-sort').onchange=loadRankings;
$('clear-rankings').onclick=()=>$('clear-dialog').showModal();
$('cancel-clear').onclick=()=>$('clear-dialog').close();
$('confirm-clear').onclick=()=>{$('clear-dialog').close();action('clear',{},loadRankings);};
document.addEventListener('keydown',event=>{
 if($('clear-dialog').open)return;
 if(event.key==='Escape'){event.preventDefault();event.stopPropagation();if(view==='settings')saveSettings();else menu();return;}
 if(event.target.matches('input,select,textarea')||!state||busy)return;
 if(view==='menu'){
  if(/^\d$/.test(event.key)){selectedLevel=event.key==='0'?10:Number(event.key);draw();}
  else if(event.code==='Space'){event.preventDefault();start();}
  else if(event.key.toLowerCase()==='s')openSettings();
  else if(event.key.toLowerCase()==='r')openRanking();
 }else if(view==='ranking'){
  if(/^\d$/.test(event.key)){$('rank-level').value=event.key==='0'?10:Number(event.key);loadRankings();}
  else if(event.code==='Space'){event.preventDefault();menu();}
 }
});
(async()=>{
 try{
  const session=await request('session');token=session.token;
  buildHoles(session.state.hole_count);
  session.state.levels.forEach(([title,description],index)=>{
   const button=document.createElement('button');button.className='level';button.dataset.level=index+1;
   const strong=document.createElement('strong');strong.textContent=title;const small=document.createElement('small');small.textContent=description;button.append(strong,small);
   button.onclick=()=>{selectedLevel=index+1;draw();};$('levels').append(button);
   const option=document.createElement('option');option.value=index+1;option.textContent=title;$('rank-level').append(option);
  });
  accept(session.state);
  setInterval(async()=>{if(busy)return;try{accept(await request('state'));}catch(error){$('notice').textContent=error.message;}},200);
 }catch(error){$('notice').textContent=`起動できません：${error.message}`;}
})();
