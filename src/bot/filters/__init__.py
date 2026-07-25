"""Кастомные фильтры aiogram."""

from src.bot.filters.admin_filter import IsAdminFilter
from src.bot.filters.application_status_filter import ApplicationStatusFilter

__all__ = ["ApplicationStatusFilter", "IsAdminFilter"]
