from fastapi import APIRouter, status

from app.database.models import Account, CreditBase, CreditHistory, CreditType
from app.database.session import SessionDep
from app.exceptions import NotFoundError
from app.responses import responses

router = APIRouter(prefix="/credits", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_credit(credit: CreditBase, session: SessionDep) -> CreditHistory:
    credit_history_db = CreditHistory.model_validate(credit)

    account = session.get(Account, credit.account_id)
    if not account:
        raise NotFoundError(detail="Account not found")

    account.credit += credit.amount
    session.add(credit_history_db)
    session.commit()
    session.refresh(credit_history_db)

    return credit_history_db


@router.delete("/")
async def delete_credit(credit: CreditBase, session: SessionDep) -> CreditHistory:
    credit_history_db = CreditHistory.model_validate(credit)
    credit_history_db.type = CreditType.DELETE

    account = session.get(Account, credit.account_id)
    if not account:
        raise NotFoundError(detail="Account not found")

    account.credit -= credit.amount
    session.add(credit_history_db)
    session.commit()
    session.refresh(credit_history_db)

    return credit_history_db
