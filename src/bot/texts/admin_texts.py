"""Текстовые шаблоны сообщений административного бота."""

from __future__ import annotations

from html import escape

from src.application.services.statistics_service import DashboardStatistics
from src.bot.texts.user_texts import format_application_status
from src.domain.entities.bank import Bank
from src.domain.entities.product import Product

ADMIN_WELCOME_TEXT = "🛠 <b>Панель администратора</b>\n\nВыберите раздел:"

# --- Раздел «⚙ Настройки» ---

ADMIN_SETTINGS_HEADER_TEXT = "⚙ <b>Настройки</b>\n\nВыберите раздел:"

# --- Справочник банков ---

ADMIN_BANKS_HEADER_TEXT = (
    "🏦 <b>Справочник банков</b>\n\n"
    "Активные банки предлагаются пользователям при сохранении реквизитов "
    "для выплаты. Нажмите на банк, чтобы включить или отключить его."
)

ADMIN_BANKS_EMPTY_TEXT = (
    "Справочник банков пуст. Нажмите «➕ Добавить банк», чтобы добавить первый — "
    "без хотя бы одного активного банка пользователи не смогут сохранить реквизиты."
)

ADD_BANK_BUTTON_TEXT = "➕ Добавить банк"

ASK_BANK_NAME_TEXT = "Введите название нового банка:"

BANK_NAME_TOO_SHORT_TEXT = "Название банка должно содержать минимум 2 символа. Попробуйте ещё раз:"

BANK_NAME_ALREADY_EXISTS_TEXT = (
    "Банк с таким названием уже есть в справочнике. Введите другое название:"
)

BANK_CREATED_TEXT = "✅ Банк добавлен и доступен для выбора пользователями."

BANK_ACTIVATED_TEXT = "✅ Банк включён и снова доступен для выбора."

BANK_DEACTIVATED_TEXT = "🚫 Банк отключён и больше не будет предложен пользователям."

BANK_NOT_FOUND_TEXT = "Банк не найден. Возможно, он уже был удалён."


def format_admin_bank_list_item(bank: Bank) -> str:
    """Формирует подпись кнопки банка в списке управления справочником.

    Args:
        bank: Доменная сущность банка.

    Returns:
        Строка с названием банка и пометкой текущего статуса.
    """
    status_marker = "✅" if bank.is_active else "🚫"
    return f"{status_marker} {bank.name}"

# --- Список и карточка товара ---

ADMIN_PRODUCTS_HEADER_TEXT = "📦 <b>Управление товарами</b>"

ADMIN_PRODUCTS_EMPTY_TEXT = "Товаров пока нет. Нажмите «➕ Добавить товар», чтобы создать первый."

ADD_PRODUCT_BUTTON_TEXT = "➕ Добавить товар"


def format_admin_product_list_item(product: Product) -> str:
    """Формирует подпись кнопки товара в списке управления каталогом.

    Args:
        product: Доменная сущность товара.

    Returns:
        Строка с названием товара и пометками статуса (скрыт/удалён).
    """
    markers = []
    if product.is_deleted:
        markers.append("🗑 удалён")
    elif product.is_hidden:
        markers.append("🙈 скрыт")
    markers_text = f" ({', '.join(markers)})" if markers else ""
    return f"{product.title} · слотов: {product.available_slots}{markers_text}"


def format_admin_product_card(product: Product) -> str:
    """Формирует подробную карточку товара для панели администратора.

    Args:
        product: Доменная сущность товара.

    Returns:
        HTML-форматированный текст карточки со всеми полями товара.
    """
    if product.is_deleted:
        status_line = "🗑 Удалён"
    elif product.is_hidden:
        status_line = "🙈 Скрыт"
    else:
        status_line = "👁 Виден в каталоге"
    return (
        f"🛍 <b>{escape(product.title)}</b> (id: {product.id})\n"
        f"Статус: {status_line}\n\n"
        f"{escape(product.description)}\n\n"
        f"💰 Цена: <b>{product.price} ₽</b>\n"
        f"💸 Кэшбэк: <b>{product.cashback_amount} ₽</b>\n"
        f"⏱ Срок выплаты: <b>{product.payout_days} дн.</b>\n"
        f"✍️ Отзыв обязателен: <b>{'да' if product.review_required else 'нет'}</b>\n"
        f"🧾 Чек обязателен: <b>{'да' if product.receipt_required else 'нет'}</b>\n"
        f"📦 Доступно заявок: <b>{product.available_slots}</b>\n"
        f"🔗 {escape(product.product_url)}\n\n"
        f"📖 Инструкция:\n{escape(product.instruction_text)}"
    )


# --- Мастер создания / редактирования товара ---

ASK_PRODUCT_TITLE_TEXT = "Введите название товара:"
PRODUCT_TITLE_EMPTY_TEXT = "⚠️ Название не может быть пустым. Попробуйте ещё раз."

