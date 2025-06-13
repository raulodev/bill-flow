from datetime import date, datetime, timezone
from typing import Annotated, Literal

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.deps import CurrentTenant, SessionDep
from app.database.models import (
    Account,
    PhaseType,
    State,
    Subscription,
    SubscriptionCreate,
    SubscriptionPhase,
    SubscriptionProduct,
    SubscriptionResponse,
    SubscriptionWithAccountAndCustomFields,
    TrialTimeUnit,
    UpdateBillingDay,
)
from app.exceptions import BadRequestError, NotFoundError
from app.logging import log_operation
from app.responses import responses

router = APIRouter(prefix="/subscriptions", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription: SubscriptionCreate, session: SessionDep, current_tenant: CurrentTenant
) -> SubscriptionResponse:

    log_operation(
        "CREATE",
        "Subscription",
        current_tenant.id,
        "PENDING",
        detail=subscription.model_dump(),
    )

    product_ids = [product.product_id for product in subscription.products]

    if len(product_ids) != len(set(product_ids)):

        log_operation(
            "CREATE",
            "Subscription",
            current_tenant.id,
            "FAILED",
            detail="A product cannot be repeated in the same subscription",
        )

        raise BadRequestError(
            detail="A product cannot be repeated in the same subscription"
        )

    if (
        subscription.trial_time_unit not in (TrialTimeUnit.UNLIMITED, None)
        and not subscription.trial_time
    ):

        log_operation(
            "CREATE",
            "Subscription",
            current_tenant.id,
            "FAILED",
            detail="trial_time is required if trial_time_unit is provided",
        )

        raise BadRequestError(
            detail="trial_time is required if trial_time_unit is provided"
        )

    if not session.get(Account, subscription.account_id):

        log_operation(
            "CREATE",
            "Subscription",
            current_tenant.id,
            "FAILED",
            detail=f"account id {subscription.account_id} not found",
        )

        raise BadRequestError(detail="Account not exists")

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

    phases = []

    if subscription.trial_time_unit == TrialTimeUnit.UNLIMITED:

        initial_phase = SubscriptionPhase(
            phase=PhaseType.TRIAL,
            tenant_id=current_tenant.id,
            start_date=subscription_db.start_date,
        )
        phases.append(initial_phase)

    if not subscription.trial_time_unit:

        initial_phase = SubscriptionPhase(
            phase=PhaseType.PAID,
            tenant_id=current_tenant.id,
            start_date=subscription_db.start_date,
        )
        phases.append(initial_phase)

    if subscription.trial_time_unit in (
        TrialTimeUnit.DAYS,
        TrialTimeUnit.WEEKS,
        TrialTimeUnit.MONTHS,
        TrialTimeUnit.YEARS,
    ):

        trial_time_unit_mapping = {
            TrialTimeUnit.DAYS: "days",
            TrialTimeUnit.WEEKS: "weeks",
            TrialTimeUnit.MONTHS: "months",
            TrialTimeUnit.YEARS: "years",
        }

        trial_time_unit = trial_time_unit_mapping.get(
            subscription.trial_time_unit, None
        )

        end_date_initial_phase = subscription_db.start_date + relativedelta(
            **{trial_time_unit: subscription_db.trial_time}
        )

        initial_phase = SubscriptionPhase(
            phase=PhaseType.TRIAL,
            tenant_id=current_tenant.id,
            start_date=subscription_db.start_date,
            end_date=end_date_initial_phase,
        )

        start_date_final_phase = end_date_initial_phase + relativedelta(days=1)

        final_phase = SubscriptionPhase(
            phase=PhaseType.PAID,
            tenant_id=current_tenant.id,
            start_date=start_date_final_phase,
        )

        subscription_db.billing_day = start_date_final_phase.day

        phases = [initial_phase, final_phase]

    subscription_db.phases = phases

    log_operation(
        operation="CREATE",
        model="Subscription",
        tenant_id=current_tenant.id,
        status="PENDING",
        detail=f"phases: {phases}",
    )

    try:
        session.commit()
        session.refresh(subscription_db)

        log_operation(
            operation="CREATE",
            model="Subscription",
            tenant_id=current_tenant.id,
            status="SUCCESS",
            detail=subscription_db.model_dump(),
        )

        return subscription_db
    except IntegrityError as exc:
        session.rollback()

        log_operation(
            operation="CREATE",
            model="Subscription",
            tenant_id=current_tenant.id,
            status="FAILED",
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
) -> list[SubscriptionResponse]:

    log_operation(
        "READ",
        "Subscription",
        current_tenant.id,
        "PENDING",
        detail=f"offset : {offset} limit: {limit} state: {state}",
    )

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

    log_operation(
        "READ",
        "Subscription",
        current_tenant.id,
        "SUCCESS",
        detail=subscriptions,
    )

    return subscriptions


