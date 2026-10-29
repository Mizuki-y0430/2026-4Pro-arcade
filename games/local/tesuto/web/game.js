"use strict";
const $ = id => document.getElementById(id);
let token='', state=null, view='menu', selectedLevel=1, busy=false, rankRequest=0;
const fonts=['system-ui,"Meiryo",sans-serif','"Yu Mincho","MS Mincho",serif','"Meiryo","Arial Rounded MT Bold",sans-serif'];
const defaults={bg_rgb:[240,239,237],accent_rgb:[183,25,41],custom_time:45,custom_lives:3,font_idx:0};
const rgbHex=rgb=>'#'+rgb.map(v=>v.toString(16).padStart(2,'0')).join('');
const hexRgb=hex=>[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));
const levelTitle=title=>title.replace(/^Lv\.\d+:\s*/, '');
// Small line drawings keep the subject names as the main action targets.
const subjectIcons=[
 '<rect x="6" y="3" width="20" height="26" rx="2"/><path d="M11 9h10M11 15h4m-2-2v4m6-2h3M11 22l4 4m0-4-4 4m8-3h3m-3 3h3"/>',
 '<path d="M11 3h10m-8 0v17a5 5 0 0 0 10 0V3M13 15h10m-5 0v7" transform="translate(-2 0)"/>',
 '<circle cx="9" cy="16" r="7"/><path d="m21 9 9 14m0-14-9 14"/>',
 '<path d="M16 7C10 3 5 4 3 5v22c4-2 9-1 13 2 4-3 9-4 13-2V5c-3-1-8-2-13 2Zm0 0v22"/>',
 '<rect x="2" y="5" width="28" height="22" rx="2"/><text x="16" y="21" text-anchor="middle" fill="currentColor" stroke="none" font-size="12" font-weight="800" font-family="sans-serif">ABC</text>',
 '<ellipse cx="16" cy="16" rx="14" ry="5"/><ellipse cx="16" cy="16" rx="14" ry="5" transform="rotate(60 16 16)"/><ellipse cx="16" cy="16" rx="14" ry="5" transform="rotate(120 16 16)"/><circle cx="16" cy="16" r="2" fill="currentColor" stroke="none"/>',
 '<rect x="6" y="4" width="20" height="19" rx="1"/><path d="m6 23-4 5h28l-4-5m-13-12-3 3 3 3m6-6 3 3-3 3m-2-7-2 8"/>',
 '<rect x="7" y="7" width="18" height="18" rx="2"/><path d="M11 1v6m5-6v6m5-6v6M11 25v6m5-6v6m5-6v6M1 11h6m-6 5h6m-6 5h6m18-10h6m-6 5h6m-6 5h6"/>',
 '<path d="m12 3-1 5-4 1-4 6 3 4-1 5 6 4 5-3 5 1 5-5-2-5 2-5-5-5-5 1Z"/><circle cx="16" cy="16" r="5"/>',
 '<path d="M10 29V10l6-7 6 7v19M3 29V15h7m12 0h7v14M1 29h30M14 29v-8h4v8M6 19v2m0 3v2m20-7v2m0 3v2"/><circle cx="16" cy="12" r="3"/>'
];
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
 $('menu-time').textContent=state.settings.custom_time;
 $('menu-lives').textContent=state.settings.custom_lives>5?`♥ ×${state.settings.custom_lives}`:Array(state.settings.custom_lives).fill('♥').join(' ');
 $('menu-lives').setAttribute('aria-label',`ライフ${state.settings.custom_lives}`);
 for(const button of $('levels').children){
  const level=Number(button.dataset.level);
  button.disabled=busy;
  button.querySelector('strong').textContent=levelTitle(state.levels[level-1][0]);button.querySelector('small').textContent=state.levels[level-1][1];
  button.setAttribute('aria-label',`${level}：${levelTitle(state.levels[level-1][0])}`);button.title=state.levels[level-1][1];
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
async function chooseLevel(level){
 if(!state||busy||view!=='menu'||!Number.isInteger(level)||level<1||level>state.levels.length)return;
 selectedLevel=level;
 await start();
}
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
$('retry').onclick=start;
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
  if(/^\d$/.test(event.key)){event.preventDefault();if(!event.repeat)chooseLevel(event.key==='0'?10:Number(event.key));}
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
   const number=document.createElement('span');number.className='level-number';number.textContent=String(index+1).padStart(2,'0');number.setAttribute('aria-hidden','true');
   const icon=document.createElement('span');icon.className='level-icon';icon.setAttribute('aria-hidden','true');icon.innerHTML=`<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${subjectIcons[index]||subjectIcons[0]}</svg>`;
   const copy=document.createElement('span');copy.className='level-copy';
   const strong=document.createElement('strong');strong.textContent=levelTitle(title);const small=document.createElement('small');small.className='level-description';small.id=`level-description-${index+1}`;small.textContent=description;copy.append(strong,small);
   button.setAttribute('aria-describedby',small.id);
   const arrow=document.createElement('span');arrow.className='level-arrow';arrow.textContent='›';arrow.setAttribute('aria-hidden','true');button.append(number,icon,copy,arrow);
   button.onclick=()=>chooseLevel(index+1);$('levels').append(button);
   const option=document.createElement('option');option.value=index+1;option.textContent=title;$('rank-level').append(option);
  });
  accept(session.state);
  setInterval(async()=>{if(busy)return;try{accept(await request('state'));}catch(error){$('notice').textContent=error.message;}},200);
 }catch(error){$('notice').textContent=`起動できません：${error.message}`;}
})();
