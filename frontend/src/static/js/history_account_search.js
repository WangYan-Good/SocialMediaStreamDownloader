// History account search functionality
class HistoryAccountSearch {
    constructor() {
        this.searchInput = document.getElementById('historySearchInput');
        this.searchBtn = document.getElementById('searchHistoryBtn');
        this.searchResults = document.getElementById('historySearchResults');
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        // Search button click
        this.searchBtn.addEventListener('click', () => {
            this.searchHistoryAccounts();
        });
        
        // Enter key in search input
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchHistoryAccounts();
            }
        });
    }
    
    async searchHistoryAccounts() {
        const searchTerm = this.searchInput.value.trim();
        
        if (!searchTerm) {
            this.showSearchResults([]);
            return;
        }
        
        try {
            this.updateSearchStatus('正在检索历史记录...');
            
            // Call the API to search history
            const response = await fetch(`/api/history/search?q=${encodeURIComponent(searchTerm)}`);
            const data = await response.json();
            
            if (response.ok) {
                this.showSearchResults(data.results || []);
                this.updateSearchStatus(`找到 ${data.count || 0} 条匹配的记录`);
            } else {
                this.showSearchError(`检索失败: ${data.message || '未知错误'}`);
            }
        } catch (error) {
            this.showSearchError(`检索时发生错误: ${error.message}`);
        }
    }
    
    showSearchResults(results) {
        if (!this.searchResults) return;
        
        // Clear current results
        this.searchResults.innerHTML = '';
        
        if (!results || results.length === 0) {
            this.searchResults.innerHTML = '<div class="history-empty">未找到匹配的记录</div>';
            return;
        }
        
        results.forEach(item => {
            const searchItem = this.createSearchResultItem(item);
            this.searchResults.appendChild(searchItem);
        });
    }
    
    createSearchResultItem(item) {
        const div = document.createElement('div');
        div.className = 'history-search-item';
        
        // Format timestamp
        const timestamp = item.timestamp ? new Date(item.timestamp).toLocaleString('zh-CN') : 'N/A';
        
        // Create the HTML structure for the search result item
        div.innerHTML = `
            <div class="history-search-item-url">${this.escapeHtml(item.url || 'N/A')}</div>
            <div class="history-search-item-meta">
                <span>平台: ${item.platform ? this.escapeHtml(item.platform) : 'N/A'}</span>
                <span>状态: ${this.getStatusDisplay(item.status)}</span>
                <span>时间: ${timestamp}</span>
            </div>
        `;
        
        // Add click event to use this URL for download
        div.addEventListener('click', () => {
            this.useHistoryItemForDownload(item);
        });
        
        return div;
    }
    
    useHistoryItemForDownload(item) {
        // Fill the main download input with the URL from history
        const linkInput = document.getElementById('linkInput');
        if (linkInput) {
            // If there's already content, append the new URL on a new line
            if (linkInput.value.trim()) {
                linkInput.value += '\n' + item.url;
            } else {
                linkInput.value = item.url;
            }
            
            // Auto-resize the textarea if there's a function for it
            if (typeof autoResize === 'function') {
                autoResize(linkInput);
            }
        }
        
        // Optionally scroll to the download section
        document.getElementById('download').scrollIntoView({ behavior: 'smooth' });
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
    
    updateSearchStatus(message) {
        if (this.searchResults) {
            // Create a temporary status element
            const statusDiv = document.createElement('div');
            statusDiv.style.cssText = 'background: #e9ecef; padding: 5px; border-radius: 4px; margin-bottom: 10px; text-align: center; font-style: italic; font-size: 0.9em;';
            statusDiv.textContent = message;
            
            // Insert at the top of the search results
            this.searchResults.insertBefore(statusDiv, this.searchResults.firstChild);
            
            // Remove status after 3 seconds
            setTimeout(() => {
                if (statusDiv.parentNode) {
                    statusDiv.parentNode.removeChild(statusDiv);
                }
            }, 3000);
        }
    }
    
    showSearchError(message) {
        if (this.searchResults) {
            this.searchResults.innerHTML = `<div class="history-empty" style="color: red;">${message}</div>`;
        }
    }
}

// Initialize history account search when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('historySearchInput')) {
        window.historyAccountSearch = new HistoryAccountSearch();
    }
});