document.addEventListener('DOMContentLoaded', function () {
    // Обработка клика по заголовкам таблицы для сортировки
    const sortableHeaders = document.querySelectorAll('.sortable-header');

    sortableHeaders.forEach(header => {
        header.addEventListener('click', function () {
            const sortField = this.getAttribute('data-sort');
            const currentSortBy = '{{ current_sort_by|default("") }}';
            const currentSortOrder = '{{ current_sort_order|default("asc") }}';

            console.log('Header clicked:', sortField);
            console.log('Current sort:', currentSortBy, currentSortOrder);

            let newSortOrder = 'asc';

            // Если кликнули по тому же полю, меняем направление сортировки
            if (sortField === currentSortBy) {
                newSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
            }

            console.log('New sort:', sortField, newSortOrder);

            // Получаем текущие параметры URL
            const urlParams = new URLSearchParams(window.location.search);

            // Устанавливаем новые параметры сортировки
            urlParams.set('sort_by', sortField);
            urlParams.set('sort_order', newSortOrder);
            urlParams.delete('page'); // Сбрасываем страницу при изменении сортировки

            const newUrl = window.location.pathname + '?' + urlParams.toString();
            console.log('Redirecting to:', newUrl);

            // Переходим на новый URL
            window.location.href = newUrl;
        });
    });

    // Добавляем визуальную обратную связь при клике
    sortableHeaders.forEach(header => {
        header.addEventListener('mousedown', function () {
            this.style.backgroundColor = 'rgba(0, 0, 0, 0.2)';
        });

        header.addEventListener('mouseup', function () {
            this.style.backgroundColor = '';
        });

        header.addEventListener('mouseleave', function () {
            this.style.backgroundColor = '';
        });
    });
});


// Автодополнение для поиска сотрудников
const searchInput = document.getElementById('search');
if (searchInput) {
    searchInput.addEventListener('input', function () {
        const query = this.value;
        if (query.length < 2) {
            document.getElementById('suggestions').innerHTML = '';
            return;
        }

        fetch(`/api/search_employees?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                const suggestions = document.getElementById('suggestions');
                suggestions.innerHTML = '';
                data.forEach(emp => {
                    const div = document.createElement('div');
                    div.className = 'list-group-item list-group-item-action';
                    div.textContent = emp.name;
                    div.style.cursor = 'pointer';
                    div.onclick = () => {
                        document.getElementById('search').value = emp.name;
                        suggestions.innerHTML = '';
                    };
                    suggestions.appendChild(div);
                });
            });
    });
}

// Функционал изменения начальника
initManagerChangeFeature();

function initManagerChangeFeature() {
    // Обработчики для кнопок изменения начальника
    document.querySelectorAll('.change-manager-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const employeeId = this.getAttribute('data-employee-id');
            showManagerEdit(employeeId);
        });
    });

    // Обработчики для кнопок сохранения
    document.querySelectorAll('.save-manager-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const employeeId = this.getAttribute('data-employee-id');
            saveManagerChange(employeeId);
        });
    });

    // Обработчики для кнопок отмены
    document.querySelectorAll('.cancel-manager-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const employeeId = this.getAttribute('data-employee-id');
            hideManagerEdit(employeeId);
        });
    });
}

function showManagerEdit(employeeId) {
    const cell = document.querySelector(`[data-employee-id="${employeeId}"].manager-cell`);
    const displayDiv = cell.querySelector('.manager-display');
    const editDiv = cell.querySelector('.manager-edit');
    const select = cell.querySelector('.manager-select');

    // Скрываем отображение, показываем редактирование
    displayDiv.style.display = 'none';
    editDiv.style.display = 'block';

    // Загружаем список потенциальных начальников
    loadPotentialManagers(employeeId, select);
}

function hideManagerEdit(employeeId) {
    const cell = document.querySelector(`[data-employee-id="${employeeId}"].manager-cell`);
    const displayDiv = cell.querySelector('.manager-display');
    const editDiv = cell.querySelector('.manager-edit');

    // Показываем отображение, скрываем редактирование
    displayDiv.style.display = 'block';
    editDiv.style.display = 'none';
}

function loadPotentialManagers(employeeId, select) {
    select.innerHTML = '<option value="">Загрузка...</option>';

    fetch(`/get_potential_managers/${employeeId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                select.innerHTML = '<option value="">— Без начальника —</option>';
                data.managers.forEach(manager => {
                    const option = document.createElement('option');
                    option.value = manager.id;
                    option.textContent = `${manager.name} (${manager.position})`;
                    select.appendChild(option);
                });
            } else {
                select.innerHTML = '<option value="">Ошибка загрузки</option>';
                showNotification(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error loading managers:', error);
            select.innerHTML = '<option value="">Ошибка загрузки</option>';
            showNotification('Ошибка при загрузке списка начальников', 'error');
        });
}

function saveManagerChange(employeeId) {
    const cell = document.querySelector(`[data-employee-id="${employeeId}"].manager-cell`);
    const select = cell.querySelector('.manager-select');
    const newManagerId = select.value;

    // Показываем индикатор загрузки
    const saveBtn = cell.querySelector('.save-manager-btn');
    const originalContent = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    saveBtn.disabled = true;

    fetch(`/change_manager/${employeeId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            manager_id: newManagerId || null
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Обновляем отображение
                updateManagerDisplay(employeeId, data.manager_name, data.manager_id);
                hideManagerEdit(employeeId);
                showNotification(data.message, 'success');
            } else {
                showNotification(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error changing manager:', error);
            showNotification('Ошибка при изменении начальника', 'error');
        })
        .finally(() => {
            // Восстанавливаем кнопку
            saveBtn.innerHTML = originalContent;
            saveBtn.disabled = false;
        });
}

function updateManagerDisplay(employeeId, managerName, managerId) {
    const cell = document.querySelector(`[data-employee-id="${employeeId}"].manager-cell`);
    const displayDiv = cell.querySelector('.manager-display');
    const managerLink = displayDiv.querySelector('.manager-link');
    const noManagerSpan = displayDiv.querySelector('.text-muted');

    if (managerName && managerId) {
        // Есть начальник - используем базовый URL
        const baseUrl = window.location.origin;
        const managerUrl = `${baseUrl}/employee/${managerId}`;

        if (managerLink) {
            managerLink.textContent = managerName;
            managerLink.href = managerUrl;
        } else {
            // Создаем новую ссылку
            const newLink = document.createElement('a');
            newLink.href = managerUrl;
            newLink.className = 'text-decoration-none manager-link';
            newLink.textContent = managerName;

            if (noManagerSpan) {
                noManagerSpan.replaceWith(newLink);
            } else {
                displayDiv.insertBefore(newLink, displayDiv.querySelector('.change-manager-btn'));
            }
        }
    } else {
        // Нет начальника
        if (managerLink) {
            const noManagerSpan = document.createElement('span');
            noManagerSpan.className = 'text-muted';
            noManagerSpan.textContent = '—';
            managerLink.replaceWith(noManagerSpan);
        }
    }
}

function showNotification(message, type) {
    // Создаем уведомление
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}
