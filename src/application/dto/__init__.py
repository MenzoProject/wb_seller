"""DTO (Data Transfer Objects) application-слоя.

DTO используются как валидированные объекты команд на входе сервисов —
они отделяют внешний ввод (из хендлеров бота) от доменных сущностей и
обеспечивают валидацию данных на границе слоёв через Pydantic.
"""

from src.application.dto.application_dto import (
    ApproveOrderDTO,
    AssignRequisitesDTO,
    CancelApplicationDTO,
    ConfirmReceiveDTO,
    CreateApplicationDTO,
    RejectApplicationDTO,
    RequestOrderScreenshotResendDTO,
    SubmitArticleDTO,
    SubmitOrderScreenshotDTO,
    SubmitReceiptLinkDTO,
    SubmitReviewScreenshotDTO,
)
from src.application.dto.payment_dto import MarkPaymentPaidDTO
from src.application.dto.product_dto import ProductCreateDTO, ProductUpdateDTO
from src.application.dto.requisites_dto import CreateRequisitesDTO, UpdateRequisitesDTO

__all__ = [
    "ApproveOrderDTO",
    "AssignRequisitesDTO",
    "CancelApplicationDTO",
    "ConfirmReceiveDTO",
    "CreateApplicationDTO",
    "RejectApplicationDTO",
    "RequestOrderScreenshotResendDTO",
    "SubmitArticleDTO",
    "SubmitOrderScreenshotDTO",
    "SubmitReceiptLinkDTO",
    "SubmitReviewScreenshotDTO",
    "MarkPaymentPaidDTO",
    "ProductCreateDTO",
    "ProductUpdateDTO",
    "CreateRequisitesDTO",
    "UpdateRequisitesDTO",
]
