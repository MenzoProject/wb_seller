"""Фоновая задача ежедневной проверки заявок, у которых наступила дата выплаты.

Открывает собственную сессию базы данных (независимую от сессий,
привязанных к обработке апдейтов Telegram), находит все заявки в статусе
WAIT_PAYMENT с наступившей расчётной датой выплаты и отправляет
администраторам единую сводку. Задача идемпотентна и безопасна для
ежедневного повторного запуска: как только администратор отмечает
заявку оплаченной, она переходит в статус PAID и больше не появляется
в выборке `list_applications_due_for_payout`.
"""

from __future__ import annotations

import logging

from aiogram import Bot

from src.bot.di.container import DIContainer
from src.bot.texts.admin_texts import PAYMENT_DUE_DIGEST_HEADER_TEXT, format_payment_due_item
from src.bot.utils.admin_notify import notify_admins
from src.domain.exceptions.base import EntityNotFoundError
from src.domain.exceptions.product_exceptions import ProductNotFoundError

logger = logging.getLogger(__name__)


async def check_payment_due_applications(
    bot: Bot, container: DIContainer, admin_ids: list[int]
) -> None:
    """Находит заявки, готовые к выплате, и отправляет администраторам сводку.

    Если ни одна заявка не готова к выплате, сводка не отправляется —
    это осознанное решение, чтобы не создавать лишний шум администраторам
    каждый день впустую.

    Args:
        bot: Экземпляр `Bot` для отправки уведомлений.
        container: DI-контейнер приложения, используемый для открытия
            независимой сессии базы данных и сборки сервисов.
        admin_ids: Список Telegram ID администраторов из настроек приложения.
    """
    logger.info("Запуск плановой проверки заявок, готовых к выплате")

    items: list[str] = []

    async with container.database.session() as session:
        services = container.build_services(session)
        due_applications = await services.application_service.list_applications_due_for_payout()

        for application in due_applications:
            assert application.id is not None

            try:
                user = await services.user_service.get_by_id(application.user_id)
                user_label = user.full_name
            except EntityNotFoundError:
                user_label = f"пользователь #{application.user_id}"

            try:
                product = await services.product_service.get_product(application.product_id)
                product_title = product.title
            except ProductNotFoundError:
                product_title = f"товар #{application.product_id}"

            try:
                payment = await services.payment_service.get_payment_by_application(
                    application.id
                )
                amount = str(payment.amount)
            except EntityNotFoundError:
                logger.warning(
                    "Для заявки id=%s в статусе WAIT_PAYMENT не найдена запись о выплате",
                    application.id,
                )
                amount = "—"

            due_date_text = (
                application.payout_due_date.strftime("%d.%m.%Y")
                if application.payout_due_date is not None
                else "—"
            )

            items.append(
                format_payment_due_item(
                    application.id, user_label, product_title, amount, due_date_text
                )
            )

    if not items:
        logger.info("Заявок, готовых к выплате, не найдено")
        return

    logger.info("Найдено %s заявок, готовых к выплате", len(items))
    digest_text = f"{PAYMENT_DUE_DIGEST_HEADER_TEXT}\n\n" + "\n".join(items)
    await notify_admins(bot, admin_ids, digest_text)
