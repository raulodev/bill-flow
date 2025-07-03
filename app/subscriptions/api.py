from datetime import date, datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.deps import CurrentTenant, SessionDep
from app.database.models import (
    Account,
    Product,
    State,
    Subscription,
    SubscriptionCreate,
    SubscriptionProduct,
    SubscriptionPublic,
    SubscriptionPublicWithAccountAndCustomFields,
    TrialTimeUnit,
    UpdateBillingDay,
)
from app.exceptions import BadRequestError, NotFoundError
from app.logging import log_operation
from app.responses import responses
from app.subscriptions.billing_day import get_billing_day
from app.subscriptions.phases import create_phases

router = APIRouter(prefix="/subscriptions", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription: SubscriptionCreate, session: SessionDep, current_tenant: CurrentTenant
) -> SubscriptionPublic:

    log_operation(
        operation="CREATE",
        model="Subscription",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=subscription.model_dump(),
    )

    product_ids = [product.product_id for product in subscription.products]

    if len(product_ids) != len(set(product_ids)):

        log_operation(
            operation="CREATE",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail="A product cannot be repeated in the same subscription",
        )

        raise BadRequestError(
            detail="A product cannot be repeated in the same subscription"
        )

    if (
        subscription.start_date
        and subscription.end_date
        and subscription.end_date <= subscription.start_date
    ):

        log_operation(
            operation="CREATE",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail="The end date cannot be less than or equal to the start date",
        )

        raise BadRequestError(
            detail="The end date cannot be less than or equal to the start date"
        )

    if (
        subscription.trial_time_unit not in (TrialTimeUnit.UNLIMITED, None)
        and not subscription.trial_time
    ):

        log_operation(
            operation="CREATE",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail="trial_time is required if trial_time_unit is provided",
        )

        raise BadRequestError(
            detail="trial_time is required if trial_time_unit is provided"
        )

    if not session.exec(
        select(Account).where(
            Account.id == subscription.account_id,
            Account.tenant_id == current_tenant.id,
        )
    ).first():

        log_operation(
            operation="CREATE",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"account id {subscription.account_id} not found",
        )

        raise BadRequestError(detail="Account not exists")

    for product in subscription.products:

        if not session.exec(
            select(Product).where(
                Product.id == product.product_id,
                Product.tenant_id == current_tenant.id,
            )
        ).first():

            log_operation(
                operation="CREATE",
                model="Subscription",
                status="FAILED",
                tenant_id=current_tenant.id,
                detail=f"product id {product.product_id} not found",
            )
            raise BadRequestError(
                detail=f"Product with id {product.product_id} not exists"
            )

    products = [
        SubscriptionProduct(
            product_id=product.product_id,
            quantity=product.quantity,
            tenant_id=current_tenant.id,
        )
        for product in subscription.products
    ]

    delattr(subscription, "products")

    subscription_db = Subscription.model_validate(
        subscription, update={"tenant_id": current_tenant.id}
    )
    session.add(subscription_db)

    subscription_db.products = products

    phases, billing_day = create_phases(
        subscription_db.trial_time_unit, subscription_db.trial_time, subscription_db
    )

    subscription_db.phases = phases
    subscription_db.billing_day = billing_day

    log_operation(
        operation="CREATE",
        model="Subscription",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"phases: {phases}",
    )

    try:
        session.commit()
        session.refresh(subscription_db)

        log_operation(
            operation="CREATE",
            model="Subscription",
            status="SUCCESS",
            tenant_id=current_tenant.id,
            detail=subscription_db.model_dump(),
        )

        return subscription_db
    except IntegrityError as exc:
        session.rollback()

        log_operation(
            operation="CREATE",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail="External id already exists",
            level="warning",
        )

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
) -> list[SubscriptionPublic]:

    log_operation(
        operation="READ",
        model="Subscription",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"offset : {offset} limit: {limit} state: {state}",
    )

    query = (
        select(Subscription)
        .where(Subscription.tenant_id == current_tenant.id)
        .offset(offset)
        .limit(limit)
    )

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

    log_operation(
        operation="READ",
        model="Subscription",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=subscriptions,
    )

    return subscriptions


