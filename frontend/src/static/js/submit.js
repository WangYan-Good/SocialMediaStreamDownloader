// 链接处理功能
document.addEventListener('DOMContentLoaded', function() {
  const submitButton = document.getElementById('submitButton');
  
  if (submitButton) {
      submitButton.addEventListener('click', processSubmit);
  }
});

async function processSubmit() {
    urls = processLink();
    score = processScoring();
    favorite = isFavorite();

    if (urls && urls.length > 0) {
        // 检查当前下载状态
        try {
            const statusResponse = await fetch('/api/download-status');
            const statusData = await statusResponse.json();
            
            // 如果有限制且没有可用槽位，提示用户
            if (statusData.is_limited && statusData.available_slots <= 0) {
                alert(`下载限制已达到上限！当前下载: ${statusData.current_downloads}/${statusData.max_downloads}，没有可用槽位。请等待一些下载完成后再试。`);
                return;
            }
            
            // 更新状态显示
            document.getElementById('currentDownloads').textContent = statusData.current_downloads + 1;
            if (statusData.is_limited) {
                document.getElementById('availableSlots').textContent = statusData.available_slots - 1;
            }
            
        } catch (error) {
            console.error('Error checking download status:', error);
            // 即使检查状态失败，也继续提交请求
        }
        
        // 发送数据到后端
        fetch('/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ urls: urls, score: score, favorite: favorite }),
        })
        .then(async response => {
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
                throw new Error(errorData.message || 'Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Success:', data);
            alert('Link submitted successfully!');
            
            // 更新状态显示
            if (data.current_downloads !== undefined) {
                document.getElementById('currentDownloads').textContent = data.current_downloads;
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('Error submitting data: ' + error.message);
        });
    } else {
        alert('No valid links found! Please enter at least one valid URL starting with http:// or https://');
    }
}

function processLink() {
  // 获取输入框中的链接
  const linkInput = document.getElementById('linkInput');
  if (!linkInput) return;
  
  const link = linkInput.value.trim();

  // 使用正则表达式解析链接
  const urlRegex = /https?:\/\/[^\s]+/g;
  const matches = link.match(urlRegex);

  return matches ? matches : [];
}

function processScoring() {
    // 获取进度条百分比
    const slider = document.getElementById('preferenceSlider');
    if (!slider) return 0;
    return isNaN(slider.value) ? 0 : slider.value;
}

function isFavorite() {
    // 获取收藏复选框的状态
    const favoriteCheckbox = document.getElementById('favoriteCheckbox');
    if (!favoriteCheckbox) return false;
    return favoriteCheckbox.checked;
}