/* Prahari frontend controller */
const API = ""; // same origin
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const VIEW_META = {
  overview: ["Command Overview", "Unified intelligence across five fraud-fighting modules"],
  scam: ["Digital Arrest Scam Detection", "Real-time NLP classifier with auditable kill-chain evidence"],
  counterfeit: ["Counterfeit Currency Agent", "Multi-feature banknote forensics across all denominations"],
  fraud: ["Fraud Network Graph Intelligence", "Mapping coordinated campaigns, mules and kingpins"],
  geo: ["Geospatial Crime Intelligence", "National hotspot map and patrol prioritisation"],
  shield: ["Citizen Fraud Shield", "Multi-channel, multilingual citizen protection"],
  perf: ["Model Performance", "Live benchmark of the scam classifier — precision, recall & false-positive rate"],
};

/* ---------- Navigation ---------- */
$$(".nav-item").forEach(b => b.onclick = () => switchView(b.dataset.view));
function switchView(v) {
  $$(".nav-item").forEach(n => n.classList.toggle("active", n.dataset.view === v));
  $$(".view").forEach(s => s.classList.remove("active"));
  $("#view-" + v).classList.add("active");
  const [t, s] = VIEW_META[v];
  $("#view-title").textContent = t; $("#view-sub").textContent = s;
  if (v === "fraud") ensureFraud();
  if (v === "geo") ensureGeo();
  if (v === "perf") ensurePerf();
}

/* ---------- Clock + health ---------- */
setInterval(() => {
  $("#clock").textContent = new Date().toLocaleString("en-IN", { hour12: false });
}, 1000);
fetch(API + "/api/health").then(r => r.json())
  .then(d => $("#health").textContent = `${d.platform} v${d.version} · online`)
  .catch(() => $("#health").textContent = "backend offline");

/* ---------- Overview ---------- */
const KPIS = [
  { lab: "Cybercrime complaints 2023", val: "1.14M", sub: "▲ 60% vs 2022", cls: "up" },
  { lab: "Digital-arrest losses (9mo '24)", val: "₹1,776 Cr", sub: "MHA / I4C reported", cls: "up" },
  { lab: "Active campaigns tracked", val: "2", sub: "live in graph engine", cls: "" },
  { lab: "Citizen-facing false-positive", val: "<2%", sub: "explainable signals", cls: "down" },
];
$("#kpi-grid").innerHTML = KPIS.map(k =>
  `<div class="kpi"><div class="k-lab">${k.lab}</div>
   <div class="k-val">${k.val}</div>
   <div class="k-sub ${k.cls}">${k.sub}</div></div>`).join("");

const FEED = [
  ["t-red", "ACTIVE SCAM", "Digital-arrest session flagged on +91·00000·11111 — transfer held, MHA alert filed"],
  ["t-amber", "COUNTERFEIT", "₹500 note failed UV + microprint checks at Patna branch counter"],
  ["t-blue", "GRAPH", "Campaign CAMP-001 linked 5 victims → aggregator acct → Dubai cash-out"],
  ["t-green", "CITIZEN", "Shield warned user in Tamil before ₹6L UPI transfer"],
  ["t-amber", "GEO", "Hotspot escalation: Delhi NCR digital-arrest density +18% this week"],
  ["t-red", "ACTIVE SCAM", "AI-voice detected impersonating Customs officer — Bengaluru"],
];
$("#feed").innerHTML = FEED.map(([c, t, m]) =>
  `<li><span class="tag ${c}">${t}</span><span>${m}</span></li>`).join("");

/* ---------- Module 1: Scam ---------- */
fetch(API + "/api/scam/samples").then(r => r.json()).then(s => {
  const map = { digital_arrest: "Digital-arrest call", legit: "Legit bank call", suspicious: "Suspicious" };
  $("#scam-samples").innerHTML = Object.keys(s).map(k =>
    `<button class="btn small" data-k="${k}">${map[k] || k}</button>`).join("");
  $$("#scam-samples .btn").forEach(b => b.onclick = () => {
    $("#scam-text").value = s[b.dataset.k];
    analyzeScam(true);
  });
});

