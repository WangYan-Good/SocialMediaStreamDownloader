// Download status monitoring
let downloadStatusInterval = null;

// Function to fetch and update download status
async function updateDownloadStatus() {
    try {
        const response = await fetch('/api/download-status');
        const data = await response.json();
        
        // Update the UI elements
        document.getElementById('currentDownloads').textContent = data.current_downloads;
        
        if (data.is_limited) {
            document.getElementById('maxDownloads').textContent = data.max_downloads;
            document.getElementById('availableSlots').textContent = data.available_slots;
        } else {
            document.getElementById('maxDownloads').textContent = '∞'; // Infinity symbol for unlimited
            document.getElementById('availableSlots').textContent = '∞';
        }
    } catch (error) {
        console.error('Error fetching download status:', error);
    }
}

// Start polling for download status
function startDownloadStatusPolling() {
    // Update immediately
    updateDownloadStatus();
    
    // Then poll every 2 seconds
    downloadStatusInterval = setInterval(updateDownloadStatus, 2000);
}

// Stop polling
function stopDownloadStatusPolling() {
    if (downloadStatusInterval) {
        clearInterval(downloadStatusInterval);
        downloadStatusInterval = null;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    startDownloadStatusPolling();
});

// Clean up when page is unloaded
window.addEventListener('beforeunload', function() {
    stopDownloadStatusPolling();
});