ASK_PRODUCT_DESCRIPTION_TEXT = "Введите описание товара для каталога:"
PRODUCT_DESCRIPTION_EMPTY_TEXT = "⚠️ Описание не может быть пустым. Попробуйте ещё раз."

ASK_PRODUCT_PRICE_TEXT = "Введите цену товара в рублях (например: 1500 или 1500.50):"
PRODUCT_PRICE_INVALID_TEXT = "⚠️ Введите цену числом, например: 1500 или 1500.50"

ASK_PRODUCT_CASHBACK_TEXT = "Введите сумму кэшбэка в рублях:"
PRODUCT_CASHBACK_INVALID_TEXT = "⚠️ Введите сумму кэшбэка числом, например: 1500"

ASK_PRODUCT_PAYOUT_DAYS_TEXT = "Через сколько дней после выполнения условий производится выплата?"
PRODUCT_PAYOUT_DAYS_INVALID_TEXT = "⚠️ Введите целое положительное число дней."

ASK_PRODUCT_REVIEW_REQUIRED_TEXT = "Нужен ли отзыв для получения кэшбэка по этому товару?"
ASK_PRODUCT_RECEIPT_REQUIRED_TEXT = "Нужна ли ссылка на чек для получения кэшбэка по этому товару?"

ASK_PRODUCT_URL_TEXT = "Отправьте ссылку на товар на маркетплейсе:"
PRODUCT_URL_EMPTY_TEXT = "⚠️ Ссылка не может быть пустой. Попробуйте ещё раз."

ASK_PRODUCT_INSTRUCTION_TEXT = "Введите текст инструкции по оформлению заказа для этого товара:"
PRODUCT_INSTRUCTION_EMPTY_TEXT = "⚠️ Инструкция не может быть пустой. Попробуйте ещё раз."

ASK_PRODUCT_SLOTS_TEXT = "Сколько заявок доступно на этот товар?"
PRODUCT_SLOTS_INVALID_TEXT = "⚠️ Введите целое неотрицательное число."

ASK_PRODUCT_PHOTO_TEXT = (
    "Отправьте фотографию товара (или нажмите «⏭ Без фото», чтобы пропустить этот шаг):"
)
PRODUCT_PHOTO_SKIP_BUTTON_TEXT = "⏭ Без фото"
PRODUCT_PHOTO_INVALID_TEXT = "⚠️ Пожалуйста, отправьте фотографию или нажмите «⏭ Без фото»."

PRODUCT_CREATED_TEXT = "✅ Товар успешно создан и добавлен в каталог!"
PRODUCT_UPDATED_TEXT = "✅ Товар успешно обновлён!"

YES_BUTTON_TEXT = "✅ Да"
NO_BUTTON_TEXT = "❌ Нет"

# --- Быстрые действия ---

PRODUCT_HIDDEN_TEXT = "🙈 Товар скрыт из каталога."
PRODUCT_UNHIDDEN_TEXT = "👁 Товар снова виден в каталоге."
PRODUCT_DELETED_TEXT = "🗑 Товар удалён."
PRODUCT_NOT_FOUND_TEXT = "⚠️ Товар не найден."

ASK_NEW_SLOTS_TEXT = "Введите новое количество доступных заявок:"
PRODUCT_SLOTS_UPDATED_TEXT = "✅ Остаток обновлён."

# --- Управление заявками ---

ADMIN_APPLICATIONS_HEADER_TEXT = "📋 <b>Заявки, ожидающие проверки</b>"
ADMIN_APPLICATIONS_EMPTY_TEXT = "Нет заявок, ожидающих проверки."

ASK_REJECT_REASON_TEXT = "Введите причину отклонения заявки:"
REJECT_REASON_EMPTY_TEXT = "⚠️ Причина не может быть пустой. Попробуйте ещё раз."

ASK_RESEND_REASON_TEXT = "Введите причину запроса повторной отправки скриншота заказа:"
RESEND_REASON_EMPTY_TEXT = "⚠️ Причина не может быть пустой. Попробуйте ещё раз."

APPLICATION_APPROVED_ADMIN_TEXT = "✅ Заявка одобрена, пользователь уведомлён."
APPLICATION_REJECTED_ADMIN_TEXT = "❌ Заявка отклонена, пользователь уведомлён."
APPLICATION_RESEND_REQUESTED_ADMIN_TEXT = "🔄 Запрошена повторная отправка, пользователь уведомлён."
APPLICATION_NOT_FOUND_ADMIN_TEXT = "⚠️ Заявка не найдена или уже была обработана."


def format_admin_application_list_item(
    application_id: int, user_full_name: str, product_title: str
) -> str:
    """Формирует подпись кнопки заявки в очереди на проверку.

    Args:
        application_id: Внутренний идентификатор заявки.
        user_full_name: Полное имя пользователя, подавшего заявку.
        product_title: Название товара, на который оформлена заявка.

    Returns:
        Строка вида '№12 · Иван Иванов · Наушники'.
    """
    return f"№{application_id} · {user_full_name} · {product_title}"


