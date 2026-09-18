/**
 * AnalystFlow AI — Frontend Interactive Application Controller
 */

let currentDataset = null;
let currentProfile = null;
let activeTab = 'dashboard';
let rawTableData = null;

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initUpload();
    initSampleButton();
    initSampleDropdown();
    initColumnSearch();
    initChat();
    initCleaningModal();
    loadDatasetsList();
});

// Toast system
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 250);
    }, 4000);
}

// Navigation
function initNavigation() {
    const links = document.querySelectorAll('.nav-link');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = link.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tabId) {
    activeTab = tabId;
    document.querySelectorAll('.nav-link').forEach(l => {
        l.classList.toggle('active', l.dataset.tab === tabId);
    });
    document.querySelectorAll('.tab-pane').forEach(p => {
        p.classList.toggle('active', p.id === `tab-${tabId}`);
    });

    if (currentDataset) {
        if (tabId === 'dashboard') loadDashboardData();
        else if (tabId === 'data') loadDataTable();
        else if (tabId === 'eda') loadEdaCharts();
        else if (tabId === 'anomalies') loadAnomalies();
        else if (tabId === 'correlations') loadCorrelations();
        else if (tabId === 'reports') loadReportPreview();
        else if (tabId === 'ask') updateAskSuggestions();
    }
}

// Datasets Management
async function loadDatasetsList() {
    try {
        const res = await fetch('/api/datasets');
        const data = await res.json();
        const select = document.getElementById('datasetSelect');
        select.innerHTML = '<option value="">-- Select Dataset --</option>';

        if (data.datasets && data.datasets.length > 0) {
            data.datasets.forEach(d => {
                const opt = document.createElement('option');
                opt.value = d.id;
                opt.textContent = `${d.original_filename} (${d.row_count} rows)`;
                select.appendChild(opt);
            });

            if (!currentDataset) {
                // Select the most recent dataset automatically
                select.value = data.datasets[0].id;
                selectDataset(data.datasets[0].id);
            }
        }
    } catch (err) {
        console.error('Failed to load datasets:', err);
    }
}

document.getElementById('datasetSelect').addEventListener('change', (e) => {
    if (e.target.value) {
        selectDataset(e.target.value);
    }
});

async function selectDataset(datasetId) {
    try {
        const res = await fetch(`/api/datasets/${datasetId}`);
        const data = await res.json();
        currentDataset = data.dataset;
        currentProfile = data.profile;

        document.getElementById('currentDatasetLabel').textContent = currentDataset.original_filename;
        document.getElementById('datasetRowColBadge').textContent = `${currentDataset.row_count} rows × ${currentDataset.col_count} cols`;
        
        showToast(`Loaded "${currentDataset.original_filename}"`, 'success');
        updateAskSuggestions();
        switchTab(activeTab);
    } catch (err) {
        showToast('Error loading dataset details.', 'error');
    }
}

// "Try Sample Dataset" Button and Dropdown Menu
function initSampleButton() {
    const btn = document.getElementById('trySampleBtn');
    if (!btn) return;
    btn.addEventListener('click', () => loadSampleDataset('sales'));
}

function initSampleDropdown() {
    const btn = document.getElementById('sampleDropdownBtn');
    const menu = document.getElementById('sampleDropdownMenu');
    if (!btn || !menu) return;

    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        menu.classList.toggle('active');
    });

    document.addEventListener('click', () => menu.classList.remove('active'));

    menu.querySelectorAll('.sample-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const type = item.dataset.type;
            menu.classList.remove('active');
            loadSampleDataset(type);
        });
    });
}

