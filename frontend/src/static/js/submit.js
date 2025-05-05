// 链接处理功能
document.addEventListener('DOMContentLoaded', function() {
  const submitButton = document.getElementById('submitButton');
  
  if (submitButton) {
      submitButton.addEventListener('click', processSubmit);
  }
});

function processSubmit() {
    urls = processLink();
    score = processScoring();

    if (urls && urls.length > 0) {
        // 发送数据到后端
        fetch('/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ urls: urls, score: score >= 0 ? score : null }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Success:', data);
            alert('Link submitted successfully!');
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