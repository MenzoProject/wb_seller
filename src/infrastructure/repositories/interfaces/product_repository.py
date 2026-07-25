"""Интерфейс репозитория для работы с товарами каталога."""

from __future__ import annotations

from typing import Protocol

from src.domain.entities.product import Product


class ProductRepository(Protocol):
    """Абстракция доступа к данным товаров, не зависящая от СУБД."""

    async def get_by_id(self, product_id: int) -> Product | None:
        """Возвращает товар по идентификатору вместе со списком фотографий.

        Args:
            product_id: Внутренний идентификатор товара.

        Returns:
            Найденный товар либо None, если товар не существует.
        """

    async def list_available(self, limit: int = 20, offset: int = 0) -> list[Product]:
        """Возвращает страницу товаров, доступных для оформления заявки.

        В выборку попадают только товары, которые не скрыты, не удалены и
        имеют хотя бы один свободный слот заявки.

        Args:
            limit: Максимальное количество товаров в результате.
            offset: Количество товаров, которые нужно пропустить.

        Returns:
            Список доступных товаров, упорядоченный по дате создания (новые вначале).
        """

    async def list_all(
        self, *, include_hidden: bool = True, include_deleted: bool = False,
        limit: int = 50, offset: int = 0,
    ) -> list[Product]:
        """Возвращает страницу товаров для панели администратора.

        Args:
            include_hidden: Включать ли в выборку скрытые товары.
            include_deleted: Включать ли в выборку мягко удалённые товары.
            limit: Максимальное количество товаров в результате.
            offset: Количество товаров, которые нужно пропустить.

        Returns:
            Список товаров, упорядоченный по дате создания (новые вначале).
        """

    async def create(self, product: Product) -> Product:
        """Создаёт новый товар вместе со связанными фотографиями.

        Args:
            product: Доменная сущность товара без присвоенного `id`.

        Returns:
            Созданный товар с присвоенным внутренним идентификатором.
        """

    async def update(self, product: Product) -> Product:
        """Обновляет данные существующего товара и полностью заменяет его фотографии.

        Args:
            product: Доменная сущность товара с заполненным `id`.

        Returns:
            Обновлённая сущность товара.

        Raises:
            EntityNotFoundError: Если товар с указанным `id` не найден.
        """

    async def count_available(self) -> int:
        """Возвращает количество товаров, доступных для оформления заявки.

        Returns:
            Количество товаров, не скрытых, не удалённых и с available_slots > 0.
        """
