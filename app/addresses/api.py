from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlmodel import select

from app.database.models import Address, AddressBase, AddressWithAccount
from app.database.session import SessionDep
from app.exceptions import NotFoundError
from app.responses import responses

router = APIRouter(prefix="/addresses", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_address(address: AddressBase, session: SessionDep) -> Address:
    address_db = Address.model_validate(address)
    session.add(address_db)
    session.commit()
    session.refresh(address_db)
    return address_db


@router.get("/")
def read_addresses(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Address]:
    addresses = session.exec(select(Address).offset(offset).limit(limit)).all()
    return addresses


@router.get("/{address_id}")
def read_address(address_id: int, session: SessionDep) -> AddressWithAccount:
    address = session.get(Address, address_id)
    if not address:
        raise NotFoundError()
    return address


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int, session: SessionDep):
    address = session.get(Address, address_id)
    if not address:
        raise NotFoundError()
    session.delete(address)
    session.commit()
    return ""


@router.put("/{address_id}")
def update_address(address_id: int, address: AddressBase, session: SessionDep):
    address_db = session.get(Address, address_id)
    if not address_db:
        raise NotFoundError()
    address_data = address.model_dump(exclude_unset=True)
    address_db.sqlmodel_update(address_data)
    session.add(address_db)
    session.commit()
    session.refresh(address_db)
    return address_db
