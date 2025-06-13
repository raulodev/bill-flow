from fastapi import APIRouter, status
from sqlmodel import select

from app.database.deps import CurrentTenant, SessionDep
from app.database.models import Account, CreditBase, CreditHistory, CreditType
from app.exceptions import NotFoundError
from app.logging import log_operation
from app.responses import responses

router = APIRouter(prefix="/credits", responses=responses)


@router.post("/add", status_code=status.HTTP_201_CREATED)
async def add_credit(
    credit: CreditBase, session: SessionDep, current_tenant: CurrentTenant
) -> CreditHistory:

    log_operation(
        "CREATE",
        "Credit",
        current_tenant.id,
        "PENDING",
        detail=credit.model_dump(),
    )

    account = session.exec(
        select(Account).where(
            Account.id == credit.account_id, Account.tenant_id == current_tenant.id
        )
    ).first()

    if not account:

        log_operation(
            operation="CREATE",
            model="Credit",
            tenant_id=current_tenant.id,
            status="FAILED",
            detail=f"account id {credit.account_id} not found",
            level="warning",
        )

        raise NotFoundError(detail="Account not found")

    credit_history_db = CreditHistory.model_validate(
        credit, update={"tenant_id": current_tenant.id}
    )

    account.credit += credit.amount
    session.add(credit_history_db)
    session.commit()
    session.refresh(credit_history_db)

    log_operation(
        operation="CREATE",
        model="Credit",
        tenant_id=current_tenant.id,
        status="SUCCESS",
    )

    return credit_history_db


@router.post("/delete")
async def delete_credit(
    credit: CreditBase, session: SessionDep, current_tenant: CurrentTenant
) -> CreditHistory:

    log_operation(
        "DELETE",
        "Credit",
        current_tenant.id,
        "PENDING",
        detail=credit.model_dump(),
    )

    account = session.exec(
        select(Account).where(
            Account.id == credit.account_id, Account.tenant_id == current_tenant.id
        )
    ).first()

    if not account:

        log_operation(
            operation="DELETE",
            model="Credit",
            tenant_id=current_tenant.id,
            status="FAILED",
            detail=f"account id {credit.account_id} not found",
            level="warning",
        )

        raise NotFoundError(detail="Account not found")

    credit_history_db = CreditHistory.model_validate(
        credit, update={"tenant_id": current_tenant.id}
    )
    credit_history_db.type = CreditType.DELETE

    account.credit -= credit.amount
    session.add(credit_history_db)
    session.commit()
    session.refresh(credit_history_db)

    log_operation(
        operation="DELETE",
        model="Credit",
        tenant_id=current_tenant.id,
        status="SUCCESS",
    )

    return credit_history_db
