from typing import Annotated

from fastapi import APIRouter, Query
from sqlmodel import select

from app.database.models import CustomField, CustomFieldBase
from app.database.session import SessionDep
from app.exceptions import NotFoundError

router = APIRouter(prefix="/customFields")


@router.post("/")
async def create_custom_field(
    custom_field: CustomFieldBase, session: SessionDep
) -> CustomField:
    custom_field_db = CustomField.model_validate(custom_field)
    session.add(custom_field_db)
    session.commit()
    session.refresh(custom_field_db)
    return custom_field_db


@router.get("/")
def read_custom_fields(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[CustomField]:
    custom_fields = session.exec(select(CustomField).offset(offset).limit(limit)).all()
    return custom_fields


@router.get("/{custom_field_id}")
def read_custom_field(custom_field_id: int, session: SessionDep) -> CustomField:
    custom_field = session.get(CustomField, custom_field_id)
    if not custom_field:
        raise NotFoundError()
    return custom_field


@router.delete("/{custom_field_id}")
def delete_custom_field(custom_field_id: int, session: SessionDep):
    custom_field = session.get(CustomField, custom_field_id)
    if not custom_field:
        raise NotFoundError()
    session.delete(custom_field)
    session.commit()
    return {"ok": True}


@router.put("/{custom_field_id}")
def update_custom_field(
    custom_field_id: int, custom_field: CustomFieldBase, session: SessionDep
):
    custom_field_db = session.get(CustomField, custom_field_id)
    if not custom_field_db:
        raise NotFoundError()
    custom_field_data = custom_field.model_dump(exclude_unset=True)
    custom_field_db.sqlmodel_update(custom_field_data)
    session.add(custom_field_db)
    session.commit()
    session.refresh(custom_field_db)
    return custom_field_db
