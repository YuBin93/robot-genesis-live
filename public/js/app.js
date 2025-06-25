// public/js/app.js (The Final Asynchronous Flow)

class RobotGenesisFinal {
    constructor() {
        this.container = document.getElementById('app-container');
    }

    init() {
        this.injectStyles();
        this.renderInitialView();
    }

    injectStyles() {
        const styleTag = document.getElementById('main-styles');
        if (!styleTag) return;
        styleTag.innerHTML = `
            :root { --bg-color: #0a0a0a; --card-bg-color: #1a1a1a; --text-color: #f0f0f0; --text-muted-color: #a0a0a0; --primary-color: #0d6efd; --border-color: #3a3a3a; --success-color: #198754; --danger-color: #dc3545;}
            body { background-color: var(--bg-color); color: var(--text-color); font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; padding: 5vh 2vw; }
            .container { width: 95%; max-width: 800px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 2.5rem; }
            .header h1 { font-size: 3rem; font-weight: 800; }
            .header .logo { display: inline-block; transform: rotate(-5deg); margin-right: 0.5rem; font-size: 2.8rem; }
            .header p { margin-top: 0.5rem; color: var(--text-muted-color); font-size: 1.1rem; }
            .search-box { margin-bottom: 2rem; position: relative; }
            .search-input { width: 100%; background: #222; border: 1px solid var(--border-color); color: #fff; padding: 1rem 1.2rem; border-radius: 8px; font-size: 1rem; box-sizing: border-box; }
            .search-btn { position: absolute; right: 0; top: 0; bottom: 0; background: var(--primary-color); border: none; width: 50px; border-radius: 0 8px 8px 0; cursor: pointer; }
            .card { background: var(--card-bg-color); padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid var(--border-color); animation: fadeIn 0.5s; }
            @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
            .card h2 { font-size: 1.5rem; margin-bottom: 1rem; }
            .entity-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; }
            .entity-card { text-align: center; }
            .entity-card .status-dot { width: 10px; height: 10px; border-radius: 50%; background-color: #ffa500; display: inline-block; margin-right: 0.5rem; animation: pulse 1.5s infinite; }
            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
            .entity-card.success .status-dot { background-color: var(--success-color); animation: none; }
            .entity-card.error .status-dot { background-color: var(--danger-color); animation: none; }
            .final-report-btn { width: 100%; padding: 1rem; font-size: 1.2rem; font-weight: bold; color: #fff; background: var(--success-color); border: none; border-radius: 8px; cursor: pointer; display: none; margin-top: 1rem; }
        `;
    }
    
    renderInitialView() {
        this.container.innerHTML = `
            <div class="container">
                <header class="header"><h1><span class="logo">🤖</span> Robot Genesis</h1><p>分步式AI战略分析引擎</p></header>
                <div class="search-box">
                    <input type="text" id="robotInput" class="search-input" placeholder="输入机器人名称启动分析...">
                    <button id="search-btn" class="search-btn">🔍</button>
                </div>
                <div id="progress-container"></div>
                <div id="final-report-container"></div>
            </div>`;
        document.getElementById('search-btn').addEventListener('click', () => this.startAnalysis());
        document.getElementById('robotInput').addEventListener('keypress', (e) => { if (e.key === 'Enter') this.startAnalysis(); });
    }

    async startAnalysis() {
        const input = document.getElementById('robotInput')?.value.trim();
        const progressContainer = document.getElementById('progress-container');
        if (!input || !progressContainer) return;

        progressContainer.innerHTML = `<div class="card">正在识别关联实体...</div>`;
        document.getElementById('final-report-container').innerHTML = '';

        try {
            const response = await fetch(`/api/start_analysis?robot=${encodeURIComponent(input)}`);
            const { task_id, entities } = await response.json();
            
            this.renderEntityPlaceholders(entities);
            const allEntityData = await this.analyzeAllEntities(entities);
            this.showFinalReportButton(allEntityData);

        } catch (error) {
            progressContainer.innerHTML = `<div class="card" style="color:red;">启动分析失败: ${error.message}</div>`;
        }
    }
    
