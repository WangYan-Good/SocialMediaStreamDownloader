// System load monitoring and alert functionality
class SystemLoadMonitor {
    constructor() {
        this.alertModal = null;
        this.currentAlerts = [];
        this.loadMonitoringInterval = null;
        this.isMonitoring = false;
        
        this.initAlertModal();
        this.startMonitoring();
    }
    
    initAlertModal() {
        // Create modal element if it doesn't exist
        if (!document.getElementById('system-alert-modal')) {
            const modalHtml = `
                <div id="system-alert-modal" class="modal-overlay">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3>⚠️ 系统负载过高</h3>
                            <span class="close-btn">&times;</span>
                        </div>
                        <div class="modal-body">
                            <p>检测到系统负载过高，可能影响下载性能：</p>
                            <ul id="alert-list"></ul>
                            <p>建议稍后再尝试下载操作。</p>
                        </div>
                        <div class="modal-footer">
                            <button id="acknowledge-btn">确认</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // Add modal styles if not already present
            if (!document.getElementById('system-alert-styles')) {
                const style = document.createElement('style');
                style.id = 'system-alert-styles';
                style.textContent = `
                    .modal-overlay {
                        display: none;
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background-color: rgba(0, 0, 0, 0.5);
                        z-index: 10000;
                        justify-content: center;
                        align-items: center;
                    }
                    
                    .modal-content {
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                        max-width: 500px;
                        width: 80%;
                        max-height: 80vh;
                        overflow-y: auto;
                    }
                    
                    .modal-header {
                        padding: 15px 20px;
                        border-bottom: 1px solid #eee;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    
                    .modal-header h3 {
                        margin: 0;
                        color: #d9534f;
                    }
                    
                    .close-btn {
                        font-size: 24px;
                        cursor: pointer;
                        color: #aaa;
                    }
                    
                    .close-btn:hover {
                        color: #000;
                    }
                    
                    .modal-body {
                        padding: 20px;
                    }
                    
                    .modal-body ul {
                        list-style-type: none;
                        padding: 0;
                    }
                    
                    .modal-body li {
                        padding: 5px 0;
                        color: #d9534f;
                        font-weight: bold;
                    }
                    
                    .modal-footer {
                        padding: 15px 20px;
                        border-top: 1px solid #eee;
                        text-align: right;
                    }
                    
                    .modal-footer button {
                        padding: 8px 16px;
                        background-color: #007bff;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    }
                    
                    .modal-footer button:hover {
                        background-color: #0056b3;
                    }
                `;
                document.head.appendChild(style);
            }
            
            // Add event listeners to modal elements
            const modal = document.getElementById('system-alert-modal');
            const closeBtn = modal.querySelector('.close-btn');
            const acknowledgeBtn = document.getElementById('acknowledge-btn');
            
            closeBtn.onclick = () => this.hideAlertModal();
            acknowledgeBtn.onclick = () => this.hideAlertModal();
            window.onclick = (event) => {
                if (event.target === modal) {
                    this.hideAlertModal();
                }
            };
        }
    }
    
    async checkSystemLoad() {
        try {
            const response = await fetch('/api/system-load');
            const data = await response.json();
            
            if (data.is_overloaded) {
                this.showAlertModal(data.alerts);
            } else if (this.currentAlerts.length > 0) {
                // System load has returned to normal, hide alert if it was shown
                this.hideAlertModal();
            }
            
            this.currentAlerts = data.alerts || [];
            
            // Update load indicators in the UI if they exist
            this.updateLoadIndicators(data);
        } catch (error) {
            console.error('Error checking system load:', error);
        }
    }
    
    updateLoadIndicators(data) {
        // Update load indicators in the UI if elements exist
        if (document.getElementById('cpu-load-indicator')) {
            const cpuElement = document.getElementById('cpu-load-indicator');
            cpuElement.textContent = `${data.load_metrics.cpu_percent.toFixed(1)}%`;
            cpuElement.className = `load-indicator ${data.load_metrics.cpu_percent > data.thresholds.cpu_percent ? 'high' : 'normal'}`;
        }
        
        if (document.getElementById('memory-load-indicator')) {
            const memElement = document.getElementById('memory-load-indicator');
            memElement.textContent = `${data.load_metrics.memory_percent.toFixed(1)}%`;
            memElement.className = `load-indicator ${data.load_metrics.memory_percent > data.thresholds.memory_percent ? 'high' : 'normal'}`;
        }
        
        if (document.getElementById('disk-load-indicator')) {
            const diskElement = document.getElementById('disk-load-indicator');
            diskElement.textContent = `${data.load_metrics.disk_percent.toFixed(1)}%`;
            diskElement.className = `load-indicator ${data.load_metrics.disk_percent > data.thresholds.disk_percent ? 'high' : 'normal'}`;
        }
        
        if (document.getElementById('network-load-indicator')) {
            const netElement = document.getElementById('network-load-indicator');
            netElement.textContent = `${data.load_metrics.network_speed_mb_s.toFixed(2)} MB/s`;
            netElement.className = `load-indicator ${data.load_metrics.network_speed_mb_s > data.thresholds.network_speed_mb_s ? 'high' : 'normal'}`;
        }
    }
    
    showAlertModal(alerts) {
        const modal = document.getElementById('system-alert-modal');
        const alertList = document.getElementById('alert-list');
        
        // Clear previous alerts
        alertList.innerHTML = '';
        
        // Add new alerts
        alerts.forEach(alert => {
            const li = document.createElement('li');
            li.textContent = alert;
            alertList.appendChild(li);
        });
        
        modal.style.display = 'flex';
    }
    
    hideAlertModal() {
        const modal = document.getElementById('system-alert-modal');
        modal.style.display = 'none';
    }
    
    startMonitoring() {
        if (!this.isMonitoring) {
            this.isMonitoring = true;
            // Check system load every 5 seconds
            this.checkSystemLoad(); // Initial check
            this.loadMonitoringInterval = setInterval(() => {
                this.checkSystemLoad();
            }, 5000);
        }
    }
    
    stopMonitoring() {
        if (this.isMonitoring) {
            this.isMonitoring = false;
            if (this.loadMonitoringInterval) {
                clearInterval(this.loadMonitoringInterval);
                this.loadMonitoringInterval = null;
            }
            this.hideAlertModal();
        }
    }
}

// Initialize system load monitor when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the system load monitor
    window.systemLoadMonitor = new SystemLoadMonitor();
});

// Also add a check before submitting downloads
document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('submitButton');
    if (submitButton) {
        const originalClickHandler = submitButton.onclick;
        submitButton.onclick = async function(e) {
            // Check system load before allowing download submission
            try {
                const response = await fetch('/api/system-load');
                const data = await response.json();
                
                if (data.is_overloaded) {
                    // Show alert modal with the overload information
                    window.systemLoadMonitor.showAlertModal(data.alerts);
                    alert('系统当前负载过高，无法处理新的下载请求。请稍后再试。');
                    return false; // Prevent the original click handler
                }
            } catch (error) {
                console.error('Error checking system load:', error);
                // Proceed anyway if we can't check the load
            }
            
            // Call the original handler if system is not overloaded
            if (originalClickHandler) {
                originalClickHandler.call(this, e);
            }
        };
    }
});