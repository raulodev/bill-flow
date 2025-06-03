from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles

from app.accounts.api import router as account_router
from app.addresses.api import router as address_router
from app.credit.api import router as credit_router
from app.custom_fields.api import router as custom_fields_router
from app.database.deps import create_db_and_tables, init_db
from app.products.api import router as product_router
from app.subscriptions.api import router as subscription_router
from app.tenant.api import router as tenant_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    init_db()
    yield


app = FastAPI(
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    title="Bill Flow API",
    version="1.0.0",
)


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


app.include_router(account_router, prefix="/v1", tags=["Accounts"])
app.include_router(credit_router, prefix="/v1", tags=["Credits"])
app.include_router(product_router, prefix="/v1", tags=["Products"])
app.include_router(address_router, prefix="/v1", tags=["Addresses"])
app.include_router(custom_fields_router, prefix="/v1", tags=["Custom Fields"])
app.include_router(subscription_router, prefix="/v1", tags=["Subscriptions"])
app.include_router(tenant_router, prefix="/v1", tags=["Tenants"])