    renderEntityPlaceholders(entities) {
        const progressContainer = document.getElementById('progress-container');
        let html = `<h2>情报收集中...</h2><div class="entity-grid">`;
        entities.forEach(entity => {
            html += `<div id="entity-${entity.name.replace(/\s+/g, '-')}" class="card entity-card">
                        <span class="status-dot"></span>
                        <span>${entity.name}</span>
                     </div>`;
        });
        html += `</div>`;
        progressContainer.innerHTML = html;
    }

    async analyzeAllEntities(entities) {
        const analysisPromises = entities.map(entity => 
            fetch(`/api/analyze_entity?name=${encodeURIComponent(entity.name)}`)
                .then(async res => {
                    const card = document.getElementById(`entity-${entity.name.replace(/\s+/g, '-')}`);
                    if (res.ok) {
                        card?.classList.add('success');
                        return res.json();
                    } else {
                        card?.classList.add('error');
                        const errorData = await res.json();
                        throw new Error(`分析 ${entity.name} 失败: ${errorData.error}`);
                    }
                })
        );
        return Promise.all(analysisPromises);
    }
    
    showFinalReportButton(allEntityData) {
        const progressContainer = document.getElementById('progress-container');
        if (!progressContainer) return;
        const button = document.createElement('button');
        button.id = 'final-report-btn';
        button.className = 'final-report-btn';
        button.innerText = '生成最终战略报告';
        button.style.display = 'block';
        button.onclick = () => this.generateFinalReport(allEntityData);
        progressContainer.appendChild(button);
    }

    async generateFinalReport(allEntityData) {
        const button = document.getElementById('final-report-btn');
        if(button) {
            button.innerText = '🧠 终极AI分析师正在撰写报告...';
            button.disabled = true;
        }
        
        try {
            const response = await fetch(`/api/generate_final_report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(allEntityData)
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '生成最终报告时服务器出错');
            }
            const finalReport = await response.json();
            this.renderFinalDashboard(finalReport);
        } catch (error) {
            document.getElementById('final-report-container').innerHTML = `<div class="card" style="color:red;">生成最终报告失败: ${error.message}</div>`;
            if(button) {
                button.innerText = '生成失败，请重试';
                button.disabled = false;
            }
        }
    }

    renderFinalDashboard(report) {
        document.getElementById('final-report-container').innerHTML = `
            <div class="card"><h2>执行摘要</h2><p>${report.executive_summary || 'N/A'}</p></div>
            <div class="card"><h2>竞争格局</h2>${this.renderLandscape(report.competitive_landscape)}</div>
            <div class="card"><h2>市场洞察</h2>${this.renderTrends(report.market_trends_and_predictions)}</div>
        `;
    }
    
    renderLandscape(landscape) {
        if (!landscape) return '<p>N/A</p>';
        let html = '<div class="competitor-grid">';
        landscape.forEach(c => {
            html += `<div class="card">
                <h3>${c.robot}</h3>
                <div class="strengths"><strong>优势:</strong><ul>${(c.strengths || []).map(s => `<li>${s}</li>`).join('')}</ul></div>
                <div class="weaknesses"><strong>劣势:</strong><ul>${(c.weaknesses || []).map(w => `<li>${w}</li>`).join('')}</ul></div>
            </div>`;
        });
        html += '</div>';
        return html;
    }

    renderTrends(trends) {
        if (!trends) return '<p>N/A</p>';
        return `
            <h4>关键技术趋势:</h4><ul>${(trends.key_technology_trends || []).map(t => `<li>${t}</li>`).join('')}</ul>
            <h4 style="margin-top:1rem;">供应链洞察:</h4><p>${trends.supply_chain_insights || 'N/A'}</p>
            <h4 style="margin-top:1rem;">未来展望:</h4><p>${trends.future_outlook_prediction || 'N/A'}</p>
        `;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new RobotGenesisFinal().init();
});
