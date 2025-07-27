from datetime import date
from typing import List

from dateutil.relativedelta import relativedelta
from sqlmodel import Session, select

from app.clock import clock
from app.database.deps import engine
from app.database.models import (
    Account,
    BillingPeriod,
    Invoice,
    InvoiceItem,
    Subscription,
)
from app.invoices.utils import is_subscription_valid_for_invoice
from app.logging import log_operation


def calculate_date_from_billing_period(billing_period: BillingPeriod, _date: date):
    """Calculate the date from the billing period.

    Args:
        billing_period (BillingPeriod):
        _date (date):
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

    return _date + billing_period_mapping.get(billing_period)


def create_invoice(account_id: int, subscription_ids: List[int], skip_validation=False):

    log_operation(
        operation="CREATE",
        model="Invoice",
        status="PENDING",
        detail=f"for account id {account_id} and subscription ids {subscription_ids}",
    )

    now = clock.now(full=True)

    with Session(engine) as session:

        account = session.get(Account, account_id)

        if not account:
            log_operation(
                operation="CREATE",
                model="Invoice",
                status="FAILED",
                detail=f"account id {account_id} not found",
                level="warning",
            )
            return

        subscriptions = session.exec(
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

        session.add(invoice)

        total_amount = 0

        for subs in subscriptions:

            if not skip_validation and not is_subscription_valid_for_invoice(
                now, subs.id
            ):
                log_operation(
                    operation="CREATE",
                    model="Invoice",
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

            subs.charged_through_date = now.date()

            subs.next_billing_date = calculate_date_from_billing_period(
                subs.billing_period, now.date()
            )

            log_operation(
                operation="UPDATE",
                model="Subscription",
                status="SUCCESS",
                detail=f"subscription id {subs.id} updated with charged through date {subs.charged_through_date} and next billing date {subs.next_billing_date}",
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

        session.commit()
        session.refresh(invoice)

        log_operation(
            operation="CREATE",
            model="Invoice",
            status="SUCCESS",
            detail=f"invoice created for account id {account_id} invoice: {invoice.model_dump()}",
        )

        return invoice.id
