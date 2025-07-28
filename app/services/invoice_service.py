from datetime import date, datetime
from typing import List, Union

from dateutil.relativedelta import relativedelta
from sqlmodel import Session, or_, select

from app.clock import clock
from app.database.models import (
    Account,
    BillingPeriod,
    Invoice,
    InvoiceItem,
    PhaseType,
    State,
    Subscription,
    SubscriptionPhase,
)
from app.logging import log_operation


def subscription_filter_statement(current_date: Union[datetime, date]):
    """Return a SQLAlchemy select statement to filter subscriptions based on the current date."""

    if isinstance(current_date, datetime):
        current_date = current_date.date()

    return (
        # pylint: disable=singleton-comparison
        select(Subscription)
        .join(SubscriptionPhase)
        .where(
            SubscriptionPhase.phase == PhaseType.EVERGREEN,
            SubscriptionPhase.start_date <= current_date,
        )
        .where(
            Subscription.state == State.ACTIVE,
            or_(
                Subscription.end_date == None,
                Subscription.end_date > current_date,
            ),
            or_(
                Subscription.charged_through_date == None,
                Subscription.charged_through_date < current_date,
            ),
            or_(
                Subscription.next_billing_date == None,
                Subscription.next_billing_date == current_date,
            ),
        )
    )


class InvoicesService:
    def __init__(self, session: Session, current_date: datetime = clock.now()):
        self.session = session
        self.current_date = current_date

    def create_invoice(
        self, account_id: int, subscription_ids: List[int], skip_validation=False
    ):
        """Create an invoice for the given account and subscription IDs.


        Args:
            account_id (int): The ID of the account to create the invoice for.
            subscription_ids (List[int]): A list of subscription IDs to include in the invoice.
            skip_validation (bool, optional): Whether to skip validation
                of subscriptions. Defaults to False.


        Returns:
            int: The ID of the created invoice.
        """
        log_operation(
            operation="CREATE",
            model="Invoice",
            status="PENDING",
            detail=f"for account id {account_id} and subscription ids {subscription_ids}",
        )

        account = self.session.get(Account, account_id)

        if not account:
            log_operation(
                operation="CREATE",
                model="Invoice",
                status="FAILED",
                detail=f"account id {account_id} not found",
                level="warning",
            )
            return None

        subscriptions = self.session.exec(
            # pylint: disable=no-member
            select(Subscription).where(
                Subscription.id.in_(subscription_ids),
                Subscription.account_id == account_id,
            )
        ).all()

        invoice = Invoice(
            tenant_id=account.tenant_id,
            account_id=account.id,
        )

        self.session.add(invoice)

        total_amount = 0

        for subs in subscriptions:

            if not skip_validation and not self.is_subscription_valid_for_invoice(
                subs.id
            ):
                log_operation(
                    operation="CREATE",
                    model="InvoiceItem",
                    status="FAILED",
                    detail=f"subscription id {subs.id} is not valid for invoice",
                    level="warning",
                )
                continue

            for subs_product in subs.products:
                amount = 0

                if subs_product.product.is_available:
                    amount = subs_product.product.price * subs_product.quantity

                invoice_item = InvoiceItem(
                    subscription_id=subs.id,
                    product_id=subs_product.product_id,
                    quantity=subs_product.quantity,
                    amount=amount,
                    tenant_id=account.tenant_id,
                    account_id=account_id,
                )

                invoice.items.append(invoice_item)

                log_operation(
                    operation="CREATE",
                    model="InvoiceItem",
                    status="SUCCESS",
                    detail=invoice_item.model_dump(),
                )

                total_amount += amount

            subs.charged_through_date = self.current_date

            subs.next_billing_date = self.determine_next_billing_date(
                subs.billing_period
            )

            log_operation(
                operation="UPDATE",
                model="Subscription",
                status="SUCCESS",
                detail=(
                    f"subscription id {subs.id} updated with charged through "
                    f"date {subs.charged_through_date} and next"
                    f" billing date {subs.next_billing_date}"
                ),
            )

        if account.credit < 0:
            log_operation(
                operation="UPDATE",
                model="Account",
                status="SUCCESS",
                detail=f"account id {account_id} has insufficient credit {account.credit}",
                level="warning",
            )

        account.credit -= total_amount

        self.session.commit()
        self.session.refresh(invoice)

        log_operation(
            operation="CREATE",
            model="Invoice",
            status="SUCCESS",
            detail=f"invoice created for account id {account_id} invoice: {invoice.model_dump()}",
        )

        return invoice.id

    def determine_next_billing_date(self, billing_period: BillingPeriod):
        """Determine the next billing date based on the billing period.

        Args:
            billing_period (BillingPeriod):
        """

        billing_period_mapping = {
            BillingPeriod.DAILY: relativedelta(days=1),
            BillingPeriod.WEEKLY: relativedelta(weeks=1),
            BillingPeriod.BIWEEKLY: relativedelta(days=15),
            BillingPeriod.THIRTY_DAYS: relativedelta(days=30),
            BillingPeriod.THIRTY_ONE_DAYS: relativedelta(days=31),
            BillingPeriod.MONTHLY: relativedelta(months=1),
            BillingPeriod.QUARTERLY: relativedelta(months=3),
            BillingPeriod.BIANNUAL: relativedelta(months=6),
            BillingPeriod.ANNUAL: relativedelta(years=1),
            BillingPeriod.SESQUIENNIAL: relativedelta(months=18),
            BillingPeriod.BIENNIAL: relativedelta(years=2),
            BillingPeriod.TRIENNIAL: relativedelta(years=3),
        }

        return self.current_date + billing_period_mapping.get(billing_period)

    def valid_subscriptions_for_invoice(
        self, account_id: int = None
    ) -> List[Subscription]:
        """Return valid subscriptions for invoice

        Args:
            account_id (int, optional): The ID of the account to filter subscriptions for. Defaults to None.

        Returns:
            List[Subscription]
        """

        log_operation(
            operation="READ",
            model="Subscriptions",
            status="PENDING",
            detail=self.current_date,
        )
        statement_select = subscription_filter_statement(self.current_date)

        if account_id:
            subscriptions = self.session.exec(
                statement_select.where(Subscription.account_id == account_id)
            ).all()

        else:
            subscriptions = self.session.exec(statement_select).all()

        log_operation(
            operation="READ",
            model="Subscriptions",
            status="SUCCESS",
            detail=f"{len(subscriptions)} valid subscription(s) for invoice found",
        )

        return subscriptions

    def is_subscription_valid_for_invoice(self, subscription_id: int):
        """
        Checks if a subscription with the given ID is valid for invoice
        generation on the current date.

        Args:
            subscription_id (int): The ID of the subscription to validate.

        Returns:
            Subscription: The subscription if it is valid, otherwise None.
        """

        statement_select = subscription_filter_statement(self.current_date)

        subscription = self.session.exec(
            statement_select.where(Subscription.id == subscription_id)
        ).first()

        return subscription
