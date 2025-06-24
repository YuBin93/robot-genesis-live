// public/js/app.js (V4.1 - Final Rendering Polish)

class RobotGenesisAppV4 {
    constructor() {
        this.container = document.getElementById('app-container');
        this.reportData = null;
    }

    init() {
        this.injectStyles();
        this.renderInitialView();
    }

    injectStyles() {
        const styleTag = document.getElementById('main-styles');
        styleTag.innerHTML = `
            :root { --bg-color: #121212; --card-bg-color: #1e1e1e; --text-color: #e0e0e0; --text-muted-color: #b3b3b3; --primary-color: #007bff; --accent-gradient: linear-gradient(90deg, #1e90ff, #ff1493); --border-color: #404040; }
            body { background-color: var(--bg-color); color: var(--text-color); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; padding: 5vh 2vw; }
            .container { width: 95%; max-width: 800px; }
            .header { text-align: center; margin-bottom: 2rem; }
            .header h1 { font-size: 2.8rem; font-weight: bold; line-height: 1.2; }
            .header .logo { font-size: 3rem; margin-right: 10px; vertical-align: middle; }
            .header .genesis { font-size: 3.2rem; background: linear-gradient(90deg, #ff8a00, #e52e71); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .header p { margin-top: 1rem; color: var(--text-muted-color); font-size: 1.1rem; }
            .search-box { margin-bottom: 2rem; position: relative; }
            .search-input { width: 100%; background: #282828; border: 1px solid var(--border-color); color: #fff; padding: 1rem 3.5rem 1rem 1.2rem; border-radius: 50px; font-size: 1rem; box-sizing: border-box; transition: all 0.2s ease; }
            .search-input:focus { border-color: var(--primary-color); box-shadow: 0 0 15px rgba(0, 123, 255, 0.5); }
            .search-btn { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); background: var(--primary-color); border: none; width: 44px; height: 44px; border-radius: 50%; cursor: pointer; display: flex; justify-content: center; align-items: center; transition: background-color 0.2s ease; }
            .search-btn svg { fill: white; width: 22px; height: 22px; }
            #report-container > div { margin-bottom: 1.5rem; }
            .card { background: var(--card-bg-color); padding: 1.5rem; border-radius: 12px; animation: fadeIn 0.5s ease forwards; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
            .card h2 { font-size: 1.5rem; margin-bottom: 1rem; border-left: 4px solid var(--primary-color); padding-left: 1rem; }
            .task-progress { text-align: center; }
            .report-nav { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1.5rem; }
            .nav-btn { padding: 0.5rem 1rem; background: #333; border: 1px solid #555; color: #ccc; border-radius: 20px; cursor: pointer; transition: all 0.2s ease; }
            .nav-btn.active { background: var(--primary-color); color: white; border-color: var(--primary-color); }
            .report-section { display: none; }
            .report-section.active { display: block; }
            table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
            th, td { padding: 0.8rem; text-align: left; border-bottom: 1px solid #444; }
            th { background-color: #2a2a2a; }
            #sankey-diagram { width: 100%; min-height: 500px; }
            #sankey-diagram svg { font-family: sans-serif; font-size: 12px; }
            #sankey-diagram .node rect { fill-opacity: .9; shape-rendering: crispEdges; stroke: #000; stroke-width: 0.5px; }
            #sankey-diagram .link { fill: none; stroke-opacity: .4; }
            #sankey-diagram .link:hover { stroke-opacity: .7; }
        `;
    }

    renderInitialView() {
        this.container.innerHTML = `
            <div class="container">
                <header class="header">
                    <h1><span class="logo">🤖</span> Robot <span class="genesis">Genesis</span></h1>
                    <p>任务驱动的产业链与战略分析</p>
                </header>
                <div class="search-box">
                    <input type="text" id="robotInput" class="search-input" placeholder="输入机器人名称启动任务链...">
                    <button id="search-btn" class="search-btn">
                        <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"></path></svg>
                    </button>
                </div>
                <div id="report-container"></div>
            </div>
        `;
        document.getElementById('search-btn').onclick = () => this.performAnalysis();
        document.getElementById('robotInput').onkeypress = (e) => { if (e.key === 'Enter') this.performAnalysis(); };
    }

