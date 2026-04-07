/* =============================================================
   Accessibility Checker Dashboard — WebYes
   Loads data from data/installs.json and data/rankings/*.json
   ============================================================= */

const EXTENSIONS = {
  webyes:               { name: 'WebYes',            color: '#4F46E5', borderWidth: 3 },
  silktide:             { name: 'Silktide',           color: '#10B981', borderWidth: 2 },
  siteimprove:          { name: 'Siteimprove',        color: '#F59E0B', borderWidth: 2 },
  accessible_web_helper:{ name: 'Acc. Web Helper',    color: '#EF4444', borderWidth: 2 },
  browserstack:         { name: 'BrowserStack',        color: '#8B5CF6', borderWidth: 2 },
  axe_devtools:         { name: 'Axe DevTools',        color: '#06B6D4', borderWidth: 2 },
  wave:                 { name: 'WAVE',               color: '#EC4899', borderWidth: 2 },
};

const EXT_KEYS   = Object.keys(EXTENSIONS);
const EXT_NAMES  = EXT_KEYS.map(k => EXTENSIONS[k].name);

let installsChart  = null;
let trendChart     = null;
let allRankings    = [];   // [{date, keywords:{kw:{ext:rank}}}]
let installData    = [];   // [{date, total_installs, weekly_installs, weekly_uninstalls}]

// ── Helpers ────────────────────────────────────────────────────

function rankBadge(rank) {
  if (rank == null) return `<span class="rank-badge rank-none">—</span>`;
  const cls = rank <= 3 ? 'rank-1-3' : rank <= 10 ? 'rank-4-10' : rank <= 20 ? 'rank-11-20' : 'rank-21p';
  return `<span class="rank-badge ${cls}">#${rank}</span>`;
}

function changeBadge(current, previous) {
  if (current == null && previous == null) return `<span class="change-flat">—</span>`;
  if (previous == null && current != null) return `<span class="change-new">NEW</span>`;
  if (current == null && previous != null) return `<span class="change-down">dropped out</span>`;
  const diff = previous - current; // positive = improved (rank went down numerically)
  if (diff === 0) return `<span class="change-flat">→ 0</span>`;
  if (diff > 0)   return `<span class="change-up">↑ ${diff}</span>`;
  return             `<span class="change-down">↓ ${Math.abs(diff)}</span>`;
}

function deltaBadge(current, previous, prefix = '') {
  if (previous == null || current == null) return '';
  const diff = current - previous;
  if (diff === 0) return `<span class="stat-delta flat">${prefix}→ no change</span>`;
  const sign = diff > 0 ? '+' : '';
  const cls  = diff > 0 ? 'up' : 'down';
  return `<span class="stat-delta ${cls}">${prefix}${sign}${diff} vs prev week</span>`;
}

function dateLabel(iso) {
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}

function subtractDays(isoDate, n) {
  const d = new Date(isoDate + 'T00:00:00');
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

function getRankingByDate(date) {
  return allRankings.find(r => r.date === date) || null;
}

// ── Data Loading ───────────────────────────────────────────────

async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.json();
}

async function loadAllData() {
  // Load installs
  try {
    const inst = await fetchJSON('data/installs.json');
    installData = (inst.entries || []).sort((a, b) => a.date.localeCompare(b.date));
  } catch (_) { installData = []; }

  // Load rankings index then each ranking file
  try {
    const index = await fetchJSON('data/rankings/index.json');
    const files = await Promise.allSettled(
      index.map(date => fetchJSON(`data/rankings/${date}.json`))
    );
    allRankings = files
      .filter(r => r.status === 'fulfilled')
      .map(r => r.value)
      .sort((a, b) => a.date.localeCompare(b.date));
  } catch (_) { allRankings = []; }
}

// ── Render Installs ────────────────────────────────────────────

