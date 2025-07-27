from datetime import datetime
from typing import List

from sqlmodel import Session, or_, select

from app.database.deps import engine
from app.database.models import PhaseType, State, Subscription, SubscriptionPhase
from app.logging import log_operation


def statement(date: datetime):

    return (
        select(Subscription)
        .join(SubscriptionPhase)
        .where(
            SubscriptionPhase.phase == PhaseType.EVERGREEN,
            SubscriptionPhase.start_date <= date.date(),
        )
        .where(
            Subscription.state == State.ACTIVE,
            or_(Subscription.end_date == None, Subscription.end_date > date.date()),
            or_(
                Subscription.charged_through_date == None,
                Subscription.charged_through_date < date.date(),
            ),
            or_(
                Subscription.next_billing_date == None,
                Subscription.next_billing_date == date.date(),
            ),
        )
    )


def valid_subscriptions_for_invoice(
    today: datetime, account_id: int = None
) -> List[Subscription]:
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
        statement_select = statement(today)

        if account_id:
            subscriptions = session.exec(
                statement_select.where(Subscription.account_id == account_id)
            ).all()

        else:
            subscriptions = session.exec(statement_select).all()

        log_operation(
            operation="READ",
            model="Subscriptions",
            status="SUCCESS",
            detail=f"{len(subscriptions)} valid subscription(s)",
        )

        return subscriptions


def is_subscription_valid_for_invoice(date: datetime, subscription_id: int):

    with Session(engine) as session:

        statement_select = statement(date)

        subscription = session.exec(
            statement_select.where(Subscription.id == subscription_id)
        ).first()

        return bool(subscription)
