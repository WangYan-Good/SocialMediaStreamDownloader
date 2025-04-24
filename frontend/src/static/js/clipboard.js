// 剪贴板功能
document.addEventListener('DOMContentLoaded', function() {
  const pasteButton = document.getElementById('pasteButton');
  const status = document.getElementById('status');
  const linkInput = document.getElementById('linkInput');

  pasteButton.addEventListener('click', async () => {
    try {
        // 请求剪贴板读取权限
        const permission = await navigator.permissions.query({
            name: 'clipboard-read'
        });
        
        if (permission.state === 'denied') {
            status.textContent = '剪贴板访问权限被拒绝';
            return;
        }
        
        // 读取剪贴板内容
        const clipboardItems = await navigator.clipboard.read();
        for (const clipboardItem of clipboardItems) {
            for (const type of clipboardItem.types) {
                if (type === 'text/plain') {
                    const blob = await clipboardItem.getType(type);
                    const text = await blob.text();
                    linkInput.value = text;
                    status.textContent = '剪贴板内容已成功读取';
                    return;
                }
            }
        }
        status.textContent = '剪贴板中没有文本内容';
      } catch (error) {
          console.error('读取剪贴板失败:', error);
          status.textContent = '读取剪贴板失败: ' + error.message;
          
          // 如果新API不可用，尝试使用旧的execCommand方法
          try {
              linkInput.focus();
              const success = document.execCommand('paste');
              if (success) {
                  status.textContent = '剪贴板内容已读取(旧方法)';
              } else {
                  status.textContent = '无法读取剪贴板内容';
              }
          } catch (oldError) {
              status.textContent = '无法读取剪贴板内容: ' + oldError.message;
          }
    }
  });
});

// document.addEventListener('DOMContentLoaded', function() {
//   const pasteButton = document.getElementById('pasteButton');
//   const status = document.getElementById('status');
//   const linkInput = document.getElementById('linkInput');
// });

// document.getElementById('pasteButton').addEventListener('click', async () => {
//   const textarea = document.getElementById('contentBox');
//   const status = document.getElementById('status');
  
//   try {
//       // 请求剪贴板读取权限
//       const permission = await navigator.permissions.query({
//           name: 'clipboard-read'
//       });
      
//       if (permission.state === 'denied') {
//           status.textContent = '剪贴板访问权限被拒绝';
//           return;
//       }
      
//       // 读取剪贴板内容
//       const clipboardItems = await navigator.clipboard.read();
//       for (const clipboardItem of clipboardItems) {
//           for (const type of clipboardItem.types) {
//               if (type === 'text/plain') {
//                   const blob = await clipboardItem.getType(type);
//                   const text = await blob.text();
//                   textarea.value = text;
//                   status.textContent = '剪贴板内容已成功读取';
//                   return;
//               }
//           }
//       }
//       status.textContent = '剪贴板中没有文本内容';
//   } catch (error) {
//       console.error('读取剪贴板失败:', error);
//       status.textContent = '读取剪贴板失败: ' + error.message;
      
//       // 如果新API不可用，尝试使用旧的execCommand方法
//       try {
//           textarea.focus();
//           const success = document.execCommand('paste');
//           if (success) {
//               status.textContent = '剪贴板内容已读取(旧方法)';
//           } else {
//               status.textContent = '无法读取剪贴板内容';
//           }
//       } catch (oldError) {
//           status.textContent = '无法读取剪贴板内容: ' + oldError.message;
//       }
//   }
// });