async function loadSampleDataset(type = 'sales') {
    showToast(`Loading sample dataset (${type})...`, 'info');
    try {
        const res = await fetch('/api/sample', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: type })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Sample dataset (${data.dataset.original_filename}) loaded!`, 'success');
            await loadDatasetsList();
            await selectDataset(data.dataset.id);
            switchTab('dashboard');
        } else {
            showToast(data.error || 'Failed to load sample dataset', 'error');
        }
    } catch (err) {
        showToast('Network error loading sample dataset.', 'error');
    }
}

// Upload Handling
function initUpload() {
    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('fileInput');

    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(name => {
        dropzone.addEventListener(name, (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(name => {
        dropzone.addEventListener(name, (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) handleFileUpload(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFileUpload(e.target.files[0]);
    });
}

async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    showToast(`Uploading and profiling ${file.name}...`, 'info');
    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (res.ok && data.success) {
            showToast(`"${file.name}" uploaded and profiled successfully!`, 'success');
            await loadDatasetsList();
            await selectDataset(data.dataset.id);
            switchTab('dashboard');
        } else {
            showToast(data.error || 'Upload failed.', 'error');
        }
    } catch (err) {
        showToast('Network error during file upload.', 'error');
    }
}

// Dashboard View
async function loadDashboardData() {
    if (!currentDataset) return;
    try {
        const res = await fetch(`/api/datasets/${currentDataset.id}/insights`);
        const data = await res.json();

        // 1. Render Health Score
        const healthScore = currentDataset.health_score || (currentProfile ? currentProfile.health_score : 0);
        document.getElementById('healthScoreNumber').textContent = healthScore;
        const healthCircle = document.getElementById('healthScoreCircle');
        if (healthScore >= 80) healthCircle.style.borderColor = 'var(--success)';
        else if (healthScore >= 60) healthCircle.style.borderColor = 'var(--warning)';
        else healthCircle.style.borderColor = 'var(--danger)';

        // 2. Render KPIs
        const kpiContainer = document.getElementById('dashboardKpis');
        kpiContainer.innerHTML = '';
        if (data.kpis && data.kpis.length > 0) {
            data.kpis.forEach(k => {
                const card = document.createElement('div');
                card.className = 'kpi-card';
                card.innerHTML = `
                    <div class="kpi-card-header">
                        <span class="kpi-card-title">${k.title}</span>
                    </div>
                    <div class="kpi-card-value">${k.value}</div>
                    <div class="kpi-card-subtitle">${k.subtitle}</div>
                `;
                kpiContainer.appendChild(card);
            });
        }

        // 3. Render Executive Highlights Banner
        const highlightsList = document.getElementById('executiveHighlightsList');
        highlightsList.innerHTML = '';
        if (data.executive_highlights && data.executive_highlights.length > 0) {
            data.executive_highlights.forEach(h => {
                const li = document.createElement('div');
                li.className = 'insight-pill-item';
                li.textContent = h;
                highlightsList.appendChild(li);
            });
        }

        // 4. Render Narrative
        const narrativeBox = document.getElementById('aiNarrativeBox');
        if (data.ai_narrative && data.ai_narrative.executive_summary) {
            narrativeBox.innerHTML = `
                <p><strong>Executive Analysis:</strong> ${data.ai_narrative.executive_summary}</p>
                ${data.ai_narrative.note ? `<p style="margin-top:8px; font-size:12px; color:var(--text-dim);"><em>${data.ai_narrative.note}</em></p>` : ''}
            `;
        }
    } catch (err) {
        console.error('Error loading dashboard data:', err);
    }
}

// Data Preview Table & Column Filter
function initColumnSearch() {
    const input = document.getElementById('columnSearchInput');
    if (!input) return;
    input.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (!rawTableData) return;
        renderFilteredTable(query);
    });
}

async function loadDataTable() {
    if (!currentDataset) return;
    try {
        const res = await fetch(`/api/datasets/${currentDataset.id}/preview?limit=50`);
        rawTableData = await res.json();
        renderFilteredTable('');
        document.getElementById('tableStatusInfo').textContent = `Showing first ${rawTableData.displayed_rows} of ${rawTableData.total_rows} records. Status: ${rawTableData.is_cleaned ? 'Cleaned' : 'Raw'}`;
    } catch (err) {
        console.error('Error loading table:', err);
    }
}

function renderFilteredTable(query) {
    if (!rawTableData || !rawTableData.columns) return;
    const thead = document.getElementById('tableHead');
    const tbody = document.getElementById('tableBody');
    thead.innerHTML = '';
    tbody.innerHTML = '';

    const cols = rawTableData.columns;
    const trHead = document.createElement('tr');
    cols.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        trHead.appendChild(th);
    });
    thead.appendChild(trHead);

    const filteredRows = rawTableData.data.filter(row => {
        if (!query) return true;
        return Object.values(row).some(val => val !== null && String(val).toLowerCase().includes(query));
    });

    filteredRows.forEach(row => {
        const tr = document.createElement('tr');
        cols.forEach(col => {
            const td = document.createElement('td');
            td.textContent = row[col] !== null ? row[col] : '-';
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}

// Dynamic Domain-Adaptive Ask Data Suggestions
function updateAskSuggestions() {
    const container = document.getElementById('chatSuggestions');
    if (!container || !currentDataset) return;

    let suggestions = [
        "How many total rows and columns are in this dataset?",
        "Show summary statistics for numeric variables",
        "Which column has the highest missing percentage?"
    ];

    const filename = (currentDataset.original_filename || '').toLowerCase();
    if (filename.includes('sales') || filename.includes('ecommerce')) {
        suggestions = [
            "What is the total revenue by product category?",
            "Which month generated the highest profit?",
            "Top 5 products by quantity sold",
            "Average discount rate per region"
        ];
    } else if (filename.includes('hr') || filename.includes('employee')) {
        suggestions = [
            "Average salary by department",
            "Highest paid job role",
            "Employee count by employment status",
            "Correlation between tenure and performance score"
        ];
    } else if (filename.includes('real_estate') || filename.includes('property')) {
        suggestions = [
            "Average price per square foot by city",
            "Most expensive property listing",
            "Property distribution by property type",
            "Correlation between square feet and price"
        ];
    }

    container.innerHTML = suggestions.map(s => `<button class="chat-suggestion">${s}</button>`).join('');

    container.querySelectorAll('.chat-suggestion').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = document.getElementById('chatInput');
            if (input) {
                input.value = btn.textContent;
                document.getElementById('chatSendBtn').click();
            }
        });
    });
}

// EDA Charts
async function loadEdaCharts() {
    if (!currentDataset) return;
    const container = document.getElementById('edaChartsContainer');
    container.innerHTML = '<div style="color:var(--text-muted)">Generating automated analytical charts...</div>';
    
    try {
        const res = await fetch(`/api/datasets/${currentDataset.id}/eda`);
        const data = await res.json();
        container.innerHTML = '';

        if (data.charts && data.charts.length > 0) {
            data.charts.forEach(chart => {
                const card = document.createElement('div');
                card.className = 'chart-card';
                const divId = `chart_${chart.id}`;
                card.innerHTML = `<div id="${divId}"></div>`;
                container.appendChild(card);
                Plotly.newPlot(divId, chart.plotly_json.data, chart.plotly_json.layout, { responsive: true, displayModeBar: false });
            });
        } else {
            container.innerHTML = '<p style="color:var(--text-muted)">No suitable columns found for automatic EDA charts.</p>';
        }
    } catch (err) {
        container.innerHTML = '<p style="color:var(--danger)">Error rendering EDA charts.</p>';
    }
}

// Anomalies
async function loadAnomalies() {
    if (!currentDataset) return;
    const container = document.getElementById('anomaliesContainer');
    container.innerHTML = '<div style="color:var(--text-muted)">Scanning records for statistical outliers...</div>';

    try {
        const res = await fetch(`/api/datasets/${currentDataset.id}/anomalies?method=iqr`);
        const data = await res.json();
        
        let html = `
            <div class="kpi-grid" style="margin-bottom:20px;">
                <div class="kpi-card">
                    <div class="kpi-card-title">Detection Method</div>
                    <div class="kpi-card-value" style="font-size:18px;">${data.method}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-card-title">Potential Anomalies</div>
                    <div class="kpi-card-value" style="color:var(--warning);">${data.total_anomalies}</div>
                    <div class="kpi-card-subtitle">${data.total_percentage}% of total records</div>
                </div>
            </div>
        `;

        if (data.anomalous_records && data.anomalous_records.length > 0) {
            html += `
                <div class="table-wrapper">
                    <table class="data-table">
                        <thead><tr><th>Index</th><th>Affected Metrics</th><th>Context / Explanation</th></tr></thead>
                        <tbody>
            `;
            data.anomalous_records.slice(0, 15).forEach(rec => {
                html += `<tr><td>#${rec.index}</td><td><span class="status-badge" style="background:var(--warning-bg);color:var(--warning);">${rec.affected_columns.join(', ')}</span></td><td>${rec.explanation}</td></tr>`;
            });
            html += `</tbody></table></div>`;
        } else {
            html += `<p style="color:var(--success);">Zero statistically significant anomalies detected in numeric distributions.</p>`;
        }
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = '<p style="color:var(--danger)">Failed to execute anomaly detection.</p>';
    }
}

