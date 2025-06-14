from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.deps import CurrentTenant, SessionDep
from app.database.models import Product, ProductBase, ProductWithCustomFields
from app.exceptions import BadRequestError, NotFoundError
from app.logging import log_operation
from app.responses import responses

router = APIRouter(prefix="/products", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductBase, session: SessionDep, current_tenant: CurrentTenant
) -> Product:

    log_operation(
        operation="CREATE",
        model="Product",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=product.model_dump(),
    )

    product_db = Product.model_validate(
        product, update={"tenant_id": current_tenant.id}
    )

    try:
        session.add(product_db)
        session.commit()
        session.refresh(product_db)

        log_operation(
            operation="CREATE",
            model="Product",
            status="SUCCESS",
            tenant_id=current_tenant.id,
            detail=product_db.model_dump(),
        )

        return product_db
    except IntegrityError as exc:
        session.rollback()

        log_operation(
            operation="CREATE",
            model="Product",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail="External id already exists",
            level="warning",
        )

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

    log_operation(
        operation="READ",
        model="Product",
        tenant_id=current_tenant.id,
        status="PENDING",
        detail=f"offset : {offset} limit: {limit} status: {status}",
    )

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

    log_operation(
        operation="READ",
        model="Product",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=products,
    )

    return products


@router.get("/{product_id}")
def read_product(
    product_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> ProductWithCustomFields:

    log_operation(
        operation="READ",
        model="Product",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"product id {product_id}",
    )

    product = session.exec(
        select(Product).where(
            Product.id == product_id, Product.tenant_id == current_tenant.id
        )
    ).first()

    if not product:

        log_operation(
            operation="READ",
            model="Product",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"product id {product_id} not found",
            level="warning",
        )

        raise NotFoundError()

    log_operation(
        operation="READ",
        model="Product",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=product.model_dump(),
    )

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    session: SessionDep,
    current_tenant: CurrentTenant,
):

    log_operation(
        operation="DELETE",
        model="Product",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"product id {product_id}",
    )

    product = session.exec(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == current_tenant.id,
            Product.is_available == True,
        )
    ).first()

    if not product:

        log_operation(
            operation="DELETE",
            model="Product",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"product id {product_id} is not available",
            level="warning",
        )

        raise NotFoundError(detail="Product is not available")

    product.is_available = False
    session.commit()

    log_operation(
        operation="DELETE",
        model="Product",
        status="SUCCESS",
        tenant_id=current_tenant.id,
        detail=f"product id {product_id} is now unavailable",
    )

    return ""


@router.put("/{product_id}")
def update_product(
    product_id: int,
    custom_field: ProductBase,
    session: SessionDep,
    current_tenant: CurrentTenant,
) -> Product:

    log_operation(
        operation="UPDATE",
        model="Product",
        status="PENDING",
        tenant_id=current_tenant.id,
        detail=f"product id {product_id} data {custom_field.model_dump()}",
    )

    product_db = session.exec(
        select(Product).where(
            Product.id == product_id, Product.tenant_id == current_tenant.id
        )
    ).first()

    if not product_db:

        log_operation(
            operation="UPDATE",
            model="Product",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail=f"product id {product_id} not found",
            level="warning",
        )

        raise NotFoundError()

    product_data = custom_field.model_dump(exclude_unset=True)
    product_db.sqlmodel_update(product_data)

    try:
        session.add(product_db)
        session.commit()
        session.refresh(product_db)

        log_operation(
            operation="UPDATE",
            model="Product",
            status="SUCCESS",
            tenant_id=current_tenant.id,
            detail=f"product id {product_id} data {product_db.model_dump()}",
        )

        return product_db

    except IntegrityError as exc:
        session.rollback()

        log_operation(
            operation="CREATE",
            model="Product",
            status="FAILED",
            tenant_id=current_tenant.id,
            detail="External id already exists",
            level="warning",
        )

        raise BadRequestError(detail="External id already exists") from exc
