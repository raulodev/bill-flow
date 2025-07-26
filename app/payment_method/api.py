from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select, update

from app.database.deps import CurrentTenant, SessionDep
from app.database.models import (
    Account,
    PaymentMethod,
    PaymentMethodBase,
    PaymentMethodPublic,
    PaymentMethodPublicWithAccountAndPlugin,
    Plugin,
)
from app.exceptions import BadRequestError, NotFoundError
from app.logging import log_operation
from app.responses import responses

router = APIRouter(prefix="/paymentMethods", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    payment_method: PaymentMethodBase,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> PaymentMethodPublic:

    log_operation(
        operation="CREATE",
        model="PaymentMethod",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=payment_method.model_dump(),
    )

    if not session.get(Account, payment_method.account_id):

        log_operation(
            operation="CREATE",
            model="PaymentMethod",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"account id {payment_method.account_id} not found",
            level="warning",
        )

        raise BadRequestError(detail="Account not exists")

    if not session.get(Plugin, payment_method.plugin_id):

        log_operation(
            operation="CREATE",
            model="PaymentMethod",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"plugin id {payment_method.plugin_id} not found",
            level="warning",
        )

        raise BadRequestError(detail="Plugin not exists")

    payment_method_db = PaymentMethod.model_validate(
        payment_method, update={"tenant_id": current_tenant.id}
    )

    try:
        session.add(payment_method_db)
        session.commit()
        session.refresh(payment_method_db)

        log_operation(
            operation="CREATE",
            model="PaymentMethod",
            status="SUCCESS",
            tenant_id=current_tenant.id,
            detail=payment_method_db.model_dump(),
        )

        if payment_method_db.is_default:
            session.exec(
                update(PaymentMethod)
                .where(
                    PaymentMethod.account_id == payment_method.account_id,
                    PaymentMethod.id != payment_method_db.id,
                )
                .values(is_default=False)
            )
            session.commit()

        return payment_method_db

    except IntegrityError as exc:
        session.rollback()

        message = "External id already exists"

        log_operation(
            operation="CREATE",
            model="PaymentMethod",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=message,
            level="warning",
        )

        raise BadRequestError(detail=message) from exc


@router.get("/")
def read_payment_methods(
    session: SessionDep,
    current_tenant: CurrentTenant,
    account_id: Annotated[
        int, Query(description="Get payment methods for account")
    ] = None,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[PaymentMethodPublic]:

    log_operation(
        operation="READ",
        model="PaymentMethod",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"account id: {account_id} offset: {offset} limit: {limit}",
    )

    stmt = (
        select(PaymentMethod)
        .where(PaymentMethod.tenant_id == current_tenant.id)
        .offset(offset)
        .limit(limit)
    )

    if account_id:
        stmt = stmt.where(PaymentMethod.account_id == account_id)

    payment_methods = session.exec(stmt).all()

    log_operation(
        operation="READ",
        model="PaymentMethod",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=payment_methods,
    )

    return payment_methods


@router.get("/{payment_method_id}")
def read_payment_method(
    payment_method_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> PaymentMethodPublicWithAccountAndPlugin:

    log_operation(
        operation="READ",
        model="PaymentMethod",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"payment method id {payment_method_id}",
    )

    payment_method = session.exec(
        select(PaymentMethod).where(
            PaymentMethod.id == payment_method_id,
            PaymentMethod.tenant_id == current_tenant.id,
        )
    ).first()

    if not payment_method:

        log_operation(
            operation="READ",
            model="PaymentMethod",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"payment method id {payment_method_id} not found",
            level="warning",
        )

        raise NotFoundError()

    log_operation(
        operation="READ",
        model="PaymentMethod",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=payment_method.model_dump(),
    )

    return payment_method


@router.delete("/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_method(
    payment_method_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
    force: Annotated[
        bool, Query(description="Force default payment method deletion")
    ] = False,
):

    log_operation(
        operation="DELETE",
        model="PaymentMethod",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"payment method id {payment_method_id}",
    )

    payment_method = session.exec(
        select(PaymentMethod).where(
            PaymentMethod.id == payment_method_id,
            PaymentMethod.tenant_id == current_tenant.id,
        )
    ).first()

    if not payment_method:

        log_operation(
            operation="DELETE",
            model="PaymentMethod",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"payment method id {payment_method_id} not found",
            level="warning",
        )

        raise NotFoundError()

    if payment_method.is_default and not force:

        log_operation(
            operation="DELETE",
            model="PaymentMethod",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"payment method id {payment_method_id} is the default method",
            level="warning",
        )

        raise BadRequestError(detail="Cannot delete default payment method")

    session.delete(payment_method)
    session.commit()

    log_operation(
        operation="DELETE",
        model="PaymentMethod",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=f"payment method id {payment_method_id}",
    )

    return ""


@router.put("/{payment_method_id}")
def update_payment_method(
    payment_method_id: int,
    payment_method: PaymentMethodBase,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> PaymentMethodPublic:

    log_operation(
        operation="UPDATE",
        model="PaymentMethod",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"payment method id {payment_method_id} data {payment_method.model_dump()}",
    )

    payment_method_db = session.exec(
        select(PaymentMethod).where(
            PaymentMethod.id == payment_method_id,
            PaymentMethod.tenant_id == current_tenant.id,
        )
    ).first()

    if not payment_method_db:

        log_operation(
            operation="UPDATE",
            model="PaymentMethod",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"payment method id {payment_method_id} not found",
            level="warning",
        )

        raise NotFoundError()

    payment_method_data = payment_method.model_dump(exclude_unset=True)

    payment_method_db.sqlmodel_update(payment_method_data)

    try:

        session.add(payment_method_db)
        session.commit()
        session.refresh(payment_method_db)

        if payment_method_db.is_default:
            session.exec(
                update(PaymentMethod)
                .where(
                    PaymentMethod.account_id == payment_method_db.account_id,
                    PaymentMethod.id != payment_method_db.id,
                )
                .values(is_default=0)
            )
            session.commit()

        log_operation(
            operation="UPDATE",
            model="PaymentMethod",
            status="SUCCESS",
            tenant_id=current_tenant.id,
            detail=f"payment method id {payment_method_id} data {payment_method_db.model_dump()}",
        )

        return payment_method_db

    except IntegrityError as exc:
        session.rollback()

        message = "External id already exists"

        log_operation(
            operation="UPDATE",
            model="PaymentMethod",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=message,
            level="warning",
        )

        raise BadRequestError(detail=message) from exc