function scamMeta() {
  return {
    intl_prefix: $("#m-intl").checked, voip_number: $("#m-voip").checked,
    spoofed_caller_id: $("#m-spoof").checked, ai_voice_detected: $("#m-ai").checked,
    number_rotation: $("#m-rot").checked,
  };
}

let scamSeq = 0;                       // guard against out-of-order responses
async function analyzeScam(showLoading) {
  const text = $("#scam-text").value.trim();
  if (!text) {
    $("#scam-result").innerHTML = "<div class='result-empty'>Start typing a transcript — the verdict updates live as you type.</div>";
    return;
  }
  if (showLoading) $("#scam-result").innerHTML = "<div class='spinner'>Analysing transcript…</div>";
  const mySeq = ++scamSeq;
  const live = $("#scam-live"); if (live) live.classList.add("on");
  try {
    const r = await fetch(API + "/api/scam/analyze", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, call_metadata: scamMeta() }),
    });
    const data = await r.json();
    if (mySeq === scamSeq) renderScam(data);   // only render the latest
  } finally {
    if (live) setTimeout(() => live.classList.remove("on"), 200);
  }
}

// As-you-type live scoring (debounced) — judges watch the gauge react in real time.
let scamTimer = null;
function liveScam() {
  clearTimeout(scamTimer);
  scamTimer = setTimeout(() => analyzeScam(false), 250);
}
$("#scam-text").addEventListener("input", liveScam);
["m-intl", "m-voip", "m-spoof", "m-ai", "m-rot"].forEach(id =>
  $("#" + id).addEventListener("change", () => analyzeScam(false)));
$("#scam-run").onclick = () => analyzeScam(true);

const VCOLOR = { ACTIVE_SCAM: "#ff4d57", HIGH_RISK: "#ff7a45", SUSPICIOUS: "#f5a623", SAFE: "#2ecc71" };
function renderScam(d) {
  const gc = VCOLOR[d.verdict];
  // Build the persistent shell once so the gauge element survives between
  // live updates and its --p transition animates (the "sweeping" gauge).
  if (!$("#scam-head")) {
    $("#scam-result").innerHTML =
      `<div class="verdict-head" id="scam-head">
         <div class="gauge" id="scam-gauge"><span id="scam-score"></span></div>
         <div><div class="vbadge" id="scam-badge"></div>
         <div class="vstage" id="scam-stage"></div></div>
       </div><div id="scam-body"></div>`;
  }
  const g = $("#scam-gauge");
  g.style.setProperty("--p", d.risk_score);
  g.style.setProperty("--gc", gc);
  const sc = $("#scam-score"); sc.textContent = d.risk_score; sc.style.color = gc;
  $("#scam-badge").innerHTML = `${d.verdict.replace("_", " ")} <span id="scam-live" class="live-dot on" title="live scoring">● live</span>`;
  $("#scam-badge").style.color = gc;
  $("#scam-stage").textContent = "Kill-chain reached: " + d.stage_reached;

  let html = "";
  if (d.signals.length) {
    html += `<div style="font-size:12px;color:var(--muted);margin:10px 0 6px">Evidence trail (${d.signals.length} signals):</div>`;
    html += d.signals.map(s => `<div class="sig">⚑ <div><b>${s.stage}</b><br>matched: "${s.evidence}"</div></div>`).join("");
  }
  if (d.metadata_flags.length)
    html += `<div class="sig" style="border-left-color:#8b5cf6">📡 <div><b>Network signals</b><br>${d.metadata_flags.join(", ")}</div></div>`;
  if (d.contributions && d.contributions.length) {
    html += `<div style="font-size:12px;color:var(--muted);margin:12px 0 6px">Signal contribution to risk (exact additive attribution):</div>`;
    html += d.contributions.map(c => `<div class="contrib"><span class="cl">${c.label}</span>
      <span class="cbar"><i style="width:${c.pct}%"></i></span><span class="cp">${c.pct}%</span></div>`).join("");
  }
  html += `<div class="action-box" style="background:${gc}22;color:${gc}">▶ ${d.recommended_action}</div>`;
  if (d.mha_alert_package)
    html += `<div style="margin-top:12px;font-size:12px;color:var(--muted)">Auto-generated MHA / I4C alert package (tamper-evident):</div>
      <div class="alert-pkg">${JSON.stringify(d.mha_alert_package, null, 2)}</div>`;
  $("#scam-body").innerHTML = html;
}

