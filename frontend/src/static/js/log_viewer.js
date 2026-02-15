// 日志查看器功能
class LogViewer {
    constructor() {
        this.logOutput = document.getElementById('logOutput');
        this.logLevelSelect = document.getElementById('logLevelSelect');
        this.logLimitInput = document.getElementById('logLimitInput');
        this.refreshBtn = document.getElementById('refreshLogsBtn');
        this.clearBtn = document.getElementById('clearLogsBtn');
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        // 刷新日志按钮
        this.refreshBtn.addEventListener('click', () => {
            this.loadLogs();
        });
        
        // 清空日志按钮
        this.clearBtn.addEventListener('click', () => {
            this.clearLogs();
        });
        
        // 回车键刷新日志
        this.logLimitInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.loadLogs();
            }
        });
    }
    
    async loadLogs() {
        const logLevel = this.logLevelSelect.value;
        const limit = this.logLimitInput.value;
        
        try {
            this.updateStatus('正在加载日志...');
            
            const response = await fetch(`/api/logs?level=${logLevel}&limit=${limit}`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayLogs(data.log_entries);
                this.updateStatus(`已加载 ${data.total_entries_returned} 条日志，来自 ${data.log_file}`);
            } else {
                this.showError(`加载日志失败: ${data.message || '未知错误'}`);
            }
        } catch (error) {
            this.showError(`加载日志时发生错误: ${error.message}`);
        }
    }
    
    displayLogs(logEntries) {
        if (!this.logOutput) return;
        
        // 清空当前内容
        this.logOutput.innerHTML = '';
        
        if (!logEntries || logEntries.length === 0) {
            this.logOutput.innerHTML = '<p>暂无日志数据</p>';
            return;
        }
        
        // 反向显示日志（最新的在最上面）
        const reversedLogs = [...logEntries].reverse();
        
        reversedLogs.forEach(entry => {
            const logElement = this.createLogEntryElement(entry);
            this.logOutput.appendChild(logElement);
        });
        
        // 滚动到底部
        this.logOutput.scrollTop = this.logOutput.scrollHeight;
    }
    
    createLogEntryElement(logText) {
        const div = document.createElement('div');
        div.className = 'log-entry';
        
        // 尝试从日志文本中提取日志级别
        const logLevelMatch = logText.match(/\[(DEBUG|INFO|WARNING|ERROR)\]/);
        if (logLevelMatch) {
            const logLevel = logLevelMatch[1];
            div.classList.add(logLevel);
            div.title = `日志级别: ${logLevel}`;
        } else {
            div.classList.add('INFO'); // 默认为INFO级别
        }
        
        // 格式化日志文本
        div.textContent = logText;
        
        return div;
    }
    
    clearLogs() {
        if (this.logOutput) {
            this.logOutput.innerHTML = '<p>日志已清空。点击"刷新日志"按钮重新加载。</p>';
        }
    }
    
    updateStatus(message) {
        if (this.logOutput) {
            // 保留现有的日志内容，并添加状态信息
            const statusDiv = document.createElement('div');
            statusDiv.style.cssText = 'position: sticky; top: 0; background: #e9ecef; padding: 5px; border-radius: 4px; margin-bottom: 10px; text-align: center; font-style: italic;';
            statusDiv.textContent = message;
            
            // 临时显示状态信息
            this.logOutput.insertBefore(statusDiv, this.logOutput.firstChild);
            
            // 3秒后移除状态信息
            setTimeout(() => {
                if (statusDiv.parentNode) {
                    statusDiv.parentNode.removeChild(statusDiv);
                }
            }, 3000);
        }
    }
    
    showError(message) {
        if (this.logOutput) {
            this.logOutput.innerHTML = `<p style="color: red;">${message}</p>`;
        }
    }
}

// 初始化日志查看器
document.addEventListener('DOMContentLoaded', function() {
    // 确保在日志标签页内容加载后初始化
    if (document.getElementById('log-content')) {
        // 延迟初始化，确保DOM元素已完全加载
        setTimeout(() => {
            new LogViewer();
        }, 100);
    }
});