(() => {
'use strict';
const $=id=>document.getElementById(id),body=$('body'),key='solstorm-digtkladde-v1';
const fields=['title','note','slug','order','published','homepage'];
let manualSlug=false,loading=false,timer;
const slugify=s=>s.toLowerCase().replaceAll('æ','ae').replaceAll('ø','oe').replaceAll('å','aa').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,100);
const firstLine=()=>body.innerText.split(/\r?\n/).map(s=>s.trim()).find(Boolean)||'';
const message=(text,error=false)=>{$('status').textContent=text;$('status').classList.toggle('error',error)};
// Only these formatting elements are ever loaded into the editor or preview.
function clean(html){
 const doc=new DOMParser().parseFromString(html,'text/html'),out=document.createElement('div');
 const allowed=new Set(['B','STRONG','I','EM','BR','DIV','P','BLOCKQUOTE']);
 function append(node,parent){
  if(node.nodeType===Node.TEXT_NODE){parent.append(document.createTextNode(node.textContent));return}
  if(node.nodeType!==Node.ELEMENT_NODE||['SCRIPT','STYLE','IFRAME','OBJECT','SVG','MATH','TEMPLATE'].includes(node.tagName))return;
  if(allowed.has(node.tagName)){const el=document.createElement(node.tagName.toLowerCase());parent.append(el);for(const child of node.childNodes)append(child,el)}
  else for(const child of node.childNodes)append(child,parent);
 }
 for(const n of doc.body.childNodes)append(n,out);return out.innerHTML;
}
function data(){return {version:1,slug:$('slug').value.trim(),title:$('title').value.trim(),note:$('note').value.trim(),order:Number($('order').value)||0,published:$('published').checked,homepage:$('homepage').checked,body:clean(body.innerHTML)}}
function refresh(){
 if(!manualSlug)$('slug').value=slugify($('title').value.trim()||firstLine());
 $('preview-name').textContent=$('title').value.trim();
 $('preview-name').hidden=!$('title').value.trim();
 $('preview-body').innerHTML=clean(body.innerHTML);$('preview-note').textContent=$('note').value;
 if(!loading){clearTimeout(timer);timer=setTimeout(()=>{try{localStorage.setItem(key,JSON.stringify(data()));$('autosave').textContent='Kladde gemt i denne browser. Gem også digtfilen som din egen kopi.'}catch{$('autosave').textContent='Browseren kunne ikke gemme kladden. Gem digtfilen på din computer.'}},350)}
}
function load(d){
 if(d.version!==1||(d.title!==undefined&&typeof d.title!=='string')||typeof d.body!=='string'||typeof d.slug!=='string')throw Error('Filen er ikke en gyldig digtfil.');
 loading=true;for(const id of fields){if(['published','homepage'].includes(id))$(id).checked=d[id]===true;else $(id).value=d[id]??(id==='order'?10:'')}
 body.innerHTML=clean(d.body);manualSlug=Boolean(d.slug);refresh();loading=false;
}
for(const id of fields)$(id).addEventListener('input',()=>{if(id==='slug')manualSlug=true;refresh()});
body.addEventListener('input',refresh);
try{document.execCommand('defaultParagraphSeparator',false,'div')}catch{}
document.querySelectorAll('[data-command]').forEach(button=>{
 button.addEventListener('mousedown',e=>e.preventDefault());
 button.addEventListener('click',()=>{body.focus();document.execCommand(button.dataset.command,false);refresh();updateButtons()});
});
function updateButtons(){for(const b of document.querySelectorAll('[aria-pressed]')){try{b.setAttribute('aria-pressed',String(document.queryCommandState(b.dataset.command)))}catch{}}}
document.addEventListener('selectionchange',()=>{if(body.contains(document.getSelection()?.anchorNode))updateButtons()});
body.addEventListener('paste',e=>{e.preventDefault();document.execCommand('insertText',false,e.clipboardData.getData('text/plain').replace(/\r\n?/g,'\n'));refresh()});
body.addEventListener('keydown',e=>{if(e.key==='Tab'){e.preventDefault();document.execCommand('insertText',false,'    ');refresh()}});
$('download').addEventListener('click',()=>{
 const d=data();
 if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(d.slug)){message('Brug små bogstaver, tal og bindestreger i adressen.',true);$('slug').focus();return}
 if(!body.textContent.trim()){message('Indsæt digtets tekst, før du gemmer.',true);body.focus();return}
 if(!Number.isInteger(d.order)||d.order<0||d.order>9999){message('Rækkefølgen skal være et helt tal fra 0 til 9999.',true);return}
 const url=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)+'\n'],{type:'application/json;charset=utf-8'}));
 const a=document.createElement('a');a.href=url;a.download=d.slug+'.digt.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);
 message('Digtfilen er gemt. Den er klar til upload i GitHub.');
});
$('open').addEventListener('click',()=>$('file').click());
$('file').addEventListener('change',async()=>{
 const f=$('file').files[0];if(!f)return;
 try{if(f.size>1024*1024)throw Error('Filen er for stor. Vælg en digtfil under 1 MB.');if((body.textContent.trim()||$('title').value.trim())&&!confirm('Åbn filen og erstat den nuværende kladde? Gem din digtfil først, hvis du vil beholde den.'))return;load(JSON.parse(await f.text()));refresh();message('Digtet er åbnet. Du kan nu rette det og gemme igen.')}catch(e){message(e.message||'Filen kunne ikke åbnes.',true)}finally{$('file').value=''}
});
$('new').addEventListener('click',()=>{
 if((body.textContent.trim()||$('title').value.trim())&&!confirm('Start et nyt digt? Gem først den nuværende digtfil, hvis du vil beholde den.'))return;
 load({version:1,title:'',slug:'',note:'',body:'',order:10,published:true,homepage:false});manualSlug=false;refresh();message('Klar til et nyt digt.');$('title').focus();
});
try{const saved=localStorage.getItem(key);if(saved){load(JSON.parse(saved));message('Din seneste kladde er gendannet fra denne browser.')}}catch{message('En tidligere kladde kunne ikke gendannes.',true)}refresh();
})();
