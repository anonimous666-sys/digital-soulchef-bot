Денис Слепцов:
"""
Конфигурационные настройки приложения
Использует pydantic для валидации переменных окружения
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional, Dict, Any
import os
from pathlib import Path

# Путь к корневой директории проекта
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """Настройки приложения"""
    
    # ==================== TELEGRAM ====================
    bot_token: str = Field(..., env="BOT_TOKEN")
    admin_ids: List[int] = Field(default=[], env="ADMIN_IDS")
    bot_mode: str = Field(default="POLLING", env="BOT_MODE")
    webhook_url: Optional[str] = Field(None, env="WEBHOOK_URL")
    webhook_path: str = Field("/webhook", env="WEBHOOK_PATH")
    
    # ==================== DATABASE ====================
    database_url: str = Field(..., env="DATABASE_URL")
    db_host: str = Field(..., env="DB_HOST")
    db_port: int = Field(5432, env="DB_PORT")
    db_name: str = Field(..., env="DB_NAME")
    db_user: str = Field(..., env="DB_USER")
    db_password: str = Field(..., env="DB_PASSWORD")
    
    # ==================== REDIS ====================
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_db: int = Field(0, env="REDIS_DB")
    
    # ==================== YANDEX CLOUD ====================
    yc_folder_id: Optional[str] = Field(None, env="YC_FOLDER_ID")
    yc_service_account_id: Optional[str] = Field(None, env="YC_SERVICE_ACCOUNT_ID")
    yc_key_id: Optional[str] = Field(None, env="YC_KEY_ID")
    yc_private_key: Optional[str] = Field(None, env="YC_PRIVATE_KEY")
    
    # Object Storage
    yc_object_storage_bucket: Optional[str] = Field(None, env="YC_OBJECT_STORAGE_BUCKET")
    yc_access_key_id: Optional[str] = Field(None, env="YC_ACCESS_KEY_ID")
    yc_secret_access_key: Optional[str] = Field(None, env="YC_SECRET_ACCESS_KEY")
    
    # ==================== APPLICATION ====================
    app_name: str = Field("Цифровой Су-Шеф", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    timezone: str = Field("Europe/Moscow", env="TIMEZONE")
    app_env: str = Field("production", env="APP_ENV")
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # Пути к файлам
    logs_dir: Path = Field(BASE_DIR / "logs", env="LOGS_DIR")
    static_dir: Path = Field(BASE_DIR / "static", env="STATIC_DIR")
    qr_codes_dir: Path = Field(BASE_DIR / "static" / "qr_codes", env="QR_CODES_DIR")
    
    # ==================== HACCP SETTINGS ====================
    akp_deviation_limit: float = Field(0.05, env="AKP_DEVIATION_LIMIT")
    temperature_min: float = Field(2.0, env="TEMPERATURE_MIN")
    temperature_max: float = Field(4.0, env="TEMPERATURE_MAX")
    shelf_life_warning_days: int = Field(3, env="SHELF_LIFE_WARNING_DAYS")
    
    # ==================== BUSINESS SETTINGS ====================
    default_currency: str = Field("RUB", env="DEFAULT_CURRENCY")
    default_unit: str = Field("кг", env="DEFAULT_UNIT")
    work_start_time: str = Field("09:00", env="WORK_START_TIME")
    work_end_time: str = Field("22:00", env="WORK_END_TIME")
    
    @validator("admin_ids", pre=True)
    def parse_admin_ids(cls, value):
        """Парсинг списка ID администраторов"""
        if isinstance(value, str):
            if value.strip():
                return [int(id.strip()) for id in value.split(",") if id.strip()]
            return []
        return value
    
    @validator("logs_dir", "static_dir", "qr_codes_dir", pre=True)
    def create_directories(cls, value):
        """Создание директорий при инициализации"""
        path = Path(value)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def redis_url(self) -> str:
        """URL для подключения к Redis"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.

redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def database_url_async(self) -> str:
        """Async URL для SQLAlchemy"""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    @property
    def is_development(self) -> bool:
        """Проверка, что это режим разработки"""
        return self.app_env.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Проверка, что это режим продакшена"""
        return self.app_env.lower() == "production"
    
    def get_log_config(self) -> Dict[str, Any]:
        """Конфигурация логирования"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "detailed": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.log_level,
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": self.log_level,
                    "formatter": "detailed",
                    "filename": self.logs_dir / "bot.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 10,
                    "encoding": "utf8"
                }
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": self.log_level,
                    "propagate": True
                }
            }
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Создаём глобальный экземпляр настроек
settings = Settings()
