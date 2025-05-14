from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


class AccountBase(SQLModel):
    first_name: str = Field(max_length=50, index=True)
    last_name: str | None = Field(max_length=50, default=None, index=True)
    email: EmailStr | None = Field(default=None, index=True)
    phone: str | None = Field(max_length=25, default=None, index=True)
    timezone: str | None = Field(max_length=50, default=None)
    external_id: int | None = None


class Account(AccountBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    custom_fields: List["CustomField"] = Relationship(
        back_populates="account", cascade_delete=True
    )
    address: Optional["Address"] = Relationship(
        back_populates="account", cascade_delete=True
    )
    created: date = Field(default=datetime.now(timezone.utc), nullable=False)
    updated: date = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


class AccountWithCustomFieldsAndAddress(AccountBase):
    custom_fields: List["CustomField"] = []
    address: Optional["Address"] = None


class AddressBase(SQLModel):
    street_number1: str | None = Field(max_length=50, default=None, index=True)
    street_number2: str | None = Field(max_length=50, default=None, index=True)
    city: str | None = Field(max_length=50, default=None, index=True)
    postal_code: str | None = Field(max_length=50, default=None, index=True)
    state: str | None = Field(max_length=100, default=None, index=True)
    province: str | None = Field(max_length=100, default=None, index=True)
    country: str | None = Field(max_length=100, default=None, index=True)
    country_id: int | None = None
    account_id: int | None = None


class Address(AddressBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int | None = Field(
        default=None, foreign_key="account.id", ondelete="CASCADE"
    )
    account: Account | None = Relationship(back_populates="address")
    created: date = Field(default=datetime.now(timezone.utc), nullable=False)
    updated: date = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


class AddressWithAccount(AddressBase):
    account: Optional["Account"] = None


class CustomFieldBase(SQLModel):
    name: str = Field(max_length=64, index=True)
    value: str = Field(max_length=255)
    account_id: int | None = None


class CustomField(CustomFieldBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int | None = Field(
        default=None, foreign_key="account.id", ondelete="CASCADE"
    )
    account: Account | None = Relationship(back_populates="custom_fields")
    created: date = Field(default=datetime.now(timezone.utc), nullable=False)
    updated: date = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


class CustomFieldWithAccount(CustomFieldBase):
    account: Optional["Account"] = None


class Category(str, Enum):
    BASE = "BASE"
    ADD_ON = "ADD_ON"


class ProductBase(SQLModel):
    name: str = Field(index=True)
    picture: str | None = None
    external_id: int | None = None
    category: Category = Category.BASE


class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    is_deleted: bool = Field(default=False)
    created: date = Field(default=datetime.now(timezone.utc), nullable=False)
    updated: date = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


class ProductPublic(ProductBase):
    id: int
    created: date
    updated: date
