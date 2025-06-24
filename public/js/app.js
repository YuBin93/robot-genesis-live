// public/js/app.js (V3.1 - Strategic Dashboard Engine - Final Complete Code)

/**
 * Robot Genesis App - V3.1
 * An AI-powered strategic intelligence dashboard for robotics.
 * This script handles all frontend logic, from UI rendering to API calls.
 */

// --- Application Entry Point ---
// Waits for the HTML document to be fully loaded before running the app.
document.addEventListener('DOMContentLoaded', () => {
    // Creates a new instance of our main application class and starts it.
    new RobotGenesisApp().init();
});

// --- Main Application Class ---
// Organizes all application logic in an object-oriented way for clarity and maintainability.
class RobotGenesisApp {
    // The constructor initializes the main container element for the UI.
    constructor() {
        this.container = document.getElementById('app-container');
        this.reportData = null; // Will store the full report from the API.
    }

    // init() is the starting point for the application instance.
    init() {
        this.injectStyles(); // 1. Inject all CSS styles into the <style> tag.
        this.renderInitialView(); // 2. Render the initial search screen.
    }

    // 1. Style Injection: Centralizes all CSS for easier management.
    injectStyles() {
        const styleTag = document.getElementById('main-styles');
        if (!styleTag) {
            console.error("Fatal Error: #main-styles tag not found in HTML.");
            return;
        }
        styleTag.innerHTML = `
            /* --- Global & Layout --- */
            :root {
                --bg-color: #0d1117;
                --card-bg-color: #161b22;
                --border-color: #30363d;
                --text-primary: #c9d1d9;
                --text-secondary: #8b949e;
                --accent-color: #58a6ff;
                --success-color: #238636;
            }
            body { background-color: var(--bg-color); color: var(--text-primary); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI', 'Segoe UI Symbol'; display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; padding: 5vh 2vw; }
            .container { width: 95%; max-width: 1200px; }
            .dashboard { display: grid; gap: 1.5rem; }
            @media (min-width: 1024px) {
                .dashboard { grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); }
                .full-width-card { grid-column: 1 / -1; }
            }

            /* --- Header & Search --- */
            .header { text-align: center; margin-bottom: 2rem; }
            .header h1 { font-size: clamp(2.5rem, 6vw, 3rem); font-weight: 800; line-height: 1.2; color: #f0f6fc; }
            .header .logo { font-size: clamp(2.8rem, 7vw, 3.2rem); margin-right: 10px; vertical-align: middle; }
            .header .genesis { font-size: clamp(3rem, 7vw, 3.5rem); background: linear-gradient(90deg, #30cfd0, #330867); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .header p { margin-top: 0.5rem; color: var(--text-secondary); font-size: 1.1rem; }
            .search-box { margin-bottom: 2rem; position: relative; }
            .search-input { width: 100%; background: #21262d; border: 1px solid var(--border-color); color: var(--text-primary); padding: 1rem 3.5rem 1rem 1.2rem; border-radius: 50px; font-size: 1rem; box-sizing: border-box; transition: all 0.2s ease; }
            .search-input:focus { border-color: var(--accent-color); box-shadow: 0 0 15px rgba(88, 166, 255, 0.5); outline: none; }
            .search-btn { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); background: var(--success-color); border: none; width: 44px; height: 44px; border-radius: 50%; cursor: pointer; display: flex; justify-content: center; align-items: center; transition: background-color 0.2s ease; }
            .search-btn:hover { background-color: #2ea043; }
            .search-btn svg { fill: white; width: 22px; height: 22px; }

            /* --- Card Styles --- */
            .card { background: var(--card-bg-color); border: 1px solid var(--border-color); padding: 1.5rem; border-radius: 12px; animation: fadeIn 0.5s ease forwards; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
            .card h2 { font-size: 1.5rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.8rem; color: #f0f6fc; }
            .card h3 { font-size: 1.3rem; margin-top: 1.5rem; margin-bottom: 0.8rem; color: var(--accent-color); }
            .card h4 { font-size: 1.1rem; margin-top: 1rem; margin-bottom: 0.5rem; color: var(--text-secondary); font-weight: 600; }
            .card p { line-height: 1.6; margin-bottom: 0.5rem; }
            .card ul { list-style-type: none; padding-left: 0; }
            .card li { margin-bottom: 0.5rem; padding-left: 1.2rem; position: relative; }
            .strengths li::before { content: '👍'; position: absolute; left: 0; }
            .weaknesses li::before { content: '👎'; position: absolute; left: 0; }
            .teardown-module { margin-top: 1rem; padding-left: 1rem; border-left: 2px solid #484f58; }
            .competitor-card h3 small { font-size: 0.8rem; color: var(--text-secondary); margin-left: 0.5rem; }
            .data-confidence-card { background-color: rgba(255, 193, 7, 0.1); border-left: 4px solid #ffc107; }

            /* --- Loader & Error --- */
            .loader { text-align: center; padding: 2rem; font-size: 1.2rem; color: var(--text-secondary); }
        `;
    }
    