function renderInstalls() {
  const el = id => document.getElementById(id);

  if (installData.length === 0) {
    el('last-updated').textContent = 'No data yet — run add_installs.py to add your first entry.';
    return;
  }

  const latest   = installData[installData.length - 1];
  const prevWeek = installData.length >= 2 ? installData[installData.length - 2] : null;

  el('stat-total').textContent     = latest.total_installs?.toLocaleString() ?? '—';
  el('stat-weekly-in').textContent = latest.weekly_installs?.toLocaleString() ?? '—';
  el('stat-weekly-out').textContent= latest.weekly_uninstalls?.toLocaleString() ?? '—';

  const net = (latest.weekly_installs ?? 0) - (latest.weekly_uninstalls ?? 0);
  el('stat-net').textContent = (net >= 0 ? '+' : '') + net;
  el('stat-net').parentElement.querySelector('.stat-delta')?.remove?.();

  if (prevWeek) {
    el('delta-total').outerHTML     = deltaBadge(latest.total_installs, prevWeek.total_installs, '').replace('stat-delta', 'stat-delta');
    el('delta-weekly-in').outerHTML = deltaBadge(latest.weekly_installs, prevWeek.weekly_installs, '').replace('stat-delta', 'stat-delta');
    el('delta-weekly-out').outerHTML= deltaBadge(latest.weekly_uninstalls, prevWeek.weekly_uninstalls, '').replace('stat-delta', 'stat-delta');
  }

  el('last-updated').textContent = `Last updated: ${latest.date}`;

  // Installs chart
  const labels = installData.map(e => dateLabel(e.date));
  const totals = installData.map(e => e.total_installs);
  const weeklyIn  = installData.map(e => e.weekly_installs);
  const weeklyOut = installData.map(e => e.weekly_uninstalls);

  if (installsChart) installsChart.destroy();
  installsChart = new Chart(document.getElementById('chart-installs'), {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Total Installs',
          data: totals,
          type: 'line',
          borderColor: '#4F46E5',
          backgroundColor: 'rgba(79,70,229,0.08)',
          borderWidth: 2.5,
          pointRadius: 4,
          fill: true,
          yAxisID: 'y1',
          tension: 0.3,
        },
        {
          label: 'Weekly Installs',
          data: weeklyIn,
          backgroundColor: 'rgba(16,185,129,0.7)',
          borderRadius: 4,
          yAxisID: 'y2',
        },
        {
          label: 'Weekly Uninstalls',
          data: weeklyOut,
          backgroundColor: 'rgba(239,68,68,0.6)',
          borderRadius: 4,
          yAxisID: 'y2',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'top', labels: { font: { size: 12 } } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y?.toLocaleString()}` } },
      },
      scales: {
        y1: { type: 'linear', position: 'left',  title: { display: true, text: 'Total Installs' }, grid: { color: '#F1F5F9' } },
        y2: { type: 'linear', position: 'right', title: { display: true, text: 'Weekly' }, grid: { display: false } },
        x:  { grid: { color: '#F1F5F9' } },
      },
    },
  });
}

// ── Render Rankings Overview Table ─────────────────────────────

function renderOverviewTable() {
  const tbody = document.getElementById('tbody-overview');

  if (allRankings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty-row">No ranking data yet. Run scripts/scrape_rankings.py to populate.</td></tr>`;
    return;
  }

  const latest  = allRankings[allRankings.length - 1];
  const keywords = Object.keys(latest.keywords || {});

  tbody.innerHTML = keywords.map(kw => {
    const row = latest.keywords[kw];
    const cells = EXT_KEYS.map(ext => {
      const cls = ext === 'webyes' ? ' class="webyes-td"' : '';
      return `<td${cls}>${rankBadge(row[ext])}</td>`;
    }).join('');
    return `<tr><td class="kw-col">${kw}</td>${cells}</tr>`;
  }).join('');
}

// ── Render WebYes Changes Table ────────────────────────────────

function renderChangesTable() {
  const tbody = document.getElementById('tbody-changes');

  if (allRankings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-row">No ranking data yet.</td></tr>`;
    return;
  }

  const latest    = allRankings[allRankings.length - 1];
  const yesterday = getRankingByDate(subtractDays(latest.date, 1));
  const lastWeek  = getRankingByDate(subtractDays(latest.date, 7));
  const keywords  = Object.keys(latest.keywords || {});

  tbody.innerHTML = keywords.map(kw => {
    const cur  = latest.keywords[kw]?.webyes ?? null;
    const dod  = yesterday?.keywords[kw]?.webyes ?? null;
    const wow  = lastWeek?.keywords[kw]?.webyes ?? null;
    return `<tr>
      <td class="kw-col">${kw}</td>
      <td class="webyes-td">${rankBadge(cur)}</td>
      <td>${rankBadge(dod)}</td>
      <td>${changeBadge(cur, dod)}</td>
      <td>${rankBadge(wow)}</td>
      <td>${changeBadge(cur, wow)}</td>
    </tr>`;
  }).join('');
}

// ── Render Trend Chart ─────────────────────────────────────────

function populateKeywordSelect() {
  const sel = document.getElementById('kw-select');
  if (allRankings.length === 0) return;

  const keywords = Object.keys(allRankings[allRankings.length - 1].keywords || {});
  sel.innerHTML  = keywords.map(kw => `<option value="${kw}">${kw}</option>`).join('');
  sel.addEventListener('change', () => renderTrendChart(sel.value));
  renderTrendChart(keywords[0]);
}

function renderTrendChart(keyword) {
  const labels   = allRankings.map(r => dateLabel(r.date));
  const datasets = EXT_KEYS.map(ext => {
    const ext_info = EXTENSIONS[ext];
    const data = allRankings.map(r => r.keywords[keyword]?.[ext] ?? null);
    return {
      label: ext_info.name,
      data,
      borderColor: ext_info.color,
      backgroundColor: ext_info.color + '22',
      borderWidth: ext_info.borderWidth,
      pointRadius: ext === 'webyes' ? 5 : 3,
      spanGaps: false,
      tension: 0.3,
    };
  });

  if (trendChart) trendChart.destroy();
  trendChart = new Chart(document.getElementById('chart-trend'), {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'top', labels: { font: { size: 12 } } },
        tooltip: {
          callbacks: {
            label: ctx => {
              const v = ctx.parsed.y;
              return ` ${ctx.dataset.label}: ${v == null ? 'not ranked' : '#' + v}`;
            },
          },
        },
      },
      scales: {
        y: {
          reverse: true,
          title: { display: true, text: 'Search Rank (lower = better)' },
          min: 1,
          ticks: { stepSize: 1, callback: v => '#' + v },
          grid: { color: '#F1F5F9' },
        },
        x: { grid: { color: '#F1F5F9' } },
      },
    },
  });
}

// ── Init ───────────────────────────────────────────────────────

(async () => {
  await loadAllData();
  renderInstalls();
  renderOverviewTable();
  renderChangesTable();
  populateKeywordSelect();
})();
