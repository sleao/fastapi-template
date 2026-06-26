"""Catalog HTTP routes — ``/products/*``.

Thin routes: parse the request → build a domain ``Command`` (writes) or query
params (reads) → call the service-layer handler with the injected UoW →
serialise via ``schemas.py``. No business logic, no ``HTTPException`` for domain
conditions, no SQLAlchemy.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from api.catalog.domain.commands import (
    CreateProduct,
    DiscontinueProduct,
    UpdateProduct,
)
from api.catalog.entrypoints.schemas import (
    CreateProductRequest,
    ProductListResponse,
    ProductResponse,
    UpdateProductRequest,
)
from api.catalog.service_layer import commands, queries
from api.shared.entrypoints.schemas import PaginationParams
from api.shared.infrastructure.auth import CurrentUserDep
from api.shared.infrastructure.dependencies import UnitOfWorkDep

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: CreateProductRequest,
    unit_of_work: UnitOfWorkDep,
    _user: CurrentUserDep,
) -> ProductResponse:
    command = CreateProduct(
        name=body.name,
        sku=body.sku,
        price_cents=body.price_cents,
        description=body.description,
    )
    product = await commands.create_product(command, unit_of_work)
    return ProductResponse.from_domain(product)


@router.get("", response_model=ProductListResponse)
async def list_products(
    unit_of_work: UnitOfWorkDep,
    _user: CurrentUserDep,
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, max_length=255),
) -> ProductListResponse:
    products, total = await queries.list_products(
        unit_of_work,
        search=search,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return ProductListResponse.from_page(
        products, page=pagination.page, per_page=pagination.per_page, total=total
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    unit_of_work: UnitOfWorkDep,
    _user: CurrentUserDep,
) -> ProductResponse:
    product = await queries.get_product(product_id, unit_of_work)
    return ProductResponse.from_domain(product)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    body: UpdateProductRequest,
    unit_of_work: UnitOfWorkDep,
    _user: CurrentUserDep,
) -> ProductResponse:
    command = UpdateProduct(
        product_id=product_id,
        name=body.name,
        price_cents=body.price_cents,
        description=body.description,
        fields_set=frozenset(body.model_fields_set),
    )
    product = await commands.update_product(command, unit_of_work)
    return ProductResponse.from_domain(product)


@router.post("/{product_id}/discontinue", response_model=ProductResponse)
async def discontinue_product(
    product_id: UUID,
    unit_of_work: UnitOfWorkDep,
    _user: CurrentUserDep,
) -> ProductResponse:
    product = await commands.discontinue_product(
        DiscontinueProduct(product_id=product_id), unit_of_work
    )
    return ProductResponse.from_domain(product)
