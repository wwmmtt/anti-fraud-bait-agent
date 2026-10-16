"""反诈诱饵管理后台 Web页面"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from storage.sqlite_client import get_all_leads, get_all_sessions, get_lead_stats, get_session_messages
from utils.extractor import load_rules, save_rules

router = APIRouter()


@router.get("/leads", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(content=HTML)


@router.get("/api/leads")
def api_leads(lead_type: str = "", session_id: str = "", q: str = ""):
    leads = get_all_leads(lead_type=lead_type, session_id=session_id)
    if q:
        q = q.lower()
        leads = [l for l in leads if q in l["lead_value"].lower() or q in l["session_id"].lower()]
    return leads


@router.get("/api/sessions")
def api_sessions():
    return get_all_sessions()


@router.get("/api/sessions/{session_id}/messages")
def api_session_messages(session_id: str):
    return get_session_messages(session_id)


@router.get("/api/stats")
def api_stats():
    return get_lead_stats()


# ===== 抽取规则管理：增/删/改/启停，写 lead_rules.json 实时生效 =====

@router.get("/api/rules")
def api_rules():
    return load_rules()


@router.post("/api/rules")
def api_add_rule(rule: dict):
    rules = load_rules()
    if not rule.get("type") or any(r["type"] == rule["type"] for r in rules):
        return {"error": "type 为空或已存在"}
    rules.append({
        "type": rule["type"].strip(),
        "name": rule.get("name") or rule["type"],
        "enabled": bool(rule.get("enabled", True)),
        "confidence": float(rule.get("confidence", 0.8)),
        "regex": rule.get("regex") or None,  # 留空 = 仅靠 LLM 抽取
    })
    save_rules(rules)
    return {"ok": True}


@router.put("/api/rules/{rtype}")
def api_update_rule(rtype: str, rule: dict):
    rules = load_rules()
    for r in rules:
        if r["type"] == rtype:
            for k in ("name", "enabled", "confidence", "regex"):
                if k in rule:
                    r[k] = rule[k]
            if r.get("regex") == "":
                r["regex"] = None
            save_rules(rules)
            return {"ok": True}
    return {"error": f"规则 {rtype} 不存在"}


@router.delete("/api/rules/{rtype}")
def api_delete_rule(rtype: str):
    save_rules([r for r in load_rules() if r["type"] != rtype])
    return {"ok": True}


HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>反诈诱饵 · 管理后台</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;background:#f0f2f5;color:#333}
.topbar{background:#1a1a2e;color:#fff;padding:15px 25px;display:flex;align-items:center;gap:20px}
.topbar h1{font-size:18px;font-weight:600}
.topbar .badge{background:#e74c3c;padding:2px 10px;border-radius:10px;font-size:12px}
.tabs{display:flex;gap:5px;padding:0 25px;background:#fff;border-bottom:1px solid #e0e0e0}
.tab{padding:14px 20px;cursor:pointer;border-bottom:2px solid transparent;font-size:14px;color:#666}
.tab.active{color:#1a1a2e;border-bottom-color:#e74c3c;font-weight:600}
.container{padding:20px 25px}
.stats{display:flex;gap:15px;margin-bottom:20px;flex-wrap:wrap}
.stat-card{background:#fff;border-radius:10px;padding:18px 22px;min-width:130px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.stat-card .num{font-size:26px;font-weight:700}
.stat-card .lbl{color:#999;font-size:12px;margin-top:4px}
.c-red{color:#e74c3c}.c-blue{color:#3498db}.c-orange{color:#f39c12}.c-green{color:#27ae60}.c-gray{color:#7f8c8d}
.toolbar{display:flex;gap:10px;margin-bottom:15px;align-items:center;flex-wrap:wrap}
.toolbar select,.toolbar input{padding:8px 12px;border:1px solid #ddd;border-radius:6px;font-size:13px}
.toolbar input[type=text]{width:220px}
.btn{padding:8px 16px;border:none;border-radius:6px;cursor:pointer;font-size:13px}
.btn-export{background:#27ae60;color:#fff}.btn-export:hover{background:#229954}
table{width:100%;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.06);border-collapse:collapse}
th{background:#1a1a2e;color:#fff;padding:11px 14px;text-align:left;font-size:12px;font-weight:500;white-space:nowrap}
td{padding:10px 14px;border-bottom:1px solid #f0f0f0;font-size:13px}
tr:hover td{background:#f8f9fa}
.tag{display:inline-block;padding:3px 9px;border-radius:4px;font-size:11px;font-weight:600}
.mono{font-family:Consolas,monospace;font-size:12px;color:#555}
.empty{text-align:center;padding:50px;color:#bbb}
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:100;align-items:center;justify-content:center}
.modal-bg.show{display:flex}
.modal{background:#fff;border-radius:12px;width:680px;max-height:80vh;display:flex;flex-direction:column;overflow:hidden}
.modal-head{padding:16px 22px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center}
.modal-head h3{font-size:16px}
.modal-close{cursor:pointer;font-size:22px;color:#999;border:none;background:none}
.modal-body{padding:20px 22px;overflow-y:auto}
.msg{margin-bottom:14px;display:flex;gap:10px}
.msg .avatar{width:32px;height:32px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:14px;color:#fff}
.av-scammer{background:#e74c3c}.av-bait{background:#3498db}
.msg .bubble{padding:9px 14px;border-radius:10px;font-size:13px;line-height:1.6;max-width:75%}
.bb-scammer{background:#fde8e8}.bb-bait{background:#e8f0fe}
.msg .meta{font-size:11px;color:#aaa;margin-top:3px}
.status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}
.dot-active{background:#27ae60}.dot-ended{background:#bbb}
</style>
</head>
<body>
<div class="topbar"><h1>反诈诱饵 · 管理后台</h1><span class="badge">Anti-Fraud Bait</span><a href="/chat" style="color:#fff;text-decoration:none;font-size:13px;background:rgba(255,255,255,.15);padding:6px 14px;border-radius:6px;margin-left:auto">← 返回聊天测试</a></div>
<div class="tabs">
  <div class="tab active" onclick="switchTab('leads')">线索管理</div>
  <div class="tab" onclick="switchTab('sessions')">会话记录</div>
  <div class="tab" onclick="switchTab('rules')">抽取规则</div>
</div>
<div class="container">
  <div class="stats" id="stats"></div>
  <div id="leadsPanel">
    <div class="toolbar">
      <select id="typeFilter" onchange="loadLeads()">
        <option value="">全部类型</option>
      </select>
      <input type="text" id="search" placeholder="搜索线索内容/会话ID..." oninput="loadLeads()">
      <button class="btn btn-export" onclick="exportLeads()">导出CSV</button>
    </div>
    <table><thead><tr><th>ID</th><th>会话ID</th><th>类型</th><th>线索内容</th><th>可信度</th><th>轮次</th><th>时间</th></tr></thead>
    <tbody id="leadsBody"></tbody></table>
  </div>
  <div id="sessionsPanel" style="display:none">
    <table><thead><tr><th>会话ID</th><th>来电号码</th><th>阶段</th><th>轮数</th><th>线索数</th><th>开始时间</th><th>操作</th></tr></thead>
    <tbody id="sessionsBody"></tbody></table>
  </div>
  <div id="rulesPanel" style="display:none">
    <div class="toolbar">
      <input type="text" id="rType" placeholder="类型英文标识，如 wechat" style="width:140px">
      <input type="text" id="rName" placeholder="显示名称，如 微信号" style="width:120px">
      <input type="text" id="rRegex" placeholder="正则表达式（留空=仅靠LLM抽取）" style="width:340px" class="mono">
      <input type="number" id="rConf" placeholder="可信度" min="0" max="1" step="0.05" value="0.8" style="width:90px">
      <button class="btn btn-export" onclick="addRule()">+ 添加规则</button>
    </div>
    <p style="color:#999;font-size:12px;margin-bottom:10px">规则改动实时生效，无需重启：启用且有正则 → 走确定性正则抽取；无正则 → 仅靠大模型按系统提示抽取。改动同时影响「正则兜底」和「Agent 抽取工具」。</p>
    <table><thead><tr><th>类型</th><th>名称</th><th>正则</th><th>可信度</th><th>状态</th><th>操作</th></tr></thead>
    <tbody id="rulesBody"></tbody></table>
  </div>
</div>
<div class="modal-bg" id="modal">
  <div class="modal">
    <div class="modal-head"><h3 id="modalTitle">会话详情</h3><button class="modal-close" onclick="closeModal()">&times;</button></div>
    <div class="modal-body" id="modalBody"></div>
  </div>
</div>
<script>
// 调色板：8 种浅色对 [背景, 文字]，按规则顺序循环；tag 颜色按 type 字符串哈希取色，保证同类型稳定
const PALETTE=[['#fde8e8','#c0392b'],['#e8f0fe','#1a73e8'],['#fef7e0','#b06000'],['#e6f4ea','#137333'],['#f3e8fd','#7d3c98'],['#e0f7fa','#006d75'],['#fce4ec','#a93226'],['#eef1f2','#7f8c8d']];
let RULES=[], ruleNames={};
function typeColor(t){let h=0;for(let i=0;i<t.length;i++)h=(h*31+t.charCodeAt(i))>>>0;return PALETTE[h%PALETTE.length];}
function tagHtml(t){const c=typeColor(t);return `<span class="tag" style="background:${c[0]};color:${c[1]}">${ruleNames[t]||t}</span>`;}
async function loadRulesData(){
  RULES=await fetch('/api/rules').then(r=>r.json());
  ruleNames={};RULES.forEach(r=>ruleNames[r.type]=r.name);
  const sel=document.getElementById('typeFilter');
  sel.innerHTML='<option value="">全部类型</option>'+RULES.map(r=>`<option value="${r.type}">${r.name}</option>`).join('');
  return RULES;
}
function switchTab(t){
  document.querySelectorAll('.tab').forEach(e=>e.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('leadsPanel').style.display=t==='leads'?'':'none';
  document.getElementById('sessionsPanel').style.display=t==='sessions'?'':'none';
  document.getElementById('rulesPanel').style.display=t==='rules'?'':'none';
  document.getElementById('stats').style.display=t==='leads'?'':'none';
  if(t==='sessions')loadSessions();
  if(t==='rules')loadRules();
}
async function loadStats(){
  const [s,rules]=await Promise.all([fetch('/api/stats').then(r=>r.json()),Promise.resolve(RULES)]);
  const cards=[`<div class="stat-card"><div class="num c-red">${s.total||0}</div><div class="lbl">总线索</div></div>`];
  rules.filter(r=>r.enabled).forEach((r,i)=>{
    const c=PALETTE[i%PALETTE.length];
    cards.push(`<div class="stat-card"><div class="num" style="color:${c[1]}">${s[r.type]||0}</div><div class="lbl">${r.name}</div></div>`);
  });
  cards.push(`<div class="stat-card"><div class="num c-gray">${s.sessions||0}</div><div class="lbl">会话数</div></div>`);
  document.getElementById('stats').innerHTML=cards.join('');
}
async function loadLeads(){
  const t=document.getElementById('typeFilter').value;
  const q=document.getElementById('search').value;
  const leads=await fetch(`/api/leads?lead_type=${t}&q=${encodeURIComponent(q)}`).then(r=>r.json());
  const body=document.getElementById('leadsBody');
  if(!leads.length){body.innerHTML='<tr><td colspan="7" class="empty">暂无线索</td></tr>';return}
  body.innerHTML=leads.map(l=>`<tr>
    <td>${l.id}</td><td class="mono">${l.session_id.slice(0,16)}...</td>
    <td>${tagHtml(l.lead_type)}</td>
    <td class="mono">${l.lead_value}</td><td>${(l.confidence*100).toFixed(0)}%</td>
    <td>${l.turn_number}</td><td>${l.created_at}</td></tr>`).join('');
}
async function loadSessions(){
  const sessions=await fetch('/api/sessions').then(r=>r.json());
  const body=document.getElementById('sessionsBody');
  if(!sessions.length){body.innerHTML='<tr><td colspan="7" class="empty">暂无会话</td></tr>';return}
  body.innerHTML=sessions.map(s=>`<tr>
    <td class="mono">${s.session_id.slice(0,16)}...</td>
    <td>${s.caller_number||'-'}</td>
    <td><span class="status-dot ${s.stage==='ended'?'dot-ended':'dot-active'}"></span>${s.stage}</td>
    <td>${s.turn_count}</td><td>${s.lead_count||0}</td><td>${s.created_at}</td>
    <td><button class="btn" style="background:#1a1a2e;color:#fff;padding:5px 12px" onclick="openDetail('${s.session_id}')">查看对话</button></td>
    </tr>`).join('');
}
async function openDetail(sid){
  document.getElementById('modal').classList.add('show');
  document.getElementById('modalTitle').textContent='会话 '+sid;
  const msgs=await fetch(`/api/sessions/${sid}/messages`).then(r=>r.json());
  if(!msgs.length){document.getElementById('modalBody').innerHTML='<p class="empty">暂无对话记录</p>';return}
  document.getElementById('modalBody').innerHTML=msgs.map(m=>{
    const isScammer=m.role==='scammer';
    return `<div class="msg" style="justify-content:${isScammer?'flex-start':'flex-end'}">
      ${isScammer?`<div class="avatar av-scammer">骗</div>`:''}
      <div><div class="bubble ${isScammer?'bb-scammer':'bb-bait'}">${m.content}</div>
      <div class="meta" style="text-align:${isScammer?'left':'right'}">第${m.turn_number}轮</div></div>
      ${!isScammer?`<div class="avatar av-bait">AI</div>`:''}
    </div>`;
  }).join('');
}
function closeModal(){document.getElementById('modal').classList.remove('show')}

// ===== 抽取规则管理 =====
async function loadRules(){
  const rules=await loadRulesData();
  loadStats();  // 规则增删改后统计卡和下拉同步刷新
  const body=document.getElementById('rulesBody');
  if(!rules.length){body.innerHTML='<tr><td colspan="6" class="empty">暂无规则</td></tr>';return}
  body.innerHTML=rules.map(r=>`<tr>
    <td class="mono">${r.type}</td><td>${r.name}</td>
    <td class="mono" style="max-width:320px;word-break:break-all">${r.regex||'<i style="color:#bbb">无（仅LLM抽取）</i>'}</td>
    <td>${(r.confidence*100).toFixed(0)}%</td>
    <td><span class="tag" style="background:${r.enabled?'#e6f4ea':'#eee'};color:${r.enabled?'#137333':'#999'}">${r.enabled?'启用':'停用'}</span></td>
    <td>
      <button class="btn" style="background:#1a1a2e;color:#fff;padding:4px 10px" onclick="toggleRule('${r.type}',${!r.enabled})">${r.enabled?'停用':'启用'}</button>
      <button class="btn" style="background:#f39c12;color:#fff;padding:4px 10px" onclick="editRule('${r.type}')">编辑</button>
      <button class="btn" style="background:#e74c3c;color:#fff;padding:4px 10px" onclick="delRule('${r.type}')">删除</button>
    </td></tr>`).join('');
}
async function addRule(){
  const type=document.getElementById('rType').value.trim();
  if(!type){alert('请填类型标识');return}
  const r=await fetch('/api/rules',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    type:type, name:document.getElementById('rName').value.trim()||type,
    regex:document.getElementById('rRegex').value.trim()||null,
    confidence:parseFloat(document.getElementById('rConf').value)||0.8, enabled:true})}).then(r=>r.json());
  if(r.error){alert(r.error);return}
  ['rType','rName','rRegex'].forEach(id=>document.getElementById(id).value='');
  loadRules();
}
async function toggleRule(type,enabled){
  await fetch(`/api/rules/${type}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:enabled})});
  loadRules();
}
async function editRule(type){
  const rules=await fetch('/api/rules').then(r=>r.json());
  const r=rules.find(x=>x.type===type);if(!r)return;
  const name=prompt('显示名称：',r.name);if(name===null)return;
  const regex=prompt('正则表达式（留空=仅靠LLM抽取）：',r.regex||'');if(regex===null)return;
  const conf=prompt('可信度(0~1)：',r.confidence);if(conf===null)return;
  await fetch(`/api/rules/${type}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name,regex:regex,confidence:parseFloat(conf)||0.8})});
  loadRules();
}
async function delRule(type){
  if(!confirm(`确定删除规则「${typeName[type]||type}」？已抽取的历史线索保留。`))return;
  await fetch(`/api/rules/${type}`,{method:'DELETE'});
  loadRules();
}

function exportLeads(){
  const t=document.getElementById('typeFilter').value;
  window.open(`/api/leads?lead_type=${t}`);
}
loadRulesData().then(()=>{loadStats();loadLeads()});
setInterval(()=>{loadStats();loadLeads()},10000);
</script>
</body></html>"""
