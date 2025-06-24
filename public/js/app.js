// public/js/app.js (V3.0 - Dashboard Engine)

document.addEventListener('DOMContentLoaded', () => {
    new RobotGenesisApp().init();
});

class RobotGenesisApp {
    constructor() {
        this.container = document.getElementById('app-container');
        this.reportData = null;
    }

    init() {
        this.injectStyles();
        this.renderInitialView();
    }

    injectStyles() {
        // ... (复制上一版完整的CSS样式) ...
        // 添加新的样式
        const styleTag = document.getElementById('main-styles');
        styleTag.innerHTML += `
            .dashboard { display: grid; gap: 1.5rem; }
            .executive-summary { grid-column: 1 / -1; }
            .competitor-card { display: flex; flex-direction: column; }
            .competitor-card h3 { font-size: 1.2rem; color: #eee; }
            .strengths, .weaknesses { margin: 0.5rem 0; }
            .strengths li::before { content: '👍'; margin-right: 0.5rem; }
            .weaknesses li::before { content: '👎'; margin-right: 0.5rem; }
            .trends-card ul { padding-left: 1rem; }
            .data-gaps-card { background-color: #2a2a2a; border-left-color: #ffc107; }
            @media (min-width: 1024px) {
                .dashboard { grid-template-columns: repeat(3, 1fr); }
                .competitor-card { grid-column: span 1; }
            }
        `;
    }
    
    renderInitialView() {
        this.container.innerHTML = `
            <div class="container">
                <header class="header">
                    <h1><span class="logo">🤖</span> Robot <span class="genesis">Genesis</span></h1>
                    <p>战略情报仪表盘</p>
                </header>
                <div class="search-box">
                    <input type="text" id="robotInput" class="search-input" placeholder="输入核心机器人名称启动分析...">
                    <button id="search-btn" class="search-btn">
                        <svg viewBox="0 0 24 24"><path d="..."></path></svg>
                    </button>
                </div>
                <div id="dashboard-container"></div>
            </div>
        `;
        document.getElementById('search-btn').onclick = () => this.performSearch();
        document.getElementById('robotInput').onkeypress = (e) => { if(e.key === 'Enter') this.performSearch(); };
    }

    async performSearch() {
        const input = document.getElementById('robotInput').value.trim();
        const dashboardContainer = document.getElementById('dashboard-container');
        if (!input) return;

        dashboardContainer.innerHTML = `<div class="loader card">📊 正在构建战略情报网络，这可能需要1-2分钟...</div>`;
        
        try {
            const response = await fetch(`/api/report?robot=${encodeURIComponent(input)}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `服务器返回错误 ${response.status}`);
            }
            this.reportData = await response.json();
            this.renderDashboard();
        } catch (error) {
            dashboardContainer.innerHTML = `<div class="card" style="color: #ff5c5c;">❌ 生成报告时出错: ${error.message}</div>`;
        }
    }

    renderDashboard() {
        const dashboardContainer = document.getElementById('dashboard-container');
        const data = this.reportData;
        dashboardContainer.innerHTML = `<div class="dashboard">
            ${this.renderExecutiveSummary(data.executive_summary)}
            ${(data.competitive_landscape || []).map(c => this.renderCompetitorCard(c)).join('')}
            ${this.renderTrendsCard(data.market_trends_and_predictions)}
            ${this.renderDataGapsCard(data.data_discrepancies_and_gaps)}
        </div>`;
    }

    renderExecutiveSummary(summary) {
        return `<div class="executive-summary card">
            <h2>战略执行摘要</h2>
            <p>${summary || 'N/A'}</p>
        </div>`;
    }

    renderCompetitorCard(competitor) {
        return `<div class="competitor-card card">
            <h3>${competitor.robot || 'N/A'}</h3>
            <div class="strengths"><strong>优势:</strong> <ul>${(competitor.strengths || []).map(s => `<li>${s}</li>`).join('')}</ul></div>
            <div class="weaknesses"><strong>劣势:</strong> <ul>${(competitor.weaknesses || []).map(w => `<li>${w}</li>`).join('')}</ul></div>
            <p><strong>战略焦点:</strong> ${competitor.strategic_focus || 'N/A'}</p>
        </div>`;
    }
    
    renderTrendsCard(trends) {
        return `<div class="trends-card card">
            <h2>市场趋势与洞察</h2>
            <h4>关键技术趋势:</h4>
            <ul>${(trends.key_technology_trends || []).map(t => `<li>${t}</li>`).join('')}</ul>
            <h4>供应链洞察:</h4>
            <p>${trends.supply_chain_insights || 'N/A'}</p>
            <h4>未来展望:</h4>
            <p>${trends.future_outlook_prediction || 'N/A'}</p>
        </div>`;
    }

    renderDataGapsCard(gaps) {
        return `<div class="data-gaps-card card">
            <h2>数据质量与缺口</h2>
            <ul>${(gaps || []).map(g => `<li>${g}</li>`).join('')}</ul>
        </div>`;
    }
}
