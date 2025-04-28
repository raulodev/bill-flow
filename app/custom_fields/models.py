from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class CustomFieldBase(SQLModel):
    name: str = Field(max_length=64)
    value: str = Field(max_length=255)


class CustomField(CustomFieldBase, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    created: date = Field(default=datetime.now(timezone.utc), nullable=False)
    updated: date = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
