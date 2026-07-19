/* Prahari frontend controller */
const API = ""; // same origin
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
/* Escape any value that originates from user input (transcript, serial,
   OCR text, chat message) before it goes into innerHTML — prevents HTML/JS
   injection from a crafted note serial or scam transcript. */
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

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
$$(".hero-cta").forEach(b => b.onclick = () => switchView(b.dataset.view));

/* Mobile nav drawer */
const _sb = $(".sidebar"), _ov = $("#nav-overlay"), _bt = $("#nav-toggle");
function navDrawer(open) { _sb.classList.toggle("open", open); if (_ov) _ov.classList.toggle("show", open); }
if (_bt) _bt.onclick = () => navDrawer(!_sb.classList.contains("open"));
if (_ov) _ov.onclick = () => navDrawer(false);
$$(".nav-item").forEach(b => b.addEventListener("click", () => navDrawer(false)));
function switchView(v) {
  $$(".nav-item").forEach(n => {
    const on = n.dataset.view === v;
    n.classList.toggle("active", on);
    if (on) n.setAttribute("aria-current", "page"); else n.removeAttribute("aria-current");
  });
  $$(".view").forEach(s => s.classList.remove("active"));
  $("#view-" + v).classList.add("active");
  const [t, s] = VIEW_META[v];
  $("#view-title").textContent = t; $("#view-sub").textContent = s;
  if (v === "fraud") ensureFraud();
  if (v === "geo") ensureGeo();
  if (v === "perf") ensurePerf();
}

/* Animated count-up for headline numbers (skipped under reduced motion —
   the final value is always rendered first as the fallback). */
function countUp(el, { num, dec = 0, pre = "", suf = "", loc = false, dur = 900 }) {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const t0 = performance.now();
  const fmt = v => pre + (loc ? Math.round(v).toLocaleString("en-IN") : v.toFixed(dec)) + suf;
  (function tick(t) {
    const p = Math.min(1, (t - t0) / dur);
    const e = 1 - Math.pow(1 - p, 3);
    el.textContent = fmt(num * e);
    if (p < 1) requestAnimationFrame(tick);
  })(t0);
}
/* Animate any KPI tile whose text starts with a number (₹1,776 Cr, 97.1%…) */
function animateKpis(sel) {
  $$(sel + " .pv, " + sel + " .iu-v").forEach(el => {
    const m = el.textContent.trim().match(/^(₹?)([\d.,]+)(.*)$/);
    if (!m) return;
    const num = parseFloat(m[2].replace(/,/g, ""));
    if (isNaN(num)) return;
    countUp(el, { num, dec: (m[2].split(".")[1] || "").length, pre: m[1],
                  suf: m[3], loc: m[2].includes(",") });
  });
}
/* Shimmer skeleton placeholder while a panel loads */
const skel = (rows = 5, h = 13) => `<div class="skel-group">` +
  Array.from({ length: rows }, (_, i) =>
    `<div class="skel" style="height:${h}px;width:${88 - (i % 3) * 14}%"></div>`).join("") + `</div>`;

/* Tiny toast for demo-scoped controls */
let toastTimer = null;
function toast(msg) {
  let t = $("#toast");
  if (!t) { t = document.createElement("div"); t.id = "toast"; document.body.appendChild(t); }
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 2600);
}

/* ---------- Clock + health ---------- */
setInterval(() => {
  $("#clock").textContent = new Date().toLocaleString("en-IN", { hour12: false });
}, 1000);
fetch(API + "/api/health").then(r => r.json())
  .then(() => $("#health").textContent = "All systems operational")
  .catch(() => $("#health").textContent = "backend offline");

/* Generic data-view navigation (quick actions, links, map expand, AI button) */
$$(".qa-btn[data-view],.link-btn[data-view],.mt-btn[data-view],.tb-ai[data-view]").forEach(b =>
  b.addEventListener("click", () => switchView(b.dataset.view)));

/* Quick-nav search: keywords jump straight to the right module */
const SEARCH_ROUTES = [
  [/(scam|arrest|call|voice|transcript)/, "scam"],
  [/(note|counterfeit|currency|ficn|fake|₹)/, "counterfeit"],
  [/(graph|network|mule|upi|ring|kingpin|campaign)/, "fraud"],
  [/(map|geo|hotspot|patrol|state|city)/, "geo"],
  [/(shield|citizen|whatsapp|chat|1930)/, "shield"],
  [/(perf|metric|precision|recall|benchmark|model|audit)/, "perf"],
];
const searchInput = $("#tb-search-input");
if (searchInput) searchInput.addEventListener("keydown", e => {
  if (e.key !== "Enter") return;
  const q = searchInput.value.trim().toLowerCase();
  if (!q) return;
  const hit = SEARCH_ROUTES.find(([re]) => re.test(q));
  if (hit) { switchView(hit[1]); toast("Opened " + VIEW_META[hit[1]][0]); }
  else toast(`No match for "${q}" — try scam, UPI, counterfeit, map, shield…`);
  searchInput.value = "";
});

/* Sidebar footer: demo-honest actions */
if ($("#sf-theme")) $("#sf-theme").onclick = () => toast("Dark command-centre theme is locked for the demo");
if ($("#sf-exit")) $("#sf-exit").onclick = () => toast("Demo session — sign-out is disabled");
if ($("#sf-notif")) $("#sf-notif").onclick = () => { switchView("overview"); toast("Live alerts appear on the Overview feed"); };

/* Map card: layers button toggles the Quick Actions overlay */
if ($("#mt-layers")) $("#mt-layers").onclick = () => {
  const qa = $("#quick-actions");
  qa.style.display = qa.style.display === "none" ? "" : "none";
};

/* ---------- Overview: command-center dashboard ---------- */
const ICO = {
  brief: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>',
  bell: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>',
  rupee: '<span style="font-size:23px;font-weight:800;line-height:1">₹</span>',
  users: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/></svg>',
};
/* National threat picture — real published figures (not demo dressing) */
const STATS = [
  { lab: "Cybercrime Losses (2024)", val: "₹22,845 Cr", anim: { num: 22845, pre: "₹", suf: " Cr", loc: true }, delta: "↑ 42% YoY · 22.68 lakh complaints", cls: "d-up", src: "I4C / MHA 2024", ico: ICO.brief, tint: "#3ea6ff" },
  { lab: "Digital-Arrest Losses (2024)", val: "₹1,935 Cr", anim: { num: 1935, pre: "₹", suf: " Cr", loc: true }, delta: "21× the 2022 figure", cls: "d-up", src: "Inc42 / MHA", ico: ICO.bell, tint: "#ff4d57" },
  { lab: "Financial Fraud Share", val: "59%", anim: { num: 59, suf: "%" }, delta: "of all Indian cybercrime", cls: "d-neut", src: "NCRB motive data (in-app)", ico: ICO.rupee, tint: "#f5a623" },
  { lab: "Fake ₹500 Notes (FY26)", val: "1.42 lakh", anim: { num: 1.42, dec: 2, suf: " lakh" }, delta: "↑ 20.5% · 97.6% caught by banks", cls: "d-up", src: "RBI Annual Report FY26", ico: ICO.users, tint: "#8b5cf6" },
  { lab: "Scam Classifier (live)", val: "…", delta: "measuring…", cls: "d-down", src: "benchmarked in-app, this session", ico: ICO.clock, tint: "#2ecc71", id: "stat-live" },
];
$("#stat-row").innerHTML = STATS.map(s => `
  <div class="stat" ${s.id ? `id="${s.id}"` : ""}>
    <div class="stat-top">
      <div><div class="stat-lab">${s.lab}</div><div class="stat-val">${s.val}</div></div>
      <div class="stat-ico" style="background:${s.tint}22;color:${s.tint}">${s.ico}</div>
    </div>
    <div class="stat-delta ${s.cls}">${s.delta}<span class="sub">· ${s.src}</span></div>
  </div>`).join("");
