// public/js/app.js (V2.0 - Final & Complete)

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

let intelligenceBriefing = null;

function initializeApp() {
    injectStyles();
    renderHeader();
    renderSearchBox();
}

function injectStyles() {
    const styleTag = document.getElementById('main-styles');
    styleTag.innerHTML = `
        body { background-color: #121212; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; padding: 5vh 2vw; }
        .container { width: 95%; max-width: 700px; }
        .header { text-align: center; margin-bottom: 2rem; }
        .header h1 { font-size: 2.8rem; font-weight: bold; line-height: 1.2; }
        .header .logo { font-size: 3rem; margin-right: 10px; vertical-align: middle; }
        .header .genesis { font-size: 3.2rem; background: linear-gradient(90deg, #ff8a00, #e52e71); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header p { margin-top: 1rem; color: #b3b3b3; font-size: 1.1rem; }
        .search-box { margin-bottom: 2rem; position: relative; }
        .search-input { width: 100%; background: #282828; border: 1px solid #404040; color: #fff; padding: 1rem 3.5rem 1rem 1.2rem; border-radius: 50px; font-size: 1rem; box-sizing: border-box; transition: all 0.2s ease; }
        .search-input:focus { border-color: #007bff; box-shadow: 0 0 15px rgba(0, 123, 255, 0.5); }
        .search-btn { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); background: #007bff; border: none; width: 44px; height: 44px; border-radius: 50%; cursor: pointer; display: flex; justify-content: center; align-items: center; transition: background-color 0.2s ease; }
        .search-btn:hover { background-color: #0056b3; }
        .search-btn svg { fill: white; width: 22px; height: 22px; }
        .results-container > div { margin-bottom: 1.5rem; }
        .card { background: #1e1e1e; padding: 1.5rem; border-radius: 12px; animation: fadeIn 0.5s ease forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .card h2 { font-size: 1.5rem; margin-bottom: 1rem; border-left: 4px solid #007bff; padding-left: 1rem; }
        .summary-card p { line-height: 1.6; color: #ccc; }
        .sources-card ul { list-style: none; padding: 0; }
        .sources-card li a { display: block; padding: 0.8rem 1rem; margin-bottom: 0.5rem; background: #2a2a2a; border-radius: 8px; text-decoration: none; color: #d0d0d0; transition: background-color 0.2s ease, color 0.2s ease; word-break: break-all; }
        .sources-card li a:hover { background-color: #383838; color: #fff; }
        .deep-dive-btn { width: 100%; padding: 1rem; font-size: 1.2rem; font-weight: bold; color: #fff; background: linear-gradient(90deg, #1e90ff, #ff1493); border: none; border-radius: 12px; cursor: pointer; transition: transform 0.2s ease; }
        .deep-dive-btn:hover { transform: scale(1.02); }
        .deep-dive-btn:disabled { background: #555; cursor: not-allowed; }
        .loader { text-align: center; padding: 2rem; font-size: 1.2rem; }
        .deep-analysis-card h4 { font-size: 1.2rem; color: #00aaff; margin-top: 1.5rem; }
        .deep-analysis-card p { line-height: 1.5; }
    `;
}

function renderHeader() {
    const header = document.querySelector('.header');
    header.innerHTML = `
        <h1><span class="logo">🤖</span> Robot <span class="genesis">Genesis</span></h1>
        <p>探索机器人宇宙 | 社区驱动，AI实时分析</p>
    `;
}

