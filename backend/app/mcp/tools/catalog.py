from typing import Any, Optional

from fastmcp import FastMCP
from sqlalchemy import func, or_

from backend.app.database import SessionLocal
from backend.app.models.category import Category
from backend.app.services.catalog_service import (
    search_catalog as db_search_catalog,
    lookup_catalog as db_lookup_catalog,
    get_product as db_get_product,
)


UCP_VERSION = "2026-08-25"


def _product_to_ucp(product: dict) -> dict:
    """
    Convert our internal product representation
    into a UCP-compatible product representation.
    """

    return {
        "id": str(product["id"]),
        "handle": product["url_slug"],
        "title": product["product_name"],
        "description": {
            "plain": product["description"] or ""
        },
        "url": f"/products/{product['url_slug']}",
        "price_range": {
            "min": {
                "amount": int(round(product["price"] * 100)),
                "currency": product["currency"],
            },
            "max": {
                "amount": int(round(product["price"] * 100)),
                "currency": product["currency"],
            },
        },
        "media": (
            [
                {
                    "type": "image",
                    "url": product["image_url"],
                }
            ]
            if product.get("image_url")
            else []
        ),
        "availability": {
            "available": product["available"],
            "quantity": product["stock_quantity"],
        },
        "category": product.get("category_name"),
    }


def _ucp_metadata(capability: str) -> dict:
    return {
        "version": UCP_VERSION,
        "capabilities": {
            capability: [
                {
                    "version": UCP_VERSION
                }
            ]
        }
    }


def register_catalog_tools(mcp: FastMCP) -> None:

    @mcp.tool()
    def search_catalog(
        meta: dict,
        catalog: dict,
    ) -> dict:
        """
        Search the product catalog.

        Returns a limited set of matching products rather than
        the entire catalog.
        """

        db = SessionLocal()

        try:
            filters = catalog.get("filters", {})
            price = filters.get("price", {})
            pagination = catalog.get("pagination", {})
            category_ids = None

            # For our first implementation, categories are matched
            # by category name.
            #
            # We will improve this to support hierarchical categories
            # and proper UCP filtering later.

            if filters.get("categories"):
                category_values = {
                    str(value).strip()
                    for value in filters["categories"]
                    if str(value).strip()
                }
                category_ids_from_input = [
                    int(value)
                    for value in category_values
                    if value.isdigit()
                ]
                category_names_from_input = [
                    value.lower()
                    for value in category_values
                    if not value.isdigit()
                ]
                category_conditions = []

                if category_ids_from_input:
                    category_conditions.append(
                        Category.id.in_(category_ids_from_input)
                    )
                if category_names_from_input:
                    category_conditions.extend(
                        [
                            func.lower(Category.category_name).in_(
                                category_names_from_input
                            ),
                            func.lower(Category.url_slug).in_(
                                category_names_from_input
                            ),
                        ]
                    )

                categories = (
                    db.query(Category)
                    .filter(
                        Category.status == "active",
                        or_(*category_conditions),
                    )
                    .all()
                )
                category_ids = [category.id for category in categories]

            result = db_search_catalog(
                db=db,
                query=catalog.get("query"),
                category_ids=category_ids,
                min_price=(price.get("min", 0) / 100 if price.get("min") is not None else None),
                max_price=(price.get("max") / 100 if price.get("max") is not None else None),
                limit=pagination.get("limit", 10),
                offset=pagination.get("offset", 0),
                cursor=pagination.get("cursor"),
            )

            products = [
                _product_to_ucp(product)
                for product in result["products"]
            ]

            return {
                "ucp": _ucp_metadata(
                    "dev.ucp.shopping.catalog.search"
                ),
                "products": products,
                "pagination": {
                    "has_next_page": result["has_more"],
                    "total_count": result["total"],
                    "cursor": result["next_cursor"],
                },
            }

        finally:
            db.close()

    @mcp.tool()
    def list_categories(meta: Optional[dict] = None) -> dict:
        """List all active product categories available for shopping."""

        del meta

        db = SessionLocal()

        try:
            categories = (
                db.query(Category)
                .filter(Category.status == "active")
                .order_by(Category.category_name, Category.id)
                .all()
            )

            return {
                "categories": [
                    {
                        "id": str(category.id),
                        "name": category.category_name,
                        "slug": category.url_slug,
                    }
                    for category in categories
                ]
            }
        finally:
            db.close()

    @mcp.tool()
    def lookup_catalog(
        meta: dict,
        catalog: dict,
    ) -> dict:
        """
        Retrieve multiple products by their product IDs.
        """

        db = SessionLocal()

        try:
            product_ids = []

            for product_id in catalog.get("ids", []):
                try:
                    product_ids.append(int(product_id))
                except ValueError:
                    continue

            products = db_lookup_catalog(
                db=db,
                product_ids=product_ids,
            )

            return {
                "ucp": _ucp_metadata(
                    "dev.ucp.shopping.catalog.lookup"
                ),
                "products": [
                    _product_to_ucp(product)
                    for product in products
                ],
            }

        finally:
            db.close()

    @mcp.tool()
    def get_product(
        meta: dict,
        catalog: dict,
    ) -> dict:
        """
        Retrieve complete details for one product.
        """

        db = SessionLocal()

        try:
            try:
                product_id = int(catalog["id"])
            except ValueError:
                return {
                    "ucp": _ucp_metadata(
                        "dev.ucp.shopping.catalog.lookup"
                    ),
                    "messages": [
                        {
                            "type": "info",
                            "code": "not_found",
                        "content": catalog.get("id"),
                        }
                    ],
                }

            product = db_get_product(
                db=db,
                product_id=product_id,
            )

            if not product:
                return {
                    "ucp": _ucp_metadata(
                        "dev.ucp.shopping.catalog.lookup"
                    ),
                    "messages": [
                        {
                            "type": "info",
                            "code": "not_found",
                        "content": catalog.get("id"),
                        }
                    ],
                }

            return {
                "ucp": _ucp_metadata(
                    "dev.ucp.shopping.catalog.lookup"
                ),
                "product": _product_to_ucp(product),
            }

        finally:
            db.close()
