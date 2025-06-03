from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.deps import CurrentUser, SessionDep
from app.database.models import Tenant, TenantBase, TenantResponse
from app.exceptions import NotFoundError, BadRequestError
from app.responses import responses
from app.security import get_password_hash

router = APIRouter(prefix="/tenants", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant: TenantBase, session: SessionDep, current_user: CurrentUser
) -> TenantResponse:

    tenant_db = Tenant.model_validate(
        tenant,
        update={
            "api_secret": get_password_hash(tenant.api_secret),
        },
    )
    try:
        session.add(tenant_db)
        session.commit()
        session.refresh(tenant_db)
        return tenant_db
    except IntegrityError as exc:
        raise BadRequestError(detail="External id already exists") from exc


@router.get("/")
def read_tenants(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[TenantResponse]:
    tenants = session.exec(select(Tenant).offset(offset).limit(limit)).all()
    return tenants
