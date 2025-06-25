// ... (之前的initializeApp, injectStyles, renderHeader, renderSearchBox, performAnalysis 保持不变)
// 只需替换或添加下面的函数

class RobotGenesisAppV4 {
    // ...
    renderReport() {
        const reportContainer = document.getElementById('report-container');
        const tasks = this.reportData?.task_outputs;
        if (!tasks) {
            reportContainer.innerHTML = `<div class="card" style="color: #ffc107;">警告：AI返回的报告结构不完整。</div>`;
            return;
        }
        const navHTML = `<div class="report-nav"> ... </div>`;
        const techHTML = this.renderTechSection(tasks.T2_hardware_mapping);
        const supplyHTML = this.renderSupplySection(tasks.T3_supplier_mapping);
        const marketHTML = this.renderMarketSection(tasks.T4_market_analysis);
        const sankeyHTML = this.renderSankeySection();
        reportContainer.innerHTML = navHTML + techHTML + supplyHTML + marketHTML + sankeyHTML;
        this.activateNavigation();
        this.drawSankeyDiagram(tasks.T5_sankey_data);
    }
    
    // ... activateNavigation 保持不变 ...
    
    renderTechSection(t2) { /* ... 使用 ?. 和 ?? 的健壮版本 ... */ }
    renderSupplySection(t3) { /* ... 使用 ?. 和 ?? 的健джин版本 ... */ }
    renderMarketSection(t4) { /* ... 使用 ?. 和 ?? 的健壮版本 ... */ }
    renderSankeySection() { /* ... 保持不变 ... */ }
    drawSankeyDiagram(sankeyData) { /* ... 使用 ?. 和 ?? 的健壮版本 ... */ }
}
