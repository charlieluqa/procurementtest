import json, html

with open('/workspace/dashboard_payload.json') as f:
    payload = json.load(f)

json_str = json.dumps(payload, separators=(',', ':'))
# Escape for JS string embedding if needed, but we can assign as JS object directly
# because JSON is a subset of JS object literal syntax.

html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Procurement Intelligence Dashboard — Synthetic NHS Exercise</title>
<style>
  :root {
    --bg: #0b1020;
    --surface: #111827;
    --elevated: #1a2332;
    --border: #223045;
    --text: #e8ecf1;
    --muted: #9aa3b2;
    --accent: #4f8cff;
    --accent-2: #2dd4bf;
    --danger: #f87171;
    --warning: #fbbf24;
    --success: #34d399;
    --info: #60a5fa;
    --font: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0; font-family: var(--font); background: var(--bg); color: var(--text);
    line-height: 1.45; font-size: 14px;
  }
  header {
    background: linear-gradient(180deg, rgba(17,24,39,0.9), rgba(11,16,32,1));
    border-bottom: 1px solid var(--border);
    padding: 24px 28px 18px;
  }
  h1 { margin: 0; font-size: 20px; font-weight: 500; letter-spacing: 0.2px; }
  .subtitle { margin-top: 6px; color: var(--muted); font-size: 13px; }
  .tagline { margin-top: 8px; color: var(--muted); font-size: 12px; }
  .grid { display: grid; gap: 16px; padding: 20px 28px; }
  .metrics { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
  .card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
    padding: 18px; transition: transform .08s ease, box-shadow .08s ease;
  }
  .card:hover { transform: translateY(-1px); box-shadow: 0 6px 24px rgba(0,0,0,0.25); }
  .card .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; }
  .card .value { font-size: 22px; font-weight: 500; letter-spacing: -0.3px; }
  .card .hint { color: var(--muted); font-size: 12px; margin-top: 6px; }
  .filters {
    display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
    padding: 0 28px 10px;
  }
  .filters input, .filters select {
    background: var(--surface); color: var(--text); border: 1px solid var(--border);
    border-radius: 8px; padding: 8px 10px; font-size: 13px; min-width: 160px;
  }
  .filters input:focus, .filters select:focus { outline: none; border-color: var(--accent); }
  .pill {
    display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px;
    font-size: 12px; font-weight: 500; border: 1px solid transparent;
  }
  .pill.confirmed { background: rgba(248,113,113,0.12); color: var(--danger); border-color: rgba(248,113,113,0.25); }
  .pill.potential { background: rgba(251,191,36,0.12); color: var(--warning); border-color: rgba(251,191,36,0.25); }
  .pill.risk { background: rgba(96,165,250,0.12); color: var(--info); border-color: rgba(96,165,250,0.25); }
  .pill.opportunity { background: rgba(45,212,191,0.12); color: var(--accent-2); border-color: rgba(45,212,191,0.25); }
  .pill.ok { background: rgba(52,211,153,0.12); color: var(--success); border-color: rgba(52,211,153,0.25); }
  .table-wrap { overflow: auto; padding: 0 28px 28px; }
  table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; }
  thead th {
    position: sticky; top: 0; background: var(--bg);
    color: var(--muted); font-weight: 500; text-align: left; padding: 10px 12px;
    border-bottom: 1px solid var(--border); white-space: nowrap;
  }
  tbody tr {
    background: var(--surface); border-bottom: 1px solid var(--border);
    cursor: pointer; transition: background .06s ease;
  }
  tbody tr:hover { background: var(--elevated); }
  tbody td { padding: 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
  .detail-panel {
    background: var(--elevated); border: 1px solid var(--border); border-radius: 12px;
    padding: 18px; margin: 8px 28px 28px; display: none;
  }
  .detail-panel.open { display: block; }
  .detail-panel h3 { margin: 0 0 10px; font-size: 16px; font-weight: 500; }
  .detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
  .kv { display: flex; justify-content: space-between; gap: 12px; padding: 6px 0; border-bottom: 1px dashed var(--border); }
  .kv .k { color: var(--muted); font-size: 12px; }
  .kv .v { color: var(--text); font-size: 13px; text-align: right; word-break: break-word; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 12px; }
  .small-table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; }
  .small-table th, .small-table td { padding: 6px 8px; border: 1px solid var(--border); text-align: left; }
  .small-table th { background: var(--surface); color: var(--muted); font-weight: 500; }
  .caveat { color: var(--warning); font-size: 12px; margin-top: 10px; }
  .muted { color: var(--muted); }
  .right { text-align: right; }
  .hidden { display: none; }
  .empty { padding: 28px; text-align: center; color: var(--muted); }
  .test-panel { padding: 0 28px 28px; }
  .test-panel pre { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px; overflow: auto; font-size: 12px; }
  button { background: var(--accent); color: #fff; border: none; border-radius: 8px; padding: 8px 12px; font-size: 13px; cursor: pointer; }
  button:hover { filter: brightness(1.1); }
  .segment { display: inline-flex; gap: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
  .segment button { background: transparent; color: var(--muted); border-radius: 0; border-right: 1px solid var(--border); }
  .segment button:last-child { border-right: none; }
  .segment button.active { background: var(--elevated); color: var(--text); }
</style>
</head>
<body>
<header>
  <h1>Procurement Intelligence Dashboard</h1>
  <div class="subtitle">Synthetic NHS exercise &middot; As of 20 October 2026 &middot; 49 contracts &middot; 302 invoices</div>
  <div class="tagline">All data fictional.  Calculations are deterministic from CSV values.  No external libraries or network required.</div>
</header>

<section class="grid metrics" id="metrics"></section>

<div class="filters">
  <input id="search" placeholder="Search findings..." />
  <select id="filterSupplier"><option value="">All suppliers</option></select>
  <select id="filterCategory"><option value="">All categories</option></select>
  <select id="filterSeverity"><option value="">All severities</option>
    <option value="confirmed">Confirmed discrepancy</option>
    <option value="potential">Potential recovery</option>
    <option value="risk">Renewal / risk</option>
    <option value="opportunity">Unvalidated savings</option>
  </select>
  <div class="segment" id="viewToggle">
    <button class="active" data-view="findings">Findings</button>
    <button data-view="contracts">Contracts</button>
    <button data-view="invoices">Invoices</button>
    <button data-view="tests">Tests</button>
  </div>
</div>

<div id="findingsView" class="table-wrap">
  <table id="findingsTable">
    <thead><tr>
      <th>Severity</th><th>Finding</th><th>Value (GBP)</th><th>Category</th><th>Supplier</th><th>ID</th>
    </tr></thead>
    <tbody id="findingsBody"></tbody>
  </table>
  <div id="findingsEmpty" class="empty hidden">No findings match the current filters.</div>
</div>

<div id="contractsView" class="table-wrap hidden">
  <table id="contractsTable">
    <thead><tr>
      <th>Contract</th><th>Trust</th><th>Category</th><th>Supplier</th><th>Annual spend</th><th>End date</th><th>Renewal</th>
    </tr></thead>
    <tbody id="contractsBody"></tbody>
  </table>
</div>

<div id="invoicesView" class="table-wrap hidden">
  <table id="invoicesTable">
    <thead><tr>
      <th>Invoice</th><th>Contract</th><th>Supplier</th><th>Date</th><th>Amount</th><th>Resubmitted</th>
    </tr></thead>
    <tbody id="invoicesBody"></tbody>
  </table>
</div>

<div id="testsView" class="test-panel hidden">
  <button id="runTests">Run embedded tests</button>
  <pre id="testOutput"></pre>
</div>

<div id="detailPanel" class="detail-panel"></div>

<script>
/* ---- EMBEDDED DATASET ---- */
const DATA = ''' + json_str + ''';

/* ---- HELPERS ---- */
const fmtGBP = (n) => "\\u00a3" + (n == null ? "—" : Number(n).toLocaleString("en-GB", {maximumFractionDigits: 2}));
const fmtDate = (d) => d;
const uniq = (arr) => [...new Set(arr)].sort();
const byId = (arr) => { const m={}; arr.forEach(x=>m[x.id]=x); return m; };

/* ---- INIT UI ---- */
const metricsEl = document.getElementById("metrics");
const s = DATA.summary;
metricsEl.innerHTML = `
  <div class="card">
    <div class="label">Annual contract spend</div>
    <div class="value" style="color:var(--text)">${fmtGBP(s.total_annual_contract_spend_gbp)}</div>
    <div class="hint">${s.contract_count} contracts across 4 trusts</div>
  </div>
  <div class="card">
    <div class="label">Upcoming renewals at risk</div>
    <div class="value" style="color:var(--info)">${s.upcoming_renewal_count}</div>
    <div class="hint">Notice deadlines missed or imminent</div>
  </div>
  <div class="card">
    <div class="label">Invoice anomaly exposure</div>
    <div class="value" style="color:var(--danger)">${fmtGBP(s.duplicate_invoice_recovery_gbp + s.unmapped_invoice_exposure_gbp + s.resubmitted_invoice_exposure_gbp)}</div>
    <div class="hint">Duplicates + unmapped + resubmitted</div>
  </div>
  <div class="card">
    <div class="label">Potential consolidation savings</div>
    <div class="value" style="color:var(--accent-2)">${fmtGBP(s.potential_consolidation_savings_gbp)}</div>
    <div class="hint">${s.unvalidated_savings_opportunities} contracts above median unit rate</div>
  </div>
`;

/* populate dropdowns */
const supSel = document.getElementById("filterSupplier");
uniq(DATA.contracts.map(c=>c.supplier).concat(DATA.invoices.map(i=>i.supplier))).forEach(su=>{
  const o=document.createElement("option"); o.value=su; o.textContent=su; supSel.appendChild(o);
});
const catSel = document.getElementById("filterCategory");
uniq(DATA.contracts.map(c=>c.category)).forEach(ca=>{
  const o=document.createElement("option"); o.value=ca; o.textContent=ca; catSel.appendChild(o);
});

/* ---- TABLE RENDERERS ---- */
function renderFindings() {
  const q = document.getElementById("search").value.toLowerCase();
  const sup = document.getElementById("filterSupplier").value;
  const cat = document.getElementById("filterCategory").value;
  const sev = document.getElementById("filterSeverity").value;

  const rows = DATA.findings.filter(f => {
    if (sev && f.severity !== sev) return false;
    const text = (f.title+" "+(f.supplier_canonical||f.supplier||"")+" "+(f.category||"")+" "+(f.contract_id||f.invoice_id||"")).toLowerCase();
    if (q && !text.includes(q)) return false;
    if (sup) {
      const fs = (f.supplier_canonical || f.supplier || "");
      if (fs !== sup) return false;
    }
    if (cat) {
      const fc = (f.category || "");
      if (fc !== cat) return false;
    }
    return true;
  });

  const tbody = document.getElementById("findingsBody");
  tbody.innerHTML = "";
  if (!rows.length) {
    document.getElementById("findingsEmpty").classList.remove("hidden");
    return;
  }
  document.getElementById("findingsEmpty").classList.add("hidden");

  rows.forEach((f, idx) => {
    const id = f.contract_id || f.invoice_id || "";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><span class="pill ${f.severity}">${f.severity}</span></td>
      <td>${escapeHtml(f.title)}</td>
      <td class="right mono">${fmtGBP(f.financial_value_gbp)}</td>
      <td>${escapeHtml(f.category || "—")}</td>
      <td>${escapeHtml(f.supplier_canonical || f.supplier || "—")}</td>
      <td class="mono">${escapeHtml(id)}</td>
    `;
    tr.addEventListener("click", () => openDetail(f, idx));
    tbody.appendChild(tr);
  });
}

function renderContracts() {
  const tbody = document.getElementById("contractsBody");
  tbody.innerHTML = "";
  DATA.contracts.forEach(c => {
    const tr = document.createElement("tr");
    const daysToEnd = Math.ceil((new Date(c.end) - new Date("2026-10-20")) / 86400000);
    const status = daysToEnd < 0 ? "expired" : daysToEnd <= 90 ? "renewal_soon" : "ok";
    tr.innerHTML = `
      <td class="mono">${escapeHtml(c.id)}</td>
      <td>${escapeHtml(c.trust)}</td>
      <td>${escapeHtml(c.category)}</td>
      <td>${escapeHtml(c.supplier)}</td>
      <td class="right mono">${fmtGBP(c.annual_spend)}</td>
      <td>${fmtDate(c.end)} ${daysToEnd<=90?`<span class="pill ${status}">${status.replace("_"," ")}</span>`:""}</td>
      <td>${c.auto_renew} (${c.notice_days}d notice)</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderInvoices() {
  const tbody = document.getElementById("invoicesBody");
  tbody.innerHTML = "";
  DATA.invoices.forEach(i => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="mono">${escapeHtml(i.id)}</td>
      <td class="mono">${escapeHtml(i.contract_id)}</td>
      <td>${escapeHtml(i.supplier)}</td>
      <td>${fmtDate(i.date)}</td>
      <td class="right mono">${fmtGBP(i.amount)}</td>
      <td>${i.resubmitted ? '<span class="pill confirmed">resubmitted</span>' : '—'}</td>
    `;
    tbody.appendChild(tr);
  });
}

/* ---- DETAIL VIEW ---- */
function openDetail(f, idx) {
  const panel = document.getElementById("detailPanel");
  panel.classList.add("open");
  let html = `<h3>${escapeHtml(f.title)}</h3><div class="detail-grid">`;

  // generic fields
  const skip = new Set(["title","severity","financial_value_gbp","finding_type"]);
  for (const [k,v] of Object.entries(f)) {
    if (skip.has(k)) continue;
    if (typeof v === "object" && v !== null) {
      html += `<div><div class="kv"><span class="k">${escapeHtml(k)}</span><span class="v mono">${escapeHtml(JSON.stringify(v))}</span></div></div>`;
    } else {
      html += `<div><div class="kv"><span class="k">${escapeHtml(k)}</span><span class="v mono">${escapeHtml(String(v))}</span></div></div>`;
    }
  }
  html += `</div>`;

  // contextual tables based on finding_type
  if (f.finding_type === "price_variance_high") {
    const peers = DATA.contracts.filter(c => c.service_code === f.service_code);
    html += `<h4 style="margin-top:14px;font-size:13px;color:var(--muted)">Comparable contracts (${escapeHtml(f.service_code)})</h4>`;
    html += `<table class="small-table"><thead><tr><th>Contract</th><th>Trust</th><th>Supplier</th><th>Units</th><th>Unit price</th><th>Annual spend</th></tr></thead><tbody>`;
    peers.sort((a,b)=>b.annual_spend - a.annual_spend).forEach(p => {
      const highlight = p.id === f.contract_id ? ' style="color:var(--accent-2);font-weight:500"' : '';
      html += `<tr><td class="mono"${highlight}>${escapeHtml(p.id)}</td><td>${escapeHtml(p.trust)}</td><td>${escapeHtml(p.supplier)}</td><td class="right">${p.units.toLocaleString()}</td><td class="right mono">${fmtGBP(p.unit_price)}</td><td class="right mono">${fmtGBP(p.annual_spend)}</td></tr>`;
    });
    html += `</tbody></table>`;
    html += `<div class="caveat">Assumption: savings to median/lowest assume clinical, operational, legal and IG equivalence.  Do not count as cash-releasing without trust confirmation.</div>`;
    html += `<div class="muted" style="margin-top:6px;font-size:12px">Calculation: annual_spend = units x unit_price.  Median spend computed across same service_code contracts only.  No volume-adjustment applied.</div>`;
  }

  if (f.finding_type === "duplicate_invoice_id") {
    const invs = DATA.invoices.filter(i => i.id === f.invoice_id);
    html += `<h4 style="margin-top:14px;font-size:13px;color:var(--muted)">Duplicate occurrences</h4>`;
    html += `<table class="small-table"><thead><tr><th>Invoice ID</th><th>Contract</th><th>Date</th><th>Amount</th><th>Source file</th><th>Type</th></tr></thead><tbody>`;
    invs.forEach(i => {
      const type = i.resubmitted ? 'resubmitted' : 'original';
      html += `<tr><td class="mono">${escapeHtml(i.id)}</td><td class="mono">${escapeHtml(i.contract_id)}</td><td>${fmtDate(i.date)}</td><td class="right mono">${fmtGBP(i.amount)}</td><td class="mono">${escapeHtml(i.source)}</td><td><span class="pill confirmed">${type}</span></td></tr>`;
    });
    html += `</tbody></table>`;
    html += `<div class="caveat">Confirmed discrepancy: same invoice_id appears multiple times.  Review whether both were paid.  Recovery potential = sum of amounts.</div>`;
  }

  if (f.finding_type === "renewal_risk") {
    html += `<div style="margin-top:10px"><div class="kv"><span class="k">Days to end date</span><span class="v">${f.days_to_end}</span></div>`;
    html += `<div class="kv"><span class="k">Days past notice deadline</span><span class="v">${f.days_past_deadline > 0 ? '+' : ''}${f.days_past_deadline}</span></div>`;
    html += `<div class="kv"><span class="k">Auto-renew</span><span class="v">${f.auto_renew}</span></div>`;
    html += `<div class="kv"><span class="k">Notice required</span><span class="v">${f.notice_days} days</span></div></div>`;
    html += `<div class="caveat">Risk classification: ${f.status.replace(/_/g,' ')}.  If auto-renew is Yes and deadline missed, contract may roll over.  If No, lapsed service risk.</div>`;
  }

  if (f.finding_type === "unmapped_invoice") {
    html += `<div class="caveat">No contract_id assigned in invoices.csv (marked MISSING).  £${f.amount_gbp.toLocaleString()} requires manual allocation to a contract or purchase order.</div>`;
  }

  if (f.finding_type === "resubmitted_invoice") {
    html += `<div class="caveat">Source filename contains "resubmitted".  Verify against original invoice to prevent duplicate payment.  Amount = ${fmtGBP(f.amount_gbp)}.</div>`;
  }

  panel.innerHTML = html;
  panel.scrollIntoView({behavior:"smooth", block:"nearest"});
}

function escapeHtml(t) {
  if (t == null) return "—";
  return String(t).replace(/[&<>"']/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}[m]));
}

/* ---- VIEW SWITCHING ---- */
function showView(name) {
  ["findings","contracts","invoices","tests"].forEach(v => {
    document.getElementById(v+"View").classList.toggle("hidden", v !== name);
  });
  document.querySelectorAll("#viewToggle button").forEach(b => b.classList.toggle("active", b.dataset.view === name));
  document.getElementById("detailPanel").classList.remove("open");
}

document.getElementById("viewToggle").addEventListener("click", e => {
  if (e.target.dataset.view) showView(e.target.dataset.view);
});

/* ---- FILTERS ---- */
["search","filterSupplier","filterCategory","filterSeverity"].forEach(id => {
  document.getElementById(id).addEventListener("input", renderFindings);
});

/* ---- EMBEDDED UNIT TESTS ---- */
document.getElementById("runTests").addEventListener("click", () => {
  const out = [];
  let pass = 0, fail = 0;
  function assert(label, cond) {
    if (cond) { pass++; out.push("PASS: "+label); }
    else { fail++; out.push("FAIL: "+label); }
  }

  assert("contract count is 49", DATA.summary.contract_count === 49);
  assert("invoice count is 302", DATA.summary.invoice_count === 302);
  assert("duplicate candidates >= 6", DATA.findings.filter(f=>f.finding_type==="duplicate_invoice_id").length >= 6);
  assert("price outliers reference contracts", DATA.findings.filter(f=>f.finding_type==="price_variance_high").every(f=>f.source && f.source.includes("contract")));
  assert("renewal risks exist", DATA.findings.filter(f=>f.finding_type==="renewal_risk").length > 0);
  assert("total annual spend positive", DATA.summary.total_annual_contract_spend_gbp > 0);
  assert("potential savings not double-counted", new Set(DATA.findings.filter(f=>f.finding_type==="price_variance_high").map(f=>f.contract_id)).size === DATA.findings.filter(f=>f.finding_type==="price_variance_high").length);
  assert("unmapped invoices have MISSING contract_id", DATA.invoices.filter(i=>i.contract_id==="MISSING").length === DATA.findings.filter(f=>f.finding_type==="unmapped_invoice").length);
  assert("resubmitted invoices match source name", DATA.invoices.filter(i=>i.resubmitted).length === DATA.findings.filter(f=>f.finding_type==="resubmitted_invoice").length);
  assert("invoice variance flags exact from CSV", DATA.summary.invoice_variance_flags === 0); // known from dataset design

  // deterministic savings arithmetic check for top finding
  const top = DATA.findings.find(f=>f.finding_type==="price_variance_high");
  if (top) {
    const expected = top.annual_spend_gbp - top.median_spend_gbp;
    assert("top savings arithmetic exact", Math.abs(top.potential_saving_to_median_gbp - expected) < 0.01);
  }

  out.push(`\\nResults: ${pass} passed, ${fail} failed`);
  document.getElementById("testOutput").textContent = out.join("\\n");
});

/* ---- INITIAL RENDER ---- */
renderFindings();
renderContracts();
renderInvoices();
</script>
</body>
</html>'''

with open('/workspace/index.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

print('Wrote /workspace/index.html')