$$("#stat-row .stat-val").forEach((el, i) => { if (STATS[i].anim) countUp(el, STATS[i].anim); });
/* 5th card is computed live from the in-app benchmark — proof, not a claim */
fetch(API + "/api/eval/metrics").then(r => r.json()).then(d => {
  const el = $("#stat-live"); if (!el) return;
  const v = el.querySelector(".stat-val");
  v.textContent = d.metrics.precision + "% precision";
  countUp(v, { num: d.metrics.precision, suf: "% precision" });
  el.querySelector(".stat-delta").innerHTML =
    `recall ${d.metrics.recall}% · FPR ${d.metrics.false_positive_rate}%<span class="sub">· benchmarked live this session</span>`;
}).catch(() => {});

const ALERTS = [
  { t: "Digital Arrest Scam Detected", sev: "#ff4d57", badge: "High Risk", loc: "Connaught Place, New Delhi", ago: "2 min ago", conf: 97 },
  { t: "UPI Fraud Attempt", sev: "#f5a623", badge: "Medium Risk", loc: "Bandra West, Mumbai", ago: "5 min ago", conf: 89 },
  { t: "Fake Currency Circulation", sev: "#8b5cf6", badge: "Medium Risk", loc: "Kukatpally, Hyderabad", ago: "10 min ago", conf: 86 },
  { t: "Cyber Threat Detected", sev: "#3ea6ff", badge: "Low Risk", loc: "Salt Lake, Kolkata", ago: "12 min ago", conf: 75 },
];
const triSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.2 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.2a2 2 0 0 0-3.4 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';

/* Topbar bell: real dropdown fed by the same alert list */
const bellBtn = $("#tb-bell"), bellPop = $("#bell-pop");
if (bellBtn && bellPop) {
  bellBtn.dataset.count = ALERTS.length;
  bellPop.innerHTML = `<div class="bp-h">AI Alerts <span class="sim-chip">simulated</span></div>` + ALERTS.map(a => `
    <button class="bp-item" data-view="scam">
      <i style="background:${a.sev}"></i>
      <span><b>${a.t}</b><em>${a.loc} · ${a.ago}</em></span>
    </button>`).join("");
  bellBtn.onclick = e => { e.stopPropagation(); bellPop.classList.toggle("open"); };
  document.addEventListener("click", e => { if (!bellPop.contains(e.target)) bellPop.classList.remove("open"); });
  $$(".bp-item", bellPop).forEach(b => b.onclick = () => { bellPop.classList.remove("open"); switchView("overview"); });
}
$("#ai-alerts").innerHTML = ALERTS.map(a => `
  <div class="ai-alert" style="--sev:${a.sev}">
    <div class="aa-ico">${triSvg}</div>
    <div class="aa-body">
      <div class="aa-top"><span class="aa-title">${a.t}</span><span class="aa-badge">${a.badge}</span></div>
      <div class="aa-meta"><span>◎ ${a.loc}</span><span>${a.ago}</span></div>
      <div class="aa-conf">AI Confidence: ${a.conf}%<span class="aa-bar"><i style="width:${a.conf}%"></i></span></div>
    </div>
  </div>`).join("");

const RECENT = [
  ["12m", "Digital arrest racket busted in 3 states", "Digital Arrest", "#ff4d57"],
  ["25m", "Fake ₹500 notes circulation detected", "Counterfeit", "#f5a623"],
  ["47m", "New phishing domains targeting banks", "Cyber Threat", "#3ea6ff"],
  ["1h", "UPI collect-request fraud spike found", "UPI Fraud", "#8b5cf6"],
  ["2h", "OTP-sharing scams increasing", "Financial Fraud", "#2ecc71"],
];
$("#feed").innerHTML = RECENT.map(([tm, txt, tag, c]) => `
  <li><span class="feed-chip">${tm}</span><span class="feed-txt">${txt}</span>
    <span class="feed-tag" style="background:${c}22;color:${c}">${tag}</span></li>`).join("");

$("#bc-time").textContent = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })
  + "  ·  " + new Date().toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

/* Render canvases at devicePixelRatio so lines/labels stay crisp on retina.
   Returns a ctx pre-scaled to CSS-pixel coordinates plus the logical size. */
function sizeCanvasForDPR(cv) {
  const dpr = window.devicePixelRatio || 1;
  const r = cv.getBoundingClientRect();
  const W = Math.max(1, Math.round(r.width)), H = Math.max(1, Math.round(r.height));
  cv.width = W * dpr; cv.height = H * dpr;
  const c = cv.getContext("2d");
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { c, W, H };
}

/* charts + mini map + graph teaser (once, on load — overview is the default view) */
function initOverview() {
  if (window.Chart) {
    Chart.defaults.color = "#93a1ba";
    Chart.defaults.font.family = "Inter, sans-serif";
    Chart.defaults.font.size = 11;
    // Incident trend (area line)
    const tc = document.getElementById("trendChart");
    if (tc) {
      const g = tc.getContext("2d");
      const grad = g.createLinearGradient(0, 0, 0, 150);
      grad.addColorStop(0, "rgba(62,166,255,.35)"); grad.addColorStop(1, "rgba(62,166,255,0)");
      const dayLabels = [...Array(7)].map((_, i) => {
        const d = new Date(Date.now() - (6 - i) * 864e5);
        return d.toLocaleDateString("en-IN", { month: "short", day: "2-digit" });
      });
      new Chart(g, {
        type: "line",
        data: {
          labels: dayLabels,
          datasets: [
            { label: "Incidents", data: [340, 420, 390, 560, 610, 720, 842], borderColor: "#3ea6ff",
              backgroundColor: grad, fill: true, tension: .4, borderWidth: 2, pointRadius: 0, pointHoverRadius: 4 },
            { label: "Alerts", data: [90, 120, 110, 150, 160, 140, 128], borderColor: "#8b5cf6",
              backgroundColor: "transparent", fill: false, tension: .4, borderWidth: 2, pointRadius: 0 },
          ],
        },
        options: { responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { x: { grid: { display: false } }, y: { grid: { color: "rgba(255,255,255,.05)" }, beginAtZero: true } } },
      });
    }
    // Top fraud categories (doughnut)
    const cc = document.getElementById("catChart");
    if (cc) {
      const cats = [["Digital Arrest", 42, "#ff4d57"], ["UPI Fraud", 28, "#f5a623"],
        ["Investment Fraud", 14, "#8b5cf6"], ["Cybercrime", 10, "#3ea6ff"], ["Other", 6, "#2ecc71"]];
      new Chart(cc.getContext("2d"), {
        type: "doughnut",
        data: { labels: cats.map(c => c[0]), datasets: [{ data: cats.map(c => c[1]),
          backgroundColor: cats.map(c => c[2]), borderColor: "transparent", cutout: "68%" }] },
        options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { display: false } } },
      });
      $("#cat-legend").innerHTML = cats.map(c =>
        `<div class="cat-row"><i style="background:${c[2]}"></i>${c[0]}<span class="cp">${c[1]}%</span></div>`).join("");
    }
  }
  // Mini geospatial map with numbered markers (Delhi NCR)
  if (window.L && document.getElementById("ov-map") && !document.getElementById("ov-map")._leaflet_id) {
    const om = L.map("ov-map", { attributionControl: false, zoomControl: false, minZoom: 8, maxZoom: 12 })
      .setView([28.6, 77.15], 9.5);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { subdomains: "abcd" }).addTo(om);
    const pins = [
      [28.70, 77.10, 12, "#ff4d57"], [28.72, 77.28, 2, "#f5a623"], [28.63, 77.22, 7, "#3ea6ff"],
      [28.61, 77.23, 8, "#ff4d57"], [28.55, 77.27, 5, "#f5a623"], [28.52, 77.10, 1, "#3ea6ff"],
      [28.47, 77.03, 2, "#2ecc71"], [28.60, 77.33, 8, "#ff4d57"], [28.53, 77.39, 5, "#f5a623"],
    ];
    pins.forEach(([la, lo, n, c]) => {
      const r = 22 + n;
      L.marker([la, lo], { icon: L.divIcon({ className: "", html:
        `<div class="ov-pin" style="width:${r}px;height:${r}px;background:${c};color:${c}"><span style="color:#fff">${n}</span></div>`,
        iconSize: [r, r], iconAnchor: [r / 2, r / 2] }) }).addTo(om);
    });
    setTimeout(() => om.invalidateSize(), 200);
    setTimeout(() => om.invalidateSize(), 600);
  }
  // Fraud graph teaser (decorative)
  const gc = document.getElementById("ovGraphCanvas");
  if (gc && gc.getContext) {
    const { c, W, H } = sizeCanvasForDPR(gc);
    const cx = W / 2, cy = H / 2;
    const cols = ["#3ea6ff", "#2ecc71", "#ff4d57", "#f5a623", "#8b5cf6"];
    const nodes = [[cx, cy, "#ff4d57", 9]];
    for (let i = 0; i < 10; i++) {
      const a = i / 10 * Math.PI * 2, rr = 52 + (i % 3) * 12;
      nodes.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr * .8, cols[i % cols.length], 6]);
    }
    c.clearRect(0, 0, W, H);
    for (let i = 1; i < nodes.length; i++) {
      c.strokeStyle = "rgba(140,155,181,.35)"; c.lineWidth = 1;
      c.beginPath(); c.moveTo(nodes[0][0], nodes[0][1]); c.lineTo(nodes[i][0], nodes[i][1]); c.stroke();
      if (i < nodes.length - 1) { c.beginPath(); c.moveTo(nodes[i][0], nodes[i][1]); c.lineTo(nodes[i + 1][0], nodes[i + 1][1]); c.stroke(); }
    }
    nodes.forEach(([x, y, col, rad]) => { c.beginPath(); c.arc(x, y, rad, 0, 7); c.fillStyle = col; c.fill(); });
  }
}
initOverview();

