from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.models import Subscription, SubscriptionBase
from app.database.session import SessionDep
from app.exceptions import BadRequestError, NotFoundError
from app.responses import responses

router = APIRouter(prefix="/subscriptions", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    product: SubscriptionBase, session: SessionDep
) -> Subscription:
    return ""
