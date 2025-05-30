from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from sqlmodel import select

from app.database.models import (
    Account,
    Subscription,
    SubscriptionCreate,
    SubscriptionProduct,
    SubscriptionResponse,
    SubscriptionWithAccountAndCustomFields,
)
from app.database.session import SessionDep
from app.exceptions import BadRequestError, NotFoundError
from app.responses import responses

router = APIRouter(prefix="/subscriptions", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription: SubscriptionCreate, session: SessionDep
) -> SubscriptionResponse:

    product_ids = [product.product_id for product in subscription.products]
    if len(product_ids) != len(set(product_ids)):
        raise BadRequestError(
            detail="A product cannot be repeated in the same subscription."
        )

    if not session.get(Account, subscription.account_id):
        raise NotFoundError(detail="Account not found")

    subscription_data = subscription.model_dump(exclude={"products"})
    subscription_db = Subscription(**subscription_data)

    session.add(subscription_db)

    products = [
        SubscriptionProduct(
            product_id=product.product_id,
            quantity=product.quantity,
        )
        for product in subscription.products
    ]

    subscription_db.products = products

    session.commit()
    session.refresh(subscription_db)
    return subscription_db


@router.get("/")
def read_subscriptions(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    state: Literal[  # pylint: disable=redefined-outer-name
        "ACTIVE", "CANCELLED", "PAUSED", "ALL"
    ] = "ALL",
) -> list[SubscriptionResponse]:

    query = select(Subscription).offset(offset).limit(limit)

    if state != "ALL":

        query = select(Subscription).filter_by(state=state).offset(offset).limit(limit)

    subscriptions = session.exec(query).all()

    return subscriptions


@router.get("/{subscription_id}")
def read_subscription(
    subscription_id: int, session: SessionDep
) -> SubscriptionWithAccountAndCustomFields:
    subscription = session.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError()
    return subscription
