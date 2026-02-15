// Settings management functionality
class SettingsManager {
    constructor() {
        this.currentConfig = {};
        
        this.initElements();
        this.initEventListeners();
        this.loadCurrentConfig();
    }
    
    initElements() {
        // Download settings
        this.maxDownloadCountInput = document.getElementById('maxDownloadCount');
        this.downloadPathInput = document.getElementById('downloadPath');
        this.maxThreadCountInput = document.getElementById('maxThreadCount');
        
        // Log settings
        this.logEnableCheckbox = document.getElementById('logEnable');
        this.logPathInput = document.getElementById('logPath');
        this.structuredLoggingCheckbox = document.getElementById('structuredLogging');
        
        // System settings
        this.savePathInput = document.getElementById('savePath');
        this.maxRetryInput = document.getElementById('maxRetry');
        
        // Buttons
        this.setMaxDownloadCountBtn = document.getElementById('setMaxDownloadCountBtn');
        this.setDownloadPathBtn = document.getElementById('setDownloadPathBtn');
        this.setMaxThreadCountBtn = document.getElementById('setMaxThreadCountBtn');
        this.setLogPathBtn = document.getElementById('setLogPathBtn');
        this.setSavePathBtn = document.getElementById('setSavePathBtn');
        this.setMaxRetryBtn = document.getElementById('setMaxRetryBtn');
        this.saveSettingsBtn = document.getElementById('saveSettingsBtn');
        this.resetSettingsBtn = document.getElementById('resetSettingsBtn');
        
        // Current config display
        this.currentConfigDisplay = document.getElementById('currentConfig');
    }
    
    initEventListeners() {
        // Button event listeners
        this.setMaxDownloadCountBtn.addEventListener('click', () => {
            this.updateMaxDownloadCount();
        });
        
        this.setDownloadPathBtn.addEventListener('click', () => {
            this.updateDownloadPath();
        });
        
        this.setMaxThreadCountBtn.addEventListener('click', () => {
            this.updateMaxThreadCount();
        });
        
        this.setLogPathBtn.addEventListener('click', () => {
            this.updateLogPath();
        });
        
        this.setSavePathBtn.addEventListener('click', () => {
            this.updateSavePath();
        });
        
        this.setMaxRetryBtn.addEventListener('click', () => {
            this.updateMaxRetry();
        });
        
        this.saveSettingsBtn.addEventListener('click', () => {
            this.saveAllSettings();
        });
        
        this.resetSettingsBtn.addEventListener('click', () => {
            this.resetSettings();
        });
        
        // Enter key in input fields
        this.bindEnterKeys();
    }
    
