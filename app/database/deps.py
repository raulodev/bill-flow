from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials
from sqlmodel import Session, SQLModel, create_engine, select

from app.database.models import Tenant, User
from app.security import get_password_hash, verify_password
from app.settings import ADMIN_PASSWORD, ADMIN_USERNAME, DATABASE_URL

connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def clear_db_and_tables():
    SQLModel.metadata.drop_all(engine)


def init_db():
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == ADMIN_USERNAME)).first()

        if not user:

            user = User(
                username=ADMIN_USERNAME,
                is_superuser=True,
                description="Admin",
                password=get_password_hash(ADMIN_PASSWORD),
            )

            session.add(user)
            session.commit()


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


def get_current_user(
    session: SessionDep,
    credentials: CredentialsDep,
) -> User:

    user = session.exec(
        select(User).where(User.username == credentials.username)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_tenant(
    session: SessionDep,
    key: ApiKeyDep,
    secret: ApiSecretDep,
) -> Tenant:

    tenant = session.exec(select(Tenant).where(Tenant.api_key == key)).first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found with this key")

    if not verify_password(secret, tenant.api_secret):
        raise HTTPException(status_code=400, detail="Incorrect tenant credentials")

    return tenant


CurrentTenant = Annotated[User, Depends(get_current_tenant)]