@router.get("/{subscription_id}")
def read_subscription(
    subscription_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> SubscriptionPublicWithAccountAndCustomFields:

    log_operation(
        operation="READ",
        model="Subscription",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"subscription id {subscription_id}",
    )

    subscription = session.exec(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.tenant_id == current_tenant.id,
        )
    ).first()

    if not subscription:

        log_operation(
            operation="READ",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"subscription id {subscription_id} not found",
            level="warning",
        )

        raise NotFoundError()

    log_operation(
        operation="READ",
        model="Subscription",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=subscription.model_dump(),
    )

    return subscription


@router.get("/external/{external_id}")
def read_subscription_by_external_id(
    external_id: str,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> SubscriptionPublicWithAccountAndCustomFields:

    log_operation(
        operation="READ",
        model="Subscription",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"subscription external id {external_id}",
    )

    subscription = session.exec(
        select(Subscription).where(
            Subscription.external_id == external_id,
            Subscription.tenant_id == current_tenant.id,
        )
    ).first()

    if not subscription:

        log_operation(
            operation="READ",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"subscription with exyernal id {external_id} not found",
            level="warning",
        )

        raise NotFoundError()

    log_operation(
        operation="READ",
        model="Subscription",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=subscription.model_dump(),
    )

    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_200_OK)
def cancel_subscription(
    subscription_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
    end_date: Annotated[date, Query(ge=datetime.now(timezone.utc).date())] = None,
) -> SubscriptionPublic:

    log_operation(
        operation="DELETE",
        model="Subscription",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"subscription id {subscription_id}",
    )

    subscription = session.exec(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.tenant_id == current_tenant.id,
        )
    ).first()

    if not subscription:

        log_operation(
            operation="DELETE",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"subscription id {subscription_id} not found",
            level="warning",
        )

        raise NotFoundError()

    if subscription.state == State.CANCELLED:

        log_operation(
            operation="DELETE",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail="The subscription is cancelled",
            level="warning",
        )

        raise BadRequestError(detail="The subscription is cancelled")

    today = datetime.now(timezone.utc).date()

    state = State.ACTIVE
    if not end_date or end_date == today:
        state = State.CANCELLED

    subscription.state = state
    subscription.end_date = end_date
    session.commit()
    session.refresh(subscription)

    log_operation(
        operation="DELETE",
        model="Subscription",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=f"subscription id {subscription_id}",
    )

    return subscription


@router.put("/{subscription_id}/billing_day")
def update_billing_day(
    subscription_id: int,
    data: UpdateBillingDay,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> SubscriptionPublicWithAccountAndCustomFields:

    log_operation(
        operation="UPDATE",
        model="Subscription",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"subscription id {subscription_id} data {data.model_dump()}",
    )

    subscription = session.exec(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.tenant_id == current_tenant.id,
        )
    ).first()

    if not subscription:

        log_operation(
            operation="UPDATE",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"subscription id {subscription_id} not found",
            level="warning",
        )

        raise NotFoundError()

    if subscription.state == State.CANCELLED:

        log_operation(
            operation="UPDATE",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail="The subscription is cancelled",
            level="warning",
        )

        raise BadRequestError(detail="The subscription is cancelled")

    billing_day = get_billing_day(subscription.billing_period, data.billing_day)

    subscription.billing_day = billing_day

    session.commit()
    session.refresh(subscription)

    log_operation(
        operation="UPDATE",
        model="Subscription",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=subscription.model_dump(),
    )

    return subscription


@router.put("/{subscription_id}/pause")
def pause_subscription(
    subscription_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
    resume: Annotated[date, Query(ge=datetime.now(timezone.utc).date())] = None,
) -> SubscriptionPublicWithAccountAndCustomFields:

    log_operation(
        operation="UPDATE",
        model="Subscription",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"subscription id {subscription_id} resume date {resume}",
    )

    subscription = session.exec(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.tenant_id == current_tenant.id,
        )
    ).first()

    if not subscription:

        log_operation(
            operation="UPDATE",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"subscription id {subscription_id} not found",
            level="warning",
        )

        raise NotFoundError()

    if subscription.state == State.CANCELLED:

        log_operation(
            operation="UPDATE",
            model="Subscription",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail="The subscription is cancelled",
            level="warning",
        )

        raise BadRequestError(detail="The subscription is cancelled")

    today = datetime.now(timezone.utc).date()

    state = State.ACTIVE
    if not resume or resume > today:
        state = State.PAUSED

    subscription.state = state
    subscription.resume_date = resume

    session.commit()
    session.refresh(subscription)

    log_operation(
        operation="UPDATE",
        model="Subscription",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=subscription.model_dump(),
    )

    return subscription
