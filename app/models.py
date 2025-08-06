from datetime import datetime, date
from app import db
from sqlalchemy import CheckConstraint
from typing import List, Optional


class Position(db.Model):
    """Должность сотрудника"""

    __tablename__ = "positions"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=True)
    level = db.Column(db.Integer, nullable=False)

    # Связь с сотрудниками (один ко многим)
    employees = db.relationship("Employee", backref="position", lazy="dynamic")

    # Ограничения
    __table_args__ = (
        CheckConstraint("level >= 1 AND level <= 5", name="valid_level"),
        db.UniqueConstraint("title", name="unique_position_title"),
    )

    def __repr__(self) -> str:
        return f"<Position {self.title} (Level {self.level})>"

    def to_dict(self) -> dict:
        """Преобразование объекта в словарь для JSON"""
        return {
            "id": self.id,
            "title": self.title,
            "level": self.level,
            "employees_count": self.employees.count(),
        }

    @staticmethod
    def get_all_positions() -> List["Position"]:
        """Получить все должности, отсортированные по уровню"""
        return Position.query.order_by(Position.level).all()

    @staticmethod
    def get_by_level(level: int) -> List["Position"]:
        """Получить должности по уровню"""
        return Position.query.filter_by(level=level).all()


class Employee(db.Model):
    """Cотрудник"""

    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey("positions.id"), nullable=False)
    hire_date = db.Column(db.Date, nullable=False, default=date.today)
    salary = db.Column(db.Numeric(10, 2), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)

    # Связь для иерархии сотрудников
    manager = db.relationship("Employee", remote_side=[id], backref="subordinates")

    # Ограничения
    __table_args__ = (
        CheckConstraint("salary > 0", name="salary_positive"),
        db.ForeignKeyConstraint(["position_id"], ["positions.id"], name="fk_position"),
        db.ForeignKeyConstraint(["manager_id"], ["employees.id"], name="fk_manager"),
    )

    def __repr__(self) -> str:
        return f'<Employee {self.full_name} ({self.position.title if self.position else "No Position"})>'

    def to_dict(self, include_subordinates: bool = False) -> dict:
        """Преобразование объекта в словарь для JSON"""
        result = {
            "id": self.id,
            "full_name": self.full_name,
            "position_id": self.position_id,
            "position_title": self.position.title if self.position else None,
            "position_level": self.position.level if self.position else None,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "salary": float(self.salary) if self.salary else None,
            "manager_id": self.manager_id,
            "manager_name": self.manager.full_name if self.manager else None,
        }

        if include_subordinates:
            result["subordinates"] = [sub.to_dict() for sub in self.subordinates]
            result["subordinates_count"] = len(self.subordinates)

        return result

    @property
    def years_of_service(self) -> int:
        """Количество лет работы в компании"""
        if self.hire_date:
            return (date.today() - self.hire_date).days // 365
        return 0

    @property
    def is_manager(self) -> bool:
        """Проверка, является ли сотрудник руководителем"""
        return len(self.subordinates) > 0

    def can_be_manager_of(self, employee: "Employee") -> bool:
        """Проверка, может ли данный сотрудник быть руководителем другого сотрудника"""
        if not self.position or not employee.position:
            return False
        return self.position.level < employee.position.level

    @staticmethod
    def get_all_employees() -> List["Employee"]:
        """Получить всех сотрудников с их должностями"""
        return Employee.query.join(Position).order_by(Employee.full_name).all()

    @staticmethod
    def get_by_position(position_id: int) -> List["Employee"]:
        """Получить сотрудников по должности"""
        return Employee.query.filter_by(position_id=position_id).all()

    @staticmethod
    def get_by_manager(manager_id: int) -> List["Employee"]:
        """Получить подчиненных конкретного руководителя"""
        return Employee.query.filter_by(manager_id=manager_id).all()

    @staticmethod
    def get_managers() -> List["Employee"]:
        """Получить всех руководителей (у которых есть подчиненные)"""
        return Employee.query.filter(Employee.subordinates.any()).all()

    @staticmethod
    def get_top_level_employees() -> List["Employee"]:
        """Получить сотрудников верхнего уровня (без руководителей)"""
        return Employee.query.filter_by(manager_id=None).all()

    @staticmethod
    def search_by_name(name: str) -> List["Employee"]:
        """Поиск сотрудников по имени"""
        return Employee.query.filter(Employee.full_name.ilike(f"%{name}%")).all()

    @staticmethod
    def get_salary_range(
        min_salary: float = None, max_salary: float = None
    ) -> List["Employee"]:
        """Получить сотрудников в диапазоне зарплат"""
        query = Employee.query
        if min_salary is not None:
            query = query.filter(Employee.salary >= min_salary)
        if max_salary is not None:
            query = query.filter(Employee.salary <= max_salary)
        return query.order_by(Employee.salary.desc()).all()

    def get_all_subordinates(self) -> List["Employee"]:
        """Получить всех подчиненных рекурсивно"""
        all_subordinates = []
        for subordinate in self.subordinates:
            all_subordinates.append(subordinate)
            all_subordinates.extend(subordinate.get_all_subordinates())
        return all_subordinates

    def validate_manager_assignment(self) -> bool:
        """Валидация назначения руководителя"""
        if self.manager_id is None:
            return True

        if self.manager_id == self.id:
            raise ValueError("Сотрудник не может быть руководителем самого себя")

        if self.manager and not self.manager.can_be_manager_of(self):
            raise ValueError(
                f"Сотрудник с уровнем {self.manager.position.level} "
                f"не может быть руководителем сотрудника с уровнем {self.position.level}"
            )

        return True
