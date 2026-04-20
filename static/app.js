/**
 * Stock Data Intelligence Dashboard — Frontend Logic
 * Handles API communication, chart rendering (Chart.js), and UI interactions.
 */

// ── API Base ──
const API = '';

// ── State ──
let companies = [];
let selectedSymbol = null;
let priceChart = null;
let compareChart = null;
let predictionChart = null;
let currentDays = 30;

// ── DOM Elements ──
const companyList = document.getElementById('companyList');
const companySearch = document.getElementById('companySearch');
const welcomeState = document.getElementById('welcomeState');
const dashboardContent = document.getElementById('dashboardContent');
const selectedCompanyName = document.getElementById('selectedCompanyName');
const selectedCompanySymbol = document.getElementById('selectedCompanySymbol');
const priceChartCanvas = document.getElementById('priceChart');
const compareChartCanvas = document.getElementById('compareChart');
const predictionChartCanvas = document.getElementById('predictionChart');

// ═══════════════════════════════════════════
//  INITIALIZATION
// ═══════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    loadCompanies();
    loadInsights();
    setupTabs();
    setupFilters();
    setupCompare();
    setupMobileMenu();

    document.getElementById('refreshBtn').addEventListener('click', () => {
        if (selectedSymbol) selectCompany(selectedSymbol);
    });
});

// ═══════════════════════════════════════════
//  API HELPERS
// ═══════════════════════════════════════════

async function fetchJSON(url) {
    try {
        const res = await fetch(API + url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error(`API Error: ${url}`, err);
        return null;
    }
}

// ═══════════════════════════════════════════
//  COMPANY LIST
// ═══════════════════════════════════════════

async function loadCompanies() {
    const data = await fetchJSON('/companies');
    if (!data) {
        companyList.innerHTML = '<p style="padding:20px;color:var(--text-muted)">Failed to load companies</p>';
        return;
    }

    companies = data;
    renderCompanyList(companies);
    populateCompareSelects(companies);
}

function renderCompanyList(list) {
    if (list.length === 0) {
        companyList.innerHTML = '<p style="padding:20px;color:var(--text-muted);text-align:center">No companies found</p>';
        return;
    }

    companyList.innerHTML = list.map(c => `
        <div class="company-item ${c.symbol === selectedSymbol ? 'active' : ''}"
             data-symbol="${c.symbol}"
             onclick="selectCompany('${c.symbol}')">
            <div class="company-icon">${c.symbol.replace('.NS', '').substring(0, 3)}</div>
            <div class="company-info">
                <div class="company-name">${c.name}</div>
                <div class="company-symbol">${c.symbol}</div>
            </div>
        </div>
    `).join('');
}

// Search filter
companySearch.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    const filtered = companies.filter(c =>
        c.name.toLowerCase().includes(q) || c.symbol.toLowerCase().includes(q)
    );
    renderCompanyList(filtered);
});

// ═══════════════════════════════════════════
//  SELECT COMPANY
// ═══════════════════════════════════════════

async function selectCompany(symbol) {
    selectedSymbol = symbol;
    const company = companies.find(c => c.symbol === symbol);

    // Update UI
    welcomeState.style.display = 'none';
    dashboardContent.style.display = 'block';
    selectedCompanyName.textContent = company ? company.name : symbol;
    selectedCompanySymbol.textContent = symbol;

    // Highlight active in sidebar
    document.querySelectorAll('.company-item').forEach(el => {
        el.classList.toggle('active', el.dataset.symbol === symbol);
    });

    // Close mobile sidebar
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebarOverlay').classList.remove('open');

    // Load data
    await Promise.all([
        loadSummary(symbol),
        loadPriceChart(symbol, currentDays),
        loadPrediction(symbol),
    ]);
}

// ═══════════════════════════════════════════
//  SUMMARY STATS
// ═══════════════════════════════════════════

async function loadSummary(symbol) {
    const data = await fetchJSON(`/summary/${symbol}`);
    if (!data) return;

    document.getElementById('statClose').textContent = data.latest_close ? `₹${data.latest_close.toLocaleString()}` : '—';
    document.getElementById('statDate').textContent = data.latest_date || '—';
    document.getElementById('statHigh52').textContent = data.high_52w ? `₹${data.high_52w.toLocaleString()}` : '—';
    document.getElementById('statLow52').textContent = data.low_52w ? `₹${data.low_52w.toLocaleString()}` : '—';

    const retEl = document.getElementById('statReturn');
    if (data.latest_daily_return !== null && data.latest_daily_return !== undefined) {
        const pct = (data.latest_daily_return * 100).toFixed(3);
        retEl.textContent = `${pct > 0 ? '+' : ''}${pct}%`;
        retEl.className = `stat-value ${pct >= 0 ? 'stat-positive' : 'stat-negative'}`;
    } else {
        retEl.textContent = '—';
        retEl.className = 'stat-value';
    }

    const volEl = document.getElementById('statVolatility');
    volEl.textContent = data.latest_volatility
        ? `Volatility: ${(data.latest_volatility * 100).toFixed(3)}%`
        : 'Volatility: —';
}

