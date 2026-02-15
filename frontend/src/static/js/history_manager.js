// History management functionality
class HistoryManager {
    constructor() {
        this.historyList = document.getElementById('historyList');
        this.historyFilter = document.getElementById('historyFilter');
        this.historyLimit = document.getElementById('historyLimit');
        this.refreshBtn = document.getElementById('refreshHistoryBtn');
        this.clearBtn = document.getElementById('clearHistoryBtn');
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        // Refresh history button
        this.refreshBtn.addEventListener('click', () => {
            this.loadHistory();
        });
        
        // Clear history button
        this.clearBtn.addEventListener('click', () => {
            this.confirmAndClearHistory();
        });
        
        // Filter and limit changes
        this.historyFilter.addEventListener('change', () => {
            this.loadHistory();
        });
        
        this.historyLimit.addEventListener('change', () => {
            this.loadHistory();
        });
        
        // Enter key in limit field
        this.historyLimit.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.loadHistory();
            }
        });
    }
    
    async loadHistory() {
        const filter = this.historyFilter.value;
        const limit = this.historyLimit.value;
        
        try {
            this.updateStatus('正在加载历史记录...');
            
            // Build query parameters
            let queryParams = `limit=${limit}`;
            if (filter !== 'all') {
                queryParams += `&status=${filter}`;
            }
            
            const response = await fetch(`/api/history?${queryParams}`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayHistory(data.history);
                this.updateStatus(`显示 ${data.history.length} 条记录，共 ${data.total_records} 条历史记录`);
            } else {
                this.showError(`加载历史记录失败: ${data.message || '未知错误'}`);
            }
        } catch (error) {
            this.showError(`加载历史记录时发生错误: ${error.message}`);
        }
    }
    
    displayHistory(historyRecords) {
        if (!this.historyList) return;
        
        // Clear current content
        this.historyList.innerHTML = '';
        
        if (!historyRecords || historyRecords.length === 0) {
            this.historyList.innerHTML = '<div class="history-empty">暂无历史记录</div>';
            return;
        }
        
        historyRecords.forEach(record => {
            const historyItem = this.createHistoryItemElement(record);
            this.historyList.appendChild(historyItem);
        });
    }
    
    createHistoryItemElement(record) {
        const div = document.createElement('div');
        div.className = `history-item ${record.status}`;
        
        // Format timestamp
        const timestamp = new Date(record.timestamp).toLocaleString('zh-CN');
        
        // Create the HTML structure for the history item
        div.innerHTML = `
            <div class="history-item-url">${this.escapeHtml(record.url)}</div>
            <div class="history-item-details">
                <span class="history-item-status">状态: <strong>${this.getStatusDisplay(record.status)}</strong></span>
                <span class="history-item-timestamp">时间: ${timestamp}</span>
                ${record.platform ? `<span class="history-item-platform">平台: ${this.escapeHtml(record.platform)}</span>` : ''}
            </div>
            ${Object.keys(record.details).length > 0 ? `
            <div class="history-item-details">
                ${this.formatDetails(record.details)}
            </div>
            ` : ''}
        `;
        
        return div;
    }
    
    getStatusDisplay(status) {
        switch(status) {
            case 'started': return '进行中';
            case 'completed': return '已完成';
            case 'failed': return '失败';
            case 'cancelled': return '已取消';
            default: return status;
        }
    }
    
    formatDetails(details) {
        let detailStr = '';
        if (details.score !== undefined) {
            detailStr += `评分: ${details.score}, `;
        }
        if (details.favorite !== undefined) {
            detailStr += `收藏: ${details.favorite ? '是' : '否'}, `;
        }
        if (details.submitted_by) {
            detailStr += `提交者: ${details.submitted_by}, `;
        }
        if (details.completed_at) {
            const completedAt = new Date(details.completed_at).toLocaleString('zh-CN');
            detailStr += `完成时间: ${completedAt}, `;
        }
        if (details.completed_by) {
            detailStr += `完成者: ${details.completed_by}, `;
        }
        
        // Remove trailing comma and space
        if (detailStr.endsWith(', ')) {
            detailStr = detailStr.slice(0, -2);
        }
        
        return detailStr ? `<strong>详情:</strong> ${detailStr}` : '';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    async confirmAndClearHistory() {
        if (confirm('确定要清空所有下载历史吗？此操作不可撤销。')) {
            try {
                const response = await fetch('/api/history/clear', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    this.displayHistory([]);
                    this.updateStatus('历史记录已清空');
                    alert(`成功清空 ${data.cleared_count} 条历史记录`);
                } else {
                    alert(`清空历史记录失败: ${data.message}`);
                }
            } catch (error) {
                alert(`清空历史记录时发生错误: ${error.message}`);
            }
        }
    }
    
    updateStatus(message) {
        if (this.historyList) {
            // Create a temporary status element
            const statusDiv = document.createElement('div');
            statusDiv.style.cssText = 'position: sticky; top: 0; background: #e9ecef; padding: 5px; border-radius: 4px; margin-bottom: 10px; text-align: center; font-style: italic;';
            statusDiv.textContent = message;
            
            // Insert at the top of the history list
            this.historyList.insertBefore(statusDiv, this.historyList.firstChild);
            
            // Remove status after 3 seconds
            setTimeout(() => {
                if (statusDiv.parentNode) {
                    statusDiv.parentNode.removeChild(statusDiv);
                }
            }, 3000);
        }
    }
    
    showError(message) {
        if (this.historyList) {
            this.historyList.innerHTML = `<div class="history-empty" style="color: red;">${message}</div>`;
        }
    }
}

// Initialize history manager
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the history manager when DOM is loaded
    if (document.getElementById('history-content')) {
        // Delay initialization to ensure DOM elements are ready
        setTimeout(() => {
            new HistoryManager();
        }, 100);
    }
});