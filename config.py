import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Базовая конфигурация приложения"""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # Настройки базы данных PostgreSQL
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT")

    # SQLAlchemy настройки для PostgreSQL
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Установить True для отладки SQL запросов


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""

    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Конфигурация для продакшена"""

    DEBUG = False


# Словарь конфигураций
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
