from decouple import config

DATABASE_URL = config("DATABASE_URL", default="sqlite:///database.db")
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://127.0.0.1:6379")
ADMIN_USERNAME = config("ADMIN_USERNAME", default="admin")
ADMIN_PASSWORD = config("ADMIN_PASSWORD", default="password")
TIME_ZONE = config("TIME_ZONE", default="UTC")
LOG_LEVEL = config("LOG_LEVEL", default="INFO")
LOG_FILE_ROTATION = config("LOG_FILE_ROTATION", default="50 MB")