/* ---------- Module 1: Scam ---------- */
fetch(API + "/api/scam/samples").then(r => r.json()).then(s => {
  const map = { digital_arrest: "Digital-arrest call", legit: "Legit bank call", suspicious: "Suspicious", phishing_link: "🔗 Phishing link" };
  $("#scam-samples").innerHTML = Object.keys(s).map(k =>
    `<button class="btn small" data-k="${k}">${map[k] || k}</button>`).join("");
  $$("#scam-samples .btn").forEach(b => b.onclick = () => {
    $("#scam-text").value = s[b.dataset.k];
    // The digital-arrest sample carries the caller number of the CAMP-001
    // kingpin phone, so fusion demonstrates a live graph hit.
    $("#scam-caller").value = b.dataset.k === "digital_arrest" ? "+91 98000 11111" : "";
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
    const caller = $("#scam-caller").value.trim();
    const r = await fetch(API + "/api/scam/analyze", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, call_metadata: scamMeta(),
        ...(caller ? { caller_number: caller } : {}) }),
    });
    const data = await r.json();
    if (mySeq === scamSeq) {
      renderScam(data);   // only render the latest
      // Fusion runs on explicit analyses only (button / sample click), not on
      // every keystroke — it writes a ledger entry per run.
      if (showLoading && (data.verdict === "ACTIVE_SCAM" || data.verdict === "HIGH_RISK"))
        runFusion(data, caller);
    }
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
    html += d.signals.map(s => `<div class="sig">⚑ <div><b>${esc(s.stage)}</b><br>matched: "${esc(s.evidence)}"</div></div>`).join("");
  }
  if (d.metadata_flags.length)
    html += `<div class="sig" style="border-left-color:#8b5cf6">📡 <div><b>Network signals</b><br>${d.metadata_flags.join(", ")}</div></div>`;
  if (d.obfuscation_normalized)
    html += `<div class="sig" style="border-left-color:#2ecc71">🛡 <div><b>Obfuscation defeated</b><br>text was disguised (leetspeak / homoglyph / spacing) — normalised before matching</div></div>`;
  if (d.url_analysis && d.url_analysis.urls_found) {
    html += d.url_analysis.findings.filter(u => u.risk >= 22).map(u =>
      `<div class="sig" style="border-left-color:#ff4d57">🔗 <div><b>${esc(u.verdict.replace("_"," "))} link (risk ${u.risk})</b><br>
        <span style="word-break:break-all">${esc(u.url)}</span><br>
        <span style="color:var(--muted)">${esc(u.reasons.slice(0,3).join(" · "))}</span></div></div>`).join("");
  }
  if (d.llm_second_opinion) {
    const o = d.llm_second_opinion;
    html += `<div class="sig" style="border-left-color:#3ea6ff">🤖 <div><b>LLM second opinion (${esc(o.model)})</b><br>${esc(o.verdict)} · risk ${o.risk} — ${esc(o.reason)}</div></div>`;
  } else if (d.llm_available === false) {
    html += `<div style="font-size:11px;color:var(--muted);margin:8px 0 2px">🤖 LLM second-opinion layer available — set ANTHROPIC_API_KEY to enable a hybrid read (rule engine remains the verdict of record).</div>`;
  }
  if (d.contributions && d.contributions.length) {
    html += `<div style="font-size:12px;color:var(--muted);margin:12px 0 6px">Signal contribution to risk (exact additive attribution):</div>`;
    html += d.contributions.map(c => `<div class="contrib"><span class="cl">${c.label}</span>
      <span class="cbar"><i style="width:${c.pct}%"></i></span><span class="cp">${c.pct}%</span></div>`).join("");
  }
  html += `<div class="action-box" style="background:${gc}22;color:${gc}">▶ ${d.recommended_action}</div>`;
  if (d.mha_alert_package)
    html += `<div style="margin-top:12px;font-size:12px;color:var(--muted)">Auto-generated MHA / I4C alert package (tamper-evident):</div>
      <div class="alert-pkg">${esc(JSON.stringify(d.mha_alert_package, null, 2))}</div>`;
  $("#scam-body").innerHTML = html;
}

/* ---------- Intelligence Fusion: one case through every module ---------- */
let fusionSeq = 0;
async function runFusion(d, caller) {
  const mySeq = ++fusionSeq;
  const body = $("#scam-body");
  if (!body) return;
  const holder = document.createElement("div");
  holder.className = "fusion";
  holder.innerHTML = `<div class="fu-h">⚡ Intelligence Fusion
      <span class="fu-sub">agentic cross-module correlation</span>
      <span class="fu-case"></span></div>
    <div class="fu-steps"><div class="spinner">Fusing intelligence across modules…</div></div>`;
  body.appendChild(holder);
  let f;
  try {
    const r = await fetch(API + "/api/fusion/analyze", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        risk_score: d.risk_score, verdict: d.verdict,
        stage_reached: d.stage_reached || "",
        ...(caller ? { caller_number: caller } : {}),
        ...(d.audit_entry ? { text_sha256: d.audit_entry.input_sha256 } : {}),
      }),
    });
    f = await r.json();
  } catch (e) {
    holder.querySelector(".fu-steps").innerHTML =
      "<p class='muted'>Fusion service unreachable.</p>";
    return;
  }
  if (mySeq !== fusionSeq || !document.contains(holder)) return;
  holder.querySelector(".fu-case").textContent = f.case_id;
  const icons = { hit: "◉", ok: "✓", watch: "◎" };
  const wrap = holder.querySelector(".fu-steps");
  wrap.innerHTML = f.steps.map(s => `
    <div class="fstep ${s.status}">
      <span class="fs-ico">${icons[s.status] || "✓"}</span>
      <span class="fs-body"><b>${s.title}</b><em>${s.detail}</em></span>
      <span class="fs-ms">${s.ms} ms</span>
    </div>`).join("");
  // staggered reveal — the "agent working the case" beat for the demo
  $$(".fstep", wrap).forEach((el, i) => setTimeout(() => el.classList.add("on"), 220 + i * 380));
}

