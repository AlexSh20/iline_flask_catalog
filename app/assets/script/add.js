// Автоматическая фильтрация руководителей по уровню должности
document.getElementById('position_id').addEventListener('change', function () {
    const selectedPositionId = this.value;
    const managerSelect = document.getElementById('manager_id');

    if (!selectedPositionId) {
        return;
    }

    // Получаем уровень выбранной должности
    const selectedOption = this.options[this.selectedIndex];
    const positionText = selectedOption.text;
    const levelMatch = positionText.match(/Уровень (\d+)/);

    if (levelMatch) {
        const selectedLevel = parseInt(levelMatch[1]);

        // Фильтруем руководителей
        Array.from(managerSelect.options).forEach(option => {
            if (option.value === '') return; // Пропускаем пустой вариант

            const managerText = option.text;
            const managerLevelMatch = managerText.match(/- .+ \(Уровень (\d+)\)/);

            if (managerLevelMatch) {
                const managerLevel = parseInt(managerLevelMatch[1]);
                option.style.display = managerLevel < selectedLevel ? 'block' : 'none';
            }
        });
    }
});