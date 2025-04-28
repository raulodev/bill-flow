from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class AddressBase(SQLModel):
    street_number1: str | None = Field(max_length=50, default=None)
    street_number2: str | None = Field(max_length=50, default=None)
    city: str | None = Field(max_length=50, default=None)
    postal_code: str | None = Field(max_length=50, default=None)
    state: str | None = Field(max_length=100, default=None)
    province: str | None = Field(max_length=100, default=None)
    country: str | None = Field(max_length=100, default=None)
    country_id: int | None = None


class Address(AddressBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created: date = Field(default=datetime.now(timezone.utc), nullable=False)
    updated: date = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
