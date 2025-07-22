from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.deps import CurrentTenant, SessionDep
from app.database.models import (
    Account,
    AccountBase,
    AccountPublic,
    AccountPublicWithCustomFieldsAndAddress,
)
from app.exceptions import BadRequestError, NotFoundError
from app.logging import log_operation
from app.responses import responses

router = APIRouter(prefix="/accounts", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_account(
    account: AccountBase, session: SessionDep, current_tenant: CurrentTenant
) -> AccountPublic:

    log_operation(
        operation="CREATE",
        model="Account",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=account.model_dump(),
    )

    account_db = Account.model_validate(
        account, update={"tenant_id": current_tenant.id}
    )

    try:
        session.add(account_db)
        session.commit()
        session.refresh(account_db)

        log_operation(
            operation="CREATE",
            model="Account",
            status="SUCCESS",
            tenant_id=current_tenant.id,
            detail=account_db.model_dump(),
        )

        return account_db
    except IntegrityError as exc:
        session.rollback()

        message = (
            "External id already exists"
            if "UNIQUE constraint failed: account.external_id" in str(exc.orig)
            else "Email already exists"
        )

        log_operation(
            operation="CREATE",
            model="Account",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=message,
            level="warning",
        )

        raise BadRequestError(detail=message) from exc


@router.get("/")
def read_accounts(
    session: SessionDep,
    current_tenant: CurrentTenant,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[AccountPublic]:

    log_operation(
        operation="READ",
        model="Account",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"offset: {offset} limit: {limit}",
    )

    accounts = session.exec(
        select(Account)
        .where(Account.tenant_id == current_tenant.id)
        .offset(offset)
        .limit(limit)
    ).all()

    log_operation(
        operation="READ",
        model="Account",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=accounts,
    )

    return accounts


@router.get("/{account_id}")
def read_account(
    account_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> AccountPublicWithCustomFieldsAndAddress:

    log_operation(
        operation="READ",
        model="Account",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"account id {account_id}",
    )

    account = session.exec(
        select(Account).where(
            Account.id == account_id, Account.tenant_id == current_tenant.id
        )
    ).first()

    if not account:

        log_operation(
            operation="READ",
            model="Account",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"account id {account_id} not found",
            level="warning",
        )

        raise NotFoundError()

    log_operation(
        operation="READ",
        model="Account",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=account.model_dump(),
    )

    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
):

    log_operation(
        operation="DELETE",
        model="Account",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"account id {account_id}",
    )

    account = session.exec(
        select(Account).where(
            Account.id == account_id, Account.tenant_id == current_tenant.id
        )
    ).first()

    if not account:

        log_operation(
            operation="DELETE",
            model="Account",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"account id {account_id} not found",
            level="warning",
        )

        raise NotFoundError()

    session.delete(account)
    session.commit()

    log_operation(
        operation="DELETE",
        model="Account",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=f"account id {account_id}",
    )

    return ""


@router.put("/{account_id}")
def update_address(
    account_id: int,
    account: AccountBase,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> AccountPublic:

    log_operation(
        operation="UPDATE",
        model="Account",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"account id {account_id} data {account.model_dump()}",
    )

    account_db = session.exec(
        select(Account).where(
            Account.id == account_id, Account.tenant_id == current_tenant.id
        )
    ).first()

    if not account_db:

        log_operation(
            operation="UPDATE",
            model="Account",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"account id {account_id} not found",
            level="warning",
        )

        raise NotFoundError()

    account_data = account.model_dump(exclude_unset=True)
    account_db.sqlmodel_update(account_data)

    try:
        session.add(account_db)
        session.commit()
        session.refresh(account_db)

        log_operation(
            operation="UPDATE",
            model="Account",
            status="SUCCESS",
            tenant_id=current_tenant.id,
            detail=f"account id {account_id} data {account_db.model_dump()}",
        )

        return account_db
    except IntegrityError as exc:
        session.rollback()

        message = (
            "External id already exists"
            if "UNIQUE constraint failed: account.external_id" in str(exc.orig)
            else "Email already exists"
        )

        log_operation(
            operation="UPDATE",
            model="Account",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=message,
            level="warning",
        )

        raise BadRequestError(detail=message) from exc
