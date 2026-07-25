"""Конфигурация приложения на основе Pydantic Settings.

Все настройки читаются из переменных окружения (и файла .env при локальном
запуске). Настройки сгруппированы по логическим блокам (бот, база данных,
Redis, планировщик, общие параметры приложения) и объединены в единый
объект `AppSettings`, который является единственной точкой доступа
к конфигурации во всём проекте.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Final

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent

_ENV_FILE: Final[Path] = BASE_DIR / ".env"


class BotSettings(BaseSettings):
    """Настройки, относящиеся непосредственно к Telegram-боту."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        env_prefix="BOT_",
        extra="ignore",
    )

    token: str = Field(..., description="Токен Telegram-бота, выданный BotFather")
    parse_mode: str = Field(
        default="HTML", description="Режим разбора текста сообщений по умолчанию"
    )
    admin_ids: list[int] = Field(
        default_factory=list,
        description="Список Telegram ID администраторов, имеющих доступ к админ-панели",
    )
    support_username: str = Field(
        default="support",
        description="Username менеджера поддержки, отображаемый пользователю без символа @",
    )
    drop_pending_updates: bool = Field(
        default=True,
        description="Сбрасывать ли накопленные апдейты при старте бота",
    )

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: object) -> list[int]:
        """Преобразует строку из переменной окружения вида '123,456' в список int.

        Args:
            value: Исходное значение переменной окружения — строка с ID через
                запятую, либо уже готовый список целых чисел.

        Returns:
            Список Telegram ID администраторов в виде целых чисел.

        Raises:
            ValueError: Если один из элементов строки не может быть
                преобразован в целое число.
        """
        if isinstance(value, list):
            return [int(item) for item in value]
        if isinstance(value, str):
            if not value.strip():
                return []
            try:
                return [int(item.strip()) for item in value.split(",") if item.strip()]
            except ValueError as error:
                raise ValueError(
                    f"Некорректный формат BOT_ADMIN_IDS: '{value}'. "
                    "Ожидается список ID через запятую, например '123456789,987654321'."
                ) from error
        raise ValueError(f"Неподдерживаемый тип значения для admin_ids: {type(value)!r}")


class DatabaseSettings(BaseSettings):
    """Настройки подключения к PostgreSQL."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        env_prefix="POSTGRES_",
        extra="ignore",
    )

    host: str = Field(default="postgres", description="Хост PostgreSQL")
    port: int = Field(default=5432, description="Порт PostgreSQL")
    user: str = Field(..., description="Пользователь базы данных")
    password: str = Field(..., description="Пароль пользователя базы данных")
    db: str = Field(..., description="Имя базы данных")
    echo: bool = Field(default=False, description="Логировать ли SQL-запросы SQLAlchemy")
    pool_size: int = Field(default=10, ge=1, description="Размер пула соединений SQLAlchemy")
    max_overflow: int = Field(
        default=20, ge=0, description="Максимальное число дополнительных соединений сверх pool_size"
    )

    @property
    def dsn(self) -> str:
        """Возвращает асинхронную строку подключения (DSN) для asyncpg.

        Returns:
            Строка подключения формата postgresql+asyncpg://...
        """
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class RedisSettings(BaseSettings):
    """Настройки подключения к Redis (используется для хранения FSM-состояний)."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        env_prefix="REDIS_",
        extra="ignore",
    )

    host: str = Field(default="redis", description="Хост Redis")
    port: int = Field(default=6379, description="Порт Redis")
    db: int = Field(default=0, description="Номер базы данных Redis")
    password: str | None = Field(default=None, description="Пароль Redis, если требуется")
    fsm_ttl_seconds: int = Field(
        default=86_400,
        description="TTL записей FSM-состояний в секундах",
    )

    @property
    def dsn(self) -> str:
        """Возвращает строку подключения к Redis.

        Returns:
            Строка подключения формата redis://[:password@]host:port/db
        """
        auth_part = f":{self.password}@" if self.password else ""
        return f"redis://{auth_part}{self.host}:{self.port}/{self.db}"


class SchedulerSettings(BaseSettings):
    """Настройки фонового планировщика APScheduler."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        env_prefix="SCHEDULER_",
        extra="ignore",
    )

    timezone: str = Field(default="Europe/Moscow", description="Часовой пояс планировщика")
    payment_check_hour: int = Field(
        default=10, ge=0, le=23, description="Час ежедневного запуска проверки выплат"
    )
    payment_check_minute: int = Field(
        default=0, ge=0, le=59, description="Минута ежедневного запуска проверки выплат"
    )


class AppSettings(BaseSettings):
    """Общие настройки приложения, не относящиеся к конкретному модулю."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(
        default="development", description="Окружение запуска: development/production"
    )
    app_name: str = Field(default="wb-ozon-reseller-bot", description="Имя приложения для логов")
    log_level: str = Field(default="INFO", description="Уровень логирования")
    log_dir: str = Field(default="./logs", description="Директория для файлов логов")
    timezone: str = Field(
        default="Europe/Moscow", description="Часовой пояс приложения по умолчанию"
    )

    bot: BotSettings = Field(default_factory=BotSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)

    @property
    def is_production(self) -> bool:
        """Признак того, что приложение запущено в production-окружении.

        Returns:
            True, если APP_ENV равен 'production', иначе False.
        """
        return self.app_env.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Возвращает закэшированный синглтон настроек приложения.

    Использование lru_cache гарантирует, что переменные окружения
    считываются один раз за время жизни процесса и настройки переиспользуются
    во всех модулях без повторного парсинга.

    Returns:
        Полностью инициализированный объект AppSettings.
    """
    return AppSettings()
