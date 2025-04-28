from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import addresses
from app.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


app.include_router(addresses.router, prefix="/v1", tags=["Addresses"])