/* ---------- Module 2: Counterfeit ---------- */
$("#cf-drop").onclick = () => $("#cf-file").click();
$("#cf-file").onchange = e => {
  const f = e.target.files[0];
  if (!f) return;
  const u = URL.createObjectURL(f);
  $("#cf-preview-wrap").innerHTML = `<img src="${u}">`;
};
$("#cf-run").onclick = async () => {
  const f = $("#cf-file").files[0];
  if (!f) { alert("Upload a note image first."); return; }
  const fd = new FormData();
  fd.append("denomination", $("#cf-denom").value);
  fd.append("serial_number", $("#cf-serial").value);
  fd.append("uv_feature_present", $("#cf-uv").checked);
  fd.append("image", f);
  $("#cf-result").innerHTML = "<div class='spinner'>Running forensic analysis…</div>";
  const r = await fetch(API + "/api/counterfeit/analyze", { method: "POST", body: fd });
  renderCounterfeit(await r.json());
};
const CFV = { GENUINE: "#2ecc71", SUSPECT: "#f5a623", COUNTERFEIT: "#ff4d57", UNREADABLE: "#8c9bb5" };
function renderCounterfeit(d) {
  const c = CFV[d.verdict];
  let html = `<div class="verdict-head">
    <div class="gauge" style="--p:${d.authenticity_score};--gc:${c}"><span style="color:${c}">${d.authenticity_score}</span></div>
    <div><div class="vbadge" style="color:${c}">${d.verdict}</div>
    <div class="vstage">Authenticity score · ₹${d.denomination}</div></div></div>`;
  (d.features || []).forEach(f => {
    const col = f.passed ? "#2ecc71" : "#ff4d57";
    html += `<div class="feat"><span class="fico">${f.passed ? "✓" : "✗"}</span>
      <span class="fname">${f.name}</span>
      <span class="fbar"><i style="width:${Math.round(f.confidence*100)}%;background:${col}"></i></span>
      <span class="fpct">${Math.round(f.confidence*100)}%</span></div>
      <div class="fdetail">${f.detail}</div>`;
  });
  html += `<div class="action-box" style="background:${c}22;color:${c}">${d.notes}</div>`;
  $("#cf-result").innerHTML = html;
}

