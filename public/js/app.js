// 在 public/js/app.js 中

// ... (其他函数保持不变) ...

renderReport() {
    const reportContainer = document.getElementById('report-container');
    // 新的报告结构
    const reportContent = this.reportData?.report_content;
    if (!reportContent) {
        reportContainer.innerHTML = `<div class="card" style="color: #ffc107;">警告：AI未能生成有效的报告内容。</div>`;
        return;
    }
    
    // 我们不再有T1-T5，而是直接从 reportContent 中获取数据
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

// 需要创建新的渲染函数
renderSummarySection(summary) { /* ... */ }
renderLandscapeSection(landscape) { /* ... */ }
renderTrendsSection(trends) { /* ... */ }
