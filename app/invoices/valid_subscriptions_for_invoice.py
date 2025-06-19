from datetime import datetime
from typing import List

from sqlmodel import Session, or_, select

from app.database.deps import engine
from app.database.models import (
    BillingPeriod,
    PhaseType,
    State,
    Subscription,
    SubscriptionPhase,
)
from app.logging import log_operation


def valid_subscriptions_for_invoice(today: datetime) -> List[Subscription]:
    """Return valid subscriptions for invoice

    Args:
        today (datetime)

    Returns:
        List[Subscription]
    """

    with Session(engine) as session:

        log_operation(
            operation="READ", model="Subscriptions", status="PENDING", detail=today
        )

        statement_select = (
            select(Subscription)
            .join(SubscriptionPhase)
            .where(
                SubscriptionPhase.phase == PhaseType.EVERGREEN,
                SubscriptionPhase.start_date <= today.date(),
            )
            .where(
                Subscription.state == State.ACTIVE,
                or_(
                    Subscription.end_date == None, Subscription.end_date > today.date()
                ),
                or_(
                    Subscription.charged_through_date == None,
                    Subscription.charged_through_date < today.date(),
                ),
                or_(
                    Subscription.next_billing_date == None,
                    Subscription.next_billing_date == today.date(),
                ),
            )
        )

        statement = statement_select.where(
            Subscription.billing_day == today.day,
            Subscription.billing_period.in_(
                [
                    BillingPeriod.MONTHLY,
                    BillingPeriod.QUARTERLY,
                    BillingPeriod.BIANNUAL,
                    BillingPeriod.ANNUAL,
                    BillingPeriod.SESQUIENNIAL,
                    BillingPeriod.BIENNIAL,
                    BillingPeriod.TRIENNIAL,
                ]
            ),
        ).union(
            statement_select.where(
                Subscription.billing_period.in_(
                    [
                        BillingPeriod.DAILY,
                        BillingPeriod.WEEKLY,
                        BillingPeriod.BIWEEKLY,
                        BillingPeriod.THIRTY_DAYS,
                        BillingPeriod.THIRTY_ONE_DAYS,
                    ]
                ),
            )
        )

        subscriptions = session.exec(statement).all()

        log_operation(
            operation="READ",
            model="Subscriptions",
            status="SUCCESS",
            detail=f"{len(subscriptions)} subscription(s)",
        )

        return subscriptions
