/* ParkSight dashboard — talks to the FastAPI backend, renders map + charts. */
const $ = (s) => document.querySelector(s);
const fmt = (n) => n.toLocaleString("en-IN");
const hourLabel = (h) => h == null ? "—" :
  `${String(h).padStart(2, "0")}:00`;

Chart.defaults.color = "#93a2c4";
Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
Chart.defaults.borderColor = "rgba(120,150,210,.10)";

let MAP, HEATLAYER, HEATDATA = [], SPOTLAYER;

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(path + " -> " + r.status);
  return r.json();
}

// ---------------- KPIs + meta ----------------
function renderOverview(o) {
  const k = o.kpis, m = o.meta;
  $("#meta").innerHTML =
    `<b>${fmt(m.source_rows)}</b> records · ${m.date_from} → ${m.date_to}` +
    `<br>${m.cell_metres} m grid · generated ${m.generated}`;
  $("#footmeta").textContent =
    `ParkSight · ${fmt(m.source_rows)} Bengaluru enforcement records`;
  $("#disclaimer").textContent = m.note;

  const kpis = [
    { v: fmt(k.total_violations), l: "Parking violations", s: "logged in period" },
    { v: k.high_impact_pct + "%", l: "High-impact", s: `${fmt(k.high_impact_violations)} main-road / junction`, hot: 1 },
    { v: k.worst_zone, l: "Worst zone", s: `impact ${fmt(Math.round(k.worst_zone_impact))}` },
    { v: hourLabel(k.peak_hour), l: "Peak hour (IST)", s: "city-wide" },
    { v: fmt(k.distinct_hotspot_cells), l: "Hotspot cells", s: "≥2 violations each" },
  ];
  $("#kpis").innerHTML = kpis.map((x) =>
    `<div class="kpi${x.hot ? " hot" : ""}">
       <div class="v">${x.v}</div><div class="l">${x.l}</div><div class="s">${x.s}</div>
     </div>`).join("");
}

// ---------------- Map ----------------
const GRAD = { 0.2: "#3ddc97", 0.45: "#ffd23d", 0.7: "#ff8a3d", 1.0: "#ff4d6d" };

function initMap(heat, spots) {
  HEATDATA = heat;
  MAP = L.map("map", { zoomControl: true, attributionControl: false })
        .setView([12.9716, 77.5946], 12);
  L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    { maxZoom: 19, subdomains: "abcd" }).addTo(MAP);
  L.control.attribution({ prefix: false })
    .addAttribution("© OpenStreetMap · CARTO").addTo(MAP);

  drawHeat("impact");

  SPOTLAYER = L.layerGroup().addTo(MAP);
  spots.forEach((s) => {
    L.circleMarker([s.lat, s.lon], {
      radius: 6, color: "#fff", weight: 1.5,
      fillColor: "#ff4d6d", fillOpacity: .9,
    }).bindPopup(
      `<b>#${s.rank} worst spot</b><br>${fmt(s.count)} violations` +
      `<br>impact ${fmt(s.impact)} · peak ${hourLabel(s.peak_hour)}` +
      `<br><span style="color:#93a2c4">${s.dominant}</span>`
    ).addTo(SPOTLAYER);
  });
}

function drawHeat(mode) {
  if (HEATLAYER) MAP.removeLayer(HEATLAYER);
  const pts = HEATDATA.map((h) => [h.lat, h.lon,
    mode === "impact" ? h.w : Math.min(1, h.n / 60)]);
  HEATLAYER = L.heatLayer(pts, {
    radius: 18, blur: 22, maxZoom: 16, minOpacity: .25, gradient: GRAD,
  }).addTo(MAP);
}

