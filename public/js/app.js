// public/js/app.js

async function searchRobot() {
    const input = document.getElementById('robotInput').value.trim();
    const resultsDiv = document.getElementById('results');
    const sankeyDiv = document.getElementById('sankey-diagram');
    
    if (!input) { return; }

    resultsDiv.innerHTML = `<div class="robot-card">🧠 正在为您实时分析 "${input}"...<br>AI大脑正在全球网络中搜索并思考...</div>`;
    sankeyDiv.innerHTML = '';

    try {
        const response = await fetch(`/api/analyze?robot=${encodeURIComponent(input)}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `服务器返回错误 ${response.status}`);
        }
        
        const robotData = await response.json();
        displayRobotInfo(robotData);
        createSankeyDiagram(robotData);

    } catch (error) {
        resultsDiv.innerHTML = `<div class="robot-card" style="color: #ff5c5c;">❌ 分析出错: ${error.message}</div>`;
        console.error('分析时出错:', error);
    }
}

// 支持回车搜索
document.getElementById('robotInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') { searchRobot(); }
});

// --- 下面的函数用于渲染数据，与之前版本基本相同 ---
function displayRobotInfo(robot) {
    const resultsDiv = document.getElementById('results');
    let html = `<div class="robot-card">
            <h2>${robot.name || 'N/A'}</h2>
            <p><strong>制造商:</strong> ${robot.manufacturer || 'N/A'}</p>
            <p><strong>类型:</strong> ${robot.type || 'N/A'}</p>
            <h3 style="margin-top: 1rem;">核心规格</h3><ul>`;
    for(const [key, value] of Object.entries(robot.specs || {})) {
        html += `<li><strong>${key}:</strong> ${value}</li>`;
    }
    html += `</ul><h3 style="margin-top: 1rem;">技术模块分析</h3>`;
    for(const [moduleName, data] of Object.entries(robot.modules || {})) {
        html += `<div style="margin: 10px 0; padding: 10px; border-left: 3px solid #007bff;">
                    <h4>${moduleName}</h4>
                    <p><strong>关键组件:</strong> ${data.components ? data.components.join('、 ') : 'N/A'}</p>
                    <p><strong>主要供应商:</strong> ${data.suppliers ? data.suppliers.join('、 ') : 'N/A'}</p>
                </div>`;
    }
    html += `</div>`;
    resultsDiv.innerHTML = html;
}
function createSankeyDiagram(robot) { /* ...从之前版本复制drawSankey和createSankeyDiagram... */ }
function drawSankey(container, data) { /* ...从之前版本复制... */ }
