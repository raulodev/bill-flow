from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlmodel import select

from app.database.deps import CurrentTenant, SessionDep
from app.database.models import (
    Account,
    CustomField,
    CustomFieldBase,
    CustomFieldWithAccountAndProduct,
    Product,
    Subscription,
)
from app.exceptions import NotFoundError, BadRequestError
from app.responses import responses

router = APIRouter(prefix="/customFields", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_custom_field(
    custom_field: CustomFieldBase, session: SessionDep, current_tenant: CurrentTenant
) -> CustomField:

    if custom_field.account_id:

        account = session.exec(
            select(Account).where(
                Account.id == custom_field.account_id,
                Account.tenant_id == current_tenant.id,
            )
        ).first()
        if not account:
            raise BadRequestError(detail="Account not found")

    if custom_field.product_id:

        product = session.exec(
            select(Product).where(
                Product.id == custom_field.product_id,
                Product.tenant_id == current_tenant.id,
            )
        ).first()
        if not product:
            raise BadRequestError(detail="Product not found")

    if custom_field.subscription_id:

        subscription = session.exec(
            select(Subscription).where(
                Subscription.id == custom_field.subscription_id,
                Subscription.tenant_id == current_tenant.id,
            )
        ).first()
        if not subscription:
            raise BadRequestError(detail="Subscription not found")

    custom_field_db = CustomField.model_validate(
        custom_field, update={"tenant_id": current_tenant.id}
    )
    session.add(custom_field_db)
    session.commit()
    session.refresh(custom_field_db)
    return custom_field_db


@router.get("/")
def read_custom_fields(
    session: SessionDep,
    current_tenant: CurrentTenant,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[CustomField]:
    custom_fields = session.exec(
        select(CustomField)
        .where(CustomField.tenant_id == current_tenant.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return custom_fields


@router.get("/{custom_field_id}")
def read_custom_field(
    custom_field_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> CustomFieldWithAccountAndProduct:
    custom_field = session.exec(
        select(CustomField).where(
            CustomField.id == custom_field_id,
            CustomField.tenant_id == current_tenant.id,
        )
    ).first()
    if not custom_field:
        raise NotFoundError()
    return custom_field


@router.delete("/{custom_field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_field(
    custom_field_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
):
    custom_field = session.exec(
        select(CustomField).where(
            CustomField.id == custom_field_id,
            CustomField.tenant_id == current_tenant.id,
        )
    ).first()
    if not custom_field:
        raise NotFoundError()
    session.delete(custom_field)
    session.commit()
    return ""


@router.put("/{custom_field_id}")
def update_custom_field(
    custom_field_id: int,
    custom_field: CustomFieldBase,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> CustomField:

    custom_field_db = session.exec(
        select(CustomField).where(
            CustomField.id == custom_field_id,
            CustomField.tenant_id == current_tenant.id,
        )
    ).first()
    if not custom_field_db:
        raise NotFoundError()
    custom_field_data = custom_field.model_dump(exclude_unset=True)
    custom_field_db.sqlmodel_update(custom_field_data)
    session.add(custom_field_db)
    session.commit()
    session.refresh(custom_field_db)
    return custom_field_db
