from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlmodel import select

from app.database.deps import CurrentTenant, SessionDep
from app.database.models import Account, Address, AddressBase, AddressWithAccount
from app.exceptions import BadRequestError, NotFoundError
from app.responses import responses

router = APIRouter(prefix="/addresses", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_address(
    address: AddressBase, session: SessionDep, current_tenant: CurrentTenant
) -> Address:

    if not session.get(Account, address.account_id):
        raise BadRequestError(detail="Account not exists")

    address_db = Address.model_validate(
        address, update={"tenant_id": current_tenant.id}
    )
    session.add(address_db)
    session.commit()
    session.refresh(address_db)
    return address_db


@router.get("/")
def read_addresses(
    session: SessionDep,
    current_tenant: CurrentTenant,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Address]:
    addresses = session.exec(
        select(Address)
        .where(Address.tenant_id == current_tenant.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return addresses


@router.get("/{address_id}")
def read_address(
    address_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> AddressWithAccount:
    address = session.exec(
        select(Address).where(
            Address.id == address_id, Address.tenant_id == current_tenant.id
        )
    ).first()

    if not address:
        raise NotFoundError()
    return address


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
):
    address = session.exec(
        select(Address).where(
            Address.id == address_id, Address.tenant_id == current_tenant.id
        )
    ).first()
    if not address:
        raise NotFoundError()
    session.delete(address)
    session.commit()
    return ""


@router.put("/{address_id}")
def update_address(
    address_id: int,
    address: AddressBase,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> Address:
    address_db = session.exec(
        select(Address).where(
            Address.id == address_id, Address.tenant_id == current_tenant.id
        )
    ).first()
    if not address_db:
        raise NotFoundError()
    address_data = address.model_dump(exclude_unset=True)
    address_db.sqlmodel_update(address_data)
    session.add(address_db)
    session.commit()
    session.refresh(address_db)
    return address_db
