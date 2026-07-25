"""Middlewares aiogram, применяемые к обработке апдейтов бота."""

from src.bot.middlewares.admin_access_middleware import AdminAccessMiddleware
from src.bot.middlewares.admin_registration_middleware import AdminRegistrationMiddleware
from src.bot.middlewares.db_session_middleware import DbSessionMiddleware
from src.bot.middlewares.logging_middleware import LoggingMiddleware
from src.bot.middlewares.services_middleware import ServicesMiddleware
from src.bot.middlewares.throttling_middleware import ThrottlingMiddleware
from src.bot.middlewares.user_registration_middleware import UserRegistrationMiddleware

__all__ = [
    "AdminAccessMiddleware",
    "AdminRegistrationMiddleware",
    "DbSessionMiddleware",
    "LoggingMiddleware",
    "ServicesMiddleware",
    "ThrottlingMiddleware",
    "UserRegistrationMiddleware",
]