/* ---------- Speech AI: AI-voice screening ---------- */
const VVCOL = { LIKELY_SYNTHETIC: "#ff4d57", UNCERTAIN: "#f5a623", LIKELY_HUMAN: "#2ecc71", UNREADABLE: "#8c9bb5" };
let voiceFile = null;
$("#voice-drop").onclick = () => $("#voice-file").click();
$("#voice-file").onchange = e => {
  const f = e.target.files[0]; if (!f) return;
  voiceFile = f;
  $("#voice-wrap").innerHTML = `🎙 ${esc(f.name)} <span style="color:var(--muted)">(${Math.round(f.size/1024)} KB)</span>`;
  e.target.value = "";
};
$("#voice-run").onclick = async () => {
  if (!voiceFile) { $("#voice-result").innerHTML = "<div class='result-empty'>⚠ Upload a WAV recording first.</div>"; return; }
  $("#voice-result").innerHTML = "<div class='spinner'>Analysing acoustics…</div>";
  const fd = new FormData(); fd.append("audio", voiceFile);
  let d;
  try { d = await (await fetch(API + "/api/voice/analyze", { method: "POST", body: fd })).json(); }
  catch (e) { $("#voice-result").innerHTML = "<div class='result-empty'>Voice service error.</div>"; return; }
  const c = VVCOL[d.verdict] || "#8c9bb5";
  let html = `<div class="verdict-head" style="margin-top:12px">
    <div class="gauge" style="--p:${d.synthetic_score};--gc:${c}"><span style="color:${c}">${d.synthetic_score}</span></div>
    <div><div class="vbadge" style="color:${c}">${esc(d.verdict.replace(/_/g," "))}</div>
    <div class="vstage">synthetic-voice likelihood · ${d.duration_s}s clip</div></div></div>`;
  (d.features || []).forEach(f => {
    const col = f.synthetic ? "#ff4d57" : "#2ecc71";
    html += `<div class="feat"><span class="fico">${f.synthetic ? "⚠" : "✓"}</span>
      <span class="fname" title="${esc(f.name)}">${esc(f.name)}</span>
      <span class="fdetail" style="margin-left:auto;text-align:right;color:${col}">${esc(f.detail)}</span></div>`;
  });
  html += `<div class="action-box" style="background:${c}22;color:${c}">${esc(d.notes)}</div>`;
  $("#voice-result").innerHTML = html;
};

/* ---------- Computer Vision: deepfake / tamper screen ---------- */
const DFCOL = { LIKELY_MANIPULATED: "#ff4d57", REVIEW: "#f5a623", LIKELY_AUTHENTIC: "#2ecc71", UNREADABLE: "#8c9bb5" };
let dfFile = null;
$("#df-drop").onclick = () => $("#df-file").click();
$("#df-file").onchange = e => {
  const f = e.target.files[0]; if (!f) return;
  dfFile = f;
  $("#df-wrap").innerHTML = `<img src="${URL.createObjectURL(f)}" alt="frame" style="max-height:150px;border-radius:8px">`;
  e.target.value = "";
};
$("#df-run").onclick = async () => {
  if (!dfFile) { $("#df-result").innerHTML = "<div class='result-empty'>⚠ Upload a video-call frame first.</div>"; return; }
  $("#df-result").innerHTML = "<div class='spinner'>Running image forensics…</div>";
  const fd = new FormData(); fd.append("image", dfFile);
  let d;
  try { d = await (await fetch(API + "/api/deepfake/analyze", { method: "POST", body: fd })).json(); }
  catch (e) { $("#df-result").innerHTML = "<div class='result-empty'>Deepfake service error.</div>"; return; }
  const c = DFCOL[d.verdict] || "#8c9bb5";
  let html = `<div class="verdict-head" style="margin-top:12px">
    <div class="gauge" style="--p:${d.manipulation_score};--gc:${c}"><span style="color:${c}">${d.manipulation_score}</span></div>
    <div><div class="vbadge" style="color:${c}">${esc(d.verdict.replace(/_/g," "))}</div>
    <div class="vstage">manipulation likelihood</div></div></div>`;
  (d.features || []).forEach(f => {
    const col = f.suspicious ? "#ff4d57" : "#2ecc71";
    html += `<div class="feat"><span class="fico">${f.suspicious ? "⚠" : "✓"}</span>
      <span class="fname" title="${esc(f.name)}">${esc(f.name)}</span>
      <span class="fdetail" style="margin-left:auto;text-align:right;color:${col}">${esc(f.detail)}</span></div>`;
  });
  html += `<div class="action-box" style="background:${c}22;color:${c}">${esc(d.notes)}</div>`;
  $("#df-result").innerHTML = html;
};

/* ---------- Module 2: Counterfeit ---------- */
const cfDrop = $("#cf-drop");
const CF_HINT = "📷<br>Click or drag &amp; drop a note image";
/* The chosen file lives here, not in the input — the input's value is cleared
   after every pick so re-selecting the SAME file fires change again. */
let cfFile = null;
cfDrop.onclick = () => $("#cf-file").click();
function cfReset(e) {
  if (e) e.stopPropagation();          // don't reopen the file picker
  cfFile = null;
  cfAnalysed = false;
  $("#cf-preview-wrap").innerHTML = CF_HINT;
  $("#cf-result").innerHTML = "<div class='result-empty'>Upload a note image to run the multi-feature security analysis.</div>";
}
function cfPreview(f) {
  cfFile = f;
  cfAnalysed = false;                   // fresh image — no prior analysis yet
  const u = URL.createObjectURL(f);
  $("#cf-preview-wrap").innerHTML =
    `<img src="${u}" alt="note preview">
     <button class="btn small cf-clear" id="cf-clear" title="Remove this image">✕ Remove — choose another</button>`;
  $("#cf-clear").onclick = cfReset;
}
$("#cf-file").onchange = e => {
  if (e.target.files[0]) cfPreview(e.target.files[0]);
  e.target.value = "";
};
/* real drag & drop (and stop the browser navigating away on a stray drop) */
["dragover", "dragenter"].forEach(ev => cfDrop.addEventListener(ev, e => {
  e.preventDefault(); cfDrop.classList.add("drag");
}));
["dragleave", "dragend"].forEach(ev => cfDrop.addEventListener(ev, () => cfDrop.classList.remove("drag")));
cfDrop.addEventListener("drop", e => {
  e.preventDefault(); cfDrop.classList.remove("drag");
  const f = e.dataTransfer.files && e.dataTransfer.files[0];
  if (!f || !f.type.startsWith("image/")) { toast("Drop an image file of the note"); return; }
  cfPreview(f);
});
window.addEventListener("dragover", e => e.preventDefault());
window.addEventListener("drop", e => e.preventDefault());
let cfSeq = 0;                    // guard against out-of-order responses
let cfAnalysed = false;           // has the current image been analysed at least once?
async function runCounterfeit(showLoading = true, force = false) {
  const f = cfFile;
  if (!f) {
    $("#cf-result").innerHTML = "<div class='result-empty'>⚠ Add a note image first — click the box on the left or drag a photo onto it.</div>";
    return;
  }
  cfAnalysed = true;
  const mySeq = ++cfSeq;
  const fd = new FormData();
  fd.append("denomination", $("#cf-denom").value);
  fd.append("serial_number", $("#cf-serial").value);
  // UV is three-state: only send a verdict if the device actually measured it —
  // "no sensor" must not be scored like "no fluorescence" (a red flag).
  const uv = $("#cf-uv").value;
  if (uv !== "unknown") fd.append("uv_feature_present", uv === "present");
  if (force) fd.append("force", "true");
  fd.append("image", f);
  if (showLoading)
    $("#cf-result").innerHTML = "<div class='spinner'>Running forensic analysis…</div>";
  const r = await fetch(API + "/api/counterfeit/analyze", { method: "POST", body: fd });
  const d = await r.json();
  if (mySeq === cfSeq) renderCounterfeit(d);   // only the latest run may render
}
$("#cf-run").onclick = () => runCounterfeit(true);

/* ---- Sample notes: load a reference note straight into the scanner ---- */
const CF_DENOMS = [10, 20, 50, 100, 200, 500, 2000];
async function loadSampleNote(denom, run = true) {
  try {
    const res = await fetch(`/static/showcase/samples/${denom}.jpg`);
    const blob = await res.blob();
    const f = new File([blob], `sample-${denom}.jpg`, { type: blob.type || "image/jpeg" });
    $("#cf-denom").value = String(denom);
    cfPreview(f);
    if (run) runCounterfeit(true);
    switchView("counterfeit");
  } catch (e) { toast("Couldn't load the sample note"); }
}
// label the dropdown-linked button with the current denomination
function cfSampleLabel() {
  const btn = $("#cf-load-sample");
  if (btn) btn.textContent = `＋ Load a ₹${$("#cf-denom").value} sample note`;
}
$("#cf-denom").addEventListener("change", cfSampleLabel);
cfSampleLabel();
if ($("#cf-load-sample"))
  $("#cf-load-sample").onclick = () => loadSampleNote($("#cf-denom").value);
