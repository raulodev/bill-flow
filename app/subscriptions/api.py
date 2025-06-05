from datetime import date, datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.deps import CurrentTenant, SessionDep
from app.database.models import (
    Account,
    State,
    Subscription,
    SubscriptionCreate,
    SubscriptionProduct,
    SubscriptionResponse,
    SubscriptionWithAccountAndCustomFields,
)
from app.exceptions import BadRequestError, NotFoundError
from app.responses import responses

router = APIRouter(prefix="/subscriptions", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription: SubscriptionCreate, session: SessionDep, current_tenant: CurrentTenant
) -> SubscriptionResponse:

    product_ids = [product.product_id for product in subscription.products]
    if len(product_ids) != len(set(product_ids)):
        raise BadRequestError(
            detail="A product cannot be repeated in the same subscription"
        )

    if (subscription.trial_time_unit and not subscription.trial_time) or (
        subscription.trial_time and not subscription.trial_time_unit
    ):
        raise BadRequestError(
            detail="Both trial_time and trial_time_unit are required if one is provided"
        )

    if not session.get(Account, subscription.account_id):
        raise BadRequestError(detail="Account not exists")

    products = [
        SubscriptionProduct(
            product_id=product.product_id,
            quantity=product.quantity,
        )
        for product in subscription.products
    ]

    delattr(subscription, "products")

    subscription_db = Subscription.model_validate(
        subscription, update={"tenant_id": current_tenant.id}
    )
    session.add(subscription_db)
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
    current_tenant: CurrentTenant,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    state: Literal[  # pylint: disable=redefined-outer-name
        "ACTIVE", "CANCELLED", "PAUSED", "ALL"
    ] = "ALL",
) -> list[SubscriptionResponse]:

    query = select(Subscription).offset(offset).limit(limit)

    if state != "ALL":

        query = (
            select(Subscription)
            .where(
                Subscription.tenant_id == current_tenant.id, Subscription.state == state
            )
            .offset(offset)
            .limit(limit)
        )

    subscriptions = session.exec(query).all()

    return subscriptions


@router.get("/{subscription_id}")
def read_subscription(
    subscription_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> SubscriptionWithAccountAndCustomFields:
    subscription = session.exec(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.tenant_id == current_tenant.id,
        )
    ).first()
    if not subscription:
        raise NotFoundError()
    return subscription


@router.get("/external/{external_id}")
def read_subscription_by_external_id(
    external_id: str,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> SubscriptionWithAccountAndCustomFields:
    subscription = session.exec(
        select(Subscription).where(
            Subscription.external_id == external_id,
            Subscription.tenant_id == current_tenant.id,
        )
    ).first()
    if not subscription:
        raise NotFoundError()
    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_200_OK)
def cancel_subscription(
    subscription_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
    end_date: Annotated[date, Query(ge=datetime.now(timezone.utc).date())] = None,
) -> SubscriptionResponse:

    subscription = session.exec(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.tenant_id == current_tenant.id,
        )
    ).first()
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
    subscription_id: int,
    day: Annotated[int, Query(ge=0, le=31)],
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> SubscriptionWithAccountAndCustomFields:

    subscription = session.exec(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.tenant_id == current_tenant.id,
        )
    ).first()
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
    current_tenant: CurrentTenant,
    resume: Annotated[date, Query(ge=datetime.now(timezone.utc).date())] = None,
) -> SubscriptionWithAccountAndCustomFields:
    subscription = session.exec(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.tenant_id == current_tenant.id,
        )
    ).first()
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
