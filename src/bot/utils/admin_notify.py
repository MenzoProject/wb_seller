"""Утилита рассылки уведомлений администраторам бота.

Полноценная административная панель с интерактивными кнопками принятия
решений появится в последующих этапах (управление заявками). На данном
этапе уведомление носит информационный характер: администратор видит
новую заявку на проверке в личных сообщениях с ботом.
"""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)


async def notify_admins(
    bot: Bot, admin_ids: list[int], text: str, photo_file_id: str | None = None
) -> None:
    """Отправляет уведомление всем администраторам, указанным в настройках.

    Ошибка отправки одному конкретному администратору (например, если он
    ни разу не запускал бота или заблокировал его) логируется и не
    прерывает рассылку остальным администраторам.

    Args:
        bot: Экземпляр `Bot` для отправки сообщений.
        admin_ids: Список Telegram ID администраторов из настроек приложения.
        text: Текст уведомления (поддерживает HTML-форматирование).
        photo_file_id: Идентификатор файла фотографии в Telegram, если
            уведомление должно сопровождаться изображением (например,
            скриншотом заказа).
    """
    for admin_id in admin_ids:
        try:
            if photo_file_id is not None:
                await bot.send_photo(chat_id=admin_id, photo=photo_file_id, caption=text)
            else:
                await bot.send_message(chat_id=admin_id, text=text)
        except TelegramAPIError:
            logger.warning(
                "Не удалось отправить уведомление администратору id=%s", admin_id, exc_info=True
            )
