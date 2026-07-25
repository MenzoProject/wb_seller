"""Текстовые шаблоны сообщений пользовательского бота."""

from __future__ import annotations

from datetime import date
from html import escape

from src.domain.entities.product import Product
from src.domain.entities.requisites import UserRequisites
from src.domain.enums.application_status import ApplicationStatus

WELCOME_TEXT = (
    "👋 Здравствуйте, {full_name}!\n\n"
    "Это бот для оформления заявок на выкуп товаров с кэшбэком на "
    "Wildberries и Ozon.\n\n"
    "Выберите товар в разделе «📦 Каталог», и я проведу вас через все "
    "шаги оформления заявки — от выбора товара до получения выплаты."
)

BLOCKED_USER_TEXT = (
    "🚫 Вы заблокированы и не можете пользоваться ботом. "
    "Если считаете это ошибкой, обратитесь в поддержку."
)

CATALOG_EMPTY_TEXT = (
    "😔 Сейчас в каталоге нет доступных товаров. Загляните немного позже — "
    "мы регулярно добавляем новые предложения."
)

CATALOG_HEADER_TEXT = (
    "📦 <b>Каталог доступных товаров</b>\n\nВыберите товар, чтобы посмотреть подробности:"
)

ORDER_OUT_OF_STOCK_TEXT = (
    "😔 К сожалению, на этот товар закончились доступные слоты заявок. "
    "Попробуйте выбрать другой товар в каталоге."
)

ORDER_UNAVAILABLE_TEXT = "😔 Этот товар сейчас недоступен для заказа."

ORDER_ALREADY_ACTIVE_TEXT = (
    "⚠️ У вас уже есть активная заявка на этот товар. Посмотреть её статус "
    "можно в разделе «📋 Мои заявки»."
)

ORDER_GENERIC_ERROR_TEXT = (
    "⚠️ Не удалось оформить заявку. Попробуйте ещё раз чуть позже или "
    "обратитесь в поддержку."
)

ASK_ARTICLE_TEXT = (
    "✅ Заявка создана!\n\n"
    "Теперь отправьте, пожалуйста, <b>артикул товара</b> на маркетплейсе "
    "(число, которое вы использовали при заказе)."
)

ARTICLE_EMPTY_TEXT = "⚠️ Артикул не может быть пустым. Отправьте, пожалуйста, артикул товара."

ASK_ORDER_SCREENSHOT_TEXT = (
    "📸 Отлично! Теперь отправьте <b>скриншот подтверждения заказа</b> "
    "(страница с оформленным заказом на маркетплейсе)."
)

ORDER_SCREENSHOT_NOT_PHOTO_TEXT = (
    "⚠️ Пожалуйста, отправьте именно фотографию (скриншот), а не текст или файл."
)

ORDER_SUBMITTED_TEXT = (
    "✅ Скриншот заказа получен! Заявка отправлена администратору на проверку.\n\n"
    "Мы уведомим вас, как только заявка будет проверена."
)

APPLICATION_CANCELLED_TEXT = "❌ Заявка отменена. Вы можете оформить новую заявку в любое время."

CANCEL_BUTTON_TEXT = "❌ Отмена"

INVALID_STATE_TRANSITION_TEXT = (
    "⚠️ Это действие сейчас недоступно — статус заявки уже изменился. "
    "Обновите список заявок в разделе «📋 Мои заявки»."
)

# --- Подтверждение получения и продолжение заявки после получения ---

ASK_CONFIRM_RECEIVE_TEXT = (
    "📦 Ваш заказ подтверждён администратором! Когда получите товар, "
    "нажмите кнопку ниже."
)

CONFIRM_RECEIVE_BUTTON_TEXT = "✅ Я получил(а) товар"

RECEIVE_CONFIRMED_TEXT = (
    "✅ Отлично! Осталось указать реквизиты, на которые нужно перевести кэшбэк."
)

ASK_REVIEW_SCREENSHOT_TEXT = (
    "✍️ Для этого товара нужно оставить отзыв. Пожалуйста, оставьте отзыв на "
    "маркетплейсе и пришлите сюда его скриншот."
)

REVIEW_SCREENSHOT_NOT_PHOTO_TEXT = (
    "⚠️ Пожалуйста, отправьте именно фотографию (скриншот отзыва)."
)

