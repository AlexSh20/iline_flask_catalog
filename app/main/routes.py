from flask import render_template, request, redirect, url_for, flash, jsonify
from app.main import bp
from app.models import Employee, Position
from app import db
from sqlalchemy import desc


@bp.route("/")
def index():
    """Главная страница с общей статистикой"""
    total_employees = Employee.query.count()
    total_positions = Position.query.count()
    managers_count = len(Employee.get_managers())

    # Последние добавленные сотрудники
    recent_employees = Employee.query.order_by(Employee.id.desc()).limit(5).all()

    return render_template(
        "index.html",
        total_employees=total_employees,
        total_positions=total_positions,
        managers_count=managers_count,
        recent_employees=recent_employees,
    )


@bp.route("/employees")
def employees():
    """Страница со списком всех сотрудников"""
    page = request.args.get("page", 1, type=int)
    per_page = 10

    position_id = request.args.get("position_id", type=int)
    search_name = request.args.get("search", "")
    sort_by = request.args.get("sort_by", "")
    sort_order = request.args.get("sort_order", "asc").lower()

    query = Employee.query.join(Position)

    sort_options = {
        "full_name": Employee.full_name,
        "position_title": Position.title,
        "position_level": Position.level,
        "salary": Employee.salary,
        "hire_date": Employee.hire_date,
        "years_of_service": Employee.years_of_service,
    }

    if sort_by in sort_options:
        sort_column = sort_options[sort_by]
        if sort_order == "desc":
            sort_column = desc(sort_column)
        query = query.order_by(sort_column)
    else:
        query = query.order_by(Employee.full_name)

    if position_id:
        query = query.filter(Employee.position_id == position_id)

    if search_name:
        query = query.filter(Employee.full_name.ilike(f"%{search_name}%"))

    employees_pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    positions = Position.get_all_positions()

    return render_template(
        "employees.html",
        employees=employees_pagination.items,
        pagination=employees_pagination,
        positions=positions,
        current_position=position_id,
        current_search=search_name,
        current_sort_by=sort_by,
        current_sort_order=sort_order,
    )


@bp.route("/employee/<int:id>")
def employee_detail(id):
    """Детальная информация о сотруднике"""
    employee = Employee.query.get_or_404(id)
    return render_template("employee_detail.html", employee=employee)


@bp.route("/positions")
def positions():
    """Страница со списком должностей"""
    positions = Position.get_all_positions()
    return render_template("positions.html", positions=positions)


@bp.route("/hierarchy")
def hierarchy():
    """Страница с организационной структурой"""
    top_level_employees = Employee.get_top_level_employees()
    return render_template("hierarchy.html", top_employees=top_level_employees)


@bp.route("/add_employee", methods=["GET", "POST"])
def add_employee():
    """Добавление нового сотрудника"""
    if request.method == "POST":
        try:
            employee = Employee(
                full_name=request.form["full_name"],
                position_id=request.form["position_id"],
                salary=float(request.form["salary"]),
                hire_date=request.form["hire_date"] or None,
                manager_id=request.form["manager_id"] or None,
            )

            # Валидация
            employee.validate_manager_assignment()

            db.session.add(employee)
            db.session.commit()

            flash("Сотрудник успешно добавлен!", "success")
            return redirect(url_for("main.employees"))

        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка при добавлении сотрудника: {str(e)}", "error")

    positions = Position.get_all_positions()
    potential_managers = (
        Employee.query.join(Position).order_by(Employee.full_name).all()
    )

    return render_template(
        "add_employee.html", positions=positions, potential_managers=potential_managers
    )


@bp.route("/edit_employee/<int:id>", methods=["GET", "POST"])
def edit_employee(id):
    """Редактирование сотрудника"""
    employee = Employee.query.get_or_404(id)

    if request.method == "POST":
        try:
            employee.full_name = request.form["full_name"]
            employee.position_id = request.form["position_id"]
            employee.salary = float(request.form["salary"])
            employee.hire_date = request.form["hire_date"] or None
            employee.manager_id = request.form["manager_id"] or None

            # Валидация
            employee.validate_manager_assignment()

            db.session.commit()

            flash("Данные сотрудника успешно обновлены!", "success")
            return redirect(url_for("main.employee_detail", id=id))

        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка при обновлении данных: {str(e)}", "error")

    positions = Position.get_all_positions()
    potential_managers = (
        Employee.query.filter(Employee.id != id)
        .join(Position)
        .order_by(Employee.full_name)
        .all()
    )

    return render_template(
        "edit_employee.html",
        employee=employee,
        positions=positions,
        potential_managers=potential_managers,
    )


