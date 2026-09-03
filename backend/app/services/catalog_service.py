from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.models.product import Product
from backend.app.models.category import Category


def _product_to_dict(product: Product, category: Optional[Category] = None) -> dict:
    return {
        "id": product.id,
        "product_name": product.product_name,
        "url_slug": product.url_slug,
        "category_id": product.category_id,
        "category_name": category.category_name if category else None,
        "description": product.description,
        "image_url": product.image_url,
        "price": float(product.price),
        "currency": "INR",
        "stock_quantity": product.stock_quantity,
        "available": product.stock_quantity > 0,
        "status": product.status,
    }


def search_catalog(
    db: Session,
    query: Optional[str] = None,
    category_id: Optional[int] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """
    Search the product catalog using database-side filtering.

    The entire catalog is never loaded into memory.
    """

    limit = min(max(limit, 1), 50)
    offset = max(offset, 0)

    products_query = (
        db.query(Product, Category)
        .join(Category, Product.category_id == Category.id)
        .filter(Product.status == "active")
        .filter(Category.status == "active")
    )

    if query:
        search_term = f"%{query.strip()}%"

        products_query = products_query.filter(
            or_(
                Product.product_name.ilike(search_term),
                Product.description.ilike(search_term),
                Category.category_name.ilike(search_term),
            )
        )

    if category_id is not None:
        products_query = products_query.filter(
            Product.category_id == category_id
        )

    if min_price is not None:
        products_query = products_query.filter(
            Product.price >= min_price
        )

    if max_price is not None:
        products_query = products_query.filter(
            Product.price <= max_price
        )

    total = products_query.count()

    rows = (
        products_query
        .order_by(Product.id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    products = [
        _product_to_dict(product, category)
        for product, category in rows
    ]

    return {
        "products": products,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(products) < total,
    }


def lookup_catalog(
    db: Session,
    product_ids: Sequence[int],
) -> list[dict]:
    """
    Retrieve multiple specific products for comparison.
    """

    if not product_ids:
        return []

    # Remove duplicates while preserving order.
    unique_ids = list(dict.fromkeys(product_ids))

    rows = (
        db.query(Product, Category)
        .join(Category, Product.category_id == Category.id)
        .filter(
            Product.id.in_(unique_ids),
            Product.status == "active",
            Category.status == "active",
        )
        .all()
    )

    products_by_id = {
        product.id: _product_to_dict(product, category)
        for product, category in rows
    }

    # Preserve the order requested by the caller.
    return [
        products_by_id[product_id]
        for product_id in unique_ids
        if product_id in products_by_id
    ]


def get_product(
    db: Session,
    product_id: int,
) -> Optional[dict]:
    """
    Retrieve one specific product.
    """

    row = (
        db.query(Product, Category)
        .join(Category, Product.category_id == Category.id)
        .filter(
            Product.id == product_id,
            Product.status == "active",
            Category.status == "active",
        )
        .first()
    )

    if not row:
        return None

    product, category = row

    return _product_to_dict(product, category)