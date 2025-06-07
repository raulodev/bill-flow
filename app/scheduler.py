from celery import Celery
from celery.schedules import crontab

from app.settings import CELERY_BROKER_URL, TIME_ZONE

app = Celery("tasks", broker=CELERY_BROKER_URL)

app.conf.timezone = TIME_ZONE


@app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):

    # test
    sender.add_periodic_task(10.0, generate_invoices.s(), name="test")

    sender.add_periodic_task(
        crontab(hour=0, minute=0), generate_invoices.s(), name="generate invoices"
    )

    sender.add_periodic_task(
        crontab(hour=0, minute=0), generate_payments.s(), name="generate payments"
    )


@app.task
def generate_invoices():
    # TODO generate invoices
    print("Task executed")


@app.task
def generate_payments():
    # TODO generate payments
    print("Task executed")