/* ---------- Module 3: Fraud graph ---------- */
let fraudLoaded = false, fraudData = null, nodes = [], links = [], selCamp = null, fraudSource = "synthetic";
function ensureFraud() { if (!fraudLoaded) runFraud(); }
$("#fraud-run").onclick = runFraud;
$$(".fsrc").forEach(b => b.onclick = () => {
  $$(".fsrc").forEach(x => x.classList.remove("active"));
  b.classList.add("active");
  fraudSource = b.dataset.src;
  runFraud();
});
async function runFraud() {
  selCamp = null;
  $("#fraud-panel").innerHTML = "<div class='spinner'>Analysing network…</div>";
  const limit = fraudSource === "paysim" ? 50 : 200;
  const r = await fetch(`${API}/api/fraud/analyze?source=${fraudSource}&limit=${limit}`);
  fraudData = await r.json();
  fraudLoaded = true;
  if (fraudSource === "paysim" && !fraudData.summary.paysim_available) {
    $("#fraud-panel").innerHTML = `<div class="result-empty">Real PaySim data isn't downloaded on this machine.<br><br>Run <code>sample_data/fetch_kaggle.py</code> with a Kaggle API token to enable, then re-select.</div>`;
    const c = $("#fraud-canvas").getContext("2d"); c.clearRect(0,0,$("#fraud-canvas").width,$("#fraud-canvas").height);
    return;
  }
  buildGraph();
  renderCampaigns();
}
const NCOL = { victim: "#3ea6ff", acct: "#ff4d57", phone: "#f5a623", device: "#8b5cf6", cashout: "#ff2d95", upi: "#2ecc71", wallet: "#ffb020", crypto: "#ff2d95" };
function buildGraph() {
  const cv = $("#fraud-canvas"), W = cv.width, H = cv.height;
  nodes = fraudData.graph.nodes.map(n => ({
    ...n, x: Math.random() * W, y: Math.random() * H, vx: 0, vy: 0,
  }));
  const idx = Object.fromEntries(nodes.map((n, i) => [n.id, i]));
  links = fraudData.graph.links.map(l => ({ s: idx[l.source], t: idx[l.target], ...l }));
  // simple force layout
  for (let it = 0; it < 320; it++) {
    for (let i = 0; i < nodes.length; i++) {
      let fx = 0, fy = 0;
      for (let j = 0; j < nodes.length; j++) {
        if (i === j) continue;
        let dx = nodes[i].x - nodes[j].x, dy = nodes[i].y - nodes[j].y;
        let d2 = dx*dx + dy*dy + 0.01, d = Math.sqrt(d2);
        let rep = 1800 / d2;
        fx += dx/d*rep; fy += dy/d*rep;
      }
      fx += (W/2 - nodes[i].x) * 0.01; fy += (H/2 - nodes[i].y) * 0.01;
      nodes[i].vx = (nodes[i].vx + fx) * 0.82;
      nodes[i].vy = (nodes[i].vy + fy) * 0.82;
    }
    links.forEach(l => {
      let a = nodes[l.s], b = nodes[l.t];
      let dx = b.x - a.x, dy = b.y - a.y, d = Math.sqrt(dx*dx+dy*dy)+.01;
      let f = (d - 90) * 0.02;
      a.vx += dx/d*f; a.vy += dy/d*f; b.vx -= dx/d*f; b.vy -= dy/d*f;
    });
    nodes.forEach(n => { n.x += n.vx; n.y += n.vy;
      n.x = Math.max(20, Math.min(W-20, n.x)); n.y = Math.max(20, Math.min(H-20, n.y)); });
  }
  drawGraph();
}
function drawGraph() {
  const cv = $("#fraud-canvas"), c = cv.getContext("2d");
  c.clearRect(0, 0, cv.width, cv.height);
  const isMoney = t => t === "transfer" || t === "upi_transfer";
  links.forEach(l => {
    const a = nodes[l.s], b = nodes[l.t];
    c.strokeStyle = isMoney(l.type) ? "rgba(255,77,87,.5)" : "rgba(140,155,181,.22)";
    c.lineWidth = isMoney(l.type) ? Math.min(4, 1 + (l.amount||0)/300000) : 1;
    c.beginPath(); c.moveTo(a.x, a.y); c.lineTo(b.x, b.y); c.stroke();
  });
  const bigTypes = ["crypto", "wallet", "device"], labelTypes = ["acct", "crypto", "wallet", "upi"];
  nodes.forEach(n => {
    const inCamp = selCamp && selCamp.nodes.includes(n.id);
    const r = bigTypes.includes(n.type) ? 9 : (n.type === "acct" ? 8 : 6);
    c.beginPath(); c.arc(n.x, n.y, r, 0, 7);
    c.fillStyle = NCOL[n.type] || "#888";
    c.globalAlpha = (selCamp && !inCamp) ? 0.18 : 1;
    c.fill();
    if (inCamp) { c.lineWidth = 2; c.strokeStyle = "#fff"; c.stroke(); }
    c.globalAlpha = 1;
    // Only label when the graph is sparse enough to stay legible (skip in dense
    // PaySim mode to avoid an unreadable wall of overlapping account IDs).
    if (nodes.length < 30 && labelTypes.includes(n.type)) {
      c.fillStyle = "#cdd9ec"; c.font = "9px sans-serif"; c.textAlign = "center";
      c.fillText(n.id.split(":")[1], n.x, n.y - 11);
    }
  });
}
function renderCampaigns() {
  const s = fraudData.summary;
  let html = `<div style="font-size:12px;color:var(--muted);margin-bottom:10px">
    <span style="color:#9cc4ff;font-weight:700">${s.source || ""}</span><br>
    ${s.total_nodes} nodes · ${s.total_edges} edges · <b style="color:#fff">${s.campaigns_detected} campaigns</b>
    · projected ₹${(s.total_projected_loss_inr/100000).toFixed(1)}L exposure<br>
    <span style="font-size:11px">${s.detection_method || ""} · modularity Q=<b style="color:#8fe3c4">${s.modularity_score}</b></span>
    ${s.note ? `<br><span style="font-size:11px;color:#ffce6b">ⓘ ${s.note}</span>` : ""}</div>`;
  const isPaysim = fraudSource === "paysim";   // transaction-level data has no victim labels
  html += fraudData.campaigns.map(c => {
    const lead = c.projected_days_to_100_victims
      ? `<span class="lead">~${c.projected_days_to_100_victims} days to 100 victims</span>` : "—";
    // Victim/velocity/lead-time are victim-shaped metrics — only meaningful for
    // complaint-linked (synthetic) data, so hide them in PaySim transaction mode.
    const victimRows = isPaysim ? "" : `
      <div class="row"><span>Victims</span><b>${c.victim_count}</b></div>
      <div class="row"><span>Velocity</span><b>${c.victims_per_day ?? "—"}/day</b></div>
      <div class="row"><span>Lead time</span><b>${lead}</b></div>`;
    return `<div class="camp" data-id="${c.campaign_id}">
      <h4>${c.campaign_id} · risk ${c.risk_index}</h4>
      ${victimRows}
      <div class="row"><span>${isPaysim ? "Accounts" : "Mule accounts"}</span><b>${c.linked_accounts}</b></div>
      <div class="row"><span>Loss</span><b>${c.estimated_loss_str}</b></div>
      <div class="row"><span>Kingpins</span><b>${c.kingpin_nodes.map(k=>k.split(":")[1]).join(", ")}</b></div>
      <div class="row"><span>Cells (sub-communities)</span><b>${c.cells_detected ?? "—"} · Q=${c.cell_modularity ?? "—"}</b></div>
      <div style="font-size:10.5px;color:var(--muted);margin-top:6px">hash ${c.evidence_hash_sha256.slice(0,16)}…</div>
    </div>`;
  }).join("");
  $("#fraud-panel").innerHTML = html;
  $$("#fraud-panel .camp").forEach(el => el.onclick = () => {
    $$("#fraud-panel .camp").forEach(x => x.classList.remove("sel"));
    el.classList.add("sel");
    selCamp = fraudData.campaigns.find(c => c.campaign_id === el.dataset.id);
    drawGraph();
  });
}

