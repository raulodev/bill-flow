from typing import Annotated, Tuple

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials
from sqlmodel import Session, SQLModel, create_engine

# pylint: disable=unused-import
from app.database.models import Tenant, User
from app.settings import DATABASE_URL

connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def clear_db_and_tables():
    SQLModel.metadata.drop_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


security = HTTPBasic()

api_key_scheme = APIKeyHeader(
    name="X-BillFlow-ApiKey",
    scheme_name="Bill Flow Api Key",
    description="Tenant Api key",
)

api_secret_scheme = APIKeyHeader(
    name="X-BillFlow-ApiSecret",
    scheme_name="Bill Flow Api Secret",
    description="Tenant Api Secret",
)


ApiKeyDep = Annotated[str, Depends(api_key_scheme)]
ApiSecretDep = Annotated[str, Depends(api_secret_scheme)]
CredentialsDep = Annotated[HTTPBasicCredentials, Depends(security)]
SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user_and_tenant(
    session: SessionDep,
    credentials: CredentialsDep,
    key: ApiKeyDep,
    secret: ApiSecretDep,
) -> Tuple[User, Tenant]:

    # user = session.get(User, 5)
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")
    # if not user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    # return user

    return (None, None)


CurrentUserAndTenant = Annotated[User, Depends(get_current_user_and_tenant)]