    // 2. Renders the initial screen with header and search box.
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
                        <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"></path></svg>
                    </button>
                </div>
                <div id="dashboard-container"></div>
            </div>
        `;
        // Bind events to the newly created elements.
        document.getElementById('search-btn').onclick = () => this.performSearch();
        document.getElementById('robotInput').onkeypress = (e) => { if(e.key === 'Enter') this.performSearch(); };
    }

    // 3. The core function to trigger the API call.
    async performSearch() {
        const input = document.getElementById('robotInput').value.trim();
        const dashboardContainer = document.getElementById('dashboard-container');
        if (!input) return;

        dashboardContainer.innerHTML = `<div class="loader card">📊 正在构建战略情报网络...<br>这可能需要1-2分钟，AI大脑正在高速运转，请保持耐心。</div>`;
        
        try {
            // Calls our V3 report API.
            const response = await fetch(`/api/report?robot=${encodeURIComponent(input)}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `服务器返回错误 ${response.status}`);
            }
            this.reportData = await response.json();
            this.renderDashboard();
        } catch (error) {
            dashboardContainer.innerHTML = `<div class="card" style="color: #ff7b72;">❌ 生成报告时出错: ${error.message}</div>`;
        }
    }

    // 4. Renders the entire dashboard based on the report data.
    renderDashboard() {
        const dashboardContainer = document.getElementById('dashboard-container');
        const data = this.reportData;
        if (!data) return;

        // Uses template literals to build the entire dashboard structure.
        dashboardContainer.innerHTML = `
            <div class="dashboard">
                ${this.renderExecutiveSummary(data.executive_summary)}
                ${(data.competitive_landscape || []).map(c => this.renderCompetitorCard(c)).join('')}
                ${this.renderTrendsCard(data.market_trends_and_predictions)}
                ${this.renderDataConfidenceCard(data.data_confidence)}
            </div>
        `;
    }

    // --- 5. Component Rendering Functions ---
    // Each function is responsible for rendering a specific card/module.
    renderExecutiveSummary(summary) {
        return `<div class="executive-summary card full-width-card">
            <h2>战略执行摘要</h2>
            <p>${summary || '暂无摘要信息。'}</p>
        </div>`;
    }

    renderCompetitorCard(competitor) {
        const teardown = competitor.technical_teardown || {};
        const analysis = competitor.strategic_analysis || {};

        let teardownHTML = '';
        // Dynamically creates the technical teardown section.
        for (const [system, details] of Object.entries(teardown)) {
            teardownHTML += `
                <div class="teardown-module">
                    <h4>${system.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</h4>
                    <p><strong>组件:</strong> ${(details.key_components || ['N/A']).join(', ')}</p>
                    <p><strong>供应商:</strong> ${(details.potential_suppliers || ['N/A']).join(', ')}</p>
                </div>
            `;
        }

        return `<div class="competitor-card card">
            <h3>${competitor.robot_name || '未知机器人'}<small>by ${competitor.manufacturer || '未知制造商'}</small></h3>
            
            <h4 style="margin-top: 1.5rem;">技术拆解</h4>
            ${teardownHTML}

            <h4 style="margin-top: 1.5rem;">战略分析</h4>
            <div class="strengths"><strong>优势:</strong> <ul>${(analysis.strengths || ['N/A']).map(s => `<li>${s}</li>`).join('')}</ul></div>
            <div class="weaknesses"><strong>劣势:</strong> <ul>${(analysis.weaknesses || ['N/A']).map(w => `<li>${w}</li>`).join('')}</ul></div>
            <p><strong>市场定位:</strong> ${analysis.market_position || 'N/A'}</p>
        </div>`;
    }
    
    renderTrendsCard(trends) {
        if (!trends) return '';
        return `<div class="trends-card card full-width-card">
            <h2>市场趋势与洞察</h2>
            <h4>关键技术趋势</h4>
            <ul>${(trends.key_technology_trends || ['N/A']).map(t => `<li>${t}</li>`).join('')}</ul>
            <h4 style="margin-top: 1rem;">供应链洞察</h4>
            <p>${trends.supply_chain_map || 'N/A'}</p>
            <h4 style="margin-top: 1rem;">未来展望</h4>
            <p>${trends.future_outlook || 'N/A'}</p>
        </div>`;
    }

    renderDataConfidenceCard(confidence) {
        if (!confidence) return '';
        return `<div class="data-confidence-card card full-width-card">
            <h2>数据质量与缺口</h2>
            <p><strong>评估:</strong> ${confidence.assessment || 'N/A'}</p>
            <h4 style="margin-top: 1rem;">已识别的数据缺口:</h4>
            <ul>${(confidence.identified_gaps || ['N/A']).map(g => `<li>${g}</li>`).join('')}</ul>
        </div>`;
    }
}