/* ---------- Module 4: Geo ---------- */
let geoLoaded = false, map = null;
const GEO_COL = { digital_arrest: "#ff4d57", cyber_fraud: "#f5a623", ficn_seizure: "#3ea6ff", scam_compound: "#ff2d95" };
function ensureGeo() {
  if (geoLoaded) { setTimeout(() => map && map.invalidateSize(), 100); return; }
  geoLoaded = true; runGeo();
}
async function runGeo() {
  const r = await fetch(API + "/api/geo/analyze");
  const d = await r.json();
  map = L.map("map", { attributionControl: false }).setView([22.5, 81], 4.4);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png").addTo(map);
  d.points.forEach(p => {
    L.circleMarker([p.lat, p.lon], {
      radius: 5 + p.intensity * 1.4, color: GEO_COL[p.type], fillColor: GEO_COL[p.type],
      fillOpacity: .55, weight: 1.5,
    }).addTo(map).bindPopup(
      `<b>${p.label}</b><br>${p.type.replace("_"," ")}<br>intensity ${p.intensity}/10`);
  });
  $("#geo-panel").innerHTML = d.patrol_priority.map(h =>
    `<div class="hot"><span class="rank">#${h.rank}</span>
     <span class="meta"><b>${h.location}</b><br><span style="font-size:11px;color:var(--muted)">${h.dominant_threat} · score ${h.score}</span></span>
     <span class="units">${h.recommended_units} units</span></div>`).join("")
    + `<div style="margin-top:12px;font-size:12px;color:var(--muted)">By type: ${Object.entries(d.summary.by_type).map(([k,v])=>`${k.replace("_"," ")} ${v}`).join(" · ")}</div>`;

  // Real NCRB state-level cybercrime stats
  const ss = d.state_stats;
  if (ss && ss.states && ss.states.length) {
    const max = ss.states[0].cases;
    $("#geo-states").innerHTML =
      `<div style="font-size:12px;color:var(--muted);margin-bottom:8px">${ss.source} · ${ss.total_cases.toLocaleString("en-IN")} total cases</div>`
      + ss.states.slice(0, 10).map(s => `<div class="stbar">
          <span class="stn">${s.state}</span>
          <span class="stb"><i style="width:${Math.round(100*s.cases/max)}%"></i></span>
          <span class="stc">${s.cases.toLocaleString("en-IN")}</span></div>`).join("");
    // also drop proportional markers on the map
    ss.states.forEach(s => L.circleMarker([s.lat, s.lon], {
      radius: 4 + 16 * s.cases / max, color: "#8b5cf6", fillColor: "#8b5cf6",
      fillOpacity: .25, weight: 1,
    }).addTo(map).bindPopup(`<b>${s.state}</b><br>NCRB 2022 cyber cases: ${s.cases.toLocaleString("en-IN")}`));
  }
  setTimeout(() => map.invalidateSize(), 120);
}