// ---------------- Zones ----------------
function renderZones(zones) {
  const max = zones[0]?.impact || 1;
  $("#zones").innerHTML = zones.map((z) => {
    const j = z.top_junctions?.[0]?.name;
    return `<div class="zone" data-lat="${z.lat}" data-lon="${z.lon}">
      <div class="rk">${z.rank}</div>
      <div>
        <div class="nm">${z.zone}
          ${z.high_pct >= 3 ? `<span class="pill hi">${z.high_pct}% high-impact</span>` : ""}
        </div>
        <div class="sub">${fmt(z.count)} violations · peak ${hourLabel(z.peak_hour)}
          · ${z.dominant.toLowerCase()}${j ? " · " + j : ""}</div>
        <div class="barwrap"><div class="bar" style="width:${(z.impact / max * 100).toFixed(1)}%"></div></div>
      </div>
      <div class="imp"><b>${fmt(Math.round(z.impact))}</b><span>impact</span></div>
    </div>`;
  }).join("");
  document.querySelectorAll(".zone").forEach((el) => {
    el.addEventListener("click", () => {
      const lat = +el.dataset.lat, lon = +el.dataset.lon;
      if (lat && MAP) MAP.setView([lat, lon], 14, { animate: true });
    });
  });
}

// ---------------- Charts ----------------
function impactColor(w) {
  if (w >= 4) return "#ff4d6d";
  if (w >= 3) return "#ff8a3d";
  if (w >= 2) return "#ffd23d";
  return "#4f8cff";
}
function renderCharts(o) {
  const vio = o.violation_breakdown.slice(0, 9);
  new Chart($("#vioChart"), {
    type: "bar",
    data: {
      labels: vio.map((v) => v.type.replace("PARKING", "PKG").slice(0, 22)),
      datasets: [{
        data: vio.map((v) => v.count),
        backgroundColor: vio.map((v) => impactColor(v.weight)),
        borderRadius: 5,
      }],
    },
    options: {
      indexAxis: "y", plugins: { legend: { display: false },
        tooltip: { callbacks: { afterLabel: (c) =>
          "impact weight ×" + vio[c.dataIndex].weight } } },
      scales: { x: { grid: { display: false } }, y: { grid: { display: false } } },
      maintainAspectRatio: false,
    },
  });

  const hrs = o.by_hour;
  new Chart($("#hourChart"), {
    type: "line",
    data: {
      labels: hrs.map((h) => hourLabel(h.hour)),
      datasets: [{
        data: hrs.map((h) => h.count), fill: true, tension: .4,
        borderColor: "#22d3ee", pointRadius: 0, borderWidth: 2,
        backgroundColor: "rgba(34,211,238,.12)",
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false }, ticks: { maxTicksLimit: 8 } },
        y: { grid: { color: "rgba(120,150,210,.08)" } } },
      maintainAspectRatio: false,
    },
  });

  const veh = o.vehicle_breakdown.slice(0, 6);
  new Chart($("#vehChart"), {
    type: "doughnut",
    data: {
      labels: veh.map((v) => v.type),
      datasets: [{ data: veh.map((v) => v.count),
        backgroundColor: ["#4f8cff", "#22d3ee", "#7b5cff", "#3ddc97", "#ffd23d", "#ff8a3d"],
        borderWidth: 0 }],
    },
    options: {
      cutout: "62%",
      plugins: { legend: { position: "right", labels: { boxWidth: 10, font: { size: 11 } } } },
      maintainAspectRatio: false,
    },
  });
}

// ---------------- Recommendations ----------------
function renderRecs(recs) {
  $("#recs").innerHTML = recs.map((r) =>
    `<div class="rec">
       <div><div class="zn">${r.zone}</div>
         <div class="dm">${r.dominant.toLowerCase()} · ${r.share}% of its load in this block</div></div>
       <div class="win">${r.window}<span>${fmt(r.window_load)} cases</span></div>
     </div>`).join("");
}

