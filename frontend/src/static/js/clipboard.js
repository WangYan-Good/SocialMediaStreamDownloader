// 复制到剪贴板
document.addEventListener('DOMContentLoaded', function () {
    // 绑定按钮点击事件
    const pasteButton = document.getElementById('pasteButton');
    const textarea = document.getElementById('linkInput');
    const status = document.getElementById('status');

    if (pasteButton) {
        pasteButton.addEventListener('click', async function () {
            // 使用 Clipboard API 获取剪贴板文本
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    textarea.value = '';
                    textarea.value = text;
                    status.textContent = '读取剪贴板内容成功！'
                }
            } catch (err) {
                // alert("自动读取剪贴板失败，请手动点击粘贴按钮。");
                status.textContent = '自动读取剪贴板失败，请手动点击粘贴按钮。';
                console.log('自动读取剪贴板失败:', err);
            }
        });
    }
});