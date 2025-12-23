// 首页功能
document.addEventListener('DOMContentLoaded', function() {
    const noteNameInput = document.getElementById('noteName');
    const tryBtns = document.querySelectorAll('.try-btn');
    
    // 生成随机字符串
    function generateRandomName() {
        const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < 8; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }
    
    // 跳转到剪贴板页面
    function goToNote(noteName) {
        if (!noteName) {
            noteName = generateRandomName();
        }
        // 简单验证剪贴板名称
        noteName = noteName.replace(/[^a-zA-Z0-9]/g, '');
        if (noteName) {
            window.location.href = `/${noteName}/`;
        }
    }
    
    // 绑定所有查看剪贴板按钮
    tryBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const noteName = noteNameInput ? noteNameInput.value.trim() : '';
            goToNote(noteName);
        });
    });
    
    // 回车键支持
    if (noteNameInput) {
        noteNameInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                goToNote(this.value.trim());
            }
        });
    }
});