// gallery of every denomination
const dg = $("#denom-samples");
if (dg) {
  dg.innerHTML = CF_DENOMS.map(d => `
    <button class="denom-card" data-d="${d}">
      <img src="/static/showcase/samples/${d}.jpg" alt="₹${d} note" loading="lazy">
      <span class="denom-tag">₹${d}</span>
      <span class="denom-cta">Scan this note ▶</span>
    </button>`).join("");
  $$(".denom-card", dg).forEach(b => b.onclick = () => loadSampleNote(+b.dataset.d));
}

/* Real-vs-Fake gallery: tap a note image to load it into the scanner.
   All showcase notes are ₹500; fakes carry the invalid serial that gets them
   rejected by the RBI grammar check. */
async function loadShowcaseNote(src, serial) {
  try {
    const blob = await (await fetch(src)).blob();
    const f = new File([blob], src.split("/").pop(), { type: blob.type || "image/jpeg" });
    $("#cf-denom").value = "500";
    $("#cf-serial").value = serial || "";
    $("#cf-uv").value = "unknown";
    cfPreview(f);
    runCounterfeit(true);
    // bring the scanner into view so the verdict is visible after the tap
    document.querySelector("#view-counterfeit .card").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) { toast("Couldn't load that note"); }
}
$$(".rf-load").forEach(img => { img.style.cursor = "pointer";
  img.onclick = () => loadShowcaseNote(img.getAttribute("src"), img.dataset.serial || "");
});
/* Changing denomination / UV / serial invalidates the verdict on screen —
   re-run automatically (debounced) so the breakdown always matches the inputs. */
let cfTimer = null;
function cfRerun() {
  // Re-run after ANY prior analysis (breakdown OR mismatch card) so the panel
  // always reflects the currently selected denomination — never a stale result.
  if (!cfFile || !cfAnalysed) return;
  clearTimeout(cfTimer);
  cfTimer = setTimeout(() => runCounterfeit(true), 300);
}
$("#cf-denom").addEventListener("change", cfRerun);
$("#cf-uv").addEventListener("change", cfRerun);
$("#cf-serial").addEventListener("input", cfRerun);
const CFV = { GENUINE: "#2ecc71", SUSPECT: "#f5a623", COUNTERFEIT: "#ff4d57", UNREADABLE: "#8c9bb5" };
function renderCounterfeit(d) {
  // Denomination-identity gate fired: the image reads as a different note.
  if (d.verdict === "MISMATCH") {
    const idd = d.identified_denomination;
    $("#cf-result").innerHTML = `
      <div class="cf-mismatch">
        <div class="cfm-head">⚠ Denomination mismatch</div>
        <p>You selected <b>₹${d.denomination}</b>, but this image reads as a <b>₹${idd}</b> note.</p>
        <p class="muted" style="font-size:12px">${d.notes}</p>
        <div class="cfm-actions">
          <button class="btn primary" id="cf-switch">Analyze as ₹${idd} ▶</button>
          <button class="btn" id="cf-force">Proceed as ₹${d.denomination} anyway</button>
        </div>
      </div>`;
    $("#cf-switch").onclick = () => { $("#cf-denom").value = String(idd); runCounterfeit(true); };
    $("#cf-force").onclick = () => runCounterfeit(true, true);
    return;
  }
  const c = CFV[d.verdict];
  let html = `<div class="verdict-head">
    <div class="gauge" style="--p:${d.authenticity_score};--gc:${c}"><span style="color:${c}">${d.authenticity_score}</span></div>
    <div><div class="vbadge" style="color:${c}">${d.verdict}</div>
    <div class="vstage">Authenticity score · ₹${d.denomination}</div></div></div>`;
  (d.features || []).forEach(f => {
    const col = f.passed ? "#2ecc71" : "#ff4d57";
    html += `<div class="feat"><span class="fico">${f.passed ? "✓" : "✗"}</span>
      <span class="fname" title="${esc(f.name)}">${esc(f.name)}</span>
      <span class="fbar"><i style="width:${Math.round(f.confidence*100)}%;background:${col}"></i></span>
      <span class="fpct">${Math.round(f.confidence*100)}%</span></div>
      <div class="fdetail">${esc(f.detail)}</div>`;
  });
  html += `<div class="action-box" style="background:${c}22;color:${c}">${d.notes}</div>`;
  $("#cf-result").innerHTML = html;
}

/* ---------- Module 3: Fraud graph ---------- */
let fraudLoaded = false, fraudData = null, nodes = [], links = [], selCamp = null;
function ensureFraud() { if (!fraudLoaded) { runFraud(); runIndiaUpi(); } }
$("#fraud-run").onclick = runFraud;
async function runFraud() {
  selCamp = null;
  $("#fraud-panel").innerHTML = skel(9);
  const r = await fetch(`${API}/api/fraud/analyze`);
  fraudData = await r.json();
  fraudLoaded = true;
  buildGraph();
  renderCampaigns();
}

