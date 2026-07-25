"""Обработчик раздела «📊 Статистика»."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from src.application.services.statistics_service import StatisticsService
from src.bot.keyboards.admin.main_menu import ADMIN_MENU_STATISTICS
from src.bot.texts.admin_texts import format_admin_statistics

router = Router(name="admin_statistics")


@router.message(F.text == ADMIN_MENU_STATISTICS)
async def handle_statistics(message: Message, statistics_service: StatisticsService) -> None:
    """Показывает администратору сводную статистику по системе.

    Args:
        message: Входящее сообщение с текстом кнопки «📊 Статистика».
        statistics_service: Сервис статистики, внедряемый `ServicesMiddleware`.
    """
    stats = await statistics_service.get_dashboard_statistics()
    await message.answer(format_admin_statistics(stats))