    bindEnterKeys() {
        // Bind Enter key to trigger corresponding button for each input
        this.maxDownloadCountInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.updateMaxDownloadCount();
        });
        
        this.downloadPathInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.updateDownloadPath();
        });
        
        this.maxThreadCountInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.updateMaxThreadCount();
        });
        
        this.logPathInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.updateLogPath();
        });
        
        this.savePathInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.updateSavePath();
        });
        
        this.maxRetryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.updateMaxRetry();
        });
    }
    
    async loadCurrentConfig() {
        try {
            this.currentConfigDisplay.textContent = '加载配置中...';
            
            const response = await fetch('/api/config');
            const data = await response.json();
            
            if (response.ok) {
                this.currentConfig = data.config;
                this.displayCurrentConfig();
                this.populateFormFields();
            } else {
                this.currentConfigDisplay.textContent = `加载配置失败: ${data.message || '未知错误'}`;
            }
        } catch (error) {
            this.currentConfigDisplay.textContent = `加载配置时发生错误: ${error.message}`;
        }
    }
    
    displayCurrentConfig() {
        if (this.currentConfigDisplay) {
            // Format and display the current configuration
            const configStr = JSON.stringify(this.currentConfig, null, 2);
            this.currentConfigDisplay.textContent = configStr;
        }
    }
    
    populateFormFields() {
        // Populate download settings
        if (this.currentConfig.max_download_count !== undefined) {
            this.maxDownloadCountInput.value = this.currentConfig.max_download_count;
        }
        
        if (this.currentConfig.save_path) {
            this.downloadPathInput.value = this.currentConfig.save_path;
            this.savePathInput.value = this.currentConfig.save_path;
        }
        
        if (this.currentConfig.max_thread !== undefined) {
            this.maxThreadCountInput.value = this.currentConfig.max_thread;
        }
        
        // Populate log settings
        if (this.currentConfig.log_enable !== undefined) {
            this.logEnableCheckbox.checked = this.currentConfig.log_enable;
        }
        
        if (this.currentConfig.log_path) {
            this.logPathInput.value = this.currentConfig.log_path;
        }
        
        if (this.currentConfig.structured_logging !== undefined) {
            this.structuredLoggingCheckbox.checked = this.currentConfig.structured_logging;
        }
        
        // Populate system settings
        if (this.currentConfig.max_retry !== undefined) {
            this.maxRetryInput.value = this.currentConfig.max_retry;
        }
    }
    
    async updateMaxDownloadCount() {
        const value = parseInt(this.maxDownloadCountInput.value);
        if (isNaN(value) || value < 1) {
            alert('请输入有效的最大下载数量（大于0）');
            return;
        }
        
        try {
            const response = await fetch('/api/config', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    max_download_count: value
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert(`最大下载数量已设置为: ${value}`);
                this.loadCurrentConfig(); // Reload config to reflect changes
            } else {
                alert(`设置失败: ${data.message || '未知错误'}`);
            }
        } catch (error) {
            alert(`设置时发生错误: ${error.message}`);
        }
    }
    
    async updateDownloadPath() {
        const value = this.downloadPathInput.value.trim();
        if (!value) {
            alert('请输入有效的下载路径');
            return;
        }
        
        try {
            const response = await fetch('/api/config', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    save_path: value
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert(`下载路径已设置为: ${value}`);
                this.loadCurrentConfig(); // Reload config to reflect changes
            } else {
                alert(`设置失败: ${data.message || '未知错误'}`);
            }
        } catch (error) {
            alert(`设置时发生错误: ${error.message}`);
        }
    }
    
    async updateMaxThreadCount() {
        const value = parseInt(this.maxThreadCountInput.value);
        if (isNaN(value) || value < 0) {
            alert('请输入有效的最大线程数（非负数）');
            return;
        }
        
        try {
            const response = await fetch('/api/config', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    max_thread: value
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert(`最大线程数已设置为: ${value}`);
                this.loadCurrentConfig(); // Reload config to reflect changes
            } else {
                alert(`设置失败: ${data.message || '未知错误'}`);
            }
        } catch (error) {
            alert(`设置时发生错误: ${error.message}`);
        }
    }
    
    async updateLogPath() {
        const value = this.logPathInput.value.trim();
        if (!value) {
            alert('请输入有效的日志路径');
            return;
        }
        
        try {
            const response = await fetch('/api/config', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    log_path: value
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert(`日志路径已设置为: ${value}`);
                this.loadCurrentConfig(); // Reload config to reflect changes
            } else {
                alert(`设置失败: ${data.message || '未知错误'}`);
            }
        } catch (error) {
            alert(`设置时发生错误: ${error.message}`);
        }
    }
    
    async updateSavePath() {
        const value = this.savePathInput.value.trim();
        if (!value) {
            alert('请输入有效的保存路径');
            return;
        }
        
        try {
            const response = await fetch('/api/config', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    save_path: value
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert(`保存路径已设置为: ${value}`);
                this.loadCurrentConfig(); // Reload config to reflect changes
            } else {
                alert(`设置失败: ${data.message || '未知错误'}`);
            }
        } catch (error) {
            alert(`设置时发生错误: ${error.message}`);
        }
    }
    
    async updateMaxRetry() {
        const value = parseInt(this.maxRetryInput.value);
        if (isNaN(value) || value < 1) {
            alert('请输入有效的最大重试次数（大于0）');
            return;
        }
        
        try {
            const response = await fetch('/api/config', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    max_retry: value
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert(`最大重试次数已设置为: ${value}`);
                this.loadCurrentConfig(); // Reload config to reflect changes
            } else {
                alert(`设置失败: ${data.message || '未知错误'}`);
            }
        } catch (error) {
            alert(`设置时发生错误: ${error.message}`);
        }
    }
    
    async saveAllSettings() {
        // Collect all settings from the form
        const settings = {};
        
        // Download settings
        const maxDownloadCount = parseInt(this.maxDownloadCountInput.value);
        if (!isNaN(maxDownloadCount) && maxDownloadCount > 0) {
            settings.max_download_count = maxDownloadCount;
        }
        
        const downloadPath = this.downloadPathInput.value.trim();
        if (downloadPath) {
            settings.save_path = downloadPath;
        }
        
        const maxThreadCount = parseInt(this.maxThreadCountInput.value);
        if (!isNaN(maxThreadCount) && maxThreadCount >= 0) {
            settings.max_thread = maxThreadCount;
        }
        
        // Log settings
        settings.log_enable = this.logEnableCheckbox.checked;
        
        const logPath = this.logPathInput.value.trim();
        if (logPath) {
            settings.log_path = logPath;
        }
        
        settings.structured_logging = this.structuredLoggingCheckbox.checked;
        
        // System settings
        const savePath = this.savePathInput.value.trim();
        if (savePath) {
            settings.save_path = savePath; // Override with system save path
        }
        
        const maxRetry = parseInt(this.maxRetryInput.value);
        if (!isNaN(maxRetry) && maxRetry > 0) {
            settings.max_retry = maxRetry;
        }
        
        try {
            const response = await fetch('/api/config', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(settings)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert('所有设置已保存成功！');
                this.loadCurrentConfig(); // Reload config to reflect changes
            } else {
                alert(`保存失败: ${data.message || '未知错误'}`);
            }
        } catch (error) {
            alert(`保存时发生错误: ${error.message}`);
        }
    }
    
    resetSettings() {
        if (confirm('确定要重置所有设置为默认值吗？此操作不可撤销。')) {
            // Reset form fields to default values
            this.maxDownloadCountInput.value = 5;
            this.downloadPathInput.value = '/mnt/video';
            this.maxThreadCountInput.value = 0;
            this.logEnableCheckbox.checked = true;
            this.logPathInput.value = './logs';
            this.structuredLoggingCheckbox.checked = false;
            this.savePathInput.value = '/mnt/video';
            this.maxRetryInput.value = 3;
            
            alert('设置已重置为默认值（请注意：这并未保存到服务器，需要点击保存设置按钮来应用更改）');
        }
    }
}

// Initialize settings manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('setting-content')) {
        window.settingsManager = new SettingsManager();
    }
});