def format_admin_application_card(
    application_id: int,
    user_mention: str,
    product_title: str,
    article: str | None,
    order_screenshot_file_id: str | None,
) -> str:
    """Формирует подробную карточку заявки для решения администратора.

    Args:
        application_id: Внутренний идентификатор заявки.
        user_mention: Строка с именем и идентификатором пользователя.
        product_title: Название товара, на который оформлена заявка.
        article: Артикул товара, указанный пользователем.
        order_screenshot_file_id: file_id скриншота заказа, если он был отправлен.

    Returns:
        HTML-форматированный текст карточки заявки.
    """
    screenshot_note = (
        "приложен ниже" if order_screenshot_file_id else "не был отправлен"
    )
    return (
        f"📋 <b>Заявка №{application_id}</b>\n\n"
        f"👤 Пользователь: {escape(user_mention)}\n"
        f"🛍 Товар: {escape(product_title)}\n"
        f"🔢 Артикул: {escape(article) if article else '—'}\n"
        f"📸 Скриншот заказа: {screenshot_note}"
    )


# --- Управление выплатами ---

ADMIN_PAYMENTS_HEADER_TEXT = "💰 <b>Выплаты, ожидающие исполнения</b>"
ADMIN_PAYMENTS_EMPTY_TEXT = "Нет выплат, ожидающих исполнения."

PAYMENT_MARKED_PAID_ADMIN_TEXT = "✅ Выплата отмечена как произведённая, пользователь уведомлён."
PAYMENT_NOT_FOUND_ADMIN_TEXT = "⚠️ Выплата не найдена или уже была обработана."


def format_admin_payment_list_item(
    application_id: int, user_full_name: str, product_title: str, amount: str
) -> str:
    """Формирует подпись кнопки выплаты в списке ожидающих исполнения.

    Args:
        application_id: Внутренний идентификатор заявки, к которой относится выплата.
        user_full_name: Полное имя получателя выплаты.
        product_title: Название товара, по которому производится выплата.
        amount: Сумма выплаты в виде строки.

    Returns:
        Строка вида '№12 · Иван Иванов · Наушники · 1500 ₽'.
    """
    return f"№{application_id} · {user_full_name} · {product_title} · {amount} ₽"


# --- Статистика ---

ADMIN_STATISTICS_HEADER_TEXT = "📊 <b>Статистика</b>"


def format_admin_statistics(stats: DashboardStatistics) -> str:
    """Формирует сообщение с агрегированной статистикой для администратора.

    Args:
        stats: Собранный сервисом статистики срез ключевых показателей.

    Returns:
        HTML-форматированный текст с основными метриками системы.
    """
    status_lines = "\n".join(
        f"  {format_application_status(status)}: {count}"
        for status, count in stats.applications_by_status.items()
        if count > 0
    )
    if not status_lines:
        status_lines = "  заявок пока нет"

    return (
        f"{ADMIN_STATISTICS_HEADER_TEXT}\n\n"
        f"👥 Пользователей: <b>{stats.total_users}</b>\n"
        f"📦 Товаров доступно в каталоге: <b>{stats.available_products_count}</b>\n\n"
        f"📋 Заявки по статусам:\n{status_lines}\n\n"
        f"💰 Выплат ожидает исполнения: <b>{stats.pending_payments_count}</b>\n"
        f"💸 Выплачено всего: <b>{stats.total_paid_amount} ₽</b>\n"
        f"📅 Выплачено за последние 30 дней: <b>{stats.paid_amount_last_30_days} ₽</b>"
    )


# --- Уведомления планировщика ---

PAYMENT_DUE_DIGEST_HEADER_TEXT = "⏰ <b>Заявки, готовые к выплате</b>"
PAYMENT_DUE_DIGEST_EMPTY_TEXT = "На сегодня заявок, готовых к выплате, нет."


def format_payment_due_item(
    application_id: int, user_full_name: str, product_title: str, amount: str, due_date: str
) -> str:
    """Формирует строку одной заявки в ежедневной сводке планировщика о выплатах.

    Args:
        application_id: Внутренний идентификатор заявки.
        user_full_name: Полное имя получателя выплаты.
        product_title: Название товара, по которому производится выплата.
        amount: Сумма выплаты в виде строки.
        due_date: Расчётная дата выплаты в виде строки (уже отформатированной).

    Returns:
        Строка вида '№12 · Иван Иванов · Наушники · 1500 ₽ · срок: 25.07.2026'.
    """
    return (
        f"№{application_id} · {user_full_name} · {product_title} · "
        f"{amount} ₽ · срок: {due_date}"
    )
