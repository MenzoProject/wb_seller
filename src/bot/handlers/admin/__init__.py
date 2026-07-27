"""Агрегация роутеров административного бота."""

from __future__ import annotations

from aiogram import Router

from src.bot.handlers.admin.admin_start import router as admin_start_router
from src.bot.handlers.admin.applications_management import (
    router as applications_management_router,
)
from src.bot.handlers.admin.banks_management import router as banks_management_router
from src.bot.handlers.admin.payments_management import router as payments_management_router
from src.bot.handlers.admin.products_management import router as products_management_router
from src.bot.handlers.admin.statistics import router as statistics_router
from src.bot.middlewares.admin_access_middleware import AdminAccessMiddleware
from src.bot.middlewares.admin_registration_middleware import AdminRegistrationMiddleware


def get_admin_router(admin_ids: list[int]) -> Router:
    """Собирает единый роутер административного бота со всеми подроутерами.

    К корневому административному роутеру подключаются два middleware,
    действующих только в его рамках: `AdminAccessMiddleware` (отклоняет
    апдейты от пользователей, не входящих в список `admin_ids`) и
    `AdminRegistrationMiddleware` (регистрирует администратора в базе
    данных и добавляет его в контекст обработчика).

    Args:
        admin_ids: Список Telegram ID администраторов из настроек приложения.

    Returns:
        Корневой `Router` административного бота со всеми подключёнными
        обработчиками и middlewares ограничения доступа.
    """
    router = Router(name="admin_root")

    admin_access_middleware = AdminAccessMiddleware(admin_ids)
    admin_registration_middleware = AdminRegistrationMiddleware()

    router.message.outer_middleware(admin_access_middleware)
    router.callback_query.outer_middleware(admin_access_middleware)
    router.message.outer_middleware(admin_registration_middleware)
    router.callback_query.outer_middleware(admin_registration_middleware)

    router.include_router(admin_start_router)
    router.include_router(products_management_router)
    router.include_router(applications_management_router)
    router.include_router(payments_management_router)
    router.include_router(statistics_router)
    router.include_router(banks_management_router)
    return router
