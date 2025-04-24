// 自动调整文本框高度
document.addEventListener('DOMContentLoaded', function() {
  const input = document.getElementById('linkInput');
  
  if (input) {
      // 初始调整
      adjustTextareaHeight(input);
      
      // 输入时调整
      input.addEventListener('input', function() {
          adjustTextareaHeight(this);
      });
  }
});

function adjustTextareaHeight(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = textarea.scrollHeight + 'px';
}