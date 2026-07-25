"""Настройка системы логирования приложения.

Логирование конфигурируется через стандартный модуль `logging` с
использованием `dictConfig`. Логи одновременно пишутся в консоль
(для сбора Docker-логами) и в файл с ежедневной ротацией и хранением
последних 14 файлов.
"""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Any

from src.config.settings import AppSettings

_LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


def configure_logging(settings: AppSettings) -> None:
    """Конфигурирует логирование приложения на основе настроек.

    Создаёт директорию для логов при её отсутствии и применяет конфигурацию
    логирования: вывод в stdout и в файл `bot.log` с ежедневной ротацией.

    Args:
        settings: Объект настроек приложения, содержащий уровень логирования
            и директорию для хранения файлов логов.
    """
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": _LOG_FORMAT,
                "datefmt": _LOG_DATE_FORMAT,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": settings.log_level,
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "default",
                "level": settings.log_level,
                "filename": str(log_dir / "bot.log"),
                "when": "midnight",
                "backupCount": 14,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console", "file"],
        },
        "loggers": {
            "aiogram": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "apscheduler": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)

    logger = logging.getLogger(__name__)
    logger.info(
        "Логирование инициализировано: уровень=%s, директория=%s",
        settings.log_level,
        log_dir.resolve(),
    )
