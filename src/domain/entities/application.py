"""Доменная сущность заявки реселлера на выкуп товара."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from src.domain.enums.application_status import ApplicationStatus
from src.domain.exceptions.application_exceptions import (
    ApplicationRejectionReasonRequiredError,
    InvalidApplicationTransitionError,
)

# Карта допустимых переходов статусов заявки. Ключ — текущий статус,
# значение — множество статусов, в которые можно перейти напрямую.
# WAIT_RECEIVE может вести сразу в WAIT_PAYMENT, минуя WAIT_REVIEW и
# WAIT_RECEIPT_LINK, если для товара не требуется ни отзыв, ни чек.
_ALLOWED_TRANSITIONS: dict[ApplicationStatus, frozenset[ApplicationStatus]] = {
    ApplicationStatus.NEW: frozenset(
        {ApplicationStatus.WAIT_ORDER_SCREEN, ApplicationStatus.REJECTED}
    ),
    ApplicationStatus.WAIT_ORDER_SCREEN: frozenset(
        {ApplicationStatus.ORDER_ON_REVIEW, ApplicationStatus.REJECTED}
    ),
    ApplicationStatus.ORDER_ON_REVIEW: frozenset(
        {
            ApplicationStatus.ORDER_APPROVED,
            ApplicationStatus.WAIT_ORDER_SCREEN,
            ApplicationStatus.REJECTED,
        }
    ),
    ApplicationStatus.ORDER_APPROVED: frozenset(
        {ApplicationStatus.WAIT_RECEIVE, ApplicationStatus.REJECTED}
    ),
    ApplicationStatus.WAIT_RECEIVE: frozenset(
        {
            ApplicationStatus.WAIT_REVIEW,
            ApplicationStatus.WAIT_RECEIPT_LINK,
            ApplicationStatus.WAIT_PAYMENT,
            ApplicationStatus.REJECTED,
        }
    ),
    ApplicationStatus.WAIT_REVIEW: frozenset(
        {
            ApplicationStatus.WAIT_RECEIPT_LINK,
            ApplicationStatus.WAIT_PAYMENT,
            ApplicationStatus.REJECTED,
        }
    ),
    ApplicationStatus.WAIT_RECEIPT_LINK: frozenset(
        {ApplicationStatus.WAIT_PAYMENT, ApplicationStatus.REJECTED}
    ),
    ApplicationStatus.WAIT_PAYMENT: frozenset(
        {ApplicationStatus.PAID, ApplicationStatus.REJECTED}
    ),
    ApplicationStatus.PAID: frozenset(),
    ApplicationStatus.REJECTED: frozenset(),
}


@dataclass(slots=True)
class Application:
    """Заявка пользователя на выкуп товара с последующей выплатой кэшбэка.

    Инкапсулирует правила переходов между статусами жизненного цикла
    заявки, описанные в `ApplicationStatus`. Любая попытка перевести
    заявку в статус, недопустимый из текущего, приводит к исключению
    `InvalidApplicationTransitionError`.

    Attributes:
        id: Внутренний идентификатор заявки. `None` для ещё не сохранённой
            в базе данных сущности.
        user_id: Идентификатор пользователя, оформившего заявку.
        product_id: Идентификатор товара, на который оформлена заявка.
        status: Текущий статус заявки.
        article: Артикул товара на маркетплейсе, указанный пользователем.
        order_screenshot_file_id: file_id скриншота подтверждения заказа.
        receipt_link: Ссылка на чек оплаты.
        review_screenshot_file_id: file_id скриншота оставленного отзыва.
        requisites_id: Идентификатор реквизитов, выбранных для выплаты.
        admin_comment: Комментарий администратора (причина отклонения или
            запроса повторной отправки данных).
        payout_due_date: Расчётная дата, на которую должна быть произведена выплата.
        created_at: Дата и время создания заявки.
        updated_at: Дата и время последнего обновления заявки.
    """

    id: int | None
    user_id: int
    product_id: int
    status: ApplicationStatus = ApplicationStatus.NEW
    article: str | None = None
    order_screenshot_file_id: str | None = None
    receipt_link: str | None = None
    review_screenshot_file_id: str | None = None
    requisites_id: int | None = None
    admin_comment: str | None = None
    payout_due_date: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def _transition_to(
        self, target_status: ApplicationStatus, *, admin_comment: str | None = None
    ) -> None:
        """Переводит заявку в новый статус с проверкой допустимости перехода.

        Args:
            target_status: Статус, в который необходимо перевести заявку.
            admin_comment: Комментарий администратора, сопровождающий переход
                (например, причина отклонения или запроса повторной отправки).

        Raises:
            InvalidApplicationTransitionError: Если переход из текущего
                статуса в целевой не предусмотрен бизнес-процессом.
        """
        allowed_targets = _ALLOWED_TRANSITIONS[self.status]
        if target_status not in allowed_targets:
            raise InvalidApplicationTransitionError(self.status, target_status)
        self.status = target_status
        if admin_comment is not None:
            self.admin_comment = admin_comment

    def submit_article(self, article: str) -> None:
        """Фиксирует артикул товара, указанный пользователем, и ожидает скриншот заказа.

        Args:
            article: Артикул товара на Wildberries или Ozon.

        Raises:
            InvalidApplicationTransitionError: Если заявка находится не в статусе NEW.
        """
        self.article = article.strip()
        self._transition_to(ApplicationStatus.WAIT_ORDER_SCREEN)

    def submit_order_screenshot(self, file_id: str) -> None:
        """Фиксирует скриншот заказа и переводит заявку на проверку администратору.

        Args:
            file_id: Идентификатор файла скриншота в Telegram.

        Raises:
            InvalidApplicationTransitionError: Если заявка не находится в
                статусе WAIT_ORDER_SCREEN.
        """
        self.order_screenshot_file_id = file_id
        self._transition_to(ApplicationStatus.ORDER_ON_REVIEW)

    def approve_order(self) -> None:
        """Подтверждает заказ администратором и переводит заявку в статус ожидания получения.

        Raises:
            InvalidApplicationTransitionError: Если заявка не находится в
                статусе ORDER_ON_REVIEW.
        """
        self._transition_to(ApplicationStatus.ORDER_APPROVED)
        self._transition_to(ApplicationStatus.WAIT_RECEIVE)

    def request_order_screenshot_resend(self, reason: str) -> None:
        """Запрашивает у пользователя повторную отправку скриншота заказа.

        Args:
            reason: Причина, по которой скриншот не был принят.

        Raises:
            InvalidApplicationTransitionError: Если заявка не находится в
                статусе ORDER_ON_REVIEW.
        """
        self._transition_to(ApplicationStatus.WAIT_ORDER_SCREEN, admin_comment=reason)

    def reject(self, reason: str) -> None:
        """Отклоняет заявку с обязательным указанием причины.

        Args:
            reason: Причина отклонения заявки, отображаемая пользователю.

        Raises:
            ApplicationRejectionReasonRequiredError: Если причина отклонения не указана.
            InvalidApplicationTransitionError: Если заявка уже находится в
                финальном статусе (PAID или REJECTED).
        """
        if not reason or not reason.strip():
            raise ApplicationRejectionReasonRequiredError()
        self._transition_to(ApplicationStatus.REJECTED, admin_comment=reason)

    def confirm_receive(self, *, review_required: bool, receipt_required: bool) -> None:
        """Фиксирует подтверждение пользователем получения товара.

        В зависимости от требований конкретного товара заявка переводится
        в статус ожидания отзыва, ожидания ссылки на чек, либо сразу в
        статус ожидания выплаты.

        Args:
            review_required: Требуется ли для этого товара отзыв.
            receipt_required: Требуется ли для этого товара ссылка на чек.

        Raises:
            InvalidApplicationTransitionError: Если заявка не находится в
                статусе WAIT_RECEIVE.
        """
        if review_required:
            self._transition_to(ApplicationStatus.WAIT_REVIEW)
        elif receipt_required:
            self._transition_to(ApplicationStatus.WAIT_RECEIPT_LINK)
        else:
            self._transition_to(ApplicationStatus.WAIT_PAYMENT)

    def submit_review_screenshot(self, file_id: str, *, receipt_required: bool) -> None:
        """Фиксирует скриншот отзыва, оставленного пользователем.

        Args:
            file_id: Идентификатор файла скриншота отзыва в Telegram.
            receipt_required: Требуется ли для этого товара ссылка на чек.

        Raises:
            InvalidApplicationTransitionError: Если заявка не находится в
                статусе WAIT_REVIEW.
        """
        self.review_screenshot_file_id = file_id
        if receipt_required:
            self._transition_to(ApplicationStatus.WAIT_RECEIPT_LINK)
        else:
            self._transition_to(ApplicationStatus.WAIT_PAYMENT)

    def submit_receipt_link(self, receipt_link: str) -> None:
        """Фиксирует ссылку на чек и переводит заявку в ожидание выплаты.

        Args:
            receipt_link: Ссылка на электронный чек об оплате.

        Raises:
            InvalidApplicationTransitionError: Если заявка не находится в
                статусе WAIT_RECEIPT_LINK.
        """
        self.receipt_link = receipt_link.strip()
        self._transition_to(ApplicationStatus.WAIT_PAYMENT)

    def calculate_payout_due_date(self, payout_days: int, from_date: date | None = None) -> date:
        """Вычисляет и сохраняет расчётную дату выплаты по заявке.

        Args:
            payout_days: Количество дней от указанной даты до даты выплаты
                (берётся из настроек товара).
            from_date: Дата, от которой отсчитывается срок выплаты. По
                умолчанию используется текущая дата.

        Returns:
            Вычисленная дата выплаты, дополнительно сохранённая в поле
            `payout_due_date`.
        """
        base_date = from_date or date.today()
        self.payout_due_date = base_date + timedelta(days=payout_days)
        return self.payout_due_date

    def assign_requisites(self, requisites_id: int) -> None:
        """Привязывает к заявке выбранный пользователем набор реквизитов для выплаты.

        Args:
            requisites_id: Идентификатор набора реквизитов пользователя.
        """
        self.requisites_id = requisites_id

    def mark_paid(self) -> None:
        """Переводит заявку в финальный статус PAID после осуществления выплаты.

        Raises:
            InvalidApplicationTransitionError: Если заявка не находится в
                статусе WAIT_PAYMENT.
        """
        self._transition_to(ApplicationStatus.PAID)

    @property
    def is_payable(self) -> bool:
        """Признак того, что заявка ожидает выплаты и наступила расчётная дата.

        Returns:
            True, если заявка находится в статусе WAIT_PAYMENT и расчётная
            дата выплаты уже наступила или равна сегодняшней.
        """
        return (
            self.status == ApplicationStatus.WAIT_PAYMENT
            and self.payout_due_date is not None
            and self.payout_due_date <= date.today()
        )
