from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.addresses.api import router as address_router
from app.custom_fields.api import router as custom_fields_router
from app.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


app.include_router(address_router, prefix="/v1", tags=["Addresses"])
app.include_router(custom_fields_router, prefix="/v1", tags=["Custom Fields"])
