// History account search functionality - Enhanced version
class HistoryAccountSearch {
    constructor() {
        this.sortBy = document.getElementById('sortBy');
        this.filterPlatform = document.getElementById('filterPlatform');
        this.filterBtn = document.getElementById('filterBtn');
        this.filteredResults = document.getElementById('filteredResults');
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        // Filter button click
        this.filterBtn.addEventListener('click', () => {
            this.filterHistoryAccounts();
        });
        
        // Enter key in filter controls
        this.sortBy.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.filterHistoryAccounts();
            }
        });
    }
    
    async filterHistoryAccounts() {
        const sortBy = this.sortBy.value;
        const platform = this.filterPlatform.value;
        
        try {
            this.updateFilterStatus('正在筛选历史记录...');
            
            // Build query parameters
            const params = new URLSearchParams();
            params.append('sort_by', sortBy);
            if (platform) params.append('platform', platform);
            
            // Call the API to filter history
            const response = await fetch(`/api/history/filter?${params.toString()}`);
            const data = await response.json();
            
            if (response.ok) {
                this.showFilteredResults(data.results || []);
                this.updateFilterStatus(`找到 ${data.count || 0} 条匹配的记录`);
            } else {
                this.showFilterError(`筛选失败: ${data.message || '未知错误'}`);
            }
        } catch (error) {
            this.showFilterError(`筛选时发生错误: ${error.message}`);
        }
    }
    
    showFilteredResults(results) {
        if (!this.filteredResults) return;
        
        // Clear current results
        this.filteredResults.innerHTML = '';
        
        if (!results || results.length === 0) {
            this.filteredResults.innerHTML = '<div class="filtered-results-empty">未找到匹配的记录</div>';
            return;
        }
        
        results.forEach(item => {
            const resultItem = this.createFilterResultItem(item);
            this.filteredResults.appendChild(resultItem);
        });
    }
    
    createFilterResultItem(item) {
        const div = document.createElement('div');
        div.className = 'filter-result-item';
        
        // Format timestamp
        const timestamp = item.timestamp ? new Date(item.timestamp).toLocaleString('zh-CN') : 'N/A';
        
        // Create the HTML structure for the filter result item
        div.innerHTML = `
            <div class="filter-result-info">
                <div class="filter-result-url">${this.escapeHtml(item.url || 'N/A')}</div>
                <div class="filter-result-meta">
                    <span>平台: ${item.platform ? this.escapeHtml(item.platform) : 'N/A'}</span>
                    <span>状态: ${this.getStatusDisplay(item.status)}</span>
                    <span>时间: ${timestamp}</span>
                </div>
            </div>
            <div class="filter-result-actions">
                <button class="download-btn" onclick="historyAccountSearch.downloadUrl('${this.escapeHtml(item.url)}')">下载</button>
                <button class="view-btn" onclick="historyAccountSearch.viewDetails('${item.id || 'N/A'}')">查看详情</button>
            </div>
        `;
        
        return div;
    }
    
    async downloadUrl(url) {
        try {
            // Prepare data for the download request
            const jsonData = {
                urls: [url],
                score: 0,
                favorite: false
            };
            
            // Send the download request to the server
            const response = await fetch('/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(jsonData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert(`下载已开始: ${data.message}`);
            } else {
                alert(`下载失败: ${data.message}`);
            }
        } catch (error) {
            alert(`下载时发生错误: ${error.message}`);
        }
    }
    
    viewDetails(id) {
        alert(`查看ID为 ${id} 的记录详情`);
    }
    
    getStatusDisplay(status) {
        switch(status) {
            case 'started': return '进行中';
            case 'completed': return '已完成';
            case 'failed': return '失败';
            case 'cancelled': return '已取消';
            default: return status || '未知';
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    updateFilterStatus(message) {
        if (this.filteredResults) {
            // Create a temporary status element
            const statusDiv = document.createElement('div');
            statusDiv.style.cssText = 'background: #e9ecef; padding: 5px; border-radius: 4px; margin-bottom: 10px; text-align: center; font-style: italic; font-size: 0.9em;';
            statusDiv.textContent = message;
            
            // Insert at the top of the filtered results
            this.filteredResults.insertBefore(statusDiv, this.filteredResults.firstChild);
            
            // Remove status after 3 seconds
            setTimeout(() => {
                if (statusDiv.parentNode) {
                    statusDiv.parentNode.removeChild(statusDiv);
                }
            }, 3000);
        }
    }
    
    showFilterError(message) {
        if (this.filteredResults) {
            this.filteredResults.innerHTML = `<div class="filtered-results-empty" style="color: red;">${message}</div>`;
        }
    }
}

// Initialize history account search when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('filterBtn')) {
        window.historyAccountSearch = new HistoryAccountSearch();
    }
});