/* Real India UPI fraud aggregate intelligence */
async function runIndiaUpi() {
  const body = $("#iu-body"); if (!body) return;
  body.innerHTML = skel(6, 15);
  let d;
  try { d = await (await fetch(API + "/api/fraud/india_stats")).json(); }
  catch (e) { body.innerHTML = "<p class='muted'>India UPI data unavailable.</p>"; return; }
  if (!d.available) {
    body.innerHTML = "<div class='result-empty'>Run <code>sample_data/fetch_india_upi.py</code> (Kaggle token) to load the India UPI fraud dataset.</div>";
    return;
  }
  $("#iu-meta").textContent = d.source;
  const kpis = [
    [d.cases.toLocaleString("en-IN"), "fraud cases", "#3ea6ff"],
    [d.total_loss_str, "total loss", "#ff4d57"],
    ["₹" + d.avg_loss_inr.toLocaleString("en-IN"), "avg / case", "#f5a623"],
    [d.otp_shared_pct + "%", "shared OTP/PIN", "#ff7a45"],
    [d.recovery_pct + "%", "fully recovered", "#2ecc71"],
  ];
  const bars = (title, arr) => {
    const max = Math.max(...arr.map(x => x.count));
    return `<div class="iu-col"><div class="iu-h">${title}</div>` + arr.map(x =>
      `<div class="iu-row"><span class="iu-l">${x.label}</span>
        <span class="iu-bar"><i style="width:${Math.round(100*x.count/max)}%"></i></span>
        <span class="iu-c">${x.count}</span></div>`).join("") + "</div>";
  };
  body.innerHTML =
    `<div class="iu-kpis">` + kpis.map(k =>
      `<div class="iu-kpi"><div class="iu-v" style="color:${k[2]}">${k[0]}</div><div class="iu-lab">${k[1]}</div></div>`).join("") + `</div>
     <div class="iu-grid">
       ${bars("Fraud type", d.by_fraud_type)}
       ${bars("Lure used", d.by_lure)}
       ${bars("UPI app", d.by_app)}
       ${bars("Top victim states", d.by_state)}
     </div>`;
  animateKpis(".iu-kpis");
}
const NCOL = { victim: "#3ea6ff", acct: "#ff4d57", phone: "#f5a623", device: "#8b5cf6", cashout: "#ff2d95", upi: "#2ecc71", wallet: "#ffb020", crypto: "#ff2d95" };
let fraudDims = { W: 760, H: 460 };
function buildGraph() {
  const cv = $("#fraud-canvas");
  fraudDims = sizeCanvasForDPR(cv);
  const W = fraudDims.W, H = fraudDims.H;
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
  const c = fraudDims.c || $("#fraud-canvas").getContext("2d");
  c.clearRect(0, 0, fraudDims.W, fraudDims.H);
  const isMoney = t => t === "transfer" || t === "upi_transfer";
  links.forEach(l => {
    const a = nodes[l.s], b = nodes[l.t];
    c.strokeStyle = isMoney(l.type) ? "rgba(255,77,87,.5)" : "rgba(140,155,181,.22)";
    c.lineWidth = isMoney(l.type) ? Math.min(4, 1 + (l.amount||0)/300000) : 1;
    c.beginPath(); c.moveTo(a.x, a.y); c.lineTo(b.x, b.y); c.stroke();
  });
  // All ringleader (kingpin) node ids across campaigns — drawn big + labelled.
  const kingpins = new Set((fraudData.campaigns || []).flatMap(c => c.kingpin_nodes || []));
  const labelTypes = ["acct", "crypto", "wallet", "upi"];
  nodes.forEach(n => {
    const inCamp = selCamp && selCamp.nodes.includes(n.id);
    const king = kingpins.has(n.id);
    const r = king ? 12 : (["crypto", "wallet", "device"].includes(n.type) ? 8 : (n.type === "acct" ? 7 : 6));
    c.globalAlpha = (selCamp && !inCamp) ? 0.15 : 1;
    if (king) {                                   // glow behind ringleader
      c.beginPath(); c.arc(n.x, n.y, r + 6, 0, 7);
      c.fillStyle = "rgba(255,77,87,.20)"; c.fill();
    }
    c.beginPath(); c.arc(n.x, n.y, r, 0, 7);
    c.fillStyle = NCOL[n.type] || "#888"; c.fill();
    if (king || inCamp) { c.lineWidth = king ? 2.5 : 2; c.strokeStyle = "#fff"; c.stroke(); }
    c.globalAlpha = 1;
    // Label the ringleader with text only for the SELECTED gang (avoids a wall
    // of overlapping "RINGLEADER" tags when every gang's kingpin shows at once).
    if (king && selCamp && inCamp) {
      c.fillStyle = "#ff8a92"; c.font = "bold 10px sans-serif"; c.textAlign = "center";
      c.fillText("★ RINGLEADER", n.x, n.y - r - 6);
      c.fillStyle = "#cdd9ec"; c.font = "9px sans-serif";
      c.fillText(n.id.split(":")[1], n.x, n.y + r + 12);
    } else if (!king && nodes.length < 30 && labelTypes.includes(n.type)) {
      c.fillStyle = "#cdd9ec"; c.font = "9px sans-serif"; c.textAlign = "center";
      c.fillText(n.id.split(":")[1], n.x, n.y - 11);
    }
  });
}
function renderCampaigns() {
  const s = fraudData.summary;
  let html = `<div class="fraud-summary">
    <b style="color:#fff">${s.campaigns_detected} coordinated gangs found</b> in ${s.total_nodes}
    linked entities — <b style="color:#ff8a92">₹${(s.total_projected_loss_inr/100000).toFixed(1)} lakh</b> at risk.
    <div style="font-size:10.5px;margin-top:4px">Click a gang to highlight it on the map.</div>
    ${s.note ? `<div style="font-size:11px;color:#ffce6b;margin-top:4px">ⓘ ${s.note}</div>` : ""}</div>`;
  html += fraudData.campaigns.map((c, i) => {
    const lead = c.projected_days_to_100_victims
      ? `<span class="lead">~${c.projected_days_to_100_victims} days to 100 victims</span>` : "—";
    const rc = c.risk_index >= 70 ? "#ff4d57" : (c.risk_index >= 40 ? "#f5a623" : "#3ea6ff");
    return `<div class="camp" data-id="${c.campaign_id}">
      <h4>Gang #${i + 1} <span class="camp-risk" style="background:${rc}22;color:${rc}">risk ${c.risk_index}/100</span></h4>
      <div class="row"><span>👤 People scammed</span><b>${c.victim_count}</b></div>
      <div class="row"><span>⚡ New victims / day</span><b>${c.victims_per_day ?? "—"}</b></div>
      <div class="row"><span>⏳ Time to 100 victims</span><b>${lead}</b></div>
      <div class="row"><span>🏦 Money-mule accounts</span><b>${c.linked_accounts}</b></div>
      <div class="row"><span>💸 Money at risk</span><b>${c.estimated_loss_str}</b></div>
      <div class="row"><span>★ Ringleader account</span><b>${c.kingpin_nodes.map(k=>k.split(":")[1]).join(", ")}</b></div>
      <div style="font-size:10.5px;color:var(--muted);margin-top:6px">🔒 court-ready evidence hash ${c.evidence_hash_sha256.slice(0,12)}…</div>
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
const GEO_LABEL = { digital_arrest: "Digital arrest", cyber_fraud: "Cyber fraud",
  ficn_seizure: "FICN seizure", scam_compound: "Scam compound (source)" };
let threatLayer = null, stateLayer = null;
async function runGeo() {
  $("#geo-panel").innerHTML = skel(6, 16);
  $("#geo-states").innerHTML = skel(8);
  $("#cm-body").innerHTML = skel(6);
  const r = await fetch(API + "/api/geo/analyze");
  const d = await r.json();
  map = L.map("map", { attributionControl: false, minZoom: 3, maxZoom: 8, worldCopyJump: false })
    .setView([20.5, 80], 4.4);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    { subdomains: "abcd", maxZoom: 19 }).addTo(map);
  L.control.attribution({ position: "bottomleft", prefix: false })
    .addAttribution("© OpenStreetMap · © CARTO").addTo(map);

  // Layer 1 (default): categorical threat hotspots
  threatLayer = L.layerGroup().addTo(map);
  d.points.forEach(p => {
    L.circleMarker([p.lat, p.lon], {
      radius: 4 + p.intensity * 1.1, color: "#0a0e17", weight: 1.5,
      fillColor: GEO_COL[p.type], fillOpacity: .9,
    }).addTo(threatLayer).bindPopup(
      `<b>${p.label}</b><br>${GEO_LABEL[p.type] || p.type}<br>intensity ${p.intensity}/10`);
  });
  // legend
  const legend = L.control({ position: "bottomright" });
  legend.onAdd = () => {
    const el = L.DomUtil.create("div", "map-legend");
    el.innerHTML = "<b>Threat type</b>" + Object.keys(GEO_LABEL).map(k =>
      `<span><i style="background:${GEO_COL[k]}"></i>${GEO_LABEL[k]}</span>`).join("");
    return el;
  };
  legend.addTo(map);
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
    // NCRB states as a SEPARATE toggleable overlay (off by default → no clutter)
    stateLayer = L.layerGroup();
    ss.states.forEach(s => L.circleMarker([s.lat, s.lon], {
      radius: 5 + 15 * s.cases / max, color: "#a78bfa", fillColor: "#8b5cf6",
      fillOpacity: .12, weight: 1.5,
    }).addTo(stateLayer).bindPopup(`<b>${s.state}</b><br>NCRB 2022 cyber cases: ${s.cases.toLocaleString("en-IN")}`));
    L.control.layers(null,
      { "Threat hotspots": threatLayer, "NCRB cybercrime (2022)": stateLayer },
      { collapsed: window.innerWidth < 760 }).addTo(map);
  }
  // Real city-level cybercrime by motive
  const cm = d.cybercrime_motives;
  if (cm && cm.available) {
    $("#cm-meta").textContent = `${cm.source} · ${cm.cities_covered} cities`;
    const maxM = cm.by_motive[0].count;
    const fraudShare = Math.round(100 * (cm.by_motive.find(m => m.label === "Fraud")?.count || 0) / cm.total_cases);
    const bars = cm.by_motive.slice(0, 10).map(m => `<div class="stbar">
      <span class="stn">${m.label}</span>
      <span class="stb"><i style="width:${Math.round(100*m.count/maxM)}%"></i></span>
      <span class="stc">${m.count.toLocaleString("en-IN")}</span></div>`).join("");
    $("#cm-body").innerHTML =
      `<div><div class="iu-h">Cybercrime by motive (national)</div>${bars}</div>
       <div><div class="iu-h" style="color:var(--ok)">Key insight</div>
        <div class="perf-kpi" style="text-align:left;padding:16px"><div class="iu-v" style="color:#ff4d57">${fraudShare}%</div>
        <div class="iu-lab" style="font-size:12px">of all Indian cybercrime is <b>financial fraud</b> — the exact threat Prahari targets across scam, UPI-graph and counterfeit modules.</div></div>
        <div class="muted" style="font-size:11px;margin-top:10px">${cm.total_cases.toLocaleString("en-IN")} motive-classified cases across ${cm.cities_covered} cities (NCRB).</div></div>`;
  } else if ($("#cm-body")) {
    $("#cm-body").innerHTML = "<p class='muted'>City-level cybercrime data unavailable.</p>";
  }
  // robust sizing: the container was hidden until this view opened
  [120, 450, 900].forEach(t => setTimeout(() => map.invalidateSize(), t));
  window.addEventListener("resize", () => map && map.invalidateSize());
}

/* ---------- Module 5: Shield ---------- */
let SH_UI = null;   // localized UI strings for the currently selected language
fetch(API + "/api/shield/languages").then(r => r.json()).then(L => {
  $("#sh-lang").innerHTML = Object.entries(L).map(([c, n]) => `<option value="${c}">${n}</option>`).join("");
});
/* Load localized UI for a language and (re)start the chat in that language —
   greeting, sample chips, placeholder, buttons and advice all switch, so a
   Hindi user sees a pure-Hindi assistant. */
async function shLoadUI(lang, resetChat) {
  try { SH_UI = await (await fetch(API + "/api/shield/ui?lang=" + lang)).json(); }
  catch (e) { return; }
  $("#sh-input").placeholder = SH_UI.placeholder;
  $("#sh-send").textContent = SH_UI.send;
  if (SH_UI.guard_cta) $("#sh-guard-open").textContent = SH_UI.guard_cta;
  if (!$("#sh-guard").hidden) guardRender();   // keep an open guard localized
  if (SH_UI.actions_title && $("#sh-actions-title")) $("#sh-actions-title").textContent = SH_UI.actions_title;
  if (SH_UI.recent && $("#sh-recent-title")) $("#sh-recent-title").textContent = SH_UI.recent;
  if (resetChat) { $("#sh-chat").innerHTML = ""; botMsg(SH_UI.greeting); }
  shSuggest(null);
  shActions(SH_UI.default_actions, "");
  shRecent();
}
$("#sh-lang").addEventListener("change", () => shLoadUI($("#sh-lang").value, true));
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
function botTyping() {
  const d = document.createElement("div");
  d.className = "msg bot typing"; d.innerHTML = "<i></i><i></i><i></i>";
  $("#sh-chat").appendChild(d); $("#sh-chat").scrollTop = 1e9;
  return d;
}
/* Suggestion chips (localized samples for the current language). */
function shSuggest(lastText) {
  const samples = (SH_UI && SH_UI.samples) || [];
  const others = samples.filter(s => s[1] !== lastText).slice(0, lastText ? 2 : 3);
  $("#sh-chips").innerHTML = others.map(s =>
    `<button class="sh-chip" data-t="${encodeURIComponent(s[1])}">${esc(s[0])}</button>`).join("");
  $$("#sh-chips .sh-chip[data-t]").forEach(b => b.onclick = () => {
    $("#sh-input").value = decodeURIComponent(b.dataset.t);
    sendShield();
  });
}

/* Recent checks — kept on this device only (localStorage), no server PII */
const SH_KEY = "prahari_recent_checks";
function shRecent() {
  let a = [];
  try { a = JSON.parse(localStorage.getItem(SH_KEY) || "[]"); } catch (e) {}
  $("#sh-recent").innerHTML = a.length ? a.map(r =>
    `<div class="rchk"><span class="feed-chip">${r.tm}</span>
       <span class="rc-txt">${esc(r.t)}</span>
       <span class="rc-tag" style="background:${r.c}22;color:${r.c}">${r.v.replace("_", " ")}</span></div>`).join("")
    : `<p class='muted' style='font-size:12px;margin:0'>${esc((SH_UI && SH_UI.no_checks) || "No checks yet — tap a sample under the chat.")}</p>`;
}
function shPushRecent(text, verdict) {
  let a = [];
  try { a = JSON.parse(localStorage.getItem(SH_KEY) || "[]"); } catch (e) {}
  a.unshift({ t: text.slice(0, 44) + (text.length > 44 ? "…" : ""), v: verdict,
              c: VCOLOR[verdict] || "#8fa1bf",
              tm: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) });
  localStorage.setItem(SH_KEY, JSON.stringify(a.slice(0, 5)));
  shRecent();
}
function shActions(steps, tone) {
  $("#sh-actions").innerHTML = steps.map((s, i) =>
    `<div class="act-step ${tone || ""}"><i>${i + 1}</i><span>${esc(s)}</span></div>`).join("");
}
function shAfterVerdict(text, d) {
  shPushRecent(text, d.verdict);
  if (d.guided_report && d.guided_report.next_steps)
    shActions(d.guided_report.next_steps, "act-hot");
  else if (d.verdict === "SAFE" && SH_UI && SH_UI.safe_actions)
    shActions(SH_UI.safe_actions, "act-ok");
  shSuggest(text);
}
/* Localized "Risk N/100 · VERDICT" line + verdict name. */
function shVerdictLine(d) {
  const u = SH_UI || {};
  const name = (u.verdict_names && u.verdict_names[d.verdict]) || d.verdict.replace("_", " ");
  return `<div style="font-size:11px;color:var(--muted);margin-top:4px">${esc(u.risk_word || "Risk")} ${d.risk_score}/100 · ${esc(name)}</div>`;
}
/* ---------- Live Call Guard — protection DURING the call ----------
   This is what separates Citizen Shield from the analyst-facing Digital Arrest
   module: the analyst analyses a transcript AFTER the fact; the citizen is
   walked through the scam WHILE it is happening, then handed a golden-hour
   clock the moment money moves. */
let guardTicked = new Set(), guardTimer = null;
function guardRender() {
  if (!SH_UI || !SH_UI.guard_steps) return;
  $("#guard-title").textContent = SH_UI.guard_title;
  $("#guard-sub").textContent = SH_UI.guard_sub;
  $("#guard-exit").textContent = SH_UI.guard_exit;
  $("#guard-other-q").textContent = SH_UI.guard_other_q || "";
  $("#guard-other-in").placeholder = SH_UI.guard_other_ph || "";
  $("#guard-other-btn").textContent = SH_UI.guard_other_btn || "";
  $("#guard-steps").innerHTML = SH_UI.guard_steps.map(([q, act], i) => `
    <div class="gstep ${guardTicked.has(i) ? "on" : ""}" data-i="${i}">
      <span class="gs-box">${guardTicked.has(i) ? "✓" : ""}</span>
      <div class="gs-body"><b>${esc(q)}</b>
        ${guardTicked.has(i) ? `<em>${esc(act)}</em>` : ""}</div>
    </div>`).join("");
  $$("#guard-steps .gstep").forEach(el => el.onclick = () => {
    const i = +el.dataset.i;
    guardTicked.has(i) ? guardTicked.delete(i) : guardTicked.add(i);
    guardRender();
  });
  // risk climbs with each confirmed tactic (+ any free-text scam verdict)
  const n = Math.min(5, guardTicked.size + guardExtra);
  const pct = Math.min(100, Math.round(n / 5 * 100));
  const lvl = n === 0 ? 0 : (n <= 2 ? 1 : 2);
  const col = ["#2ecc71", "#f5a623", "#ff4d57"][lvl];
  $("#guard-bar").style.width = pct + "%";
  $("#guard-bar").style.background = col;
  $("#guard-verdict").textContent = SH_UI.guard_lvl[lvl];
  $("#guard-verdict").style.color = col;
  $("#guard-verdict").style.background = col + "1a";
  // money question appears once it looks like a scam
  if (lvl < 2) { $("#guard-money").innerHTML = ""; clearInterval(guardTimer); guardTimer = null; return; }
  if ($("#guard-money").dataset.on === "1") return;
  $("#guard-money").dataset.on = "1";
  $("#guard-money").innerHTML = `
    <div class="gm-q">${esc(SH_UI.guard_money_q)}</div>
    <div class="gm-btns">
      <button class="btn" id="gm-no">${esc(SH_UI.guard_money_no)}</button>
      <button class="btn primary" id="gm-yes">${esc(SH_UI.guard_money_yes)}</button>
    </div>`;
  $("#gm-no").onclick = () => { $("#guard-money").innerHTML =
    `<div class="gm-q" style="color:#7ee2a8">✓ ${esc(SH_UI.guard_lvl[2])}</div>`; };
  $("#gm-yes").onclick = guardGoldenHour;
}
/* Money already sent → start the golden-hour countdown + exact 1930 script. */
function guardGoldenHour() {
  const end = Date.now() + 60 * 60 * 1000;
  $("#guard-money").innerHTML = `
    <div class="gm-timer"><div class="gm-clock" id="gm-clock">60:00</div>
      <div class="gm-lab">${esc(SH_UI.guard_timer)}</div></div>
    <a class="btn primary gm-call" href="tel:1930">${esc(SH_UI.guard_call)}</a>
    <div class="gm-steps">${SH_UI.guard_after.map((a, i) =>
      `<div class="act-step act-hot"><i>${i + 1}</i><span>${esc(a)}</span></div>`).join("")}</div>`;
  clearInterval(guardTimer);
  guardTimer = setInterval(() => {
    const left = Math.max(0, end - Date.now());
    const m = Math.floor(left / 60000), sec = Math.floor(left % 60000 / 1000);
    const el = $("#gm-clock");
    if (!el) return clearInterval(guardTimer);
    el.textContent = `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
    if (left <= 0) clearInterval(guardTimer);
  }, 1000);
}
/* "None of these" — the citizen describes it in their own words and we run the
   real classifier, so the guard still works for scripts we haven't listed. */
