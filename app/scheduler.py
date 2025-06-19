import datetime

from celery import Celery
from celery.schedules import crontab

from app.invoices.create import create_invoice
from app.invoices.valid_subscriptions_for_invoice import valid_subscriptions_for_invoice
from app.settings import CELERY_BROKER_URL, TIME_ZONE

app = Celery("tasks", broker=CELERY_BROKER_URL)

app.conf.timezone = TIME_ZONE


@app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):

    sender.add_periodic_task(
        crontab(hour=0, minute=0), generate_invoices.s(), name="generate invoices"
    )


@app.task
def generate_invoices():

    today = datetime.datetime.now(datetime.timezone.utc).today().replace(microsecond=0)

    subscriptions = valid_subscriptions_for_invoice(today)

    for subscription in subscriptions:
        create_invoice(subscription.id)