// Correlations
async function loadCorrelations() {
    if (!currentDataset) return;
    const container = document.getElementById('correlationsContainer');
    container.innerHTML = '<div style="color:var(--text-muted)">Computing pairwise correlation matrix...</div>';

    try {
        const res = await fetch(`/api/datasets/${currentDataset.id}/correlations`);
        const data = await res.json();

        container.innerHTML = `
            <div id="corrHeatmap" style="margin-bottom:24px;"></div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
                <div class="table-wrapper">
                    <div style="padding:12px 16px; font-weight:700; color:var(--success);">Top Positive Associations</div>
                    <table class="data-table">
                        <thead><tr><th>Pair</th><th>Correlation (r)</th><th>Strength</th></tr></thead>
                        <tbody>
                            ${data.top_positive.map(p => `<tr><td>${p.column_1} &bull; ${p.column_2}</td><td>${p.correlation}</td><td>${p.strength}</td></tr>`).join('')}
                        </tbody>
                    </table>
                </div>
                <div class="table-wrapper">
                    <div style="padding:12px 16px; font-weight:700; color:var(--warning);">Top Inverse Associations</div>
                    <table class="data-table">
                        <thead><tr><th>Pair</th><th>Correlation (r)</th><th>Strength</th></tr></thead>
                        <tbody>
                            ${data.top_negative.map(p => `<tr><td>${p.column_1} &bull; ${p.column_2}</td><td>${p.correlation}</td><td>${p.strength}</td></tr>`).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
            <p style="margin-top:16px; font-size:12px; color:var(--text-dim); text-align:center;"><em>${data.disclaimer}</em></p>
        `;

        if (data.heatmap_json) {
            Plotly.newPlot('corrHeatmap', data.heatmap_json.data, data.heatmap_json.layout, { responsive: true, displayModeBar: false });
        }
    } catch (err) {
        container.innerHTML = '<p style="color:var(--danger)">Error calculating correlation matrix.</p>';
    }
}