ASK_RECEIPT_LINK_TEXT = (
    "🧾 Для этого товара нужна ссылка на чек об оплате. Пришлите её, пожалуйста, сообщением."
)

RECEIPT_LINK_EMPTY_TEXT = "⚠️ Ссылка не может быть пустой. Пришлите, пожалуйста, ссылку на чек."


def format_wait_payment_text(payout_due_date: date | None) -> str:
    """Формирует сообщение об ожидании выплаты с расчётной датой.

    Args:
        payout_due_date: Расчётная дата выплаты, если она уже вычислена.

    Returns:
        Текст сообщения, сообщающий пользователю дату ожидаемой выплаты.
    """
    if payout_due_date is not None:
        return (
            "🎉 Все данные получены! Выплата запланирована на "
            f"<b>{payout_due_date.strftime('%d.%m.%Y')}</b>. Мы уведомим вас, "
            "как только деньги будут переведены."
        )
    return (
        "🎉 Все данные получены! Ожидайте выплату — мы уведомим вас, как "
        "только деньги будут переведены."
    )


def format_order_rejected_notification(application_id: int, reason: str) -> str:
    """Формирует уведомление пользователю об отклонении заявки администратором.

    Args:
        application_id: Внутренний идентификатор отклонённой заявки.
        reason: Причина отклонения, указанная администратором.

    Returns:
        HTML-форматированный текст уведомления.
    """
    return f"❌ Ваша заявка №{application_id} отклонена.\n\nПричина: {escape(reason)}"


def format_order_resend_requested_notification(reason: str) -> str:
    """Формирует уведомление пользователю о запросе повторной отправки скриншота.

    Args:
        reason: Причина, по которой скриншот не был принят.

    Returns:
        HTML-форматированный текст уведомления с просьбой отправить скриншот снова.
    """
    return (
        f"🔄 Администратор запросил повторную отправку скриншота заказа.\n\n"
        f"Причина: {escape(reason)}\n\n"
        f"Пожалуйста, отправьте скриншот подтверждения заказа ещё раз."
    )


def format_payment_received_notification(application_id: int) -> str:
    """Формирует уведомление пользователю о произведённой выплате.

    Args:
        application_id: Внутренний идентификатор оплаченной заявки.

    Returns:
        Текст уведомления о полученной выплате.
    """
    return (
        f"🎉 Выплата по заявке №{application_id} произведена! "
        f"Спасибо, что пользуетесь нашим сервисом."
    )


# --- Мои заявки ---

MY_APPLICATIONS_HEADER_TEXT = "📋 <b>Ваши заявки</b>"

NO_APPLICATIONS_TEXT = (
    "У вас пока нет ни одной заявки. Загляните в «📦 Каталог», чтобы оформить первую!"
)

_APPLICATION_STATUS_LABELS: dict[ApplicationStatus, str] = {
    ApplicationStatus.NEW: "🆕 Новая",
    ApplicationStatus.WAIT_ORDER_SCREEN: "📸 Ожидает скриншот заказа",
    ApplicationStatus.ORDER_ON_REVIEW: "🔍 На проверке у администратора",
    ApplicationStatus.ORDER_APPROVED: "✅ Заказ подтверждён",
    ApplicationStatus.WAIT_RECEIVE: "📦 Ожидает получения товара",
    ApplicationStatus.WAIT_REVIEW: "✍️ Ожидает отзыв",
    ApplicationStatus.WAIT_RECEIPT_LINK: "🧾 Ожидает ссылку на чек",
    ApplicationStatus.WAIT_PAYMENT: "💸 Ожидает выплату",
    ApplicationStatus.PAID: "✅ Выплачено",
    ApplicationStatus.REJECTED: "❌ Отклонена",
}


def format_application_status(status: ApplicationStatus) -> str:
    """Возвращает человекочитаемое название статуса заявки на русском языке.

    Args:
        status: Статус заявки.

    Returns:
        Строка с эмодзи и названием статуса, понятным пользователю.
    """
    return _APPLICATION_STATUS_LABELS.get(status, status.value)


# --- Реквизиты ---

REQUISITES_HEADER_TEXT = "💳 <b>Ваши реквизиты для выплат</b>"

NO_REQUISITES_TEXT = "У вас пока нет сохранённых реквизитов."

ASK_FULL_NAME_TEXT = "Введите ФИО получателя выплаты (как в паспорте или в банковском приложении):"

