from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

from app.settings import DATABASE_URL

jobstores = {"default": SQLAlchemyJobStore(url=DATABASE_URL)}

scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=utc)


@scheduler.scheduled_job("interval", seconds=5, coalesce=True)
def do_something():
    pass
    # Recoger lista de subscripciones por bcd
    # Generar facturas
    # Hacer intentos de pago
