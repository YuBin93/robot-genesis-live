// public/js/app.js (V5.0 - Function Calling Renderer)

class RobotGenesisAppV5 {
    constructor() {
        this.container = document.getElementById('app-container');
        if (!this.container) { console.error("Fatal Error: #app-container not found."); return; }
        this.reportData = null;
    }

    init() {
        this.injectStyles();
        this.renderInitialView();
    }

    injectStyles() {
        const styleTag = document.getElementById('main-styles');
        if (!styleTag) return;
        styleTag.innerHTML = `
            :root { --bg-color: #121212; --card-bg-color: #1e1e1e; --text-color: #e0e0e0; --text-muted-color: #b3b3b3; --primary-color: #007bff; --accent-gradient: linear-gradient(90deg, #1e90ff, #ff1493); --border-color: #404040; --success-color: #28a745; --danger-color: #dc3545;}
            body { background-color: var(--bg-color); color: var(--text-color); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; padding: 5vh 2vw; }
            .container { width: 95%; max-width: 800px; }
            .header { text-align: center; margin-bottom: 2rem; }
            h1, h2, h3, h4 { color: #fff; }
            .header h1 { font-size: 2.8rem; font-weight: bold; line-height: 1.2; }
            .header .logo { font-size: 3rem; margin-right: 10px; vertical-align: middle; }
            .header .genesis { font-size: 3.2rem; background: linear-gradient(90deg, #ff8a00, #e52e71); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .header p { margin-top: 1rem; color: var(--text-muted-color); font-size: 1.1rem; }
            .search-box { margin-bottom: 2rem; position: relative; }
            .search-input { width: 100%; background: #282828; border: 1px solid var(--border-color); color: #fff; padding: 1rem 3.5rem 1rem 1.2rem; border-radius: 50px; font-size: 1rem; box-sizing: border-box; transition: all 0.2s ease; }
            .search-input:focus { border-color: var(--primary-color); box-shadow: 0 0 15px rgba(0, 123, 255, 0.5); }
            .search-btn { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); background: var(--primary-color); border: none; width: 44px; height: 44px; border-radius: 50%; cursor: pointer; display: flex; justify-content: center; align-items: center; }
            .search-btn svg { fill: white; width: 22px; height: 22px; }
            #report-container > div { margin-bottom: 1.5rem; }
            .card { background: var(--card-bg-color); padding: 1.5rem; border-radius: 12px; animation: fadeIn 0.5s ease forwards; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
            .card h2 { font-size: 1.5rem; margin-bottom: 1rem; border-left: 4px solid var(--primary-color); padding-left: 1rem; }
            .report-nav { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1.5rem; }
            .nav-btn { padding: 0.5rem 1rem; background: #333; border: 1px solid #555; color: #ccc; border-radius: 20px; cursor: pointer; }
            .nav-btn.active { background: var(--primary-color); color: white; border-color: var(--primary-color); }
            .report-section { display: none; }
            .report-section.active { display: block; }
            .competitor-grid { display: grid; gap: 1rem; }
            .competitor-card h3 { font-size: 1.2rem; margin-bottom: 0.8rem; }
            .strengths li::before { content: '👍'; margin-right: 0.5rem; color: var(--success-color); }
            .weaknesses li::before { content: '👎'; margin-right: 0.5rem; color: var(--danger-color); }
            ul { list-style: none; padding-left: 0.5rem; }
            @media (min-width: 768px) { .competitor-grid { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); } }
        `;
    }
    
    renderInitialView() {
        this.container.innerHTML = `...`; // 与V4.3相同
    }

    async performAnalysis() {
        // ... 与V4.3相同，只是API端点是 /api
    }

    renderReport() {
        const reportContainer = document.getElementById('report-container');
        const reportContent = this.reportData?.report_content;
        if (!reportContent) {
            reportContainer.innerHTML = `<div class="card" style="color: #ffc107;">警告：AI未能生成有效的报告内容。</div>`;
            return;
        }
        
        const navHTML = `
            <div class="report-nav">
                <button class="nav-btn active" data-section="summary">执行摘要</button>
                <button class="nav-btn" data-section="landscape">竞争格局</button>
                <button class="nav-btn" data-section="trends">市场洞察</button>
            </div>
        `;
        
        const summaryHTML = this.renderSummarySection(reportContent.executive_summary);
        const landscapeHTML = this.renderLandscapeSection(reportContent.competitive_landscape);
        const trendsHTML = this.renderTrendsSection(reportContent.market_trends_and_predictions);

        reportContainer.innerHTML = navHTML + summaryHTML + landscapeHTML + trendsHTML;
        this.activateNavigation();
    }

    activateNavigation() {
        // ... 与V4.3相同
    }
    
    renderSummarySection(summary) {
        return `<div id="section-summary" class="report-section active card"><h2>执行摘要</h2><p>${summary || 'N/A'}</p></div>`;
    }

    renderLandscapeSection(landscape) {
        if (!landscape || landscape.length === 0) return '<div id="section-landscape" class="report-section card"><h2>竞争格局</h2><p>未能生成竞品分析。</p></div>';
        let html = '<div id="section-landscape" class="report-section card"><h2>竞争格局</h2><div class="competitor-grid">';
        landscape.forEach(c => {
            html += `<div class="competitor-card card">
                <h3>${c.robot || '未知机器人'}</h3>
                <div class="strengths"><strong>优势:</strong> <ul>${(c.strengths || []).map(s => `<li>${s}</li>`).join('')}</ul></div>
                <div class="weaknesses"><strong>劣势:</strong> <ul>${(c.weaknesses || []).map(w => `<li>${w}</li>`).join('')}</ul></div>
                <p><strong>战略焦点:</strong> ${c.strategic_focus || 'N/A'}</p>
            </div>`;
        });
        html += '</div></div>';
        return html;
    }
    
    renderTrendsSection(trends) {
        if (!trends) return '<div id="section-trends" class="report-section card"><h2>市场洞察</h2><p>未能生成市场趋势分析。</p></div>';
        return `<div id="section-trends" class="report-section card">
            <h2>市场洞察</h2>
            <h4>关键技术趋势:</h4>
            <ul>${(trends.key_technology_trends || []).map(t => `<li>${t}</li>`).join('')}</ul>
            <h4 style="margin-top:1rem;">供应链洞察:</h4>
            <p>${trends.supply_chain_insights || 'N/A'}</p>
            <h4 style="margin-top:1rem;">未来展望:</h4>
            <p>${trends.future_outlook_prediction || 'N/A'}</p>
        </div>`;
    }
}

document.addEventListener('DOMContentLoaded', () => { new RobotGenesisAppV5().init(); });
