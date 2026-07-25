"""Инициализация планировщика APScheduler и регистрация фоновых задач."""

from __future__ import annotations

import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.bot.di.container import DIContainer
from src.config.settings import AppSettings
from src.infrastructure.scheduler.jobs.payment_due_job import check_payment_due_applications

logger = logging.getLogger(__name__)

_PAYMENT_DUE_JOB_ID = "payment_due_check"


def create_scheduler(settings: AppSettings) -> AsyncIOScheduler:
    """Создаёт асинхронный планировщик APScheduler с заданным часовым поясом.

    Args:
        settings: Полностью инициализированные настройки приложения.

    Returns:
        Экземпляр `AsyncIOScheduler`, готовый для регистрации задач и запуска.
    """
    return AsyncIOScheduler(timezone=settings.scheduler.timezone)


def register_payment_due_job(
    scheduler: AsyncIOScheduler, bot: Bot, container: DIContainer, settings: AppSettings
) -> None:
    """Регистрирует ежедневную задачу проверки заявок, готовых к выплате.

    Задача запускается ежедневно в момент времени, заданный настройками
    (`settings.scheduler.payment_check_hour` и `payment_check_minute`), в
    часовом поясе планировщика.

    Args:
        scheduler: Планировщик, в который добавляется задача.
        bot: Экземпляр `Bot`, используемый задачей для отправки уведомлений.
        container: DI-контейнер приложения, используемый задачей для
            доступа к базе данных и сервисам.
        settings: Полностью инициализированные настройки приложения.
    """
    scheduler.add_job(
        check_payment_due_applications,
        trigger=CronTrigger(
            hour=settings.scheduler.payment_check_hour,
            minute=settings.scheduler.payment_check_minute,
            timezone=settings.scheduler.timezone,
        ),
        kwargs={"bot": bot, "container": container, "admin_ids": settings.bot.admin_ids},
        id=_PAYMENT_DUE_JOB_ID,
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info(
        "Зарегистрирована ежедневная проверка выплат: %02d:%02d (%s)",
        settings.scheduler.payment_check_hour,
        settings.scheduler.payment_check_minute,
        settings.scheduler.timezone,
    )