@router.get("/{subscription_id}")
def read_subscription(
    subscription_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> SubscriptionWithAccountAndCustomFields:

    log_operation(
        "READ",
        "Subscription",
        current_tenant.id,
        "PENDING",
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
            "READ",
            "Subscription",
            current_tenant.id,
            "FAILED",
            detail=f"subscription id {subscription_id} not found",
            level="warning",
        )

        raise NotFoundError()

    log_operation(
        "READ",
        "Subscription",
        current_tenant.id,
        "SUCCESS",
        detail=subscription.model_dump(),
    )

    return subscription


@router.get("/external/{external_id}")
def read_subscription_by_external_id(
    external_id: str,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> SubscriptionWithAccountAndCustomFields:

    log_operation(
        "READ",
        "Subscription",
        current_tenant.id,
        "PENDING",
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
            "READ",
            "Subscription",
            current_tenant.id,
            "FAILED",
            detail=f"subscription with exyernal id {external_id} not found",
            level="warning",
        )

        raise NotFoundError()

    log_operation(
        "READ",
        "Subscription",
        current_tenant.id,
        "SUCCESS",
        detail=subscription.model_dump(),
    )

    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_200_OK)
def cancel_subscription(
    subscription_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
    end_date: Annotated[date, Query(ge=datetime.now(timezone.utc).date())] = None,
) -> SubscriptionResponse:

    log_operation(
        operation="DELETE",
        model="Subscription",
        tenant_id=current_tenant.id,
        status="PENDING",
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
            tenant_id=current_tenant.id,
            status="FAILED",
            detail=f"subscription id {subscription_id} not found",
            level="warning",
        )

        raise NotFoundError()

    if subscription.state == State.CANCELLED:

        log_operation(
            operation="DELETE",
            model="Subscription",
            tenant_id=current_tenant.id,
            status="FAILED",
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
        tenant_id=current_tenant.id,
        status="SUCCESS",
        detail=f"subscription id {subscription_id}",
    )

    return subscription


@router.put("/{subscription_id}/billing_day")
def update_billing_day(
    subscription_id: int,
    data: UpdateBillingDay,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> SubscriptionWithAccountAndCustomFields:

    log_operation(
        operation="UPDATE",
        model="Subscription",
        tenant_id=current_tenant.id,
        status="PENDING",
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
            tenant_id=current_tenant.id,
            status="FAILED",
            detail=f"subscription id {subscription_id} not found",
            level="warning",
        )

        raise NotFoundError()

    if subscription.state == State.CANCELLED:

        log_operation(
            operation="UPDATE",
            model="Subscription",
            tenant_id=current_tenant.id,
            status="FAILED",
            detail="The subscription is cancelled",
            level="warning",
        )

        raise BadRequestError(detail="The subscription is cancelled")

    subscription.billing_day = data.billing_day

    session.commit()
    session.refresh(subscription)

    log_operation(
        operation="UPDATE",
        model="Subscription",
        tenant_id=current_tenant.id,
        status="SUCCESS",
        detail=subscription.model_dump(),
    )

    return subscription


@router.put("/{subscription_id}/pause")
def pause_subscription(
    subscription_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
    resume: Annotated[date, Query(ge=datetime.now(timezone.utc).date())] = None,
) -> SubscriptionWithAccountAndCustomFields:

    log_operation(
        operation="UPDATE",
        model="Subscription",
        tenant_id=current_tenant.id,
        status="PENDING",
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
            tenant_id=current_tenant.id,
            status="FAILED",
            detail=f"subscription id {subscription_id} not found",
            level="warning",
        )

        raise NotFoundError()

    if subscription.state == State.CANCELLED:

        log_operation(
            operation="UPDATE",
            model="Subscription",
            tenant_id=current_tenant.id,
            status="FAILED",
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
        tenant_id=current_tenant.id,
        status="SUCCESS",
        detail=subscription.model_dump(),
    )

    return subscription
