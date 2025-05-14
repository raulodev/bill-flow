from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.models import Account, AccountBase, AccountWithCustomFieldsAndAddress
from app.database.session import SessionDep
from app.exceptions import NotFoundError, BadRequestError

router = APIRouter(prefix="/accounts")


@router.post("/")
async def create_account(account: AccountBase, session: SessionDep) -> Account:
    account_db = Account.model_validate(account)

    try:
        session.add(account_db)
        session.commit()
        session.refresh(account_db)
        return account_db
    except IntegrityError as exc:
        raise BadRequestError(detail="Email already exists") from exc


@router.get("/")
def read_accounts(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Account]:
    accounts = session.exec(select(Account).offset(offset).limit(limit)).all()
    return accounts


@router.get("/{account_id}")
def read_account(
    account_id: int, session: SessionDep
) -> AccountWithCustomFieldsAndAddress:
    account = session.get(Account, account_id)
    if not account:
        raise NotFoundError()
    return account


@router.delete("/{account_id}")
def delete_account(account_id: int, session: SessionDep):
    account = session.get(Account, account_id)
    if not account:
        raise NotFoundError()
    session.delete(account)
    session.commit()
    return {"ok": True}


@router.put("/{account_id}")
def update_address(account_id: int, account: AccountBase, session: SessionDep):
    account_db = session.get(Account, account_id)
    if not account_db:
        raise NotFoundError()
    account_data = account.model_dump(exclude_unset=True)
    account_db.sqlmodel_update(account_data)
    session.add(account_db)
    session.commit()
    session.refresh(account_db)
    return account_db
