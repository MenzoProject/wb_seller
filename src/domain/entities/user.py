"""Доменная сущность пользователя (реселлера)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class User:
    """Пользователь бота — реселлер Wildberries или Ozon.

    Attributes:
        id: Внутренний идентификатор пользователя. `None` для ещё не
            сохранённой в базе данных сущности.
        telegram_id: Уникальный идентификатор пользователя в Telegram.
        full_name: Полное имя пользователя.
        username: Username пользователя в Telegram без символа '@'.
        phone: Номер телефона пользователя, если был предоставлен.
        is_blocked: Признак блокировки пользователя администратором.
        created_at: Дата и время регистрации пользователя.
        updated_at: Дата и время последнего обновления данных пользователя.
    """

    id: int | None
    telegram_id: int
    full_name: str
    username: str | None = None
    phone: str | None = None
    is_blocked: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def display_name(self) -> str:
        """Возвращает наиболее подходящее для отображения имя пользователя.

        Returns:
            Username с префиксом '@', если он указан, иначе полное имя.
        """
        return f"@{self.username}" if self.username else self.full_name

    @property
    def mention(self) -> str:
        """Возвращает строку для упоминания пользователя в сообщениях администратору.

        Returns:
            Строка вида 'Имя (@username, ID: 123456789)' либо
            'Имя (ID: 123456789)', если username отсутствует.
        """
        username_part = f", @{self.username}" if self.username else ""
        return f"{self.full_name} (ID: {self.telegram_id}{username_part})"

    def block(self) -> None:
        """Помечает пользователя как заблокированного."""
        self.is_blocked = True

    def unblock(self) -> None:
        """Снимает блокировку с пользователя."""
        self.is_blocked = False
