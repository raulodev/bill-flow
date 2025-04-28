from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from app.addresses.models import Address
from app.custom_fields.models import CustomField

connect_args = {"check_same_thread": False}
engine = create_engine("sqlite:///database.db", connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
