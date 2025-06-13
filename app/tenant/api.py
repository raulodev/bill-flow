from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.deps import CurrentUser, SessionDep
from app.database.models import Tenant, TenantBase, TenantResponse, TenantUpdate
from app.exceptions import BadRequestError, NotFoundError
from app.logging import log_operation
from app.responses import responses
from app.security import get_password_hash

router = APIRouter(prefix="/tenants", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant: TenantBase, session: SessionDep, current_user: CurrentUser
) -> TenantResponse:

    log_operation(
        operation="CREATE",
        model="Tenant",
        status="PENDING",
        user_id=current_user.id,
        detail=tenant.model_dump(exclude={"api_secret"}),
    )

    tenant_db = Tenant.model_validate(
        tenant,
        update={
            "api_secret": get_password_hash(tenant.api_secret),
            "user_id": current_user.id,
        },
    )
    try:
        session.add(tenant_db)
        session.commit()
        session.refresh(tenant_db)

        log_operation(
            operation="CREATE",
            model="Tenant",
            status="SUCCESS",
            user_id=current_user.id,
            detail=tenant.model_dump(exclude={"api_secret"}),
        )

        return tenant_db
    except IntegrityError as exc:
        session.rollback()

        message = (
            "Api key already exists"
            if "UNIQUE constraint failed: tenant.api_key" in str(exc.orig)
            else "External id already exists"
        )

        log_operation(
            operation="CREATE",
            model="Tenant",
            status="FAILED",
            user_id=current_user.id,
            detail=message,
        )

        raise BadRequestError(detail=message) from exc


@router.get("/")
def read_tenants(
    session: SessionDep,
    current_user: CurrentUser,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[TenantResponse]:

    log_operation(
        operation="READ",
        model="Tenant",
        status="PENDING",
        user_id=current_user.id,
        detail=f"offset : {offset} limit: {limit}",
    )

    tenants = session.exec(select(Tenant).offset(offset).limit(limit)).all()

    log_operation(
        operation="READ",
        model="Tenant",
        status="SUCCESS",
        user_id=current_user.id,
        detail=f"offset : {offset} limit: {limit}",
    )

    return tenants


@router.put("/{tenant_id}")
def update_tenants(
    tenant_id: int,
    tenant: TenantUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> TenantResponse:

    log_operation(
        operation="UPDATE",
        model="Tenant",
        status="PENDING",
        user_id=current_user.id,
        detail=f"tenant id {tenant_id} data {tenant.model_dump(exclude={'api_secret'})}",
    )

    tenant_db = session.exec(select(Tenant).where(Tenant.id == tenant_id)).first()

    if not tenant_db:

        log_operation(
            operation="UPDATE",
            model="Tenant",
            status="FAILED",
            user_id=current_user.id,
            detail=f"tenant id {tenant_id} not found",
        )

        raise NotFoundError()

    tenant_data = tenant.model_dump(exclude_unset=True)

    if tenant_data.get("api_secret"):
        tenant_data["api_secret"] = get_password_hash(tenant.api_secret)

    tenant_db.sqlmodel_update(tenant_data)

    try:
        session.add(tenant_db)
        session.commit()
        session.refresh(tenant_db)

        log_operation(
            operation="UPDATE",
            model="Tenant",
            status="SUCCESS",
            user_id=current_user.id,
            detail=tenant_db.model_dump(exclude={"api_secret"}),
        )

        return tenant_db
    except IntegrityError as exc:
        session.rollback()

        message = (
            "Api key already exists"
            if "UNIQUE constraint failed: tenant.api_key" in str(exc.orig)
            else "External id already exists"
        )

        log_operation(
            operation="UPDATE",
            model="Tenant",
            status="FAILED",
            user_id=current_user.id,
            detail=message,
        )

        raise BadRequestError(detail=message) from exc