// ---------------- 7-day forecast ----------------
function renderForecast(f) {
  if (!f) return;
  const hist = f.history, fc = f.forecast;
  const labels = hist.map((h) => h.date).concat(fc.map((p) => p.date));
  const H = hist.length;
  const histData = hist.map((h) => h.value).concat(Array(fc.length).fill(null));
  // connect the forecast line to the last actual point
  const meanData = Array(H - 1).fill(null)
    .concat([hist[H - 1].value], fc.map((p) => p.mean));
  const hiData = Array(H).fill(null).concat(fc.map((p) => p.hi));
  const loData = Array(H).fill(null).concat(fc.map((p) => p.lo));

  const short = (d) => d.slice(5);          // MM-DD
  new Chart($("#fcChart"), {
    type: "line",
    data: {
      labels: labels.map(short),
      datasets: [
        { label: "80% band", data: hiData, borderColor: "transparent",
          backgroundColor: "rgba(123,92,255,.16)", fill: "+1",
          pointRadius: 0, tension: .3 },
        { label: "_lo", data: loData, borderColor: "transparent",
          pointRadius: 0, fill: false, tension: .3 },
        { label: "Actual", data: histData, borderColor: "#22d3ee",
          borderWidth: 2, pointRadius: 0, tension: .3 },
        { label: "Forecast", data: meanData, borderColor: "#7b5cff",
          borderWidth: 2, borderDash: [6, 4], pointRadius: 0, tension: .3 },
      ],
    },
    options: {
      plugins: {
        legend: { labels: { filter: (i) => !i.text.startsWith("_") && i.text !== "80% band",
          boxWidth: 12, font: { size: 11 } } },
        tooltip: { filter: (i) => !i.dataset.label.startsWith("_") },
      },
      scales: { x: { grid: { display: false }, ticks: { maxTicksLimit: 9, font: { size: 10 } } },
        y: { grid: { color: "rgba(120,150,210,.08)" }, beginAtZero: false } },
      maintainAspectRatio: false,
    },
  });

  const trend = f.weekly_trend_pct;
  const next7 = fc.reduce((s, p) => s + p.mean, 0);
  $("#fcNote").innerHTML =
    `Next 7 days: <b style="color:#eaf0ff">~${fmt(next7)}</b> violations ` +
    `(${trend >= 0 ? "+" : ""}${trend}% /week trend, ±${fmt(f.sigma)}/day). ` +
    `Model: linear trend × learned weekday factors — a Saturday is forecast ` +
    `differently from a Tuesday.`;
}

// ---------------- Enforcement coverage curve ----------------
function renderCoverage(cov) {
  const c = cov.curve;
  new Chart($("#covChart"), {
    type: "line",
    data: {
      datasets: [
        { label: "Targeted (worst zones first)",
          data: c.map((p) => ({ x: p.effort_pct, y: p.cov_high })),
          borderColor: "#4f8cff", backgroundColor: "rgba(79,140,255,.12)",
          fill: true, pointRadius: 0, tension: .25, borderWidth: 2.5 },
        { label: "Untargeted (random)",
          data: [{ x: 0, y: 0 }, { x: 100, y: 100 }],
          borderColor: "var(--mut2)", borderDash: [5, 5], borderWidth: 1.5,
          pointRadius: 0, fill: false },
      ],
    },
    options: {
      plugins: { legend: { labels: { boxWidth: 12, font: { size: 11 } } },
        tooltip: { callbacks: { title: (i) => `${i[0].parsed.x}% of zones`,
          label: (i) => `${i.parsed.y}% of high-impact covered` } } },
      scales: {
        x: { type: "linear", min: 0, max: 100, title: { display: true,
          text: "% of enforcement effort (zones deployed)", font: { size: 11 } },
          grid: { color: "rgba(120,150,210,.08)" } },
        y: { min: 0, max: 100, title: { display: true,
          text: "% high-impact covered", font: { size: 11 } },
          grid: { color: "rgba(120,150,210,.08)" } },
      },
      maintainAspectRatio: false,
    },
  });

  const m = cov.markers;
  $("#covMarkers").innerHTML = [80, 50].map((p) =>
    `<div class="cov-chip"><b>${p}% covered</b>
       <span class="z">${m[p].zones} zones</span> · ${m[p].effort_pct}% effort</div>`
  ).join("") +
    `<div class="cov-chip"><b>${cov.total_zones} zones</b> total across the city</div>`;
}