function renderSearchBox() {
    const searchBox = document.querySelector('.search-box');
    searchBox.innerHTML = `
        <input type="text" id="robotInput" class="search-input" placeholder="输入任何机器人名称 (e.g., Figure 02)">
        <button onclick="performSearch()" class="search-btn">
            <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"></path></svg>
        </button>
    `;
    document.getElementById('robotInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });
}

async function performSearch() {
    const input = document.getElementById('robotInput').value.trim();
    const resultsContainer = document.getElementById('results-container');
    if (!input) return;
    resultsContainer.innerHTML = `<div class="loader card">🧠 正在联系AI情报官，请稍候...</div>`;
    try {
        const response = await fetch(`/api/analyze?robot=${encodeURIComponent(input)}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `服务器返回错误 ${response.status}`);
        }
        intelligenceBriefing = await response.json();
        renderIntelligenceBriefing(intelligenceBriefing);
    } catch (error) {
        resultsContainer.innerHTML = `<div class="card" style="color: #ff5c5c;">❌ 分析出错: ${error.message}</div>`;
    }
}

function renderIntelligenceBriefing(data) {
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '';
    const { robotInfo, summary, sources } = data;
    resultsContainer.innerHTML += `
        <div class="summary-card card">
            <h2>${robotInfo.name} - 摘要</h2>
            <p><strong>制造商:</strong> ${robotInfo.manufacturer}<br><strong>类型:</strong> ${robotInfo.type}</p>
            <p style="margin-top: 1rem;">${summary}</p>
        </div>
    `;
    let sourcesHTML = '<div class="sources-card card"><h2>信息源</h2><ul>';
    if (sources.official) sourcesHTML += `<li><a href="${sources.official}" target="_blank" rel="noopener noreferrer"><strong>官网:</strong> ${sources.official}</a></li>`;
    if (sources.wikipedia) sourcesHTML += `<li><a href="${sources.wikipedia}" target="_blank" rel="noopener noreferrer"><strong>维基百科:</strong> ${sources.wikipedia}</a></li>`;
    (sources.news || []).forEach(item => sourcesHTML += `<li><a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.title}</a></li>`);
    (sources.videos || []).forEach(item => sourcesHTML += `<li><a href="${item.url}" target="_blank" rel="noopener noreferrer">🎬 ${item.title}</a></li>`);
    sourcesHTML += '</ul></div>';
    resultsContainer.innerHTML += sourcesHTML;
    resultsContainer.innerHTML += `
        <div class="deep-dive-card">
            <button id="deep-dive-btn" class="deep-dive-btn">🤖 启动AI进行深度技术分析</button>
        </div>
        <div id="deep-analysis-results"></div>
    `;
    document.getElementById('deep-dive-btn').addEventListener('click', performDeepDive);
}

async function performDeepDive() {
    const deepDiveBtn = document.getElementById('deep-dive-btn');
    const deepAnalysisContainer = document.getElementById('deep-analysis-results');
    if (!intelligenceBriefing || !intelligenceBriefing.sources) {
        deepAnalysisContainer.innerHTML = `<div class="card" style="color: #ff5c5c;">错误：缺少用于深度分析的信息源。</div>`;
        return;
    }
    deepDiveBtn.innerText = '🧠 AI正在阅读所有资料并深度思考中...';
    deepDiveBtn.disabled = true;
    const { official, wikipedia, news, videos } = intelligenceBriefing.sources;
    const allUrls = [official, wikipedia, ...(news || []).map(n => n.url), ...(videos || []).map(v => v.url)].filter(Boolean);
    try {
        const response = await fetch(`/api/deep_analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urls: allUrls })
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `深度分析服务器返回错误 ${response.status}`);
        }
        const deepAnalysisResult = await response.json();
        renderDeepAnalysis(deepAnalysisResult);
        deepDiveBtn.style.display = 'none';
    } catch (error) {
        deepAnalysisContainer.innerHTML = `<div class="card" style="color: #ff5c5c;">❌ 深度分析出错: ${error.message}</div>`;
        deepDiveBtn.innerText = '分析失败，请重试';
        deepDiveBtn.disabled = false;
    }
}

function renderDeepAnalysis(data) {
    const deepAnalysisContainer = document.getElementById('deep-analysis-results');
    let html = `<div class="deep-analysis-card card"><h2>深度技术分析</h2>`;
    if (data.technical_summary) {
        html += `<p style="margin-bottom: 1rem;">${data.technical_summary}</p>`;
    }
    for (const [key, system] of Object.entries(data)) {
        if (typeof system === 'object' && system !== null && key !== 'technical_summary') {
            html += `<div style="margin-top: 1.5rem; border-left: 3px solid #1e90ff; padding-left: 1rem;">
                        <h4>${key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</h4>
                        <p><strong>组件:</strong> ${(system.components || ['N/A']).join(', ')}</p>
                        <p><strong>伙伴/供应商:</strong> ${(system.suppliers_and_partners || ['N/A']).join(', ')}</p>
                        <p><strong>分析:</strong> ${system.analysis || 'N/A'}</p>
                    </div>`;
        }
    }
    html += `</div>`;
    deepAnalysisContainer.innerHTML = html;
}
