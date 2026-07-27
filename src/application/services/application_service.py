"""Сервис бизнес-логики жизненного цикла заявки на выкуп товара.

Это центральный сервис системы: он оркестрирует переходы статусов заявки
(реализованные в доменной сущности `Application`), согласованно обновляет
связанные агрегаты (резервирование/освобождение слотов товара, создание
записи о выплате) и ведёт журнал аудита ключевых событий.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.application_dto import (
    ApproveOrderDTO,
    AssignRequisitesDTO,
    CancelApplicationDTO,
    ConfirmReceiveDTO,
    CreateApplicationDTO,
    RejectApplicationDTO,
    RequestOrderScreenshotResendDTO,
    SubmitArticleDTO,
    SubmitOrderScreenshotDTO,
    SubmitReceiptLinkDTO,
    SubmitReviewScreenshotDTO,
)
from src.domain.entities.application import Application
from src.domain.entities.log import Log
from src.domain.entities.payment import Payment
from src.domain.enums.application_status import ApplicationStatus
from src.domain.exceptions.application_exceptions import (
    ApplicationAlreadyActiveError,
    ApplicationNotFoundError,
)
from src.domain.exceptions.product_exceptions import ProductNotFoundError
from src.domain.exceptions.requisites_exceptions import RequisitesNotFoundError
from src.infrastructure.repositories.interfaces.application_repository import (
    ApplicationRepository,
)
from src.infrastructure.repositories.interfaces.log_repository import LogRepository
from src.infrastructure.repositories.interfaces.payment_repository import PaymentRepository
from src.infrastructure.repositories.interfaces.product_repository import ProductRepository
from src.infrastructure.repositories.interfaces.requisites_repository import (
    RequisitesRepository,
)

logger = logging.getLogger(__name__)


class ApplicationService:
    """Сервис, инкапсулирующий бизнес-логику жизненного цикла заявок."""

    def __init__(
        self,
        application_repository: ApplicationRepository,
        product_repository: ProductRepository,
        payment_repository: PaymentRepository,
        requisites_repository: RequisitesRepository,
        log_repository: LogRepository,
        session: AsyncSession,
    ) -> None:
        """Инициализирует сервис необходимыми репозиториями.

        Args:
            application_repository: Реализация репозитория заявок.
            product_repository: Реализация репозитория товаров (для проверки
                доступности товара и параметров кэшбэка).
            payment_repository: Реализация репозитория выплат (для создания
                записи о выплате при переходе заявки в ожидание оплаты).
            requisites_repository: Реализация репозитория реквизитов (для
                проверки принадлежности реквизитов пользователю).
            log_repository: Реализация репозитория журнала аудита.
            session: Асинхронная сессия SQLAlchemy, разделяемая всеми
                репозиториями этого сервиса в рамках текущей единицы работы
                (обрабатываемого апдейта Telegram). Используется напрямую
                только для явного управления атомарностью многошаговых
                операций через `_atomic` (см. `create_application`).
        """
        self._application_repository = application_repository
        self._product_repository = product_repository
        self._payment_repository = payment_repository
        self._requisites_repository = requisites_repository
        self._log_repository = log_repository
        self._session = session

    @asynccontextmanager
    async def _atomic(self) -> AsyncIterator[None]:
        """Открывает вложенную транзакцию (SAVEPOINT) для группы связанных операций.

        Многошаговые операции этого сервиса (например, резервирование слота
        товара и последующее создание заявки в `create_application`) должны
        либо применяться полностью, либо не применяться вовсе. Внешняя
        сессия БД фиксируется (`commit`) только по завершении обработки
        всего апдейта Telegram в `DbSessionMiddleware`, поэтому её отдельный
        rollback здесь недоступен без потери прогресса всей транзакции.

        `session.begin_nested()` открывает SAVEPOINT: если исключение
        возникает внутри блока `async with`, откатываются только изменения,
        сделанные с момента открытия SAVEPOINT (например, уже выполненное
        уменьшение `available_slots` товара), после чего исключение
        пробрасывается дальше без изменений во внешней транзакции. Это
        гарантирует атомарность создания заявки независимо от того, как
        именно вызывающий код (обработчик бота) обработает исключение —
        даже если обработчик перехватит его и не пробросит выше, частично
        применённые изменения уже будут отменены на уровне SAVEPOINT.

        Yields:
            None. Используется исключительно как менеджер контекста.
        """
        async with self._session.begin_nested():
            yield

    async def get_application(self, application_id: int) -> Application:
        """Возвращает заявку по внутреннему идентификатору.

        Args:
            application_id: Внутренний идентификатор заявки.

        Returns:
            Найденная доменная сущность заявки.

        Raises:
            ApplicationNotFoundError: Если заявка с указанным `id` не найдена.
        """
        application = await self._application_repository.get_by_id(application_id)
        if application is None:
            raise ApplicationNotFoundError(application_id)
        return application

    async def _finalize_wait_payment_if_reached(self, application: Application) -> None:
        """Довычисляет дату выплаты и создаёт запись о выплате при входе в WAIT_PAYMENT.

        Метод вызывается после каждого перехода статуса заявки, который
        потенциально может привести её в статус WAIT_PAYMENT (ожидание
        выплаты может наступить тремя разными путями в зависимости от
        того, требуются ли для товара отзыв и чек). Если заявка
        действительно достигла WAIT_PAYMENT, вычисляется расчётная дата
        выплаты и создаётся связанная запись `Payment` в статусе PENDING.

        Args:
            application: Заявка, для которой требуется проверить достижение
                статуса WAIT_PAYMENT.
        """
        if application.status != ApplicationStatus.WAIT_PAYMENT:
            return

        product = await self._product_repository.get_by_id(application.product_id)
        if product is None:
            logger.error(
                "Товар id=%s для заявки id=%s не найден при расчёте даты выплаты",
                application.product_id,
                application.id,
            )
            return

        application.calculate_payout_due_date(product.payout_days)

        existing_payment = await self._payment_repository.get_by_application_id(
            application.id if application.id is not None else 0
        )
        if existing_payment is None:
            await self._payment_repository.create(
                Payment(
                    id=None,
                    application_id=application.id if application.id is not None else 0,
                    amount=product.cashback_amount,
                )
            )
            logger.info(
                "Создана выплата PENDING для заявки id=%s на сумму %s",
                application.id,
                product.cashback_amount,
            )

    async def create_application(self, dto: CreateApplicationDTO) -> Application:
        """Создаёт новую заявку на выкуп товара, резервируя слот товара.

        Раздел резервирования слота товара и создания заявки выполняется в
        рамках вложенной транзакции (`_atomic`, SAVEPOINT): если создание
        заявки завершится ошибкой на любом шаге, уже уменьшённое количество
        доступных слотов товара будет откачено, и остаток товара не
        изменится — частичное применение изменений невозможно.

        Args:
            dto: Данные для создания заявки (пользователь и товар).

        Returns:
            Созданная доменная сущность заявки в статусе NEW.

        Raises:
            ProductNotFoundError: Если товар с указанным `id` не найден.
            ProductUnavailableError: Если товар скрыт или удалён из каталога.
            ProductOutOfStockError: Если у товара закончились доступные слоты.
            ApplicationAlreadyActiveError: Если у пользователя уже есть
                незавершённая заявка на этот же товар.
        """
        active_application = await self._application_repository.get_active_application(
            dto.user_id, dto.product_id
        )
        if active_application is not None:
            raise ApplicationAlreadyActiveError(dto.user_id, dto.product_id)

        async with self._atomic():
            product = await self._product_repository.get_by_id(dto.product_id)
            if product is None:
                raise ProductNotFoundError(dto.product_id)

            product.reserve_slot()
            await self._product_repository.update(product)

            application = Application(
                id=None,
                user_id=dto.user_id,
                product_id=dto.product_id,
                status=ApplicationStatus.NEW,
            )
            created_application = await self._application_repository.create(application)

            await self._log_repository.create(
                Log(
                    id=None,
                    action="application_created",
                    entity_type="Application",
                    user_id=dto.user_id,
                    entity_id=created_application.id,
                    payload={"product_id": dto.product_id},
                )
            )

        logger.info(
            "Создана заявка id=%s пользователем id=%s на товар id=%s",
            created_application.id,
            dto.user_id,
            dto.product_id,
        )
        return created_application

    async def submit_article(self, dto: SubmitArticleDTO) -> Application:
        """Фиксирует артикул товара, отправленный пользователем.

        Args:
            dto: Идентификатор заявки и артикул товара.

        Returns:
            Обновлённая доменная сущность заявки в статусе WAIT_ORDER_SCREEN.

        Raises:
            ApplicationNotFoundError: Если заявка не найдена.
            InvalidApplicationTransitionError: Если заявка не в статусе NEW.
        """
        application = await self.get_application(dto.application_id)
        application.submit_article(dto.article)
        return await self._application_repository.update(application)

    async def submit_order_screenshot(self, dto: SubmitOrderScreenshotDTO) -> Application:
        """Фиксирует скриншот заказа и переводит заявку на проверку администратору.

        Args:
            dto: Идентификатор заявки и file_id скриншота заказа.

        Returns:
            Обновлённая доменная сущность заявки в статусе ORDER_ON_REVIEW.

        Raises:
            ApplicationNotFoundError: Если заявка не найдена.
            InvalidApplicationTransitionError: Если заявка не в статусе WAIT_ORDER_SCREEN.
        """
        application = await self.get_application(dto.application_id)

        async with self._atomic():
            application.submit_order_screenshot(dto.file_id)
            updated_application = await self._application_repository.update(application)

            await self._log_repository.create(
                Log(
                    id=None,
                    action="order_screenshot_submitted",
                    entity_type="Application",
                    user_id=application.user_id,
                    entity_id=application.id,
                )
            )
        return updated_application

    async def approve_order(self, dto: ApproveOrderDTO) -> Application:
        """Подтверждает заказ администратором.

        Заявка переводится сразу в статус WAIT_RECEIVE (минуя промежуточный
        статус ORDER_APPROVED, который используется как внутренний шаг
        перехода в доменной сущности).

        Args:
            dto: Идентификатор заявки и идентификатор администратора.

        Returns:
            Обновлённая доменная сущность заявки в статусе WAIT_RECEIVE.

        Raises:
            ApplicationNotFoundError: Если заявка не найдена.
            InvalidApplicationTransitionError: Если заявка не в статусе ORDER_ON_REVIEW.
        """
        application = await self.get_application(dto.application_id)

        async with self._atomic():
            application.approve_order()
            updated_application = await self._application_repository.update(application)

            await self._log_repository.create(
                Log(
                    id=None,
                    action="order_approved",
                    entity_type="Application",
                    admin_id=dto.admin_id,
                    entity_id=application.id,
                )
            )
        return updated_application

    async def request_order_screenshot_resend(
        self, dto: RequestOrderScreenshotResendDTO
    ) -> Application:
        """Запрашивает у пользователя повторную отправку скриншота заказа.

        Args:
            dto: Идентификатор заявки, идентификатор администратора и причина.

        Returns:
            Обновлённая доменная сущность заявки в статусе WAIT_ORDER_SCREEN.

        Raises:
            ApplicationNotFoundError: Если заявка не найдена.
            InvalidApplicationTransitionError: Если заявка не в статусе ORDER_ON_REVIEW.
        """
        application = await self.get_application(dto.application_id)

        async with self._atomic():
            application.request_order_screenshot_resend(dto.reason)
            updated_application = await self._application_repository.update(application)

            await self._log_repository.create(
                Log(
                    id=None,
                    action="order_screenshot_resend_requested",
                    entity_type="Application",
                    admin_id=dto.admin_id,
                    entity_id=application.id,
                    payload={"reason": dto.reason},
                )
            )
        return updated_application

    async def reject_application(self, dto: RejectApplicationDTO) -> Application:
        """Отклоняет заявку администратором, освобождая зарезервированный слот товара.

        Args:
            dto: Идентификатор заявки, идентификатор администратора и причина отклонения.

        Returns:
            Обновлённая доменная сущность заявки в статусе REJECTED.

        Raises:
            ApplicationNotFoundError: Если заявка не найдена.
            ApplicationRejectionReasonRequiredError: Если причина отклонения не указана.
            InvalidApplicationTransitionError: Если заявка уже в финальном статусе.
        """
        application = await self.get_application(dto.application_id)

        async with self._atomic():
            application.reject(dto.reason)
            updated_application = await self._application_repository.update(application)

            product = await self._product_repository.get_by_id(application.product_id)
            if product is not None:
                product.release_slot()
                await self._product_repository.update(product)

            await self._log_repository.create(
                Log(
                    id=None,
                    action="application_rejected",
                    entity_type="Application",
                    admin_id=dto.admin_id,
                    entity_id=application.id,
                    payload={"reason": dto.reason},
                )
            )

        logger.info(
            "Заявка id=%s отклонена администратором id=%s: %s",
            application.id,
            dto.admin_id,
            dto.reason,
        )
        return updated_application

    async def cancel_by_user(self, dto: CancelApplicationDTO) -> Application:
        """Отменяет заявку по инициативе самого пользователя, освобождая слот товара.

        В отличие от `reject_application` (действие администратора с
        обязательной причиной), этот метод предназначен для случая, когда
        пользователь сам передумал до завершения проверки администратором,
        и не требует указания причины.

        Args:
            dto: Идентификатор заявки и идентификатор пользователя (для
                проверки, что заявка принадлежит именно ему).

        Returns:
            Обновлённая доменная сущность заявки в статусе REJECTED.

        Raises:
            ApplicationNotFoundError: Если заявка не найдена либо не
                принадлежит указанному пользователю.
            InvalidApplicationTransitionError: Если заявка уже в финальном статусе.
        """
        application = await self.get_application(dto.application_id)
        if application.user_id != dto.user_id:
            raise ApplicationNotFoundError(dto.application_id)

        async with self._atomic():
            application.reject("Отменено пользователем")
            updated_application = await self._application_repository.update(application)

            product = await self._product_repository.get_by_id(application.product_id)
            if product is not None:
                product.release_slot()
                await self._product_repository.update(product)

            await self._log_repository.create(
                Log(
                    id=None,
                    action="application_cancelled_by_user",
                    entity_type="Application",
                    user_id=dto.user_id,
                    entity_id=application.id,
                )
            )

        logger.info(
            "Заявка id=%s отменена пользователем id=%s", application.id, dto.user_id
        )
        return updated_application

    async def confirm_receive(self, dto: ConfirmReceiveDTO) -> Application:
        """Фиксирует подтверждение пользователем получения товара.

        Args:
            dto: Идентификатор заявки.

        Returns:
            Обновлённая доменная сущность заявки в статусе WAIT_REVIEW,
            WAIT_RECEIPT_LINK или WAIT_PAYMENT в зависимости от требований товара.

        Raises:
            ApplicationNotFoundError: Если заявка не найдена.
            InvalidApplicationTransitionError: Если заявка не в статусе WAIT_RECEIVE.
        """
        application = await self.get_application(dto.application_id)
        product = await self._product_repository.get_by_id(application.product_id)
        if product is None:
            raise ProductNotFoundError(application.product_id)

        async with self._atomic():
            application.confirm_receive(
                review_required=product.review_required,
                receipt_required=product.receipt_required,
            )
            await self._finalize_wait_payment_if_reached(application)
            updated_application = await self._application_repository.update(application)

            await self._log_repository.create(
                Log(
                    id=None,
                    action="receive_confirmed",
                    entity_type="Application",
                    user_id=application.user_id,
                    entity_id=application.id,
                )
            )
        return updated_application

    async def submit_review_screenshot(self, dto: SubmitReviewScreenshotDTO) -> Application:
        """Фиксирует скриншот отзыва, оставленного пользователем.

        Args:
            dto: Идентификатор заявки и file_id скриншота отзыва.

        Returns:
            Обновлённая доменная сущность заявки в статусе WAIT_RECEIPT_LINK
            или WAIT_PAYMENT в зависимости от того, требуется ли чек для товара.

        Raises:
            ApplicationNotFoundError: Если заявка не найдена.
            InvalidApplicationTransitionError: Если заявка не в статусе WAIT_REVIEW.
        """
        application = await self.get_application(dto.application_id)
        product = await self._product_repository.get_by_id(application.product_id)
        if product is None:
            raise ProductNotFoundError(application.product_id)

        async with self._atomic():
            application.submit_review_screenshot(
                dto.file_id, receipt_required=product.receipt_required
            )
            await self._finalize_wait_payment_if_reached(application)
            updated_application = await self._application_repository.update(application)

            await self._log_repository.create(
                Log(
                    id=None,
                    action="review_screenshot_submitted",
                    entity_type="Application",
                    user_id=application.user_id,
                    entity_id=application.id,
                )
            )
        return updated_application

    async def submit_receipt_link(self, dto: SubmitReceiptLinkDTO) -> Application:
        """Фиксирует ссылку на чек и переводит заявку в ожидание выплаты.

        Args:
            dto: Идентификатор заявки и ссылка на чек.

        Returns:
            Обновлённая доменная сущность заявки в статусе WAIT_PAYMENT.

        Raises:
            ApplicationNotFoundError: Если заявка не найдена.
            InvalidApplicationTransitionError: Если заявка не в статусе WAIT_RECEIPT_LINK.
        """
        application = await self.get_application(dto.application_id)

        async with self._atomic():
            application.submit_receipt_link(dto.receipt_link)
            await self._finalize_wait_payment_if_reached(application)
            updated_application = await self._application_repository.update(application)

            await self._log_repository.create(
                Log(
                    id=None,
                    action="receipt_link_submitted",
                    entity_type="Application",
                    user_id=application.user_id,
                    entity_id=application.id,
                )
            )
        return updated_application

    async def assign_requisites(self, dto: AssignRequisitesDTO) -> Application:
        """Привязывает к заявке выбранный пользователем набор реквизитов.

        Args:
            dto: Идентификатор заявки и идентификатор реквизитов.

        Returns:
            Обновлённая доменная сущность заявки.

        Raises:
            ApplicationNotFoundError: Если заявка не найдена.
            RequisitesNotFoundError: Если реквизиты с указанным `id` не найдены.
        """
        application = await self.get_application(dto.application_id)

        requisites = await self._requisites_repository.get_by_id(dto.requisites_id)
        if requisites is None:
            raise RequisitesNotFoundError(dto.requisites_id)

        application.assign_requisites(dto.requisites_id)
        return await self._application_repository.update(application)

    async def list_user_applications(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[Application]:
        """Возвращает страницу заявок конкретного пользователя.

        Args:
            user_id: Внутренний идентификатор пользователя.
            limit: Максимальное количество заявок в результате.
            offset: Количество заявок, которые нужно пропустить.

        Returns:
            Список заявок пользователя.
        """
        return await self._application_repository.list_by_user(
            user_id, limit=limit, offset=offset
        )

    async def list_applications_by_status(
        self, status: ApplicationStatus, limit: int = 50, offset: int = 0
    ) -> list[Application]:
        """Возвращает страницу заявок с указанным статусом для очереди администратора.

        Args:
            status: Статус заявок для фильтрации.
            limit: Максимальное количество заявок в результате.
            offset: Количество заявок, которые нужно пропустить.

        Returns:
            Список заявок с указанным статусом.
        """
        return await self._application_repository.list_by_status(
            status, limit=limit, offset=offset
        )

    async def list_applications_due_for_payout(
        self, as_of: date | None = None
    ) -> list[Application]:
        """Возвращает заявки, ожидающие выплаты, у которых наступила расчётная дата.

        Используется планировщиком APScheduler для ежедневного уведомления
        администраторов о заявках, готовых к выплате.

        Args:
            as_of: Дата, относительно которой производится поиск. По
                умолчанию используется текущая дата.

        Returns:
            Список заявок, готовых к выплате.
        """
        return await self._application_repository.list_due_for_payout(as_of or date.today())

    async def count_applications_by_status(self, status: ApplicationStatus) -> int:
        """Возвращает количество заявок с указанным статусом.

        Args:
            status: Статус заявок для подсчёта.

        Returns:
            Количество заявок в указанном статусе.
        """
        return await self._application_repository.count_by_status(status)
