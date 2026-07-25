"""Сервис бизнес-логики работы с товарами каталога."""

from __future__ import annotations

import logging

from src.application.dto.product_dto import ProductCreateDTO, ProductUpdateDTO
from src.domain.entities.log import Log
from src.domain.entities.product import Product
from src.domain.exceptions.product_exceptions import ProductNotFoundError, ProductValidationError
from src.infrastructure.repositories.interfaces.log_repository import LogRepository
from src.infrastructure.repositories.interfaces.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class ProductService:
    """Сервис, инкапсулирующий бизнес-логику управления товарами каталога."""

    def __init__(
        self, product_repository: ProductRepository, log_repository: LogRepository
    ) -> None:
        """Инициализирует сервис репозиториями товаров и журнала аудита.

        Args:
            product_repository: Реализация репозитория товаров.
            log_repository: Реализация репозитория журнала аудита.
        """
        self._product_repository = product_repository
        self._log_repository = log_repository

    async def get_product(self, product_id: int) -> Product:
        """Возвращает товар по внутреннему идентификатору.

        Args:
            product_id: Внутренний идентификатор товара.

        Returns:
            Найденная доменная сущность товара.

        Raises:
            ProductNotFoundError: Если товар с указанным `id` не найден.
        """
        product = await self._product_repository.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        return product

    async def list_catalog(self, limit: int = 20, offset: int = 0) -> list[Product]:
        """Возвращает страницу товаров, доступных для оформления заявки.

        Args:
            limit: Максимальное количество товаров в результате.
            offset: Количество товаров, которые нужно пропустить.

        Returns:
            Список товаров, доступных пользователю в каталоге.
        """
        return await self._product_repository.list_available(limit=limit, offset=offset)

    async def list_admin_products(
        self,
        *,
        include_hidden: bool = True,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Product]:
        """Возвращает страницу товаров для панели администратора.

        Args:
            include_hidden: Включать ли в выборку скрытые товары.
            include_deleted: Включать ли в выборку мягко удалённые товары.
            limit: Максимальное количество товаров в результате.
            offset: Количество товаров, которые нужно пропустить.

        Returns:
            Список товаров для отображения администратору.
        """
        return await self._product_repository.list_all(
            include_hidden=include_hidden,
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
        )

    async def create_product(self, dto: ProductCreateDTO) -> Product:
        """Создаёт новый товар в каталоге.

        Args:
            dto: Валидированные данные нового товара.

        Returns:
            Созданная доменная сущность товара.
        """
        product = Product(
            id=None,
            title=dto.title,
            description=dto.description,
            price=dto.price,
            cashback_amount=dto.cashback_amount,
            payout_days=dto.payout_days,
            review_required=dto.review_required,
            receipt_required=dto.receipt_required,
            product_url=dto.product_url,
            instruction_text=dto.instruction_text,
            available_slots=dto.available_slots,
            photo_file_ids=list(dto.photo_file_ids),
        )
        created_product = await self._product_repository.create(product)

        await self._log_repository.create(
            Log(
                id=None,
                action="product_created",
                entity_type="Product",
                admin_id=dto.admin_id,
                entity_id=created_product.id,
                payload={"title": created_product.title},
            )
        )
        logger.info(
            "Товар id=%s создан администратором id=%s", created_product.id, dto.admin_id
        )
        return created_product

    async def update_product(self, dto: ProductUpdateDTO) -> Product:
        """Обновляет все редактируемые поля существующего товара.

        Args:
            dto: Валидированные данные для обновления товара.

        Returns:
            Обновлённая доменная сущность товара.

        Raises:
            ProductNotFoundError: Если товар с указанным `id` не найден.
        """
        product = await self.get_product(dto.product_id)

        product.title = dto.title
        product.description = dto.description
        product.price = dto.price
        product.cashback_amount = dto.cashback_amount
        product.payout_days = dto.payout_days
        product.review_required = dto.review_required
        product.receipt_required = dto.receipt_required
        product.product_url = dto.product_url
        product.instruction_text = dto.instruction_text
        product.available_slots = dto.available_slots
        product.photo_file_ids = list(dto.photo_file_ids)

        updated_product = await self._product_repository.update(product)

        await self._log_repository.create(
            Log(
                id=None,
                action="product_updated",
                entity_type="Product",
                admin_id=dto.admin_id,
                entity_id=updated_product.id,
            )
        )
        logger.info(
            "Товар id=%s обновлён администратором id=%s", updated_product.id, dto.admin_id
        )
        return updated_product

    async def hide_product(self, product_id: int, admin_id: int) -> Product:
        """Скрывает товар из каталога, не удаляя его безвозвратно.

        Args:
            product_id: Внутренний идентификатор товара.
            admin_id: Внутренний идентификатор администратора, скрывшего товар.

        Returns:
            Обновлённая доменная сущность товара.

        Raises:
            ProductNotFoundError: Если товар с указанным `id` не найден.
        """
        product = await self.get_product(product_id)
        product.hide()
        updated_product = await self._product_repository.update(product)

        await self._log_repository.create(
            Log(
                id=None,
                action="product_hidden",
                entity_type="Product",
                admin_id=admin_id,
                entity_id=product_id,
            )
        )
        return updated_product

    async def unhide_product(self, product_id: int, admin_id: int) -> Product:
        """Возвращает ранее скрытый товар в каталог.

        Args:
            product_id: Внутренний идентификатор товара.
            admin_id: Внутренний идентификатор администратора, вернувшего товар.

        Returns:
            Обновлённая доменная сущность товара.

        Raises:
            ProductNotFoundError: Если товар с указанным `id` не найден.
        """
        product = await self.get_product(product_id)
        product.unhide()
        updated_product = await self._product_repository.update(product)

        await self._log_repository.create(
            Log(
                id=None,
                action="product_unhidden",
                entity_type="Product",
                admin_id=admin_id,
                entity_id=product_id,
            )
        )
        return updated_product

    async def delete_product(self, product_id: int, admin_id: int) -> Product:
        """Помечает товар как удалённый (мягкое удаление).

        Args:
            product_id: Внутренний идентификатор товара.
            admin_id: Внутренний идентификатор администратора, удалившего товар.

        Returns:
            Обновлённая доменная сущность товара.

        Raises:
            ProductNotFoundError: Если товар с указанным `id` не найден.
        """
        product = await self.get_product(product_id)
        product.mark_deleted()
        updated_product = await self._product_repository.update(product)

        await self._log_repository.create(
            Log(
                id=None,
                action="product_deleted",
                entity_type="Product",
                admin_id=admin_id,
                entity_id=product_id,
            )
        )
        logger.info("Товар id=%s удалён администратором id=%s", product_id, admin_id)
        return updated_product

    async def change_available_slots(
        self, product_id: int, new_slots: int, admin_id: int
    ) -> Product:
        """Изменяет количество доступных для оформления заявок товара.

        Args:
            product_id: Внутренний идентификатор товара.
            new_slots: Новое количество доступных слотов заявок.
            admin_id: Внутренний идентификатор администратора, изменившего остаток.

        Returns:
            Обновлённая доменная сущность товара.

        Raises:
            ProductNotFoundError: Если товар с указанным `id` не найден.
            ProductValidationError: Если новое количество слотов отрицательное.
        """
        product = await self.get_product(product_id)
        if new_slots < 0:
            raise ProductValidationError("Количество доступных заявок не может быть отрицательным")
        previous_slots = product.available_slots
        product.available_slots = new_slots
        updated_product = await self._product_repository.update(product)

        await self._log_repository.create(
            Log(
                id=None,
                action="product_slots_changed",
                entity_type="Product",
                admin_id=admin_id,
                entity_id=product_id,
                payload={"previous_slots": previous_slots, "new_slots": new_slots},
            )
        )
        return updated_product

    async def count_available(self) -> int:
        """Возвращает количество товаров, доступных для оформления заявки.

        Returns:
            Количество товаров, доступных в каталоге.
        """
        return await self._product_repository.count_available()
