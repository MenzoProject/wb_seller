"""Агрегация роутеров пользовательского бота."""

from __future__ import annotations

from aiogram import Router

from src.bot.handlers.user.application_flow import router as application_flow_router
from src.bot.handlers.user.catalog import router as catalog_router
from src.bot.handlers.user.instructions import router as instructions_router
from src.bot.handlers.user.my_applications import router as my_applications_router
from src.bot.handlers.user.requisites import router as requisites_router
from src.bot.handlers.user.start import router as start_router
from src.bot.handlers.user.support import router as support_router


def get_user_router() -> Router:
    """Собирает единый роутер пользовательского бота из всех подроутеров.

    Порядок подключения важен: роутеры с обработчиками прерывания FSM по
    нажатию кнопки главного меню (`application_flow_router`,
    `requisites_router`) подключаются раньше роутеров с обычными
    обработчиками этих же кнопок, чтобы прерывание срабатывало корректно,
    когда пользователь находится в процессе многошагового ввода.

    Returns:
        Корневой `Router` пользовательского бота со всеми подключёнными
        обработчиками.
    """
    router = Router(name="user_root")
    router.include_router(start_router)
    router.include_router(application_flow_router)
    router.include_router(requisites_router)
    router.include_router(my_applications_router)
    router.include_router(catalog_router)
    router.include_router(instructions_router)
    router.include_router(support_router)
    return router
