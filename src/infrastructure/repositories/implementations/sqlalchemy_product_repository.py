"""Реализация репозитория товаров на основе SQLAlchemy 2.x Async."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.product import Product
from src.domain.exceptions.base import EntityNotFoundError
from src.infrastructure.database.models.product import Product as ProductModel
from src.infrastructure.database.models.product_photo import ProductPhoto as ProductPhotoModel


class SQLAlchemyProductRepository:
    """Реализация `ProductRepository` поверх асинхронной сессии SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий переданной сессией базы данных.

        Args:
            session: Активная асинхронная сессия SQLAlchemy, привязанная
                к текущей единице работы (transaction/unit of work).
        """
        self._session = session

    @staticmethod
    def _to_entity(model: ProductModel) -> Product:
        """Преобразует ORM-модель товара в доменную сущность.

        Args:
            model: ORM-модель товара с предварительно загруженными фотографиями.

        Returns:
            Доменная сущность товара со списком file_id фотографий.
        """
        return Product(
            id=model.id,
            title=model.title,
            description=model.description,
            price=model.price,
            cashback_amount=model.cashback_amount,
            payout_days=model.payout_days,
            review_required=model.review_required,
            receipt_required=model.receipt_required,
            product_url=model.product_url,
            instruction_text=model.instruction_text,
            available_slots=model.available_slots,
            is_hidden=model.is_hidden,
            is_deleted=model.is_deleted,
            photo_file_ids=[photo.file_id for photo in model.photos],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, product_id: int) -> Product | None:
        """Возвращает товар по идентификатору вместе со списком фотографий."""
        statement = (
            select(ProductModel)
            .options(selectinload(ProductModel.photos))
            .where(ProductModel.id == product_id)
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def list_available(self, limit: int = 20, offset: int = 0) -> list[Product]:
        """Возвращает страницу товаров, доступных для оформления заявки."""
        statement = (
            select(ProductModel)
            .options(selectinload(ProductModel.photos))
            .where(
                ProductModel.is_hidden.is_(False),
                ProductModel.is_deleted.is_(False),
                ProductModel.available_slots > 0,
            )
            .order_by(ProductModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(statement)
        return [self._to_entity(model) for model in result.scalars().all()]

    async def list_all(
        self,
        *,
        include_hidden: bool = True,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Product]:
        """Возвращает страницу товаров для панели администратора."""
        statement = select(ProductModel).options(selectinload(ProductModel.photos))

        if not include_hidden:
            statement = statement.where(ProductModel.is_hidden.is_(False))
        if not include_deleted:
            statement = statement.where(ProductModel.is_deleted.is_(False))

        statement = (
            statement.order_by(ProductModel.created_at.desc()).limit(limit).offset(offset)
        )

        result = await self._session.execute(statement)
        return [self._to_entity(model) for model in result.scalars().all()]

    async def create(self, product: Product) -> Product:
        """Создаёт новый товар вместе со связанными фотографиями."""
        model = ProductModel(
            title=product.title,
            description=product.description,
            price=product.price,
            cashback_amount=product.cashback_amount,
            payout_days=product.payout_days,
            review_required=product.review_required,
            receipt_required=product.receipt_required,
            product_url=product.product_url,
            instruction_text=product.instruction_text,
            available_slots=product.available_slots,
            is_hidden=product.is_hidden,
            is_deleted=product.is_deleted,
            photos=[
                ProductPhotoModel(file_id=file_id, position=position)
                for position, file_id in enumerate(product.photo_file_ids)
            ],
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model, attribute_names=["photos"])
        return self._to_entity(model)

    async def update(self, product: Product) -> Product:
        """Обновляет данные существующего товара и полностью заменяет его фотографии."""
        statement = (
            select(ProductModel)
            .options(selectinload(ProductModel.photos))
            .where(ProductModel.id == product.id)
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            raise EntityNotFoundError("Товар", product.id if product.id is not None else 0)

        model.title = product.title
        model.description = product.description
        model.price = product.price
        model.cashback_amount = product.cashback_amount
        model.payout_days = product.payout_days
        model.review_required = product.review_required
        model.receipt_required = product.receipt_required
        model.product_url = product.product_url
        model.instruction_text = product.instruction_text
        model.available_slots = product.available_slots
        model.is_hidden = product.is_hidden
        model.is_deleted = product.is_deleted

        model.photos.clear()
        model.photos.extend(
            ProductPhotoModel(file_id=file_id, position=position)
            for position, file_id in enumerate(product.photo_file_ids)
        )

        await self._session.flush()
        await self._session.refresh(model, attribute_names=["photos"])
        return self._to_entity(model)

    async def count_available(self) -> int:
        """Возвращает количество товаров, доступных для оформления заявки."""
        statement = (
            select(func.count())
            .select_from(ProductModel)
            .where(
                ProductModel.is_hidden.is_(False),
                ProductModel.is_deleted.is_(False),
                ProductModel.available_slots > 0,
            )
        )
        result = await self._session.execute(statement)
        return result.scalar_one()
