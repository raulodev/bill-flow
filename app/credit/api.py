from fastapi import APIRouter

from app.database.models import CreditBase, CreditHistory, Account
from app.database.session import SessionDep
from app.exceptions import NotFoundError

router = APIRouter(prefix="/credits")


@router.post("/")
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

    account = session.get(Account, credit.account_id)
    if not account:
        raise NotFoundError(detail="Account not found")

    account.credit -= credit.amount
    session.add(credit_history_db)
    session.commit()
    session.refresh(credit_history_db)

    return credit_history_db
