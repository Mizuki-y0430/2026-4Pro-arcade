"use strict";
const $ = id => document.getElementById(id);
// Final approved single-sheet guides. Keep the text diagrams as an image-error fallback.
const guidePosters = new Set([
  "kosen-survivor", "balloon-hunter", "yuugure-fishing",
  "brain-mole", "realtime-chess", "realtime-shogi"
]);
function loadGuidePoster(game) {
  if (!guidePosters.has(game.id)) return;
  const image = $("guide-poster-image"), link = $("guide-poster-link");
  const source = `/showcase/assets/${game.id}-rules-poster.png`;
  link.href = source;
  link.setAttribute("aria-label", `${game.title}の操作とルールの画像を拡大する（別タブ）`);
  image.alt = `${game.title}の操作とルール。文章での説明は、この下の「詳しいルール・その他の操作を見る」から確認できます。`;
  image.onload = () => {
    $("guide-poster").hidden = false;
    $("rules-sections").hidden = true;
    document.body.classList.add("poster-page");
  };
  image.onerror = () => {
    $("guide-poster").hidden = true;
    $("rules-sections").hidden = !illustratedGuides[game.id];
    document.body.classList.remove("poster-page");
  };
  image.src = source;
}
function showItems(id, items) {
  $(id).replaceChildren(...items.map(text => {const item=document.createElement("li");item.textContent=text;return item;}));
}
// All built-in guides use the same contract. See RULES_FORMAT.md.
const illustratedGuides = {
  "kosen-survivor": {
    summary:"単位を集めて、進級・卒業を目指すスネークゲーム。",
    goal:{title:"3年生85・4年生125・5年生167単位！",copy:"通常カード1枚で＋5単位。ボーナスは＋10単位。選んだ学年の目標以上でクリアです。",art:"credits"},
    steps:[
      {title:"学年を選んで開始",copy:"3・4・5年生から選び、「挑戦する」で始めよう。",art:"grades",inputs:["クリック・タップ","Space / Enter"]},
      {title:"方向を変えて単位へ",copy:"矢印キー・WASD、または画面の方向ボタンで移動。真後ろには曲がれません。",art:"snake",inputs:["↑ ↓ ← →","W A S D","方向ボタン"]},
      {title:"落単と壁をよける",copy:"点滅する札は出現予告。矢印の向きに動く落単をよけよう。",art:"hazard",inputs:["↑ ↓ ← →","方向ボタン"]}
    ],
    finish:[{title:"目標に届けばクリア",copy:"選んだ学年の目標単位数以上を集めよう。",mark:"✓"},{title:"落単7単位・壁・自分の体で終了",copy:"落単は6単位までOK。落単の札が胴体に当たるのはセーフです。",mark:"!"}]
  },
  "balloon-hunter": {
    summary:"30秒間で風船を割って、できるだけ高得点を目指そう。",
    goal:{title:"小さい風船ほど高得点！",copy:"小は3点・中は2点・大は1点。色に関係なく、大きさで得点が決まります。",art:"balloon-points"},
    steps:[
      {title:"スタートする",copy:"スタートボタンかEnterで、30秒チャレンジ開始。",art:"start",inputs:["クリック・タップ","Enter"]},
      {title:"風船をねらう",copy:"空に出てくる風船を見つけよう。小さい風船が高得点です。",art:"balloons",inputs:["マウス・指でねらう"]},
      {title:"押して割る",copy:"風船をクリック・タップ。続けて割って、得点を伸ばそう。",art:"balloon-hit",inputs:["クリック・タップ"]}
    ],
    finish:[{title:"30秒で結果発表",copy:"終了までに集めた得点が、その回の記録になります。",mark:"⏱"},{title:"もう一度挑戦できる",copy:"結果画面のスタートボタンで、次の30秒に挑戦しよう。",mark:"↻"}]
  },
  "yuugure-fishing": {
    summary:"動く針を黄色のエリアで止めて、魚を釣り上げよう。",
    goal:{title:"60秒で、魚の得点を集めよう！",copy:"アジ10点・サバ15点・タイ25点・カレイ40点・キンメダイ100点。難しい魚ほど成功エリアが狭くなります。",art:"fish"},
    steps:[
      {title:"開始すると自動で投げる",copy:"「釣りを始める」かSpace・Enterで開始。魚がかかるのを待とう。",art:"fishing-cast",inputs:["クリック・タップ","Space / Enter"]},
      {title:"黄色の中で合わせる",copy:"HITしたら5秒以内に1回。針が黄色のエリアに来たら止めよう。",art:"timing",inputs:["Enter","合わせるボタン"]},
      {title:"次の仕掛けも自動",copy:"成功・失敗の約1.4秒後に自動で投げ直します。Spaceなら待たずに次へ。",art:"recast",inputs:["投げ直しは自動","Spaceですぐ次へ"]}
    ],
    finish:[{title:"60秒で結果発表",copy:"釣れた匹数と合計得点を表示します。",mark:"⏱"},{title:"外すか5秒で魚が逃げる",copy:"その魚は失敗ですが、ゲームは続きます。次の魚をねらおう。",mark:"!"}]
  },
  "brain-mole": {
    summary:"4匹の中から、問題の正解を持つモグラを選ぼう。",
    goal:{title:"正解で＋100点！",copy:"不正解は−50点とライフ−1。スコアは0点未満になりません。",art:"mole-correct"},
    steps:[
      {title:"分野を押して開始",copy:"遊びたい分野を押すと、そのまま開始。数字キー1〜9・0でも選べます。",art:"subjects",inputs:["クリック・タップ","1〜9 / 0"]},
      {title:"問題と答えを見る",copy:"上の問題を読み、4匹が持つ答えの中から正解を探そう。",art:"mole-question",inputs:["問題と答えを確認"]},
      {title:"正解のモグラを押す",copy:"答えを持つモグラを押して回答。正解したら次の問題へ進もう。",art:"mole-hit",inputs:["クリック・タップ","Tab → Enter"]}
    ],
    finish:[{title:"時間切れ・ライフ0で終了",copy:"標準は45秒・ライフ3。設定から変更できます。",mark:"⏱"},{title:"結果はランキングに登録",copy:"結果画面で名前を入れて登録。再挑戦や分野の選び直しもできます。",mark:"✓"}]
  },
  "realtime-chess": {
    summary:"白の駒を動かして、赤のAIとリアルタイム対戦。",
    goal:{title:"相手のキングをチェックメイト！",copy:"相手のキングが、王手から逃げられない状態になれば勝ちです。",art:"chess-goal"},
    steps:[
      {title:"スタートする",copy:"3秒のカウントダウンで開始。最初は「はじめて」で、AIは約3秒ごとに動きます。",art:"start",inputs:["スタートボタン"]},
      {title:"白い駒を選ぶ",copy:"自分の白い駒を選ぶと、動ける場所に赤い印が出ます。",art:"chess-select",inputs:["クリック・タップ","矢印キー → Enter"]},
      {title:"印のマスへ動かす",copy:"移動先を押して決定。自分の待ち時間は標準0.5秒です。",art:"chess-move",inputs:["クリック・タップ","矢印キー → Enter"]}
    ],
    finish:[{title:"相手を詰ませると勝ち",copy:"自分のキングが詰むと負け。王手ではなく、動ける手がない場合は引き分けです。",mark:"✓"},{title:"考えている間もAIは動く",copy:"持ち時間の制限はありません。停止ボタン・Q・Escで対局を止められます。",mark:"!"}]
  },
  "realtime-shogi": {
    summary:"相手の手を待たずに指せる、リアルタイムの将棋。",
    goal:{title:"相手の玉を詰ませよう！",copy:"相手の玉が、王手から逃げられない状態になれば勝ちです。",art:"shogi-goal"},
    steps:[
      {title:"スタートする",copy:"スタートボタンを押し、3秒のカウントダウン後に開始。あなたは下側の先手です。",art:"start",inputs:["スタートボタン"]},
      {title:"自分の駒を選ぶ",copy:"自分の駒を押すと、動けるマスに緑の印が出ます。",art:"shogi-select",inputs:["クリック・タップ","矢印キー → Enter"]},
      {title:"印のマスへ動かす",copy:"移動先を押して決定。持ち駒も、選んで空いたマスへ打てます。",art:"shogi-move",inputs:["クリック・タップ","矢印キー → Enter"]}
    ],
    finish:[{title:"相手の玉を詰ませると勝ち",copy:"自分の玉が詰むと負け。同じ局面が4回で千日手。ただし連続王手などの例外があります。",mark:"✓"},{title:"相手を待たずに指せる",copy:"自分の待ち時間が終われば次の手へ。停止ボタン・Q・Escで止められます。成りは表示から選びます。",mark:"!"}]
  }
};
const ink="#20272c",red="#ed243e",gold="#ffd449";
const label=(x,y,value,size=17,color=ink)=>`<text x="${x}" y="${y}" text-anchor="middle" font-size="${size}" font-weight="800" fill="${color}">${value}</text>`;
const arrow=(x,y)=>`<path d="M${x} ${y}h30m-8-7 8 7-8 7" fill="none" stroke="${red}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>`;
const cursor=(x,y)=>`<path d="m${x} ${y} 0 29 8-7 7 14 7-4-7-12 11-1Z" fill="#fff" stroke="${ink}" stroke-width="2.5" stroke-linejoin="round"/>`;
const panel=(x,y,w,h,fill="#fff")=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="5" fill="${fill}" stroke="${ink}" stroke-width="2"/>`;
function balloon(x,y,r){return `<ellipse cx="${x}" cy="${y}" rx="${r}" ry="${r*1.12}" fill="${red}" stroke="${ink}" stroke-width="2.5"/><path d="M${x} ${y+r*1.12}q-10 12 0 19" fill="none" stroke="${ink}" stroke-width="2"/>`;}
function mole(x,y,value,correct=false){return `<path d="M${x-22} ${y}v-21c0-31 44-31 44 0v21" fill="#bb8b60" stroke="#69472f" stroke-width="2"/><circle cx="${x-8}" cy="${y-26}" r="2.5" fill="${ink}"/><circle cx="${x+8}" cy="${y-26}" r="2.5" fill="${ink}"/><ellipse cx="${x}" cy="${y-18}" rx="6" ry="4" fill="#edd1aa"/>${panel(x-23,y-10,46,27,correct?"#fff0a6":"#fff")}${label(x,y+10,value,21)}`;}
function boardArt(shogi,moved){
 let body="";for(let r=0;r<3;r++)for(let c=0;c<5;c++)body+=`<rect x="${30+c*34}" y="${6+r*32}" width="34" height="32" fill="${shogi?'#eed1a0':(r+c)%2?'#343a40':'#fff'}" stroke="#8b8377" stroke-width="1"/>`;
 const color=shogi?'#349b57':red;body+=`<rect x="65" y="71" width="32" height="30" fill="none" stroke="${red}" stroke-width="3"/>`;
 for(const x of (shogi?[81]:[81,115]))body+=`<circle cx="${x}" cy="54" r="5" fill="${color}"/>`;
 if(shogi)body+=`<path d="m70 ${moved?31:63} 11-5 11 5v29H70Z" fill="#f6d59b" stroke="${ink}" stroke-width="2"/>${label(81,moved?51:83,'歩',17)}`;
 else body+=label(81,moved?65:96,'♙',36);
 if(moved)body+=`<path d="M111 84V48m-6 7 6-7 6 7" stroke="${red}" fill="none" stroke-width="3"/>`;
 else body+=cursor(86,70);
 return [body,shogi?(moved?'緑の印のマスへ歩を1マス進める例':'先手の歩を選ぶと、1マス前に緑の印が出る例'):(moved?'白のポーンを赤い印のある前のマスへ進める例':'白のポーンを選び、移動先に赤い印が出る例')];
}
function diagramContent(kind){
 switch(kind){
 case 'start':return [panel(44,28,152,52)+`<path d="m61 43 0 22 15-11Z" fill="${gold}"/>`+label(134,61,'スタート',21)+cursor(159,66),'スタートボタンを押して始める'];
 case 'grades':return [[['3年',85],['4年',125],['5年',167]].map(([n,g],i)=>panel(9+i*77,17,68,73,i===0?'#fff0a6':'#fff')+label(43+i*77,45,n,18)+label(43+i*77,75,g+'',23)).join('')+cursor(52,65),'3年85・4年125・5年167単位の学年選択から選ぶ'];
 case 'credits':return [panel(12,24,67,63)+label(45,48,'単位',19)+label(45,75,'+5',24,red)+arrow(91,57)+panel(133,24,94,63,'#fff0a6')+label(180,49,'目標へ',18)+label(180,75,'進級・卒業',15),'1枚5単位のカードを集めて目標へ進む'];
 case 'snake':return [`<path d="M28 77h40V49h65" fill="none" stroke="${ink}" stroke-width="18" stroke-linejoin="round"/><path d="M28 77h40V49h65" fill="none" stroke="${red}" stroke-width="12" stroke-linejoin="round"/>${panel(122,37,25,25)}<circle cx="139" cy="44" r="2.5" fill="${ink}"/>${panel(177,31,40,40)}${label(197,57,'+5',19,red)}${arrow(146,49)}`,'方向を変えながらスネークの頭を単位カードへ近づける'];
 case 'hazard':return [panel(22,30,56,56,'#fff0a6')+label(50,65,'!',34,red)+`<path d="M99 79h50V30h58" fill="none" stroke="${red}" stroke-width="10" stroke-linejoin="round"/>`+label(51,103,'落単',16)+label(182,101,'よけよう',16),'落単の札を避けて曲がるスネークの例'];
 case 'balloon-points':return [balloon(43,36,13)+balloon(117,36,21)+balloon(194,36,28)+label(43,103,'小 3点',17)+label(117,103,'中 2点',17)+label(194,103,'大 1点',17),'小さい風船は3点、中は2点、大は1点。同じ色でも大きさで得点が違う'];
 case 'balloons':return [balloon(53,32,15)+balloon(118,58,26)+balloon(191,35,18)+`<circle cx="53" cy="32" r="25" stroke="${ink}" stroke-dasharray="4 4" fill="none" stroke-width="2"/>`,'大小の風船のうち小さい風船をねらう例'];
 case 'balloon-hit':return [balloon(91,44,26)+cursor(99,52)+panel(158,17,68,34,'#fff0a6')+label(192,41,'+2点',19),'風船をクリックまたはタップして得点を得る例'];
 case 'fish':case 'fishing-cast':return [`<path d="M8 85h224m-210 9h50m110 7h42" stroke="#75bac9" stroke-width="3"/><path d="M28 82 91 14m0 0h64v47" stroke="${ink}" stroke-width="3" fill="none"/><ellipse cx="156" cy="65" rx="7" ry="15" fill="${red}" stroke="${ink}" stroke-width="2"/>${kind==='fish'?`<path d="m177 72-14-10v25l14-8q28 17 40-6-15-22-40-1Z" fill="#69adc5" stroke="${ink}" stroke-width="2"/><circle cx="204" cy="69" r="2" fill="${ink}"/>`:label(166,31,'自動で投げる',17)}`,kind==='fish'?'魚を釣り、60秒で得点を集める目標を示す魚とウキの図':'開始すると自動で竿を投げ、ウキに魚がかかるのを待つ'];
 case 'timing':return [panel(15,37,210,30,'#343a40')+`<rect x="132" y="39" width="45" height="26" fill="${gold}"/><path d="M151 25v54" stroke="#fff" stroke-width="8"/><path d="M151 25v54" stroke="${red}" stroke-width="4"/>`+label(155,18,'ここで止める',16)+label(120,102,'Enter ／ 合わせる',18),'動く赤い針が黄色の成功エリアにあるとき、Enterか合わせるボタンを押す'];
 case 'recast':return [panel(10,28,78,55,'#fff0a6')+label(49,53,'結果',20)+label(49,73,'成功・失敗',12)+arrow(99,55)+panel(143,28,87,55)+label(186,51,'自動で',16)+label(186,72,'次の魚へ',16),'成功・失敗の結果表示後、自動で次の魚へ進む'];
 case 'subjects':return [panel(19,18,202,31,'#fff0a6')+label(113,40,'01 基礎数学',18)+panel(19,60,202,31)+label(113,82,'02 基礎理科',18)+cursor(173,37),'挑戦する分野のボタンを押すと、そのままゲームが始まる'];
 case 'mole-correct':case 'mole-question':case 'mole-hit':return [label(120,29,'3 + 4 = ?',22)+[6,7,8,9].map((n,i)=>mole(31+i*59,85,n,kind!=='mole-question'&&n===7)).join('')+(kind==='mole-hit'?cursor(94,72):kind==='mole-correct'?label(191,44,'+100',19,red):''),'問題3足す4に対し、4匹の持つ6・7・8・9から正解の7を選ぶ例'];
 case 'chess-select':return boardArt(false,false);
 case 'chess-move':return boardArt(false,true);
 case 'shogi-select':return boardArt(true,false);
 case 'shogi-move':return boardArt(true,true);
 case 'chess-goal':return [panel(24,14,73,83)+label(60,74,'♚',52,red)+arrow(108,54)+label(191,51,'王手から',19)+label(191,79,'逃げられない',16),'相手のキングが王手から逃げられない状態を目指す。これは盤面の再現ではなく目標の模式図'];
 case 'shogi-goal':return [`<path d="m33 29 30-13 30 13v66H33Z" fill="#efd1a0" stroke="${ink}" stroke-width="3"/>${label(63,75,'玉',39)}${arrow(107,54)}${label(188,51,'王手から',19)}${label(188,79,'逃げられない',17)}`,'相手の玉が王手から逃げられない状態を目指す。これは盤面の再現ではなく目標の模式図'];
 default:return ['', ''];
 }
}
function makeDiagram(kind){
 const [body,alt]=diagramContent(kind),figure=document.createElement('figure');figure.className='instruction-diagram';
 figure.innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 112" role="img" aria-label="${alt}">${body}</svg>`;
 return figure;
}
function renderIllustratedGuide(guide){
 $('goal-title').textContent=guide.goal.title;$('goal-copy').textContent=guide.goal.copy;$('goal-diagram').replaceChildren(makeDiagram(guide.goal.art));
 const steps=guide.steps.map((step,index)=>{
  const item=document.createElement('li');item.className='operation-step';
  const title=document.createElement('h3');title.className='step-title';const number=document.createElement('span');number.className='step-number';number.textContent=String(index+1).padStart(2,'0');title.append(number,document.createTextNode(step.title));
  const copy=document.createElement('p');copy.className='step-copy';copy.textContent=step.copy;
  const tags=document.createElement('div');tags.className='input-tags';
  for(const input of step.inputs){const tag=document.createElement(/^(Space|Enter|Tab|↑|W A S D|1〜9|矢印キー)/.test(input)?'kbd':'span');tag.textContent=input;tags.append(tag);}
  item.append(title,makeDiagram(step.art),copy,tags);return item;
 });
 $('operation-steps').replaceChildren(...steps);
 $('finish-list').replaceChildren(...guide.finish.map(end=>{
  const item=document.createElement('li'),mark=document.createElement('span'),body=document.createElement('div'),title=document.createElement('strong');item.className=end.mark==='!'?'finish-warning':'';mark.className='finish-mark';mark.setAttribute('aria-hidden','true');mark.textContent=end.mark;title.textContent=end.title;body.append(title,document.createTextNode(end.copy));item.append(mark,body);return item;
 }));
}
async function loadRules() {
  try {
    const response = await fetch("/api/games", {cache: "no-store"});
    if (!response.ok) throw new Error("ルールを読み込めませんでした。ページを再読み込みしてください。");
    const {games} = await response.json();
    const game = games.find(item => item.id === location.pathname.split("/")[2]);
    if (!game) throw new Error("ゲームが見つかりません。ゲーム一覧から選び直してください。");
    $("rules-title").textContent = game.menu_title || game.title;
    document.title = `${game.title}のルール — 4Pro Arcade`;
    const guide=illustratedGuides[game.id];
    $("rules-summary").textContent = guide?.summary || game.description || "";
    showItems("rules-list", game.rules?.length ? game.rules : ["詳しいルールは準備中です。"]);
    showItems("operations-list", game.operations?.length ? game.operations : [game.controls || "操作方法は準備中です。"]);
    if(guide)renderIllustratedGuide(guide);
    $("rules-sections").hidden = !guide;
    $("rules-details").hidden = false;
    $("rules-details").open = !guide;
    const available = !["unregistered", "missing"].includes(game.status);
    $("rules-play").hidden = !available;
    $("rules-play").href = `/?play=${encodeURIComponent(game.id)}`;
    $("rules-status").textContent = available ? "準備ができたら、下のボタンでスタート！" : game.message;
    loadGuidePoster(game);
  } catch (error) {
    $("rules-title").textContent = "ルールと操作方法";
    $("rules-error").textContent = error.message;
    $("rules-error").hidden = false;
  } finally {
    $("rules-main").setAttribute("aria-busy", "false");
  }
}
loadRules();
