"""聊天交互页面：扮演骗子跟 AI"王阿姨"对话，默认入口"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()


@router.get("/chat", response_class=HTMLResponse)
def chat_page():
    return HTMLResponse(content=HTML)


@router.get("/")
def root():
    """默认入口：跳转到聊天页面"""
    return RedirectResponse(url="/chat")


HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>反诈诱饵 · 聊天测试</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;background:#f0f2f5;color:#333;height:100vh;display:flex;flex-direction:column}
.topbar{background:#1a1a2e;color:#fff;padding:12px 25px;display:flex;align-items:center;gap:20px;flex-shrink:0}
.topbar h1{font-size:17px;font-weight:600}
.topbar .badge{background:#e74c3c;padding:2px 10px;border-radius:10px;font-size:12px}
.topbar a{color:#fff;text-decoration:none;font-size:13px;background:rgba(255,255,255,.15);padding:6px 14px;border-radius:6px;margin-left:auto}
.topbar a:hover{background:rgba(255,255,255,.25)}
.statusbar{background:#fff;border-bottom:1px solid #e8e8e8;padding:8px 25px;font-size:12px;color:#888;display:flex;gap:25px;flex-shrink:0}
.statusbar b{color:#1a1a2e}
.chatwrap{flex:1;overflow-y:auto;padding:25px;display:flex;flex-direction:column;gap:16px}
.msg{display:flex;gap:10px;max-width:75%}
.msg.me{align-self:flex-end;flex-direction:row-reverse}
.msg .avatar{width:36px;height:36px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:14px;color:#fff}
.av-ai{background:#3498db}.av-me{background:#e74c3c}
.msg .bubble{padding:10px 15px;border-radius:12px;font-size:14px;line-height:1.7;white-space:pre-wrap}
.bb-ai{background:#fff;border:1px solid #e8e8e8;border-top-left-radius:3px}
.bb-me{background:#1a73e8;color:#fff;border-top-right-radius:3px}
.msg .meta{font-size:11px;color:#aaa;margin-top:4px}
.msg.me .meta{text-align:right}
.typing{display:none;align-self:flex-start;color:#999;font-size:13px;padding:6px 12px;background:#fff;border-radius:10px;border:1px solid #e8e8e8}
.inputbar{background:#fff;border-top:1px solid #e0e0e0;padding:14px 25px;display:flex;gap:12px;flex-shrink:0}
.inputbar textarea{flex:1;resize:none;border:1px solid #ddd;border-radius:8px;padding:10px 14px;font-size:14px;font-family:inherit;height:46px;outline:none}
.inputbar textarea:focus{border-color:#1a73e8}
.inputbar button{background:#1a73e8;color:#fff;border:none;border-radius:8px;padding:0 26px;font-size:14px;cursor:pointer}
.inputbar button:hover{background:#1557b0}
.inputbar button:disabled{background:#9bb8e8;cursor:not-allowed}
.hint{color:#999;font-size:12px;text-align:center;padding:8px}
</style>
</head>
<body>
<div class="topbar">
  <h1>反诈诱饵 · 聊天测试</h1><span class="badge">你扮演骗子</span>
  <a href="/leads">线索管理后台 →</a>
</div>
<div class="statusbar">
  <span>会话: <b id="sid">...</b></span>
  <span>阶段: <b id="stage">greeting</b></span>
  <span>轮数: <b id="turn">0</b></span>
  <span>累计线索: <b id="leadcnt">0</b></span>
</div>
<div class="chatwrap" id="chat">
  <div class="hint">你现在是"骗子"。试着冒充公检法 / 客服 / 熟人，报出卡号、钱包、网址，看王阿姨会不会套出来。</div>
</div>
<div class="typing" id="typing">王阿姨正在输入…</div>
<div class="inputbar">
  <textarea id="input" placeholder="输入骗子的话，Enter 发送，Shift+Enter 换行" autofocus></textarea>
  <button id="send" onclick="sendMsg()">发送</button>
</div>
<script>
let sessionId=null, turnCount=0, stage='greeting', leadTotal=0;
const chat=document.getElementById('chat'), input=document.getElementById('input'),
      sendBtn=document.getElementById('send'), typing=document.getElementById('typing');

async function init(){
  const r=await fetch('/session/start',{method:'POST',headers:{'Content-Type':'application/json'},body:'{"caller_number":"web_console"}'});
  sessionId=(await r.json()).session_id;
  document.getElementById('sid').textContent=sessionId;
}
function addMsg(text,me){
  const div=document.createElement('div');
  div.className='msg'+(me?' me':'');
  div.innerHTML=`<div class="avatar ${me?'av-me':'av-ai'}">${me?'骗':'AI'}</div>
    <div><div class="bubble ${me?'bb-me':'bb-ai'}"></div>
    <div class="meta">${me?'':'第'+turnCount+'轮 · 王阿姨'}</div></div>`;
  div.querySelector('.bubble').textContent=text;
  chat.appendChild(div);
  chat.scrollTop=chat.scrollHeight;
}
function updateStatus(d){
  if(d.stage){stage=d.stage;document.getElementById('stage').textContent=stage}
  if(d.turn_count!==undefined){turnCount=d.turn_count;document.getElementById('turn').textContent=turnCount}
  if(d.leads_found){leadTotal+=d.leads_found.length;document.getElementById('leadcnt').textContent=leadTotal}
}
async function sendMsg(){
  const text=input.value.trim();
  if(!text||!sessionId)return;
  input.value='';sendBtn.disabled=true;typing.style.display='block';
  addMsg(text,true);
  try{
    const r=await fetch('/turn',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({session_id:sessionId,scammer_text:text})});
    const d=await r.json();
    typing.style.display='none';
    addMsg(d.reply_text,false);
    updateStatus(d);
  }catch(e){
    typing.style.display='none';
    addMsg('[请求失败: '+e.message+'，检查服务是否在跑]',false);
  }
  sendBtn.disabled=false;input.focus();
}
input.addEventListener('keydown',e=>{
  if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMsg()}
});
init();
</script>
</body></html>"""
