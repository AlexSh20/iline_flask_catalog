document.addEventListener('DOMContentLoaded', function () {
    // Обработчики для кнопок развернуть/свернуть все
    document.getElementById('expandAll').addEventListener('click', function () {
        document.querySelectorAll('.subordinates-container').forEach(function (el) {
            el.classList.add('show');
        });
        document.querySelectorAll('.toggle-btn').forEach(function (btn) {
            btn.setAttribute('aria-expanded', 'true');
        });
    });

    document.getElementById('collapseAll').addEventListener('click', function () {
        document.querySelectorAll('.subordinates-container').forEach(function (el) {
            el.classList.remove('show');
        });
        document.querySelectorAll('.toggle-btn').forEach(function (btn) {
            btn.setAttribute('aria-expanded', 'false');
        });
    });

    // Обработчик для кнопок переключения
    document.querySelectorAll('.toggle-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', !isExpanded);
        });
    });
});