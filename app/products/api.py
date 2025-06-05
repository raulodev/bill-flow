from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.deps import CurrentTenant, SessionDep
from app.database.models import Product, ProductBase, ProductWithCustomFields
from app.exceptions import BadRequestError, NotFoundError
from app.responses import responses

router = APIRouter(prefix="/products", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductBase, session: SessionDep, current_tenant: CurrentTenant
) -> Product:
    product_db = Product.model_validate(
        product, update={"tenant_id": current_tenant.id}
    )

    try:
        session.add(product_db)
        session.commit()
        session.refresh(product_db)
        return product_db
    except IntegrityError as exc:
        raise BadRequestError(detail="External id already exists") from exc


@router.get("/")
def read_products(
    session: SessionDep,
    current_tenant: CurrentTenant,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    status: Literal[  # pylint: disable=redefined-outer-name
        "ALL", "AVAILABLE", "NO_AVAILABLE"
    ] = "ALL",
) -> list[Product]:

    query = (
        select(Product)
        .where(Product.tenant_id == current_tenant.id)
        .offset(offset)
        .limit(limit)
    )

    if status == "AVAILABLE":
        query = (
            select(Product)
            .where(Product.tenant_id == current_tenant.id, Product.is_available == True)
            .offset(offset)
            .limit(limit)
        )

    elif status == "NO_AVAILABLE":
        query = (
            select(Product)
            .where(
                Product.tenant_id == current_tenant.id, Product.is_available == False
            )
            .offset(offset)
            .limit(limit)
        )

    products = session.exec(query).all()
    return products


@router.get("/{product_id}")
def read_product(
    product_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> ProductWithCustomFields:
    product = session.exec(
        select(Product).where(
            Product.id == product_id, Product.tenant_id == current_tenant.id
        )
    ).first()
    if not product:
        raise NotFoundError()
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
):

    product = session.exec(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == current_tenant.id,
            Product.is_available == True,
        )
    ).first()
    if not product:
        raise NotFoundError()

    product.is_available = False
    session.commit()
    return ""


@router.put("/{product_id}")
def update_product(
    product_id: int,
    custom_field: ProductBase,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> Product:
    product_db = session.exec(
        select(Product).where(
            Product.id == product_id, Product.tenant_id == current_tenant.id
        )
    ).first()
    if not product_db:
        raise NotFoundError()
    product_data = custom_field.model_dump(exclude_unset=True)
    product_db.sqlmodel_update(product_data)
    session.add(product_db)
    session.commit()
    session.refresh(product_db)
    return product_db