// Cleaning Modal & Actions
function initCleaningModal() {
    const modal = document.getElementById('cleanModal');
    const openBtn = document.getElementById('openCleanModalBtn');
    const closeBtn = document.getElementById('closeCleanModalBtn');
    const applyBtn = document.getElementById('applyCleaningBtn');

    if (openBtn) {
        openBtn.addEventListener('click', async () => {
            if (!currentDataset) return;
            modal.classList.add('active');
            const body = document.getElementById('cleanModalBody');
            body.innerHTML = 'Analyzing dataset for quality issues...';

            try {
                const res = await fetch(`/api/datasets/${currentDataset.id}/clean`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: 'review' })
                });
                const data = await res.json();
                if (data.detected_issues && data.detected_issues.length > 0) {
                    body.innerHTML = `
                        <p style="margin-bottom:12px;"><strong>${data.total_issues} potential issue(s) identified:</strong></p>
                        <ul style="padding-left:20px; display:flex; flex-direction:column; gap:8px;">
                            ${data.detected_issues.map(i => `<li><strong>${i.type.replace('_', ' ').toUpperCase()}</strong>: ${i.description}</li>`).join('')}
                        </ul>
                    `;
                } else {
                    body.innerHTML = '<p style="color:var(--success);">No quality issues detected. The dataset is already clean!</p>';
                }
            } catch (err) {
                body.innerHTML = '<p style="color:var(--danger);">Error analyzing dataset for cleaning.</p>';
            }
        });
    }

    if (closeBtn) closeBtn.addEventListener('click', () => modal.classList.remove('active'));

    if (applyBtn) {
        applyBtn.addEventListener('click', async () => {
            applyBtn.disabled = true;
            applyBtn.textContent = 'Applying Safe Clean...';
            try {
                const res = await fetch(`/api/datasets/${currentDataset.id}/clean`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: 'apply' })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Safe cleaning completed! Original dataset preserved.', 'success');
                    modal.classList.remove('active');
                    await selectDataset(currentDataset.id);
                    switchTab('data');
                }
            } catch (err) {
                showToast('Error applying cleaning.', 'error');
            } finally {
                applyBtn.disabled = false;
                applyBtn.textContent = 'Apply Safe Cleaning';
            }
        });
    }
}