// ═══════════════════════════════════════════
//  PRICE CHART
// ═══════════════════════════════════════════

async function loadPriceChart(symbol, days) {
    const data = await fetchJSON(`/data/${symbol}?days=${days}`);
    if (!data || !data.data || data.data.length === 0) return;

    const labels = data.data.map(d => d.date);
    const closes = data.data.map(d => d.close);
    const sma = data.data.map(d => d.moving_avg_7d);

    if (priceChart) priceChart.destroy();

    priceChart = new Chart(priceChartCanvas, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Close Price',
                    data: closes,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.08)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: days <= 30 ? 3 : 0,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#3b82f6',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                },
                {
                    label: '7-Day SMA',
                    data: sma,
                    borderColor: '#8b5cf6',
                    borderWidth: 2,
                    borderDash: [6, 3],
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 12 },
                        usePointStyle: true,
                        pointStyle: 'circle',
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(148, 163, 184, 0.2)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    titleFont: { family: 'Inter', weight: '600' },
                    bodyFont: { family: 'Inter' },
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ₹${ctx.parsed.y?.toLocaleString()}`,
                    },
                },
            },
            scales: {
                x: {
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                    ticks: {
                        color: '#64748b',
                        font: { family: 'Inter', size: 11 },
                        maxTicksLimit: 12,
                        maxRotation: 45,
                    },
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                    ticks: {
                        color: '#64748b',
                        font: { family: 'Inter', size: 11 },
                        callback: (v) => '₹' + v.toLocaleString(),
                    },
                },
            },
        },
    });
}

// ═══════════════════════════════════════════
//  CHART FILTERS (30D, 90D, 6M, 1Y)
// ═══════════════════════════════════════════

function setupFilters() {
    document.querySelectorAll('.chart-filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.chart-filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentDays = parseInt(btn.dataset.days);
            if (selectedSymbol) loadPriceChart(selectedSymbol, currentDays);
        });
    });
}

// ═══════════════════════════════════════════
//  TABS
// ═══════════════════════════════════════════

function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // Deactivate all
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            // Activate clicked
            btn.classList.add('active');
            const tabId = `tabContent${capitalize(btn.dataset.tab)}`;
            document.getElementById(tabId).classList.add('active');
        });
    });
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// ═══════════════════════════════════════════
//  COMPARE
// ═══════════════════════════════════════════

function populateCompareSelects(list) {
    const s1 = document.getElementById('compareStock1');
    const s2 = document.getElementById('compareStock2');
    const options = list.map(c => `<option value="${c.symbol}">${c.name} (${c.symbol})</option>`).join('');
    s1.innerHTML = options;
    s2.innerHTML = options;
    // Default second to a different stock
    if (list.length > 1) s2.selectedIndex = 1;
}

function setupCompare() {
    document.getElementById('compareBtn').addEventListener('click', loadCompareChart);
}

async function loadCompareChart() {
    const sym1 = document.getElementById('compareStock1').value;
    const sym2 = document.getElementById('compareStock2').value;
    if (!sym1 || !sym2) return;

    const data = await fetchJSON(`/compare?symbol1=${sym1}&symbol2=${sym2}&days=${currentDays}`);
    if (!data) return;

    const labels = data.stock1.data.map(d => d.date);
    const closes1 = data.stock1.data.map(d => d.close);
    const closes2 = data.stock2.data.map(d => d.close);

    // Normalize to percentage change from first value
    const base1 = closes1[0] || 1;
    const base2 = closes2[0] || 1;
    const norm1 = closes1.map(v => ((v - base1) / base1) * 100);
    const norm2 = closes2.map(v => ((v - base2) / base2) * 100);

    if (compareChart) compareChart.destroy();

    compareChart = new Chart(compareChartCanvas, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: data.stock1.company,
                    data: norm1,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.05)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                },
                {
                    label: data.stock2.company,
                    data: norm2,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.05)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 12 },
                        usePointStyle: true,
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(148, 163, 184, 0.2)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y?.toFixed(2)}%`,
                    },
                },
            },
            scales: {
                x: {
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                    ticks: { color: '#64748b', font: { family: 'Inter', size: 11 }, maxTicksLimit: 12, maxRotation: 45 },
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                    ticks: {
                        color: '#64748b',
                        font: { family: 'Inter', size: 11 },
                        callback: (v) => v.toFixed(1) + '%',
                    },
                    title: {
                        display: true,
                        text: '% Change from Start',
                        color: '#64748b',
                        font: { family: 'Inter', size: 12 },
                    },
                },
            },
        },
    });
}

