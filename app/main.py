from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.addresses.api import router as address_router
from app.custom_fields.api import router as custom_fields_router
from app.accounts.api import router as account_router
from app.database.session import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Bill Flow API",
        version="1.0.0",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.include_router(address_router, prefix="/v1", tags=["Addresses"])
app.include_router(custom_fields_router, prefix="/v1", tags=["Custom Fields"])
app.include_router(account_router, prefix="/v1", tags=["Accounts"])
