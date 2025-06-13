from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlmodel import select

from app.database.deps import CurrentTenant, SessionDep
from app.database.models import Account, Address, AddressBase, AddressWithAccount
from app.exceptions import BadRequestError, NotFoundError
from app.logging import log_operation
from app.responses import responses

router = APIRouter(prefix="/addresses", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_address(
    address: AddressBase, session: SessionDep, current_tenant: CurrentTenant
) -> Address:

    log_operation(
        operation="CREATE",
        model="Address",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=address.model_dump(),
    )

    if not session.get(Account, address.account_id):

        log_operation(
            operation="CREATE",
            model="Address",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"account id {address.account_id} not found",
            level="warning",
        )

        raise BadRequestError(detail="Account not exists")

    address_db = Address.model_validate(
        address, update={"tenant_id": current_tenant.id}
    )
    session.add(address_db)
    session.commit()
    session.refresh(address_db)

    log_operation(
        operation="CREATE",
        model="Address",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=address_db.model_dump(),
    )

    return address_db


@router.get("/")
def read_addresses(
    session: SessionDep,
    current_tenant: CurrentTenant,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Address]:

    log_operation(
        operation="READ",
        model="Address",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"offset : {offset} limit: {limit}",
    )

    addresses = session.exec(
        select(Address)
        .where(Address.tenant_id == current_tenant.id)
        .offset(offset)
        .limit(limit)
    ).all()

    log_operation(
        operation="READ",
        model="Address",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=addresses,
    )

    return addresses


@router.get("/{address_id}")
def read_address(
    address_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> AddressWithAccount:

    log_operation(
        operation="READ",
        model="Address",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"address id {address_id}",
    )

    address = session.exec(
        select(Address).where(
            Address.id == address_id, Address.tenant_id == current_tenant.id
        )
    ).first()

    if not address:

        log_operation(
            operation="READ",
            model="Address",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"address id {address_id} not found",
            level="warning",
        )

        raise NotFoundError()

    log_operation(
        operation="READ",
        model="Address",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=address.model_dump(),
    )

    return address


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
):

    log_operation(
        operation="DELETE",
        model="Address",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"address id {address_id}",
    )

    address = session.exec(
        select(Address).where(
            Address.id == address_id, Address.tenant_id == current_tenant.id
        )
    ).first()

    if not address:

        log_operation(
            operation="DELETE",
            model="Address",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"address id {address_id} not found",
            level="warning",
        )

        raise NotFoundError()

    session.delete(address)
    session.commit()

    log_operation(
        operation="DELETE",
        model="Address",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=f"address id {address_id}",
    )

    return ""


@router.put("/{address_id}")
def update_address(
    address_id: int,
    address: AddressBase,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> Address:

    log_operation(
        operation="UPDATE",
        model="Address",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"address id {address_id} data {address.model_dump()}",
    )

    address_db = session.exec(
        select(Address).where(
            Address.id == address_id, Address.tenant_id == current_tenant.id
        )
    ).first()

    if not address_db:

        log_operation(
            operation="UPDATE",
            model="Address",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"address id {address_id} not found",
            level="warning",
        )

        raise NotFoundError()

    address_data = address.model_dump(exclude_unset=True)
    address_db.sqlmodel_update(address_data)
    session.add(address_db)
    session.commit()
    session.refresh(address_db)

    log_operation(
        operation="UPDATE",
        model="Address",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=f"account id {address_id} data {address_db.model_dump()}",
    )

    return address_db