FULL_NAME_TOO_SHORT_TEXT = "⚠️ ФИО указано слишком коротко. Попробуйте ещё раз."

ASK_PHONE_TEXT = "Теперь введите номер телефона, привязанный к банку для перевода:"

PHONE_INVALID_TEXT = (
    "⚠️ Некорректный формат номера телефона. Попробуйте ещё раз, "
    "например: +7 900 123-45-67"
)

ASK_BANK_TEXT = "Выберите банк получателя:"

NO_BANKS_AVAILABLE_TEXT = "⚠️ Сейчас нет доступных банков для выбора. Обратитесь в поддержку."

REQUISITES_SAVED_TEXT = "✅ Реквизиты сохранены!"

REQUISITES_DELETED_TEXT = "🗑 Реквизиты удалены."

REQUISITES_SET_DEFAULT_TEXT = "⭐ Эти реквизиты теперь используются по умолчанию."

REQUISITES_ADD_BUTTON_TEXT = "➕ Добавить реквизиты"

REQUISITES_ADD_NEW_FOR_APPLICATION_TEXT = "➕ Указать новые реквизиты"


def format_requisites_label(requisites: UserRequisites, bank_name: str) -> str:
    """Формирует короткую подпись набора реквизитов для кнопки или списка.

    Args:
        requisites: Доменная сущность реквизитов пользователя.
        bank_name: Название банка, к которому привязаны реквизиты.

    Returns:
        Строка вида '⭐ Иванов Иван · Тинькофф'.
    """
    star = "⭐ " if requisites.is_default else ""
    return f"{star}{requisites.full_name} · {bank_name}"


# --- Инструкция и поддержка ---

INSTRUCTION_TEXT = (
    "📖 <b>Как пользоваться ботом</b>\n\n"
    "1. Откройте «📦 Каталог» и выберите товар.\n"
    "2. Нажмите «Оформить заявку» и отправьте артикул товара и скриншот "
    "подтверждения заказа.\n"
    "3. Дождитесь проверки заказа администратором.\n"
    "4. Когда получите товар, нажмите кнопку «Я получил(а) товар» в чате с ботом.\n"
    "5. При необходимости оставьте отзыв и/или пришлите ссылку на чек — бот "
    "подскажет, что именно нужно для конкретного товара.\n"
    "6. Укажите реквизиты для выплаты (или выберите ранее сохранённые).\n"
    "7. Дождитесь выплаты — актуальный статус всегда виден в разделе "
    "«📋 Мои заявки»."
)

SUPPORT_TEXT_TEMPLATE = (
    "💬 По всем вопросам, связанным с заявками и выплатами, обращайтесь к "
    "менеджеру поддержки: @{username}"
)


def format_product_catalog_item(product: Product) -> str:
    """Формирует краткое описание товара для кнопки в списке каталога.

    Args:
        product: Доменная сущность товара.

    Returns:
        Строка вида 'Название — 1500 ₽ кэшбэка', пригодная для подписи
        инлайн-кнопки каталога.
    """
    return f"{product.title} — {product.cashback_amount} ₽ кэшбэка"


def format_product_card_text(product: Product) -> str:
    """Формирует подробную карточку товара для отображения перед оформлением заявки.

    Args:
        product: Доменная сущность товара.

    Returns:
        HTML-форматированный текст карточки товара со всеми условиями.
    """
    conditions: list[str] = []
    if product.review_required:
        conditions.append("оставить отзыв")
    if product.receipt_required:
        conditions.append("предоставить ссылку на чек")

    conditions_text = (
        "Для получения кэшбэка потребуется: " + ", ".join(conditions) + "."
        if conditions
        else "Дополнительных условий для получения кэшбэка нет."
    )

    return (
        f"🛍 <b>{escape(product.title)}</b>\n\n"
        f"{escape(product.description)}\n\n"
        f"💰 Цена товара: <b>{product.price} ₽</b>\n"
        f"💸 Сумма кэшбэка: <b>{product.cashback_amount} ₽</b>\n"
        f"⏱ Срок выплаты: <b>{product.payout_days} дн.</b> после выполнения условий\n"
        f"📦 Доступно заявок: <b>{product.available_slots}</b>\n\n"
        f"ℹ️ {conditions_text}\n\n"
        f"🔗 Ссылка на товар: {escape(product.product_url)}\n\n"
        f"📖 <b>Инструкция по заказу:</b>\n{escape(product.instruction_text)}"
    )