// ---------------- Rising hotspot zones ----------------
function renderRisingZones(zf) {
  const arrow = { rising: "▲", falling: "▼", steady: "→" };
  const sub = {
    rising: "activity climbing — pre-position patrols",
    falling: "cooling vs. prior fortnight — can reallocate",
    steady: "stable demand — hold current coverage",
  };
  $("#fzones").innerHTML = zf.map((z) =>
    `<div class="fzone">
       <div class="rk">${z.rank}</div>
       <div>
         <div class="nm">${z.zone}</div>
         <div class="sub">${sub[z.trend]}</div>
       </div>
       <div class="trend ${z.trend}">${arrow[z.trend]} ${z.momentum_pct >= 0 ? "+" : ""}${z.momentum_pct}%</div>
       <div class="load"><b>${fmt(z.pred_next7)}</b><span>next 7d</span></div>
     </div>`).join("");
}

// ---------------- Live scorer ----------------
const SCORER_TYPES = [
  ["PARKING IN A MAIN ROAD", 5], ["NO PARKING", 3], ["DOUBLE PARKING", 4.5],
  ["WRONG PARKING", 2], ["PARKING NEAR ROAD CROSSING", 4],
  ["PARKING NEAR BUSTOP/SCHOOL/HOSPITAL ETC", 3], ["PARKING ON FOOTPATH", 1.5],
];
const picked = new Set(["PARKING IN A MAIN ROAD", "NO PARKING"]);

function renderPicker() {
  $("#vioPicker").innerHTML = SCORER_TYPES.map(([t, w]) =>
    `<div class="chip${picked.has(t) ? " on" : ""}" data-t="${t}">
       ${t.replace("PARKING", "Pkg").replace(/ ETC$/, "").toLowerCase()}<b>×${w}</b></div>`
  ).join("");
  document.querySelectorAll("#vioPicker .chip").forEach((c) =>
    c.addEventListener("click", () => {
      const t = c.dataset.t;
      picked.has(t) ? picked.delete(t) : picked.add(t);
      renderPicker(); score();
    }));
}
async function score() {
  const count = +$("#countRange").value;
  $("#countOut").textContent = count;
  const r = await api("/api/score", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ violation_types: [...picked], daily_count: count }),
  });
  $("#scoreOut").innerHTML =
    `<div class="num ${r.band}">${fmt(r.impact_score)}</div>
     <div class="band ${r.band}">${r.band} priority</div>
     <div class="act">${r.recommended_action}</div>`;
}

// ---------------- Boot ----------------
(async function () {
  try {
    const [o, z, h, rec, cov, fore] = await Promise.all([
      api("/api/overview"), api("/api/zones"),
      api("/api/heat"), api("/api/recommendations"),
      api("/api/coverage"), api("/api/forecast"),
    ]);
    renderOverview(o);
    renderCharts(o);
    renderZones(z.zones);
    renderRecs(rec.recommendations);
    initMap(h.heat, h.top_spots);
    renderForecast(fore.forecast);
    renderCoverage(cov);
    renderRisingZones(fore.zone_forecast);

    $("#heatToggle").addEventListener("click", (e) => {
      const b = e.target.closest("button"); if (!b) return;
      document.querySelectorAll("#heatToggle button").forEach((x) => x.classList.remove("on"));
      b.classList.add("on"); drawHeat(b.dataset.mode);
    });
    renderPicker();
    $("#countRange").addEventListener("input", score);
    score();
  } catch (err) {
    document.body.insertAdjacentHTML("afterbegin",
      `<div style="position:fixed;top:0;left:0;right:0;background:#ff4d6d;color:#fff;
       padding:10px;text-align:center;z-index:99">Failed to load: ${err.message}
       — is the API running? (uvicorn backend.app:app --port 8010)</div>`);
    console.error(err);
  }
})();