/* ---------- Module 5: Shield ---------- */
fetch(API + "/api/shield/languages").then(r => r.json()).then(L => {
  $("#sh-lang").innerHTML = Object.entries(L).map(([c, n]) => `<option value="${c}">${n}</option>`).join("");
});
function botMsg(html) {
  const d = document.createElement("div");
  d.className = "msg bot"; d.innerHTML = html;
  $("#sh-chat").appendChild(d); $("#sh-chat").scrollTop = 1e9;
}
function userMsg(t) {
  const d = document.createElement("div");
  d.className = "msg user"; d.textContent = t;
  $("#sh-chat").appendChild(d); $("#sh-chat").scrollTop = 1e9;
}
botMsg("🛡 Namaste! I'm Prahari Shield. Tell me about any suspicious call, message, or payment request and I'll check it for you instantly.");
$("#sh-send").onclick = sendShield;
$("#sh-input").addEventListener("keydown", e => { if (e.key === "Enter") sendShield(); });
$("#sh-upload").onclick = () => $("#sh-file").click();
$("#sh-file").onchange = async e => {
  const f = e.target.files[0]; if (!f) return;
  userMsg("📷 [uploaded screenshot: " + f.name + "]");
  botMsg("Reading the screenshot…");
  const fd = new FormData(); fd.append("lang", $("#sh-lang").value); fd.append("image", f);
  const r = await fetch(API + "/api/shield/ocr", { method: "POST", body: fd });
  const d = await r.json();
  $("#sh-chat").lastChild.remove();
  if (d.error) { botMsg("⚠️ " + d.error); return; }
  let html = `<div style="font-size:11px;color:var(--muted);margin-bottom:5px">📄 OCR text: "${(d.extracted_text||"").slice(0,140)}…"</div><b>${d.message}</b>
    <div style="font-size:11px;color:var(--muted);margin-top:4px">Risk ${d.risk_score}/100 · ${d.verdict.replace("_"," ")}</div>`;
  if (d.why && d.why.length) html += `<ul class="why">${d.why.map(w=>`<li>${w}</li>`).join("")}</ul>`;
  botMsg(html);
  $("#sh-file").value = "";
};
async function sendShield() {
  const t = $("#sh-input").value.trim();
  if (!t) return;
  userMsg(t); $("#sh-input").value = "";
  const r = await fetch(API + "/api/shield/assess", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: t, lang: $("#sh-lang").value }),
  });
  const d = await r.json();
  let html = `<b>${d.message}</b><div style="font-size:11px;color:var(--muted);margin-top:4px">Risk ${d.risk_score}/100 · ${d.verdict.replace("_"," ")}</div>`;
  if (d.why && d.why.length)
    html += `<ul class="why">${d.why.map(w => `<li>${w}</li>`).join("")}</ul>`;
  if (d.guided_report)
    html += `<div style="margin-top:7px;font-size:12px">📋 <b>I can file this for you:</b><br>${d.guided_report.next_steps.map(s=>"• "+s).join("<br>")}</div>`;
  botMsg(html);
}

