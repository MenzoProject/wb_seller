"""Исключения доменного слоя, связанные с реквизитами пользователей и банками."""

from __future__ import annotations

from src.domain.exceptions.base import DomainError, EntityNotFoundError


class RequisitesNotFoundError(EntityNotFoundError):
    """Набор реквизитов с указанным идентификатором не найден."""

    def __init__(self, requisites_id: int) -> None:
        """Инициализирует исключение отсутствия реквизитов.

        Args:
            requisites_id: Идентификатор запрашиваемых реквизитов.
        """
        super().__init__("Реквизиты", requisites_id)
        self.requisites_id = requisites_id


class InvalidRequisitesDataError(DomainError):
    """Данные реквизитов не прошли валидацию (пустое ФИО, некорректный телефон и т.д.)."""

    def __init__(self, message: str) -> None:
        """Инициализирует исключение валидации данных реквизитов.

        Args:
            message: Описание конкретной ошибки валидации.
        """
        super().__init__(message)


class BankNotFoundError(EntityNotFoundError):
    """Банк с указанным идентификатором не найден."""

    def __init__(self, bank_id: int) -> None:
        """Инициализирует исключение отсутствия банка.

        Args:
            bank_id: Идентификатор запрашиваемого банка.
        """
        super().__init__("Банк", bank_id)
        self.bank_id = bank_id


class BankInactiveError(DomainError):
    """Банк недоступен для выбора (деактивирован администратором)."""

    def __init__(self, bank_id: int) -> None:
        """Инициализирует исключение недоступности банка.

        Args:
            bank_id: Идентификатор недоступного банка.
        """
        super().__init__(f"Банк id={bank_id} недоступен для выбора")
        self.bank_id = bank_id


class BankNameAlreadyExistsError(DomainError):
    """Банк с таким названием уже существует в справочнике."""

    def __init__(self, name: str) -> None:
        """Инициализирует исключение дублирования названия банка.

        Args:
            name: Название банка, уже присутствующее в справочнике.
        """
        super().__init__(f"Банк с названием «{name}» уже существует")
        self.name = name
