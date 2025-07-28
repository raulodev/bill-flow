import datetime
from collections import defaultdict
from typing import List

from celery import Celery
from celery.schedules import crontab
from sqlmodel import Session, select

from app.clock import clock
from app.database.deps import engine
from app.database.models import (
    Invoice,
    InvoiceItem,
    InvoicePaymentStatus,
    Payment,
    PaymentItem,
)
from app.logging import log_operation
from app.plugins.setup import plugin_manager, setup_plugins
from app.services.invoice_service import InvoicesService
from app.settings import CELERY_BROKER_URL, TIME_ZONE

celery_app = Celery("tasks", broker=CELERY_BROKER_URL)

celery_app.conf.timezone = TIME_ZONE


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):

    sender.add_periodic_task(
        crontab(hour=0, minute=0), generate_invoices.s(), name="generate invoices"
    )


@celery_app.task
def generate_subscription_invoice(subscription_id: int):

    with Session(engine) as session:

        invoice_service = InvoicesService(session)

        subscription = invoice_service.is_subscription_valid_for_invoice(
            subscription_id
        )

        if not subscription:
            log_operation(
                operation="CREATE",
                model="Invoice",
                status="FAILED",
                detail=f"subscription id {subscription_id} is not valid for invoice",
                level="warning",
            )
            return

        invoice_id = invoice_service.create_invoice(
            subscription.account_id, [subscription_id], skip_validation=True
        )

        log_operation(
            operation="CREATE",
            model="Invoice",
            status="SUCCESS",
            detail=f"invoice {invoice_id} created for account id {subscription.account_id} subscription id {subscription_id}",
        )


@celery_app.task
def generate_invoices():

    with Session(engine) as session:

        invoice_service = InvoicesService(session)

        subscriptions = invoice_service.valid_subscriptions_for_invoice()

        group_by = defaultdict(list)  # Group by user id
        for s in subscriptions:
            group_by[s.account_id].append(s.id)

        for account_id, subscription_ids in group_by.items():
            invoice_service.create_invoice(
                account_id, subscription_ids, skip_validation=True
            )


@celery_app.task
def process_invoice_payments(invoice_id: int, invoice_items_ids: List[int] = None):

    setup_plugins(install_plugin_deps=False, save_in_db=False)

    with Session(engine) as session:

        invoice = session.get(Invoice, invoice_id)

        if not invoice:

            log_operation(
                operation="READ",
                model="Invoice",
                status="FAILED",
                detail=f"invoice id {invoice_id} not found",
                level="warning",
            )

            return

        if invoice.payment_status in (
            InvoicePaymentStatus.CANCELLED,
            InvoicePaymentStatus.PAID,
        ):

            log_operation(
                operation="CREATE",
                model="Payment",
                status="FAILED",
                detail=f"invoice id {invoice_id} have status {invoice.payment_status.value}",
                level="warning",
            )

            return

    #  Tomar datos de la cuenta para obtener el metodo de pago

    # tenant = invoice.account.tenant

    # # Agregar informacion del tenant (custom fields (poner custom fields))

    # tenant = {"id": tenant.id, "name": tenant.name}

    # # Agregar custom fields
    # account = invoice.account.model_dump(exclude={"created", "updated"})

    # total_amount = sum(item.amount for item in invoice.items)

    # invoice_items = []

    # for item in invoice.items:

    #     if invoice_items_ids and item.id not in invoice_items_ids:
    #         continue

    #     product = item.product
    #     subscription = item.subscription

    #     invoice_items.append(
    #         {
    #             "product": {
    #                 "id": product.id,
    #                 "name": product.name,
    #                 "price": product.price,
    #                 "custom_fields": [
    #                     {"name": field.name, "value": field.value}
    #                     for field in product.custom_fields
    #                 ],
    #             },
    #             "subscription": {
    #                 "id": subscription.id,
    #                 "custom_fields": [
    #                     {"name": field.name, "value": field.value}
    #                     for field in subscription.custom_fields
    #                 ],
    #             },
    #             "id": item.id,
    #             "quantity": item.quantity,
    #             "amount": item.amount,
    #         }
    #     )

    # try:

    #     funct = getattr(plugin_manager.hook, "payment")

    #     results = funct(
    #         invoice_id=invoice_id,
    #         total_amount=total_amount,
    #         invoice_items=invoice_items,
    #         account=account,
    #     )[-1]

    #     print(results)

    # except AttributeError as e:
    #     print(e)
