function single_input() {
    // 点击按钮时获取剪贴板文本并写入输入框
    // 使用 Clipboard API 获取剪贴板文本
    navigator.clipboard.readText()
        .then(function (text) {
            // 将剪贴板文本写入输入框
            $('#linkInput').val(text);
        })
        .catch(function (error) {
            console.error('读取剪贴板失败: ', error);
        });
}