import os
from app import create_app, db
from app.models import Employee, Position
from flask_migrate import upgrade


def deploy():
    app = create_app()

    with app.app_context():
        # Создание таблиц базы данных
        db.create_all()

        # Применение миграций
        upgrade()


app = create_app(os.getenv("FLASK_CONFIG") or "default")


@app.shell_context_processor
def make_shell_context():
    """Контекст для Flask shell"""
    return {"db": db, "Employee": Employee, "Position": Position}


@app.cli.command()
def init_db():
    """Инициализация базы данных"""
    db.create_all()
    print("База данных инициализирована!")


@app.cli.command()
def seed_db():
    """Заполнение базы данных тестовыми данными"""
    from datetime import date, timedelta
    import random

    print("Начинаем создание тестовых данных...")

    # Создаем должности, если их нет
    positions_count = Position.query.count()
    print(f"Найдено должностей: {positions_count}")

    if positions_count == 0:
        positions_data = [
            ("CEO", 1),
            ("Manager", 2),
            ("Team Lead", 3),
            ("Senior Developer", 4),
            ("Developer", 5),
        ]

        for title, level in positions_data:
            position = Position(title=title, level=level)
            db.session.add(position)

        db.session.commit()
        print("Должности созданы!")

    # Создаем тестовых сотрудников, если их нет
    employees_count = Employee.query.count()
    print(f"Найдено сотрудников: {employees_count}")

    if employees_count == 0:
        names = [
            "Иванов Иван Иванович",
            "Петров Петр Петрович",
            "Сидоров Сидор Сидорович",
            "Козлов Козьма Козьмич",
            "Смирнов Смирн Смирнович",
        ]

        # Получаем должности
        ceo_position = Position.query.filter_by(level=1).first()
        manager_position = Position.query.filter_by(level=2).first()
        developer_position = Position.query.filter_by(level=5).first()

        print(f"CEO позиция: {ceo_position}")
        print(f"Manager позиция: {manager_position}")
        print(f"Developer позиция: {developer_position}")

        # Создаем CEO
        ceo = Employee(
            full_name=names[0],
            position_id=ceo_position.id,
            hire_date=date.today() - timedelta(days=365),
            salary=200000,
        )
        db.session.add(ceo)
        db.session.commit()
        print(f"CEO создан: {ceo.full_name}")

        # Создаем менеджера
        manager = Employee(
            full_name=names[1],
            position_id=manager_position.id,
            hire_date=date.today() - timedelta(days=200),
            salary=150000,
            manager_id=ceo.id,
        )
        db.session.add(manager)
        db.session.commit()
        print(f"Менеджер создан: {manager.full_name}")

        # Создаем разработчиков
        for name in names[2:]:
            employee = Employee(
                full_name=name,
                position_id=developer_position.id,
                hire_date=date.today() - timedelta(days=random.randint(30, 300)),
                salary=random.randint(80000, 120000),
                manager_id=manager.id,
            )
            db.session.add(employee)

        db.session.commit()
        print("Тестовые сотрудники созданы!")

    print("Создание тестовых данных завершено!")


if __name__ == "__main__":
    app.run(debug=True)
