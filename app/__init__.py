from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config


# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name="default"):

    app = Flask(__name__)

    # Загрузка конфигурации
    app.config.from_object(config[config_name])

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)

    # Модели для работы с миграциями
    from app import models  # noqa: F401

    # blueprints
    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    return app