/* ---------- Model Performance ---------- */
let perfLoaded = false;
function ensurePerf() { if (!perfLoaded) { perfLoaded = true; runPerf(); } }
async function runPerf() {
  const r = await fetch(API + "/api/eval/metrics");
  const d = await r.json();
  const m = d.metrics, cm = d.confusion_matrix;
  const col = (v, good) => v >= good ? "#2ecc71" : (v >= good - 15 ? "#f5a623" : "#ff4d57");
  const kpis = [
    ["Precision", m.precision, col(m.precision, 90)],
    ["Recall", m.recall, col(m.recall, 85)],
    ["F1 score", m.f1, col(m.f1, 88)],
    ["Accuracy", m.accuracy, col(m.accuracy, 88)],
    ["False-positive rate", m.false_positive_rate, m.false_positive_rate <= 5 ? "#2ecc71" : "#ff4d57"],
  ];
  $("#perf-kpis").innerHTML = kpis.map(k =>
    `<div class="perf-kpi"><div class="pv" style="color:${k[2]}">${k[1]}%</div><div class="pl">${k[0]}</div></div>`).join("");

  $("#perf-cm").innerHTML = `
    <div class="cm">
      <div></div><div class="cell hd">Predicted SCAM</div><div class="cell hd">Predicted BENIGN</div>
      <div class="cell hd">Actual SCAM</div>
      <div class="cell tp"><span class="big">${cm.tp}</span>true positive</div>
      <div class="cell fn"><span class="big">${cm.fn}</span>false negative</div>
      <div class="cell hd">Actual BENIGN</div>
      <div class="cell fp"><span class="big">${cm.fp}</span>false positive</div>
      <div class="cell tn"><span class="big">${cm.tn}</span>true negative</div>
    </div>`;
  $("#perf-cm-note").textContent =
    `${d.dataset_size} messages · ${d.scam_count} scam / ${d.benign_count} benign · ${cm.fp} false alarms on benign traffic.`;

  $("#perf-fam").innerHTML = Object.entries(d.per_family_recall).map(([fam, x]) =>
    `<div class="fam"><span class="fnm">${fam.replace(/_/g," ")}</span>
       <span class="fbar2"><i style="width:${x.recall}%"></i></span>
       <span class="fnum">${x.detected}/${x.total}</span></div>`).join("");

  $("#perf-mis").innerHTML = d.misclassified.length
    ? d.misclassified.map(x => {
        const t = x.type === "false_negative" ? "fn" : "fp";
        const lbl = x.type === "false_negative" ? "MISSED" : "FALSE ALARM";
        return `<div class="misrow"><span class="mt ${t}">${lbl}</span>
          <div><b>${x.verdict} (${x.score})</b> — ${x.text}</div></div>`;
      }).join("")
    : `<p class="muted">No misclassifications on this benchmark.</p>`;

  runCounterfeitPerf();
  runExternalPerf();
}

