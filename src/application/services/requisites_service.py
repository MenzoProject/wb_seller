"""Сервис бизнес-логики работы с платёжными реквизитами пользователя."""

from __future__ import annotations

import logging

from src.application.dto.requisites_dto import CreateRequisitesDTO, UpdateRequisitesDTO
from src.domain.entities.bank import Bank
from src.domain.entities.requisites import UserRequisites
from src.domain.exceptions.requisites_exceptions import (
    BankInactiveError,
    BankNameAlreadyExistsError,
    BankNotFoundError,
    RequisitesNotFoundError,
)
from src.infrastructure.repositories.interfaces.requisites_repository import (
    RequisitesRepository,
)

logger = logging.getLogger(__name__)


class RequisitesService:
    """Сервис, инкапсулирующий бизнес-логику управления реквизитами пользователей."""

    def __init__(self, requisites_repository: RequisitesRepository) -> None:
        """Инициализирует сервис репозиторием реквизитов и банков.

        Args:
            requisites_repository: Реализация репозитория реквизитов и банков.
        """
        self._requisites_repository = requisites_repository

    async def list_user_requisites(self, user_id: int) -> list[UserRequisites]:
        """Возвращает все сохранённые наборы реквизитов пользователя.

        Args:
            user_id: Внутренний идентификатор пользователя.

        Returns:
            Список реквизитов пользователя.
        """
        return await self._requisites_repository.list_by_user(user_id)

    async def get_default_or_first(self, user_id: int) -> UserRequisites | None:
        """Возвращает реквизиты пользователя по умолчанию либо первые из сохранённых.

        Используется при оформлении заявки, чтобы предложить пользователю
        заранее сохранённые реквизиты вместо повторного ввода данных.

        Args:
            user_id: Внутренний идентификатор пользователя.

        Returns:
            Реквизиты по умолчанию, либо первые сохранённые реквизиты, либо
            None, если у пользователя нет сохранённых реквизитов.
        """
        default_requisites = await self._requisites_repository.get_default_for_user(user_id)
        if default_requisites is not None:
            return default_requisites

        all_requisites = await self._requisites_repository.list_by_user(user_id)
        return all_requisites[0] if all_requisites else None

    async def list_banks(self) -> list[Bank]:
        """Возвращает список банков, доступных для выбора пользователем.

        Returns:
            Список активных банков.
        """
        return await self._requisites_repository.list_active_banks()

    async def list_all_banks(self) -> list[Bank]:
        """Возвращает полный справочник банков для панели администратора.

        В отличие от `list_banks`, включает и деактивированные банки, чтобы
        администратор мог видеть их и при необходимости включить обратно.

        Returns:
            Список всех банков, упорядоченный по названию.
        """
        return await self._requisites_repository.list_all_banks()

    async def create_bank(self, name: str) -> Bank:
        """Добавляет новый банк в справочник (доступное для выбора действие администратора).

        Args:
            name: Название нового банка.

        Returns:
            Созданная доменная сущность банка.

        Raises:
            BankNameAlreadyExistsError: Если банк с таким названием (без
                учёта регистра) уже существует в справочнике.
        """
        normalized_name = name.strip()
        existing_bank = await self._requisites_repository.get_bank_by_name(normalized_name)
        if existing_bank is not None:
            raise BankNameAlreadyExistsError(normalized_name)

        bank = await self._requisites_repository.create_bank(normalized_name)
        logger.info("Создан банк id=%s name=%r", bank.id, bank.name)
        return bank

    async def set_bank_active(self, bank_id: int, is_active: bool) -> Bank:
        """Включает либо отключает банк для выбора пользователями.

        Args:
            bank_id: Внутренний идентификатор банка.
            is_active: Новое значение признака доступности банка.

        Returns:
            Обновлённая доменная сущность банка.

        Raises:
            BankNotFoundError: Если банк с указанным `id` не найден.
        """
        bank = await self._requisites_repository.get_bank_by_id(bank_id)
        if bank is None:
            raise BankNotFoundError(bank_id)

        updated_bank = await self._requisites_repository.set_bank_active(bank_id, is_active)
        logger.info(
            "Банк id=%s (%s) переключён в состояние is_active=%s",
            bank_id,
            bank.name,
            is_active,
        )
        return updated_bank

    async def _ensure_bank_active(self, bank_id: int) -> None:
        """Проверяет, что указанный банк существует и доступен для выбора.

        Args:
            bank_id: Внутренний идентификатор проверяемого банка.

        Raises:
            BankNotFoundError: Если банк с указанным `id` не найден.
            BankInactiveError: Если банк деактивирован администратором.
        """
        bank = await self._requisites_repository.get_bank_by_id(bank_id)
        if bank is None:
            raise BankNotFoundError(bank_id)
        if not bank.is_active:
            raise BankInactiveError(bank_id)

    async def create_requisites(self, dto: CreateRequisitesDTO) -> UserRequisites:
        """Создаёт новый набор реквизитов пользователя.

        Если это первый набор реквизитов пользователя либо явно запрошено
        использование по умолчанию, он автоматически становится реквизитами
        по умолчанию (с одновременным снятием этого признака с остальных).

        Args:
            dto: Валидированные данные нового набора реквизитов.

        Returns:
            Созданная доменная сущность реквизитов.

        Raises:
            BankNotFoundError: Если банк с указанным `id` не найден.
            BankInactiveError: Если банк деактивирован администратором.
            InvalidRequisitesDataError: Если ФИО или телефон не прошли валидацию.
        """
        await self._ensure_bank_active(dto.bank_id)

        existing_requisites = await self._requisites_repository.list_by_user(dto.user_id)
        should_be_default = dto.is_default or not existing_requisites

        if should_be_default:
            await self._requisites_repository.unset_default_for_user(dto.user_id)

        requisites = UserRequisites(
            id=None,
            user_id=dto.user_id,
            full_name=dto.full_name,
            phone=dto.phone,
            bank_id=dto.bank_id,
            is_default=should_be_default,
        )
        created_requisites = await self._requisites_repository.create(requisites)
        logger.info(
            "Созданы реквизиты id=%s для пользователя id=%s",
            created_requisites.id,
            dto.user_id,
        )
        return created_requisites

    async def update_requisites(self, dto: UpdateRequisitesDTO) -> UserRequisites:
        """Обновляет данные существующего набора реквизитов пользователя.

        Args:
            dto: Валидированные данные для обновления реквизитов.

        Returns:
            Обновлённая доменная сущность реквизитов.

        Raises:
            RequisitesNotFoundError: Если реквизиты с указанным `id` не найдены
                либо не принадлежат указанному пользователю.
            BankNotFoundError: Если банк с указанным `id` не найден.
            BankInactiveError: Если банк деактивирован администратором.
            InvalidRequisitesDataError: Если ФИО или телефон не прошли валидацию.
        """
        requisites = await self._requisites_repository.get_by_id(dto.requisites_id)
        if requisites is None or requisites.user_id != dto.user_id:
            raise RequisitesNotFoundError(dto.requisites_id)

        await self._ensure_bank_active(dto.bank_id)

        requisites.full_name = dto.full_name
        requisites.phone = dto.phone
        requisites.bank_id = dto.bank_id

        return await self._requisites_repository.update(requisites)

    async def delete_requisites(self, requisites_id: int, user_id: int) -> None:
        """Удаляет набор реквизитов пользователя.

        Args:
            requisites_id: Внутренний идентификатор удаляемых реквизитов.
            user_id: Внутренний идентификатор пользователя (для проверки прав).

        Raises:
            RequisitesNotFoundError: Если реквизиты не найдены либо не
                принадлежат указанному пользователю.
        """
        requisites = await self._requisites_repository.get_by_id(requisites_id)
        if requisites is None or requisites.user_id != user_id:
            raise RequisitesNotFoundError(requisites_id)

        await self._requisites_repository.delete(requisites_id)
        logger.info("Реквизиты id=%s пользователя id=%s удалены", requisites_id, user_id)

    async def set_default(self, requisites_id: int, user_id: int) -> UserRequisites:
        """Назначает указанный набор реквизитов используемым по умолчанию.

        Args:
            requisites_id: Внутренний идентификатор реквизитов.
            user_id: Внутренний идентификатор пользователя (для проверки прав).

        Returns:
            Обновлённая доменная сущность реквизитов с is_default=True.

        Raises:
            RequisitesNotFoundError: Если реквизиты не найдены либо не
                принадлежат указанному пользователю.
        """
        requisites = await self._requisites_repository.get_by_id(requisites_id)
        if requisites is None or requisites.user_id != user_id:
            raise RequisitesNotFoundError(requisites_id)

        await self._requisites_repository.unset_default_for_user(
            user_id, exclude_id=requisites_id
        )
        requisites.make_default()
        return await self._requisites_repository.update(requisites)
