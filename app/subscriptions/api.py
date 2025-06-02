from datetime import date, datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.models import (
    Account,
    State,
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
        raise BadRequestError(detail="Account not exists")

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

    try:

        session.commit()
        session.refresh(subscription_db)
        return subscription_db

    except IntegrityError as exc:
        raise BadRequestError(detail="External id already exists") from exc


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


@router.get("/external/{external_id}")
def read_subscription_by_external_id(
    external_id: str, session: SessionDep
) -> SubscriptionWithAccountAndCustomFields:
    subscription = session.exec(
        select(Subscription).filter_by(external_id=external_id)
    ).one_or_none()
    if not subscription:
        raise NotFoundError()
    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_200_OK)
def cancel_subscription(
    subscription_id: int,
    session: SessionDep,
    end_date: Annotated[date, Query(ge=datetime.now(timezone.utc).date())] = None,
) -> SubscriptionResponse:
    subscription = session.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError()

    if subscription.state == State.CANCELLED:
        raise BadRequestError(detail="The subscription is cancelled")

    today = datetime.now(timezone.utc).date()

    state = State.ACTIVE
    if not end_date or end_date == today:
        state = State.CANCELLED

    subscription.state = state
    subscription.end_date = end_date
    session.commit()
    session.refresh(subscription)
    return subscription


@router.put("/{subscription_id}/billing_day")
def update_billing_day(
    subscription_id: int, day: Annotated[int, Query(ge=0, le=31)], session: SessionDep
) -> SubscriptionWithAccountAndCustomFields:
    subscription = session.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError()

    if subscription.state == State.CANCELLED:
        raise BadRequestError(detail="The subscription is cancelled")

    subscription.billing_day = day

    session.commit()
    session.refresh(subscription)
    return subscription


@router.put("/{subscription_id}/pause")
def pause_subscription(
    subscription_id: int,
    session: SessionDep,
    resume: Annotated[date, Query(ge=datetime.now(timezone.utc).date())] = None,
) -> SubscriptionWithAccountAndCustomFields:
    subscription = session.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError()

    if subscription.state == State.CANCELLED:
        raise BadRequestError(detail="The subscription is cancelled")

    today = datetime.now(timezone.utc).date()

    state = State.ACTIVE
    if not resume or resume > today:
        state = State.PAUSED

    subscription.state = state
    subscription.resume_date = resume

    session.commit()
    session.refresh(subscription)
    return subscription
