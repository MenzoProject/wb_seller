"""FSM-состояния пользовательского и административного ботов."""

from src.bot.states.admin_states import (
    ApplicationReviewStates,
    ProductFormStates,
    ProductSlotsChangeStates,
)
from src.bot.states.requisites_states import RequisitesStates
from src.bot.states.user_states import ApplicationFlowStates

__all__ = [
    "ApplicationFlowStates",
    "ApplicationReviewStates",
    "ProductFormStates",
    "ProductSlotsChangeStates",
    "RequisitesStates",
]