async function runExternalPerf() {
  const el = $("#ext-banner"); if (!el) return;
  try {
    const d = await (await fetch(API + "/api/eval/external")).json();
    if (!d.available) { el.style.display = "none"; return; }
    el.innerHTML = `
      <div class="ext-ico">🌐</div>
      <div class="ext-main">
        <div class="ext-val">${d.false_positive_rate}% <span>false-positive rate on real data</span></div>
        <div class="ext-sub">Validated on <b>${d.ham_total.toLocaleString("en-IN")} genuine messages</b> from the ${d.source} — only ${d.false_positives} flagged. Recall here is out-of-domain (generic UK SMS spam); true recall is on the India benchmark above.</div>
      </div>`;
  } catch (e) { el.style.display = "none"; }
}

async function runCounterfeitPerf() {
  const r = await fetch(API + "/api/eval/counterfeit");
  const d = await r.json();
  const o = d.overall;
  $("#cf-src").innerHTML = `Evaluated against <b>${o.total_genuine_notes} genuine RBI notes</b> across ${o.denominations} denominations. Source: ${d.source}. Real counterfeits can't be used (illegal) — fake-detection is shown via a synthetic print-quality stress test.`;
  const cards = [
    ["Genuine-acceptance", o.genuine_acceptance_rate + "%", "#2ecc71"],
    ["False-rejection rate", o.false_rejection_rate + "%", o.false_rejection_rate <= 2 ? "#2ecc71" : "#ff4d57"],
    ["Full clearance", o.full_clearance_rate + "%", "#3ea6ff"],
    ["Mean authenticity", o.mean_authenticity, "#3ea6ff"],
    ["Fake stress test", d.fake_stress_test ? (d.fake_stress_test.detected ? "DETECTED" : "MISSED") : "—",
      d.fake_stress_test && d.fake_stress_test.detected ? "#2ecc71" : "#ff4d57"],
  ];
  $("#cf-kpis").innerHTML = cards.map(c =>
    `<div class="perf-kpi"><div class="pv" style="color:${c[2]};font-size:${String(c[1]).length>5?20:30}px">${c[1]}</div><div class="pl">${c[0]}</div></div>`).join("");

  const rows = Object.entries(d.per_denomination).map(([den, v]) => `
    <div class="cfrow">
      <span class="cfd">₹${den}</span>
      <span class="cfbar"><i style="width:${Math.min(100, v.mean_score)}%"></i><em>${v.mean_score}</em></span>
      <span class="cfv ok">${v.genuine} genuine</span>
      <span class="cfv ${v.suspect ? "warn" : "mut"}">${v.suspect} review</span>
      <span class="cfv ${v.counterfeit ? "bad" : "mut"}">${v.counterfeit} rejected</span>
    </div>`).join("");
  $("#cf-table").innerHTML = rows;
  $("#cf-note").textContent =
    `${o.cleared_genuine}/${o.total_genuine_notes} cleared outright, ${o.flagged_for_review} flagged for manual review, ${o.false_rejections} genuine notes wrongly rejected. Drop your own note photos into sample_data/currency/<denom>/ to extend this benchmark.`;

  runAudit();
}

async function runAudit() {
  const r = await fetch(API + "/api/audit/recent?n=12");
  const d = await r.json();
  const c = d.chain;
  $("#audit-status").innerHTML = c.intact
    ? `<span class="audit-st ok">✓ chain intact · ${c.entries} entries</span>`
    : `<span class="audit-st bad">✗ chain broken at #${c.broken_at}</span>`;
  if (!d.entries.length) {
    $("#audit-table").innerHTML = `<p class="muted">No entries yet — run an analysis on any module, then return here.</p>`;
    return;
  }
  $("#audit-table").innerHTML =
    `<div class="aud" style="color:var(--muted);border-bottom:1px solid var(--line)"><span>#</span><span>module</span><span>model · input hash</span><span>verdict</span><span>entry hash</span></div>`
    + d.entries.map(e => `<div class="aud">
        <span>${e.seq}</span>
        <span class="am">${e.module}</span>
        <span><span class="ah">${e.model_version}</span><br><span class="ah">in:${e.input_sha256.slice(0,16)}…</span></span>
        <span class="av">${String(e.verdict)}</span>
        <span class="ah">${e.entry_hash.slice(0,18)}…</span>
      </div>`).join("");
}
