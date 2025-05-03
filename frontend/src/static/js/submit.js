// 链接处理功能
document.addEventListener('DOMContentLoaded', function() {
  const submitButton = document.getElementById('submitButton');
  
  if (submitButton) {
      submitButton.addEventListener('click', processLink);
  }
});

function processLink() {
  // 获取输入框中的链接
  const linkInput = document.getElementById('linkInput');
  if (!linkInput) return;
  
  const link = linkInput.value.trim();

  // 使用正则表达式解析链接
  const urlRegex = /https?:\/\/[^\s]+/g;
  const matches = link.match(urlRegex);

  if (matches && matches.length > 0) {
      // 如果有匹配的链接，发送到后端处理
      fetch('/', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify({ urls: matches }),
      })
      .then(response => {
          if (!response.ok) {
              throw new Error('Network response was not ok');
          }
          return response.json();
      })
      .then(data => {
          console.log('Success:', data);
          alert('Links processed successfully!');
      })
      .catch((error) => {
          console.error('Error:', error);
          alert('Error processing links: ' + error.message);
      });
  } else {
      alert('No valid links found! Please enter at least one valid URL starting with http:// or https://');
  }
}