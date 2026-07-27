"""Клавиатуры административного бота."""

from src.bot.keyboards.admin.applications import (
    AdminApplicationsCallback,
    get_admin_application_card_keyboard,
    get_admin_applications_queue_keyboard,
)
from src.bot.keyboards.admin.banks import (
    AdminBanksCallback,
    get_admin_banks_list_keyboard,
    get_admin_settings_keyboard,
)
from src.bot.keyboards.admin.main_menu import (
    ADMIN_MENU_BUTTON_TEXTS,
    ADMIN_MENU_PAYMENTS,
    ADMIN_MENU_PRODUCTS,
    ADMIN_MENU_REQUESTS,
    ADMIN_MENU_SETTINGS,
    ADMIN_MENU_STATISTICS,
    get_admin_main_menu_keyboard,
)
from src.bot.keyboards.admin.payments import AdminPaymentsCallback, get_admin_payments_list_keyboard
from src.bot.keyboards.admin.products import (
    AdminProductsCallback,
    ProductPhotoSkipCallback,
    YesNoCallback,
    get_admin_product_card_keyboard,
    get_admin_products_list_keyboard,
    get_photo_step_keyboard,
    get_yes_no_keyboard,
)

__all__ = [
    "ADMIN_MENU_BUTTON_TEXTS",
    "ADMIN_MENU_PAYMENTS",
    "ADMIN_MENU_PRODUCTS",
    "ADMIN_MENU_REQUESTS",
    "ADMIN_MENU_SETTINGS",
    "ADMIN_MENU_STATISTICS",
    "AdminApplicationsCallback",
    "AdminBanksCallback",
    "AdminPaymentsCallback",
    "AdminProductsCallback",
    "ProductPhotoSkipCallback",
    "YesNoCallback",
    "get_admin_application_card_keyboard",
    "get_admin_applications_queue_keyboard",
    "get_admin_banks_list_keyboard",
    "get_admin_main_menu_keyboard",
    "get_admin_payments_list_keyboard",
    "get_admin_product_card_keyboard",
    "get_admin_products_list_keyboard",
    "get_admin_settings_keyboard",
    "get_photo_step_keyboard",
    "get_yes_no_keyboard",
]
