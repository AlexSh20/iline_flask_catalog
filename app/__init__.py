from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_wtf.csrf import CSRFProtect

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()


def setup_logging(app):
    """Настройка логирования"""
    if not app.debug:
        if not os.path.exists("logs"):
            os.makedirs("logs", exist_ok=True)

        file_handler = RotatingFileHandler(
            "logs/app.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("App startup")


def create_app(config_name="default"):

    app = Flask(__name__)

    # Загрузка конфигурации
    app.config.from_object(config[config_name])

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)

    # CSRF защита
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Модели для работы с миграциями
    from app import models  # noqa: F401

    # blueprints
    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    setup_logging(app)

    return app
