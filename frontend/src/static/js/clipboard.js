async function pasteFromClipboard() {
    const textarea = document.getElementById('linkInput');
    const status = document.getElementById('status');

    // 使用 Clipboard API 获取剪贴板文本
    try {
        const text = await navigator.clipboard.readText();
        if (text) {
            textarea.value = '';
            textarea.value = text;
            status.textContent = '读取剪贴板内容成功！';
        }
    } catch (err) {
        status.textContent = '自动读取剪贴板失败，请手动点击粘贴按钮。';
        console.error('自动读取剪贴板失败:', err);
    }
}