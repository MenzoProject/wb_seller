"""Клавиатуры пользовательского бота."""

from src.bot.keyboards.user.application_flow import (
    CancelApplicationCallback,
    ConfirmReceiveCallback,
    get_cancel_application_keyboard,
    get_confirm_receive_keyboard,
)
from src.bot.keyboards.user.applications import (
    ResumeApplicationCallback,
    get_resume_actions_keyboard,
)
from src.bot.keyboards.user.catalog import (
    CatalogCallback,
    get_catalog_list_keyboard,
    get_product_card_keyboard,
)
from src.bot.keyboards.user.main_menu import (
    MENU_BUTTON_TEXTS,
    MENU_CATALOG,
    MENU_INSTRUCTION,
    MENU_MY_APPLICATIONS,
    MENU_REQUISITES,
    MENU_SUPPORT,
    get_main_menu_keyboard,
)
from src.bot.keyboards.user.requisites import (
    ApplicationRequisitesCallback,
    BankSelectCallback,
    RequisitesCallback,
    get_application_requisites_keyboard,
    get_bank_selection_keyboard,
    get_requisites_management_keyboard,
)

__all__ = [
    "ApplicationRequisitesCallback",
    "BankSelectCallback",
    "CancelApplicationCallback",
    "CatalogCallback",
    "ConfirmReceiveCallback",
    "MENU_BUTTON_TEXTS",
    "MENU_CATALOG",
    "MENU_INSTRUCTION",
    "MENU_MY_APPLICATIONS",
    "MENU_REQUISITES",
    "MENU_SUPPORT",
    "RequisitesCallback",
    "ResumeApplicationCallback",
    "get_application_requisites_keyboard",
    "get_bank_selection_keyboard",
    "get_cancel_application_keyboard",
    "get_catalog_list_keyboard",
    "get_confirm_receive_keyboard",
    "get_main_menu_keyboard",
    "get_product_card_keyboard",
    "get_requisites_management_keyboard",
    "get_resume_actions_keyboard",
]