let guardExtra = 0;   // extra risk contributed by free-text checks
async function guardAsk() {
  const t = $("#guard-other-in").value.trim();
  if (!t) return;
  $("#guard-other-out").innerHTML = "<div class='spinner'></div>";
  let d;
  try {
    d = await (await fetch(API + "/api/shield/assess", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: t, lang: $("#sh-lang").value }),
    })).json();
  } catch (e) { $("#guard-other-out").innerHTML = ""; return; }
  const c = VCOLOR[d.verdict] || "#8fa1bf";
  $("#guard-other-out").innerHTML = `
    <div class="go-out" style="border-color:${c}55;background:${c}14">
      <b style="color:${c}">${esc(d.message)}</b>
      ${(d.why || []).length ? `<ul class="why">${d.why.slice(0,3).map(w => `<li>${esc(w)}</li>`).join("")}</ul>` : ""}
    </div>`;
  $("#guard-other-in").value = "";
  // a scam verdict here counts toward the live risk meter like a ticked tactic
  if (d.verdict === "ACTIVE_SCAM" || d.verdict === "HIGH_RISK") guardExtra = 3;
  else if (d.verdict === "SUSPICIOUS") guardExtra = Math.max(guardExtra, 1);
  guardRender();
}
$("#guard-other-btn").onclick = guardAsk;
$("#guard-other-in").addEventListener("keydown", e => { if (e.key === "Enter") guardAsk(); });

