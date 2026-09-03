from typing import Any, Optional

from fastmcp import FastMCP

from backend.app.database import SessionLocal
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
        query: Optional[str] = None,
        categories: Optional[list[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """
        Search the product catalog.

        Returns a limited set of matching products rather than
        the entire catalog.
        """

        db = SessionLocal()

        try:
            category_id = None

            # For our first implementation, categories are matched
            # by category name.
            #
            # We will improve this to support hierarchical categories
            # and proper UCP filtering later.

            if categories:
                from backend.app.models.category import Category

                category = (
                    db.query(Category)
                    .filter(
                        Category.category_name.in_(categories),
                        Category.status == "active",
                    )
                    .first()
                )

                if category:
                    category_id = category.id

            result = db_search_catalog(
                db=db,
                query=query,
                category_id=category_id,
                min_price=min_price,
                max_price=max_price,
                limit=limit,
                offset=offset,
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
                },
            }

        finally:
            db.close()

    @mcp.tool()
    def lookup_catalog(
        ids: list[str],
    ) -> dict:
        """
        Retrieve multiple products by their product IDs.
        """

        db = SessionLocal()

        try:
            product_ids = []

            for product_id in ids:
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
        id: str,
    ) -> dict:
        """
        Retrieve complete details for one product.
        """

        db = SessionLocal()

        try:
            try:
                product_id = int(id)
            except ValueError:
                return {
                    "ucp": _ucp_metadata(
                        "dev.ucp.shopping.catalog.lookup"
                    ),
                    "messages": [
                        {
                            "type": "info",
                            "code": "not_found",
                            "content": id,
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
                            "content": id,
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