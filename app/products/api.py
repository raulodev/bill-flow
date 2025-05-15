from typing import Annotated

from fastapi import APIRouter, Query, status
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlmodel import select

from app.database.models import Product, ProductBase, ProductPublic
from app.database.session import SessionDep
from app.exceptions import NotFoundError, BadRequestError
from app.responses import responses

router = APIRouter(prefix="/products", responses=responses)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductBase, session: SessionDep) -> ProductPublic:
    product_db = Product.model_validate(product)

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
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[ProductPublic]:
    products = session.exec(
        select(Product).filter_by(is_deleted=False).offset(offset).limit(limit)
    ).all()
    return products


@router.get("/{product_id}")
def read_product(product_id: int, session: SessionDep) -> ProductPublic:
    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError()
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, session: SessionDep):

    try:
        product = session.exec(
            select(Product).filter_by(id=product_id, is_deleted=False)
        ).one()

        product.is_deleted = True
        session.commit()
        return ""
    except NoResultFound as exc:
        raise NotFoundError() from exc


@router.put("/{product_id}")
def update_product(product_id: int, custom_field: ProductBase, session: SessionDep):
    product_db = session.get(Product, product_id)
    if not product_db:
        raise NotFoundError()
    product_data = custom_field.model_dump(exclude_unset=True)
    product_db.sqlmodel_update(product_data)
    session.add(product_db)
    session.commit()
    session.refresh(product_db)
    return product_db
