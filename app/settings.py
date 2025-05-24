from decouple import config

DATABASE_URL = config("DATABASE_URL", default="sqlite:///database.db")
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://127.0.0.1:6379")