function guardOpen(on) {
  $("#sh-guard").hidden = !on;
  $("#sh-phone").hidden = on;
  $("#sh-guard-open").hidden = on;
  if (on) {
    guardTicked = new Set(); guardExtra = 0;
    $("#guard-money").dataset.on = ""; $("#guard-money").innerHTML = "";
    $("#guard-other-out").innerHTML = ""; $("#guard-other-in").value = "";
    guardRender();
  }
  else { clearInterval(guardTimer); guardTimer = null; }
}
$("#sh-guard-open").onclick = () => guardOpen(true);
$("#guard-exit").onclick = () => guardOpen(false);

/* Kick off the chat in the default (English) language. */
shLoadUI("en", true);
$("#sh-send").onclick = sendShield;
$("#sh-input").addEventListener("keydown", e => { if (e.key === "Enter") sendShield(); });
$("#sh-upload").onclick = () => $("#sh-file").click();
$("#sh-file").onchange = async e => {
  const f = e.target.files[0]; if (!f) return;
  userMsg("📷 " + f.name);
  const ty = botTyping();
  const fd = new FormData(); fd.append("lang", $("#sh-lang").value); fd.append("image", f);
  const r = await fetch(API + "/api/shield/ocr", { method: "POST", body: fd });
  const d = await r.json();
  ty.remove();
  if (d.error) { botMsg("⚠️ " + esc(d.error)); return; }
  const ocrLbl = (SH_UI && SH_UI.ocr_label) || "📄 OCR text";
  let html = `<div style="font-size:11px;color:var(--muted);margin-bottom:5px">${ocrLbl}: "${esc((d.extracted_text||"").slice(0,140))}…"</div><b>${esc(d.message)}</b>`
    + shVerdictLine(d);
  if (d.why && d.why.length) html += `<ul class="why">${d.why.map(w=>`<li>${esc(w)}</li>`).join("")}</ul>`;
  botMsg(html);
  shPushRecent("📷 " + ((d.extracted_text || "screenshot").slice(0, 40)), d.verdict);
  if (d.guided_report && d.guided_report.next_steps) shActions(d.guided_report.next_steps, "act-hot");
  $("#sh-file").value = "";
};
async function sendShield() {
  const t = $("#sh-input").value.trim();
  if (!t) return;
  userMsg(t); $("#sh-input").value = "";
  const ty = botTyping();
  let d;
  try {
    const r = await fetch(API + "/api/shield/assess", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: t, lang: $("#sh-lang").value }),
    });
    d = await r.json();
  } catch (e) {
    ty.remove(); botMsg("⚠️ Could not reach the Shield service — is the backend running?");
    return;
  }
  ty.remove();
  let html = `<b>${esc(d.message)}</b>` + shVerdictLine(d);
  if (d.why && d.why.length)
    html += `<ul class="why">${d.why.map(w => `<li>${esc(w)}</li>`).join("")}</ul>`;
  if (d.guided_report) {
    const fileLbl = (SH_UI && SH_UI.file_label) || "📋 I can file this for you:";
    html += `<div style="margin-top:7px;font-size:12px"><b>${esc(fileLbl)}</b><br>${d.guided_report.next_steps.map(s=>"• "+esc(s)).join("<br>")}</div>`;
  }
  botMsg(html);
  shAfterVerdict(t, d);
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
  animateKpis("#perf-kpis");

  // Held-out, independently-sourced benchmark — shown separately & honestly.
  const h = d.held_out;
  if (h) {
    $("#perf-heldout").innerHTML = `
      <div class="heldout">
        <div class="heldout-h">🔬 Held-out test — <b>independently sourced</b>, not self-generated
          <span class="sim-chip" style="margin-left:8px">true out-of-sample</span></div>
        <div class="heldout-kpis">
          <span><b style="color:${col(h.precision,90)}">${h.precision}%</b> precision</span>
          <span><b style="color:${col(h.recall,85)}">${h.recall}%</b> recall</span>
          <span><b style="color:${col(h.accuracy,85)}">${h.accuracy}%</b> accuracy</span>
          <span><b style="color:${h.false_positive_rate<=5?'#2ecc71':'#ff4d57'}">${h.false_positive_rate}%</b> false alarms</span>
          <span class="muted">${h.size} msgs · ${h.scam} scam / ${h.benign} benign</span>
        </div>
        <div class="muted" style="font-size:11px;margin-top:8px">${esc(h.source)} We report this lower-but-honest number separately from the in-house corpus above.</div>
      </div>`;
  }

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
}

async function runCounterfeitPerf() {
  const r = await fetch(API + "/api/eval/counterfeit");
  const d = await r.json();
  const o = d.overall;
  $("#cf-src").innerHTML = `Evaluated against <b>${o.total_genuine_notes} genuine RBI notes</b> across ${o.denominations} denominations (controlled capture). Source: ${d.source}. Real counterfeits can't be used (illegal) — fake-detection is shown via a synthetic print-quality stress test. A real-world mobile-photo stress test (195 Kaggle images) is documented in the README — it quantifies the v1-heuristic ceiling and the CNN upgrade on the roadmap.`;
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
  animateKpis("#cf-kpis");

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