// ═══════════════════════════════════════════
//  PREDICTION
// ═══════════════════════════════════════════

async function loadPrediction(symbol) {
    const infoEl = document.getElementById('predictionInfo');
    infoEl.innerHTML = '<div class="spinner"></div>';

    const data = await fetchJSON(`/predict/${symbol}`);
    if (!data) {
        infoEl.innerHTML = '<span style="color:var(--text-muted)">Prediction unavailable</span>';
        return;
    }

    // Info badges
    const trendClass = data.historical_trend.direction === 'Upward' ? 'trend-up' : 'trend-down';
    const trendIcon = data.historical_trend.direction === 'Upward' ? '📈' : '📉';
    infoEl.innerHTML = `
        <span class="prediction-badge model">🤖 ${data.model}</span>
        <span class="prediction-badge ${trendClass}">${trendIcon} ${data.historical_trend.direction} (₹${data.historical_trend.slope_per_day}/day)</span>
        <span class="prediction-badge r2">🎯 R² = ${data.r_squared}</span>
    `;

    // Get recent historical data for context
    const histData = await fetchJSON(`/data/${symbol}?days=30`);
    if (!histData || !histData.data) return;

    const histLabels = histData.data.map(d => d.date);
    const histCloses = histData.data.map(d => d.close);
    const predLabels = data.predictions.map(d => d.date);
    const predCloses = data.predictions.map(d => d.predicted_close);

    // Combine
    const allLabels = [...histLabels, ...predLabels];
    const historicalLine = [...histCloses, ...new Array(predLabels.length).fill(null)];
    const predictionLine = [...new Array(histLabels.length - 1).fill(null), histCloses[histCloses.length - 1], ...predCloses];

    if (predictionChart) predictionChart.destroy();

    predictionChart = new Chart(predictionChartCanvas, {
        type: 'line',
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: 'Historical Close',
                    data: historicalLine,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.08)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                },
                {
                    label: 'Predicted (ML)',
                    data: predictionLine,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.08)',
                    borderWidth: 2.5,
                    borderDash: [8, 4],
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointHoverRadius: 7,
                    pointBackgroundColor: '#f59e0b',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 12 },
                        usePointStyle: true,
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(148, 163, 184, 0.2)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => {
                            if (ctx.parsed.y === null) return '';
                            return `${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString()}`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                    ticks: { color: '#64748b', font: { family: 'Inter', size: 11 }, maxTicksLimit: 12, maxRotation: 45 },
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                    ticks: {
                        color: '#64748b',
                        font: { family: 'Inter', size: 11 },
                        callback: (v) => '₹' + v.toLocaleString(),
                    },
                },
            },
        },
    });
}

// ═══════════════════════════════════════════
//  INSIGHTS: TOP GAINERS / LOSERS
// ═══════════════════════════════════════════

async function loadInsights() {
    const [gainers, losers] = await Promise.all([
        fetchJSON('/top-gainers'),
        fetchJSON('/top-losers'),
    ]);

    renderInsightList('gainersList', gainers, true);
    renderInsightList('losersList', losers, false);
}

function renderInsightList(elementId, data, isGainer) {
    const el = document.getElementById(elementId);
    if (!data || data.length === 0) {
        el.innerHTML = '<li style="padding:16px;color:var(--text-muted);text-align:center">No data available</li>';
        return;
    }

    el.innerHTML = data.map((item, i) => {
        const pct = (item.daily_return * 100).toFixed(3);
        const color = isGainer ? 'var(--accent-emerald)' : 'var(--accent-rose)';
        const sign = isGainer ? '+' : '';
        return `
            <li class="insight-item" onclick="selectCompany('${item.symbol}')" style="cursor:pointer">
                <div class="insight-left">
                    <div class="insight-rank">${i + 1}</div>
                    <div class="insight-info">
                        <span class="insight-company">${item.company}</span>
                        <span class="insight-symbol">${item.symbol}</span>
                    </div>
                </div>
                <span class="insight-value" style="color:${color}">${sign}${pct}%</span>
            </li>
        `;
    }).join('');
}

// ═══════════════════════════════════════════
//  MOBILE MENU
// ═══════════════════════════════════════════

function setupMobileMenu() {
    const toggle = document.getElementById('mobileToggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    toggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
    });

    overlay.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
    });
}