@bp.route("/delete_employee/<int:id>", methods=["POST"])
def delete_employee(id):
    """Удаление сотрудника"""
    employee = Employee.query.get_or_404(id)

    try:
        # Проверяем, есть ли подчиненные
        if employee.subordinates:
            flash("Нельзя удалить сотрудника, у которого есть подчиненные!", "error")
            return redirect(url_for("main.employee_detail", id=id))

        db.session.delete(employee)
        db.session.commit()

        flash("Сотрудник успешно удален!", "success")
        return redirect(url_for("main.employees"))

    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при удалении сотрудника: {str(e)}", "error")
        return redirect(url_for("main.employee_detail", id=id))


@bp.route("/change_manager/<int:employee_id>", methods=["POST"])
def change_manager(employee_id):
    """Изменение начальника сотрудника через AJAX"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        new_manager_id = request.json.get("manager_id")

        # Если manager_id пустой или None, убираем начальника
        if not new_manager_id or new_manager_id == "":
            employee.manager_id = None
            db.session.commit()
            return jsonify(
                {
                    "success": True,
                    "message": "Начальник успешно удален",
                    "manager_name": None,
                }
            )

        # Проверяем, что новый начальник существует
        new_manager = Employee.query.get(new_manager_id)
        if not new_manager:
            return jsonify(
                {"success": False, "message": "Указанный начальник не найден"}
            )

        # Проверяем, что сотрудник не назначает себя начальником
        if new_manager_id == employee_id:
            return jsonify(
                {
                    "success": False,
                    "message": "Сотрудник не может быть начальником самого себя",
                }
            )

        # Проверяем иерархию - начальник должен быть выше по уровню
        if not new_manager.can_be_manager_of(employee):
            return jsonify(
                {
                    "success": False,
                    "message": f"Сотрудник уровня {new_manager.position.level} не может быть начальником сотрудника уровня {employee.position.level}",
                }
            )

        # Проверяем на циклические зависимости
        if _would_create_cycle(employee, new_manager):
            return jsonify(
                {
                    "success": False,
                    "message": "Назначение этого начальника создаст циклическую зависимость",
                }
            )

        # Обновляем начальника
        employee.manager_id = new_manager_id
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": f"Начальник успешно изменен на {new_manager.full_name}",
                "manager_name": new_manager.full_name,
                "manager_id": new_manager.id,
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify(
            {"success": False, "message": f"Ошибка при изменении начальника: {str(e)}"}
        )


def _would_create_cycle(employee, new_manager):
    """Проверка на создание циклической зависимости"""
    current = new_manager
    visited = set()

    while current and current.manager_id:
        if current.manager_id == employee.id:
            return True
        if current.manager_id in visited:
            break
        visited.add(current.manager_id)
        current = current.manager

    return False


@bp.route("/get_potential_managers/<int:employee_id>")
def get_potential_managers(employee_id):
    """Получение списка потенциальных начальников для сотрудника"""
    try:
        employee = Employee.query.get_or_404(employee_id)

        # Получаем всех сотрудников, которые могут быть начальниками
        potential_managers = (
            Employee.query.join(Position)
            .filter(
                Employee.id != employee_id,  # Исключаем самого сотрудника
                Position.level
                < employee.position.level,  # Только вышестоящие по уровню
            )
            .order_by(Employee.full_name)
            .all()
        )

        # Фильтруем тех, кто может создать циклическую зависимость
        valid_managers = []
        for manager in potential_managers:
            if not _would_create_cycle(employee, manager):
                valid_managers.append(
                    {
                        "id": manager.id,
                        "name": manager.full_name,
                        "position": manager.position.title,
                        "level": manager.position.level,
                    }
                )

        return jsonify({"success": True, "managers": valid_managers})

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": f"Ошибка при получении списка начальников: {str(e)}",
            }
        )
