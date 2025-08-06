// Автоматическая фильтрация руководителей по уровню должности
document.getElementById('position_id').addEventListener('change', function () {
    const selectedPositionId = this.value;
    const managerSelect = document.getElementById('manager_id');
    const currentManagerId = {{ employee.manager_id | tojson if employee.manager_id else 'null'
}};

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
            const shouldShow = managerLevel < selectedLevel;
            option.style.display = shouldShow ? 'block' : 'none';

            // Если текущий руководитель стал недоступен, сбрасываем выбор
            if (!shouldShow && option.value == currentManagerId) {
                managerSelect.value = '';
            }
        }
    });
}
});

// Предупреждение при изменении должности, если есть подчиненные
{% if employee.subordinates %}
document.getElementById('position_id').addEventListener('change', function () {
    const originalPositionId = {{ employee.position_id | tojson
}};
if (this.value != originalPositionId) {
    let warning = document.getElementById('hierarchy-warning');
    if (!warning) {
        const alertDiv = document.createElement('div');
        alertDiv.id = 'hierarchy-warning';
        alertDiv.className = 'alert alert-warning mt-2';
        alertDiv.textContent = 'Внимание: у сотрудника есть подчиненные. Изменение должности может повлиять на иерархию.';
        const positionField = document.getElementById('position_id');
        positionField.parentNode.insertBefore(alertDiv, positionField.nextSibling);
    }
} else {
    const warning = document.getElementById('hierarchy-warning');
    if (warning) {
        warning.remove();
    }
}
});
{% endif %}