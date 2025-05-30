from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.models import (
    Subscription,
    SubscriptionCreate,
    SubscriptionProduct,
)
from app.database.session import SessionDep
from app.exceptions import BadRequestError, NotFoundError
from app.responses import responses

router = APIRouter(prefix="/subscriptions", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_subscription(subscription: SubscriptionCreate, session: SessionDep):

    product_ids = [product.product_id for product in subscription.products]
    if len(product_ids) != len(set(product_ids)):
        raise BadRequestError(
            detail="A product cannot be repeated in the same subscription."
        )

    subscription_data = subscription.model_dump(exclude={"products"})
    subscription_db = Subscription(**subscription_data)

    session.add(subscription_db)

    product_entries = [
        SubscriptionProduct(
            product_id=product.product_id,
            quantity=product.quantity,
        )
        for product in subscription.products
    ]

    subscription_db.products = product_entries

    try:
        session.commit()
        session.refresh(subscription_db)
        return subscription_db
    except IntegrityError as exc:
        raise BadRequestError(
            detail="A product cannot be repeated in the same subscription"
        ) from exc