// Ask Your Data / Chat
function initChat() {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSendBtn');
    const history = document.getElementById('chatHistory');

    const sendQuestion = async () => {
        const q = input.value.trim();
        if (!q || !currentDataset) return;
        input.value = '';

        // Add user bubble
        appendChatMsg('user', q);
        const loadingId = appendChatMsg('assistant', 'Analyzing dataset & querying SQL engine...');

        try {
            const res = await fetch(`/api/datasets/${currentDataset.id}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: q })
            });
            const data = await res.json();
            
            document.getElementById(loadingId).remove();

            let responseHtml = `<div>${data.answer}</div>`;
            if (data.sql_used) {
                responseHtml += `
                    <div class="chat-sql-box">
                        <div style="font-size:10px; text-transform:uppercase; color:var(--text-muted); margin-bottom:4px;">SQL Query Used:</div>
                        <code>${data.sql_used}</code>
                    </div>
                `;
            }

            if (data.rows && data.rows.length > 0 && data.columns) {
                responseHtml += `
                    <div class="table-wrapper" style="margin-top:10px; max-height:200px;">
                        <table class="data-table">
                            <thead><tr>${data.columns.map(c => `<th>${c}</th>`).join('')}</tr></thead>
                            <tbody>
                                ${data.rows.slice(0, 5).map(r => `<tr>${r.map(val => `<td>${val !== null ? val : '-'}</td>`).join('')}</tr>`).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            }

            appendChatHtml('assistant', responseHtml);
        } catch (err) {
            document.getElementById(loadingId).remove();
            appendChatMsg('assistant', 'Error communicating with analytics query engine.');
        }
    };

    if (sendBtn) sendBtn.addEventListener('click', sendQuestion);
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendQuestion();
        });
    }

    // Quick suggestion clicks
    document.querySelectorAll('.chat-suggestion').forEach(btn => {
        btn.addEventListener('click', () => {
            input.value = btn.textContent;
            sendQuestion();
        });
    });
}

function appendChatMsg(sender, text) {
    const id = `msg_${Date.now()}`;
    const history = document.getElementById('chatHistory');
    const msg = document.createElement('div');
    msg.id = id;
    msg.className = `chat-msg ${sender}`;
    msg.textContent = text;
    history.appendChild(msg);
    history.scrollTop = history.scrollHeight;
    return id;
}

function appendChatHtml(sender, html) {
    const history = document.getElementById('chatHistory');
    const msg = document.createElement('div');
    msg.className = `chat-msg ${sender}`;
    msg.innerHTML = html;
    history.appendChild(msg);
    history.scrollTop = history.scrollHeight;
}

// Report View
async function loadReportPreview() {
    if (!currentDataset) return;
    const frame = document.getElementById('reportPreviewFrame');
    frame.innerHTML = '<div style="color:var(--text-muted)">Compiling executive intelligence report...</div>';

    try {
        const res = await fetch(`/api/datasets/${currentDataset.id}/report?format=json`);
        const data = await res.json();
        
        frame.innerHTML = `
            <div style="display:flex; justify-content:flex-end; gap:12px; margin-bottom:16px;">
                <a class="btn btn-secondary btn-sm" href="/api/datasets/${currentDataset.id}/report?format=markdown" download>Download Markdown (.md)</a>
                <a class="btn btn-primary btn-sm" href="/api/datasets/${currentDataset.id}/report?format=html_download" download>Download Executive HTML (.html)</a>
            </div>
            <iframe srcdoc="${data.html.replace(/"/g, '&quot;')}" style="width:100%; height:700px; border:1px solid var(--border-color); border-radius:var(--radius-md);"></iframe>
        `;
    } catch (err) {
        frame.innerHTML = '<p style="color:var(--danger)">Error generating report preview.</p>';
    }
}