    async performAnalysis() {
        const input = document.getElementById('robotInput').value.trim();
        const reportContainer = document.getElementById('report-container');
        if (!input) return;
        reportContainer.innerHTML = `<div class="loader card task-progress">✅ 任务启动：正在构建情报网络，这可能需要1-2分钟...</div>`;
        try {
            const response = await fetch(`/api?robot=${encodeURIComponent(input)}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.details || errorData.error || `服务器返回错误 ${response.status}`);
            }
            this.reportData = await response.json();
            this.renderReport();
        } catch (error) {
            reportContainer.innerHTML = `<div class="card" style="color: #ff5c5c;">❌ 生成报告时出错: ${error.message}</div>`;
        }
    }

    renderReport() {
        const reportContainer = document.getElementById('report-container');
        if (!this.reportData || !this.reportData.task_outputs) {
            reportContainer.innerHTML = `<div class="card" style="color: #ffc107;">警告：AI返回的报告结构不完整。</div>`;
            return;
        }
        const tasks = this.reportData.task_outputs;
        const navHTML = `
            <div class="report-nav">
                <button class="nav-btn active" data-section="tech">技术架构</button>
                <button class="nav-btn" data-section="supply">供应链</button>
                <button class="nav-btn" data-section="market">市场格局</button>
                <button class="nav-btn" data-section="sankey">产业链图谱</button>
            </div>
        `;
        const techHTML = this.renderTechSection(tasks.T2_hardware_mapping);
        const supplyHTML = this.renderSupplySection(tasks.T3_supplier_mapping);
        const marketHTML = this.renderMarketSection(tasks.T4_market_analysis);
        const sankeyHTML = this.renderSankeySection();
        reportContainer.innerHTML = navHTML + techHTML + supplyHTML + marketHTML + sankeyHTML;
        this.activateNavigation();
        // 默认首先绘制一次图谱
        this.drawSankeyDiagram(tasks.T5_sankey_data);
    }
    
    activateNavigation() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.onclick = (e) => {
                const targetBtn = e.target;
                if (targetBtn.classList.contains('active')) return;
                document.querySelector('.nav-btn.active')?.classList.remove('active');
                document.querySelector('.report-section.active')?.classList.remove('active');
                targetBtn.classList.add('active');
                const sectionId = `section-${targetBtn.dataset.section}`;
                document.getElementById(sectionId)?.classList.add('active');
            };
        });
    }
    
    renderTechSection(t2) {
        let html = `<div id="section-tech" class="report-section active card"><h2>技术架构与硬件映射</h2>`;
        const mappings = t2 && t2.hardware_mappings ? t2.hardware_mappings : [];
        if (mappings.length === 0) {
            html += `<p>未能从信息源中解析出详细的技术与硬件映射关系。</p>`;
        } else {
            html += '<table><thead><tr><th>功能组件</th><th>硬件模块</th><th>用途</th></tr></thead><tbody>';
            mappings.forEach(m => { html += `<tr><td>${m.function || 'N/A'}</td><td>${m.hardware || 'N/A'}</td><td>${m.purpose || 'N/A'}</td></tr>`; });
            html += '</tbody></table>';
        }
        html += `</div>`;
        return html;
    }

    renderSupplySection(t3) {
        let html = `<div id="section-supply" class="report-section card"><h2>供应链分析</h2>`;
        const mappings = t3 && t3.supplier_mappings ? t3.supplier_mappings : [];
        if (mappings.length === 0) {
            html += `<p>未能从信息源中解析出详细的供应商信息。</p>`;
        } else {
            mappings.forEach(m => {
                html += `<h4>${m.hardware || '未知硬件'}</h4><ul>`;
                (m.suppliers || []).forEach(s => { html += `<li>${s.name} (${s.country || '地区未知'})</li>`; });
                html += '</ul>';
            });
        }
        html += `</div>`;
        return html;
    }
    
    renderMarketSection(t4) {
        let summaryText = (t4 && t4.market_analysis_summary) || '未能生成市场分析摘要。';
        if (typeof summaryText === 'object') {
            summaryText = JSON.stringify(summaryText, null, 2);
        }
        return `<div id="section-market" class="report-section card"><h2>市场格局分析</h2><p style="white-space: pre-wrap;">${summaryText}</p></div>`;
    }

    renderSankeySection() {
        return `<div id="section-sankey" class="report-section card"><h2>产业链图谱</h2><div id="sankey-diagram"></div><p style="text-align:center; font-size: 0.9rem; color: #888; margin-top: 1rem;">此图谱展示了从功能需求到硬件再到供应商的技术流向。</p></div>`;
    }

    drawSankeyDiagram(sankeyData) {
        const container = document.getElementById('sankey-diagram');
        if (!container) return;
        if (!sankeyData || !sankeyData.nodes || !sankeyData.links || sankeyData.nodes.length === 0 || sankeyData.links.length === 0) {
            container.innerHTML = '<p style="text-align:center; padding: 2rem;">无法生成产业链图谱，AI未能返回有效的图谱数据。</p>';
            return;
        }
        container.innerHTML = '';

        const width = container.clientWidth;
        const height = Math.max(500, sankeyData.nodes.length * 25);
        const svg = d3.select(container).append("svg").attr("viewBox", `0 0 ${width} ${height}`);

        const sankey = d3.sankey().nodeWidth(20).nodePadding(10).extent([[1, 5], [width - 1, height - 5]]);
        const graph = { nodes: sankeyData.nodes.map(d => ({...d})), links: sankeyData.links.map(d => ({...d})) };
        const {nodes, links} = sankey(graph);

        const color = d3.scaleOrdinal(d3.schemeTableau10);
        
        svg.append("g").selectAll("rect").data(nodes).join("rect")
            .attr("x", d => d.x0).attr("y", d => d.y0)
            .attr("height", d => d.y1 - d.y0).attr("width", d => d.x1 - d.x0)
            .attr("fill", d => color(d.id.replace(/ .*/, "")))
            .append("title").text(d => `${d.id}\n${d.value}`);

        const link = svg.append("g").attr("fill", "none").attr("stroke-opacity", 0.6)
            .selectAll("path").data(links).join("path")
            .attr("d", d3.sankeyLinkHorizontal())
            .attr("stroke", d => color(d.source.id.replace(/ .*/, "")))
            .attr("stroke-width", d => Math.max(1, d.width));
        
        link.append("title").text(d => `${d.source.id} → ${d.target.id}\nValue: ${d.value}`);

        svg.append("g").style("font", "12px sans-serif").attr("fill", "#fff")
            .selectAll("text").data(nodes).join("text")
            .attr("x", d => d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6)
            .attr("y", d => (d.y1 + d.y0) / 2).attr("dy", "0.35em")
            .attr("text-anchor", d => d.x0 < width / 2 ? "start" : "end")
            .text(d => d.id);
    }
}

// 启动应用
new RobotGenesisAppV4().init();
